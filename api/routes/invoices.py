from fastapi import APIRouter, HTTPException, Form, Request
import os
import platform
import subprocess
import sys
from datetime import datetime
from api.database_manager import db
from api.admin_pin import require_admin_pin
from api.license_guard import require_valid_license
from utils.app_paths import get_app_data_dir

router = APIRouter()


def _invoice_number(visit_id, visit_date):
    if hasattr(visit_date, "strftime"):
        date_part = visit_date.strftime("%Y%m%d")
    else:
        try:
            date_part = datetime.fromisoformat(str(visit_date)).strftime("%Y%m%d")
        except Exception:
            date_part = datetime.now().strftime("%Y%m%d")
    return f"INV-{date_part}-{int(visit_id):05d}"


def _visit_original_price_and_unit(visit_data, app_settings):
    service_name = (visit_data.service_name or "Bekam").strip()
    quantity = max(1, int(visit_data.point_count or 1))
    unit_label = "titik" if service_name.lower() == "bekam" else "layanan"
    unit_price = float(app_settings.get_price_per_point() or 0)

    if getattr(visit_data, "service_id", None):
        service = db.get_service(visit_data.service_id)
        if service:
            unit_label = service.unit_label or unit_label
            unit_price = float(service.price_per_unit or 0)

    stored_final_price = float(getattr(visit_data, "final_price", None) or visit_data.price or 0)
    stored_original_price = float(getattr(visit_data, "original_price", None) or 0)
    stored_discount_amount = float(getattr(visit_data, "discount_amount", None) or 0)
    original_price = stored_original_price or (unit_price * quantity)
    final_price = stored_final_price
    if original_price <= 0 or original_price < final_price:
        original_price = final_price
    discount_amount = stored_discount_amount if stored_discount_amount > 0 else (max(0, original_price - final_price) if visit_data.discount_applied else 0)
    return original_price, discount_amount, unit_label

def _parse_date_filter(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.fromisoformat(f"{text}T00:00:00")


def _invoice_file_exists(path):
    if not str(path or "").strip():
        return False
    try:
        _resolve_invoice_path(path)
        return True
    except HTTPException:
        return False


def _parse_datetime_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _pdf_status(invoice_status, invoice_path, file_exists, pdf_generated_at=None, payment_updated_at=None):
    if str(invoice_status or "active").strip().lower() == "void":
        return "void"
    if not str(invoice_path or "").strip():
        return "not_generated"
    if not file_exists:
        return "missing"
    generated_at = _parse_datetime_value(pdf_generated_at)
    updated_at = _parse_datetime_value(payment_updated_at)
    if updated_at and (not generated_at or updated_at > generated_at):
        return "stale"
    return "fresh"


@router.get("/invoices")
def get_invoices(
    period: str = "all",
    page: int = 1,
    page_size: int = 100,
    search: str = "",
    date_from: str = "",
    date_to: str = "",
):
    try:
        from sqlalchemy.orm import joinedload
        from sqlalchemy import func
        from database import Visit, HerbalTransaction
        
        invoices_data = []
        page = max(1, int(page or 1))
        page_size = min(250, max(10, int(page_size or 100)))
        fetch_limit = page * page_size
        search_term = str(search or "").strip().lower()
        parsed_from = _parse_date_filter(date_from)
        parsed_to = _parse_date_filter(date_to)
        with db.Session() as session:
            visit_query = session.query(Visit).options(joinedload(Visit.patient))
            herbal_query = session.query(HerbalTransaction).options(joinedload(HerbalTransaction.herbal))
            
            # ── Invoice Filter Period Logic ──
            if period != "all":
                start_date = db._period_start_date(period)

                if start_date:
                    visit_query = visit_query.filter(Visit.date >= start_date)
                    herbal_query = herbal_query.filter(HerbalTransaction.date >= start_date)
            if parsed_from:
                visit_query = visit_query.filter(Visit.date >= parsed_from)
                herbal_query = herbal_query.filter(HerbalTransaction.date >= parsed_from)
            if parsed_to:
                visit_query = visit_query.filter(Visit.date <= parsed_to)
                herbal_query = herbal_query.filter(HerbalTransaction.date <= parsed_to)
            herbal_query = herbal_query.filter(
                HerbalTransaction.visit_id.is_(None),
                HerbalTransaction.transaction_type == "sale",
            )
            
            # Fetch bounded windows to prevent massive RAM usage, then merge/sort/paginate.
            visits = visit_query.order_by(Visit.date.desc()).limit(fetch_limit).all()
            herbal_trans = herbal_query.order_by(HerbalTransaction.date.desc()).limit(fetch_limit).all()
            visit_ids = [v.id for v in visits]
            herbal_totals = {}
            if visit_ids:
                herbal_totals = dict(
                    session.query(
                        HerbalTransaction.visit_id,
                        func.coalesce(func.sum(HerbalTransaction.total_price), 0),
                    )
                    .filter(
                        HerbalTransaction.visit_id.in_(visit_ids),
                        HerbalTransaction.transaction_type == "sale",
                    )
                    .group_by(HerbalTransaction.visit_id)
                    .all()
                )
            
            combined = []
            
            for v in visits:
                combined.append({
                    "id": f"v_{v.id}",
                    "date_obj": v.date,
                    "sort_id": int(v.id or 0),
                    "name": v.patient.name if v.patient else "Unknown",
                    "price": float(v.price or 0) + float(herbal_totals.get(v.id, 0) or 0),
                    "path": v.invoice_path,
                    "invoice_status": getattr(v, "invoice_status", None) or "active",
                    "void_reason": getattr(v, "void_reason", None),
                    "pdf_generated_at": getattr(v, "pdf_generated_at", None),
                    "payment_updated_at": getattr(v, "payment_updated_at", None),
                    "payment_status": getattr(v, "payment_status", None) or "paid",
                    "payment_method": getattr(v, "payment_method", None) or "cash",
                    "amount_paid": getattr(v, "amount_paid", None),
                    "paid_at": getattr(v, "paid_at", None),
                    "payment_provider": getattr(v, "payment_provider", None) or "manual",
                    "payment_reference": getattr(v, "payment_reference", None) or "",
                    "payment_url": getattr(v, "payment_url", None) or "",
                    "payment_channel": getattr(v, "payment_channel", None) or "",
                    "payment_expired_at": getattr(v, "payment_expired_at", None),
                    "payment_gateway_status": getattr(v, "payment_gateway_status", None) or "",
                })
                
            herbal_groups = {}
            for h in herbal_trans:
                group_key = h.sale_group_id or f"legacy-{h.id}"
                entry = herbal_groups.setdefault(group_key, {
                    "id": f"hg_{h.sale_group_id}" if h.sale_group_id else f"h_{h.id}",
                    "date_obj": h.date,
                    "sort_id": int(h.id or 0),
                    "names": [],
                    "price": 0,
                    "path": h.invoice_path if hasattr(h, "invoice_path") else None,
                    "invoice_status": getattr(h, "invoice_status", None) or "active",
                    "void_reason": getattr(h, "void_reason", None),
                    "pdf_generated_at": getattr(h, "pdf_generated_at", None),
                    "payment_updated_at": getattr(h, "payment_updated_at", None),
                    "payment_status": getattr(h, "payment_status", None) or "paid",
                    "payment_method": getattr(h, "payment_method", None) or "cash",
                    "amount_paid": getattr(h, "amount_paid", None),
                    "paid_at": getattr(h, "paid_at", None),
                    "payment_provider": getattr(h, "payment_provider", None) or "manual",
                    "payment_reference": getattr(h, "payment_reference", None) or "",
                    "payment_url": getattr(h, "payment_url", None) or "",
                    "payment_channel": getattr(h, "payment_channel", None) or "",
                    "payment_expired_at": getattr(h, "payment_expired_at", None),
                    "payment_gateway_status": getattr(h, "payment_gateway_status", None) or "",
                })
                if h.date and (not entry["date_obj"] or h.date > entry["date_obj"]):
                    entry["date_obj"] = h.date
                entry["sort_id"] = max(int(entry.get("sort_id") or 0), int(h.id or 0))
                if h.invoice_path:
                    entry["path"] = h.invoice_path
                if getattr(h, "pdf_generated_at", None) and (not entry.get("pdf_generated_at") or h.pdf_generated_at > entry.get("pdf_generated_at")):
                    entry["pdf_generated_at"] = h.pdf_generated_at
                if getattr(h, "payment_updated_at", None) and (not entry.get("payment_updated_at") or h.payment_updated_at > entry.get("payment_updated_at")):
                    entry["payment_updated_at"] = h.payment_updated_at
                if (getattr(h, "invoice_status", None) or "active") == "void":
                    entry["invoice_status"] = "void"
                    entry["void_reason"] = getattr(h, "void_reason", None)
                if getattr(h, "payment_reference", None):
                    entry.update({
                        "payment_status": getattr(h, "payment_status", None) or "paid",
                        "payment_method": getattr(h, "payment_method", None) or "cash",
                        "amount_paid": getattr(h, "amount_paid", None),
                        "paid_at": getattr(h, "paid_at", None),
                        "payment_provider": getattr(h, "payment_provider", None) or "manual",
                        "payment_reference": getattr(h, "payment_reference", None) or "",
                        "payment_url": getattr(h, "payment_url", None) or "",
                        "payment_channel": getattr(h, "payment_channel", None) or "",
                        "payment_expired_at": getattr(h, "payment_expired_at", None),
                        "payment_gateway_status": getattr(h, "payment_gateway_status", None) or "",
                    })
                entry["names"].append(f"{h.herbal.name} x{h.quantity}" if h.herbal else f"Herbal x{h.quantity}")
                entry["price"] += float(h.total_price or 0)

            for h in herbal_groups.values():
                combined.append({
                    "id": h["id"],
                    "date_obj": h["date_obj"],
                    "sort_id": h.get("sort_id") or 0,
                    "name": "Herbal: " + ", ".join(h["names"]),
                    "price": h["price"],
                    "path": h["path"],
                    "invoice_status": h["invoice_status"],
                    "void_reason": h["void_reason"],
                    "pdf_generated_at": h.get("pdf_generated_at"),
                    "payment_updated_at": h.get("payment_updated_at"),
                    "payment_status": h.get("payment_status", "paid"),
                    "payment_method": h.get("payment_method", "cash"),
                    "amount_paid": h.get("amount_paid"),
                    "paid_at": h.get("paid_at"),
                    "payment_provider": h.get("payment_provider", "manual") or "manual",
                    "payment_reference": h.get("payment_reference", ""),
                    "payment_url": h.get("payment_url", ""),
                    "payment_channel": h.get("payment_channel", ""),
                    "payment_expired_at": h.get("payment_expired_at"),
                    "payment_gateway_status": h.get("payment_gateway_status", ""),
                })
            if search_term:
                combined = [
                    item for item in combined
                    if search_term in str(item.get("name", "")).lower()
                ]
                
            # Helper sorting function robust against strange date formats
            def safe_date_val(d):
                if hasattr(d, 'timestamp'):
                    return d.timestamp()
                try:
                    # fallback for string stored dates
                    return datetime.fromisoformat(str(d)).timestamp()
                except Exception:
                    return 0
                    
            combined.sort(key=lambda x: (safe_date_val(x['date_obj']), int(x.get("sort_id") or 0)), reverse=True)
            
            combined = combined[(page - 1) * page_size:page * page_size]

            # Fix #5: Batch file-exists check — kumpulkan path unik dulu, cek sekaligus
            unique_paths = {item.get("path") for item in combined if item.get("path")}
            path_exists_cache = {p: _invoice_file_exists(p) for p in unique_paths}

            for item in combined:
                file_exists = path_exists_cache.get(item.get("path"), False)
                d_obj = item['date_obj']
                if hasattr(d_obj, 'strftime'):
                    date_str = d_obj.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(d_obj)

                invoices_data.append({
                    "id": item['id'],
                    "date": date_str,
                    "name": item['name'],
                    "price": item['price'],
                    "path": item['path'],
                    "file_exists": file_exists,
                    "invoice_status": item.get("invoice_status", "active"),
                    "void_reason": item.get("void_reason"),
                    "pdf_generated_at": item.get("pdf_generated_at").isoformat(timespec="seconds") if hasattr(item.get("pdf_generated_at"), "isoformat") else item.get("pdf_generated_at"),
                    "payment_updated_at": item.get("payment_updated_at").isoformat(timespec="seconds") if hasattr(item.get("payment_updated_at"), "isoformat") else item.get("payment_updated_at"),
                    "pdf_status": _pdf_status(item.get("invoice_status"), item.get("path"), file_exists, item.get("pdf_generated_at"), item.get("payment_updated_at")),
                    "payment_status": item.get("payment_status") or "paid",
                    "payment_method": item.get("payment_method") or "cash",
                    "amount_paid": item.get("amount_paid"),
                    "paid_at": item.get("paid_at"),
                    "payment_provider": item.get("payment_provider") or "manual",
                    "payment_reference": item.get("payment_reference") or "",
                    "payment_url": item.get("payment_url") or "",
                    "payment_channel": item.get("payment_channel") or "",
                    "payment_expired_at": item.get("payment_expired_at"),
                    "payment_gateway_status": item.get("payment_gateway_status") or "",
                })

        return invoices_data
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat daftar invoice. Coba lagi atau hubungi admin.")

@router.post("/generate_invoice")
async def generate_invoice_endpoint(visit_id: int = Form(...)):
    try:
        require_valid_license()
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        from helpers.invoice_helper import InvoiceHelper

        # Get visit from DB
        visit_data, patient_name, therapist_name = db.get_visit_for_invoice(visit_id)
        if not visit_data:
            raise HTTPException(status_code=404, detail="Kunjungan tidak ditemukan.")
        if getattr(visit_data, "invoice_status", "active") == "void":
            raise HTTPException(status_code=400, detail="Invoice kunjungan sudah dibatalkan.")

        s = AppSettings()
        settings = s.get_clinic_profile()

        existing_invoice_path = getattr(visit_data, "invoice_path", None)
        date_str = visit_data.date.strftime("%d/%m/%Y %H:%M") if hasattr(visit_data.date, 'strftime') else str(visit_data.date)
        invoice_number = _invoice_number(visit_id, visit_data.date)
        original_price, discount_amount, unit_label = _visit_original_price_and_unit(visit_data, s)
        herbal_items = db.get_herbal_transactions_for_visit(visit_id)

        # Output ke folder invoices/ di direktori data aplikasi (APPDATA bila exe)
        from utils.app_paths import get_app_data_dir
        invoices_dir = os.path.join(get_app_data_dir(), "invoices")

        helper = InvoiceHelper(output_dir=invoices_dir)
        invoice_path = helper.generate_invoice(
            patient_name=patient_name,
            date=date_str,
            points=visit_data.point_count,
            price=float(visit_data.price or 0),
            therapist_name=therapist_name or "--",
            custom_settings=settings,
            discount_rule_name=visit_data.discount_rule_name,
            service_name=visit_data.service_name or "Bekam",
            invoice_number=invoice_number,
            is_free_visit=bool(visit_data.is_free_visit),
            free_visit_reason=visit_data.free_visit_reason,
            unit_label=unit_label,
            original_price=original_price,
            discount_amount=discount_amount,
            herbal_items=herbal_items,
            payment_method=getattr(visit_data, "payment_method", None),
            payment_status=getattr(visit_data, "payment_status", None),
            payment_provider=getattr(visit_data, "payment_provider", None),
            payment_reference=getattr(visit_data, "payment_reference", None),
            payment_url=getattr(visit_data, "payment_url", None),
        )

        # Update database with the newly generated path
        db.update_visit_invoice_path(visit_id, invoice_path)
        audit_action = "invoice_pdf_refreshed" if existing_invoice_path else "invoice_generated"
        audit_message = "PDF invoice kunjungan diperbarui." if existing_invoice_path else "Invoice kunjungan dibuat."
        db.log_audit(audit_action, "visit", visit_id, audit_message, {
            "invoice_number": invoice_number,
            "patient_name": patient_name,
            "service_name": visit_data.service_name or "Bekam",
            "therapist_name": therapist_name or "--",
            "quantity": visit_data.point_count,
            "unit_label": unit_label,
            "price": float(visit_data.price or 0),
            "discount_amount": discount_amount,
            "is_free_visit": bool(visit_data.is_free_visit),
            "payment_status": getattr(visit_data, "payment_status", None),
            "payment_method": getattr(visit_data, "payment_method", None),
            "previous_path": existing_invoice_path,
            "new_path": invoice_path,
        })

        return {
            "status": "success",
            "message": "PDF invoice berhasil diperbarui." if existing_invoice_path else "Invoice berhasil dibuat.",
            "path": invoice_path,
            "invoice_number": invoice_number,
            "refreshed": bool(existing_invoice_path),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal membuat invoice. Tutup lalu buka aplikasi, atau hubungi admin.")


@router.post("/generate_herbal_invoice")
async def generate_herbal_invoice_endpoint(transaction_id: int = Form(None), sale_group_id: str = Form("")):
    try:
        require_valid_license()
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        from helpers.invoice_helper import InvoiceHelper

        normalized_group_id = str(sale_group_id or "").strip()
        transaction = (
            db.get_herbal_sale_group_for_invoice(normalized_group_id)
            if normalized_group_id
            else db.get_herbal_transaction_for_invoice(transaction_id)
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaksi herbal tidak ditemukan.")
        if transaction.get("invoice_status") == "void":
            raise HTTPException(status_code=400, detail="Invoice herbal sudah dibatalkan.")

        existing_invoice_path = transaction.get("invoice_path")
        s = AppSettings()
        settings = s.get_clinic_profile()
        invoices_dir = os.path.join(get_app_data_dir(), "invoices")
        if normalized_group_id:
            invoice_number = f"HBL-{normalized_group_id}"
        else:
            invoice_number = _invoice_number(transaction_id, transaction["date"]).replace("INV-", "HBL-")

        helper = InvoiceHelper(output_dir=invoices_dir)
        invoice_path = helper.generate_herbal_invoice(
            buyer_name=transaction["buyer_name"],
            date=transaction["date"],
            items=transaction["items"],
            total=transaction["total"],
            custom_settings=settings,
            invoice_number=invoice_number,
            note=transaction["note"],
            payment_method=transaction.get("payment_method"),
            payment_status=transaction.get("payment_status"),
            payment_provider=transaction.get("payment_provider"),
            payment_reference=transaction.get("payment_reference"),
            payment_url=transaction.get("payment_url"),
        )

        if normalized_group_id:
            db.update_herbal_group_invoice_path(normalized_group_id, invoice_path)
        else:
            db.update_herbal_invoice_path(transaction_id, invoice_path)
        audit_action = "herbal_invoice_pdf_refreshed" if existing_invoice_path else "herbal_invoice_generated"
        audit_message = "PDF invoice herbal diperbarui." if existing_invoice_path else "Invoice herbal dibuat."
        db.log_audit(
            audit_action,
            "herbal_invoice",
            normalized_group_id or transaction_id,
            audit_message,
            {
                "invoice_number": invoice_number,
                "buyer_name": transaction["buyer_name"],
                "item_count": len(transaction["items"]),
                "total": transaction["total"],
                "payment_status": transaction.get("payment_status"),
                "payment_method": transaction.get("payment_method"),
                "previous_path": existing_invoice_path,
                "new_path": invoice_path,
            },
        )

        return {
            "status": "success",
            "message": "PDF invoice herbal berhasil diperbarui." if existing_invoice_path else "Invoice herbal berhasil dibuat.",
            "path": invoice_path,
            "invoice_number": invoice_number,
            "refreshed": bool(existing_invoice_path),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal membuat invoice herbal. Tutup lalu buka aplikasi, atau hubungi admin.")


@router.post("/void_invoice")
async def void_invoice_endpoint(
    request: Request,
    invoice_type: str = Form(...),
    visit_id: int = Form(None),
    transaction_id: int = Form(None),
    sale_group_id: str = Form(""),
    reason: str = Form(...),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        normalized_type = str(invoice_type or "").strip()
        normalized_reason = str(reason or "").strip()
        if not normalized_reason:
            raise HTTPException(status_code=400, detail="Alasan void invoice wajib diisi.")
        if normalized_type == "visit":
            db.void_visit_invoice(visit_id, normalized_reason)
        elif normalized_type == "herbal":
            db.void_herbal_invoice(transaction_id=transaction_id, sale_group_id=sale_group_id, reason=normalized_reason)
        else:
            raise HTTPException(status_code=400, detail="Tipe invoice tidak valid.")
        return {"status": "success", "message": "Invoice berhasil dibatalkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update_invoice_payment")
async def update_invoice_payment_endpoint(
    request: Request,
    invoice_type: str = Form(...),
    visit_id: int = Form(None),
    transaction_id: int = Form(None),
    sale_group_id: str = Form(""),
    payment_status: str = Form(...),
    payment_method: str = Form(...),
    amount_paid: float = Form(None),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        result = db.update_invoice_manual_payment(
            invoice_type=invoice_type,
            visit_id=visit_id,
            transaction_id=transaction_id,
            sale_group_id=sale_group_id,
            payment_status=payment_status,
            payment_method=payment_method,
            amount_paid=amount_paid,
        )
        return {
            "status": "success",
            "message": "Status pembayaran berhasil diperbarui.",
            "payment": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _allowed_invoice_roots():
    app_data_dir = os.path.abspath(get_app_data_dir())
    project_root = _project_root()
    return [
        os.path.realpath(os.path.join(app_data_dir, "invoices")),
        os.path.realpath(os.path.join(app_data_dir, "exports")),
        os.path.realpath(os.path.join(project_root, "invoices")),
    ]


def _is_within_allowed_roots(path, roots):
    real_path = os.path.realpath(os.path.abspath(path))
    for root in roots:
        try:
            if os.path.commonpath([real_path, root]) == root:
                return True
        except ValueError:
            continue
    return False


def _resolve_invoice_path(path: str) -> str:
    if not str(path or "").strip():
        raise HTTPException(status_code=400, detail="Path invoice tidak boleh kosong.")

    normalized = str(path).strip().replace("\\", os.sep).replace("/", os.sep)
    roots = _allowed_invoice_roots()
    app_data_dir = os.path.abspath(get_app_data_dir())
    project_root = _project_root()

    if os.path.isabs(normalized):
        candidates = [normalized]
    else:
        candidates = [
            os.path.join(app_data_dir, normalized),
            os.path.join(project_root, normalized),
            os.path.join(app_data_dir, "invoices", normalized),
        ]

    safe_candidates = [os.path.realpath(os.path.abspath(candidate)) for candidate in candidates if _is_within_allowed_roots(candidate, roots)]
    if not safe_candidates:
        raise HTTPException(status_code=403, detail="Akses file invoice di luar folder aplikasi tidak diizinkan.")

    for candidate in safe_candidates:
        if os.path.exists(candidate):
            return candidate

    raise HTTPException(status_code=404, detail=f"File invoice tidak ditemukan: {safe_candidates[0]}")


def _open_file_with_default_app(resolved_path: str):
    if hasattr(os, "startfile"):
        os.startfile(resolved_path)
        return

    system_name = platform.system().lower()
    command = ["open", resolved_path] if system_name == "darwin" else ["xdg-open", resolved_path]
    subprocess.run(command, check=False)


def _try_open_file_with_default_app(resolved_path: str):
    try:
        _open_file_with_default_app(resolved_path)
        return True, ""
    except Exception as e:
        return False, str(e)


@router.get("/open_invoice")
def open_invoice(path: str):
    try:
        resolved_path = _resolve_invoice_path(path)

        _open_file_with_default_app(resolved_path)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/print_invoice")
def print_invoice(path: str):
    try:
        require_valid_license()
        resolved_path = _resolve_invoice_path(path)

        if not os.path.exists(resolved_path):
            raise HTTPException(status_code=404, detail=f"File tidak ditemukan: {resolved_path}")

        # Coba print dengan win32api (Windows)
        try:
            import win32api
            import win32print
            win32api.ShellExecute(
                0,
                "print",
                resolved_path,
                f'/d:"{win32print.GetDefaultPrinter()}"',
                ".",
                0
            )
            return {"status": "success", "message": "Proses cetak ke printer default berhasil dimulai."}
        except ImportError:
            # Fallback: buka file dengan PDF viewer default
            opened, open_error = _try_open_file_with_default_app(resolved_path)
            message = "File dibuka di PDF viewer untuk dicetak." if opened else f"Silent print tidak tersedia. PDF tetap dibuat: {open_error}"
            return {"status": "success", "message": message}
        except Exception as win_err:
            opened, open_error = _try_open_file_with_default_app(resolved_path)
            if opened:
                return {"status": "success", "message": f"Dibuka via viewer (printer error: {win_err})."}
            return {"status": "success", "message": f"Silent print gagal dan viewer tidak bisa dibuka. PDF tetap tersedia. Error: {win_err}; {open_error}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
