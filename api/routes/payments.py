from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func

from api.database_manager import db
from helpers.payment_gateway import (
    GATEWAY_METHODS,
    PROVIDER_UNAVAILABLE_MESSAGE,
    VALID_PAYMENT_METHODS,
    check_payment_status,
    create_payment,
    get_payment_provider_info,
    is_available_gateway_provider,
    map_gateway_status,
)

router = APIRouter(prefix="/payments")

FINAL_PAYMENT_STATUSES = {"paid", "failed", "expired", "void"}


def _require_app_token_header(request: Request):
    if not str(request.headers.get("X-App-Token", "")).strip():
        raise HTTPException(status_code=403, detail="Token aplikasi wajib dikirim.")


def _normalize_source_type(value):
    source_type = str(value or "").strip().lower()
    if source_type not in {"visit", "herbal"}:
        raise HTTPException(status_code=400, detail="Tipe sumber pembayaran tidak valid.")
    return source_type


def _normalize_method(value):
    method = str(value or "").strip().lower()
    if method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Metode pembayaran tidak valid.")
    if method not in GATEWAY_METHODS:
        raise HTTPException(status_code=400, detail="Metode pembayaran ini memakai jalur manual.")
    return method


def _normalize_provider(value):
    provider = str(value or "").strip().lower()
    try:
        info = get_payment_provider_info(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail="Provider ini belum didukung. Gunakan Pembayaran Internal atau Midtrans.")
    if info["provider_id"] == "manual":
        raise HTTPException(status_code=400, detail="Provider ini memakai jalur manual.")
    if not is_available_gateway_provider(provider):
        raise HTTPException(status_code=400, detail=PROVIDER_UNAVAILABLE_MESSAGE)
    return provider


def _resolve_requested_provider(value):
    provider = str(value or "").strip().lower()
    if provider:
        return provider
    from settings import AppSettings

    return AppSettings().get_payment_gateway_default_provider()


def _safe_gateway_error(exc):
    message = str(exc or "").strip()
    safe_messages = {
        "Midtrans server key belum diisi.",
        "Midtrans production belum diaktifkan. Gunakan sandbox terlebih dahulu.",
        "Metode pembayaran ini tidak didukung Midtrans sandbox.",
        "Metode pembayaran ini belum mendukung link pembayaran otomatis.",
        "Provider pembayaran ini belum aktif.",
        "Provider pembayaran belum didukung.",
        PROVIDER_UNAVAILABLE_MESSAGE,
    }
    if message in safe_messages:
        return message
    if "midtrans" in message.lower():
        return "Midtrans belum bisa memproses pembayaran. Periksa pengaturan pembayaran online dan coba lagi."
    return message[:180] if message else "Link pembayaran belum bisa diproses."


def _serialize_payment(row, source_type, source_id, amount):
    return {
        "source_type": source_type,
        "source_id": source_id,
        "amount": int(float(amount or 0)),
        "payment_status": getattr(row, "payment_status", None) or "paid",
        "payment_method": getattr(row, "payment_method", None) or "cash",
        "amount_paid": int(float(getattr(row, "amount_paid", 0) or 0)),
        "paid_at": getattr(row, "paid_at", None),
        "payment_provider": getattr(row, "payment_provider", None) or "manual",
        "payment_reference": getattr(row, "payment_reference", None) or "",
        "payment_url": getattr(row, "payment_url", None) or "",
        "payment_channel": getattr(row, "payment_channel", None) or "",
        "payment_expired_at": getattr(row, "payment_expired_at", None),
        "payment_gateway_status": getattr(row, "payment_gateway_status", None) or "",
    }


def _apply_gateway_status_update(session, rows, source_type, source_id, normalized_reference, old_status, gateway_status, payment_status, amount):
    if str(old_status or "").strip().lower() in FINAL_PAYMENT_STATUSES:
        return {
            "ignored": True,
            "reason": "payment_already_final",
            "amount_paid": int(float(getattr(rows[0], "amount_paid", 0) or 0)),
        }

    paid_at = datetime.now().isoformat() if payment_status == "paid" else None
    amount_paid = amount if payment_status == "paid" else 0
    now = datetime.now()
    try:
        for row in rows:
            row.payment_gateway_status = gateway_status
            row.payment_status = payment_status
            row.amount_paid = amount_paid
            row.paid_at = paid_at
            row.payment_updated_at = now
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal update status pembayaran: {str(e)[:100]}")

    if old_status != payment_status:
        db.log_audit("gateway_status_changed", source_type, source_id, "Status gateway berubah.", {
            "payment_reference": normalized_reference,
            "old_status": old_status,
            "new_status": payment_status,
            "gateway_status": gateway_status,
        })
    if payment_status == "paid":
        db.log_audit("gateway_payment_paid", source_type, source_id, "Pembayaran gateway menjadi paid.", {
            "payment_reference": normalized_reference,
            "amount_paid": amount_paid,
        })
    elif payment_status in {"expired", "failed"}:
        db.log_audit(f"gateway_payment_{payment_status}", source_type, source_id, f"Pembayaran gateway {payment_status}.", {
            "payment_reference": normalized_reference,
        })

    return {"ignored": False, "reason": "updated", "amount_paid": amount_paid}


def _find_payment_source(session, source_type, source_id):
    from database import HerbalTransaction, Visit

    if source_type == "visit":
        row = session.get(Visit, int(source_id))
        if not row:
            raise HTTPException(status_code=404, detail="Kunjungan tidak ditemukan.")
        herbal_total = (
            session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0))
            .filter(
                HerbalTransaction.visit_id == row.id,
                HerbalTransaction.transaction_type == "sale",
            )
            .scalar()
        )
        return row, [row], int(float(row.price or 0) + float(herbal_total or 0)), str(row.id)

    source_text = str(source_id or "").strip()
    if source_text.startswith("group:"):
        source_text = source_text[6:]
    query = session.query(HerbalTransaction).filter(
        HerbalTransaction.transaction_type == "sale",
        HerbalTransaction.visit_id.is_(None),
    )
    if source_text.isdigit():
        first = query.filter(HerbalTransaction.id == int(source_text)).first()
        if not first:
            raise HTTPException(status_code=404, detail="Transaksi herbal tidak ditemukan.")
        rows = (
            query.filter(HerbalTransaction.sale_group_id == first.sale_group_id)
            .order_by(HerbalTransaction.id.asc())
            .all()
            if first.sale_group_id
            else [first]
        )
    else:
        rows = query.filter(HerbalTransaction.sale_group_id == source_text).order_by(HerbalTransaction.id.asc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Transaksi herbal tidak ditemukan.")
    amount = sum(float(row.total_price or 0) for row in rows)
    canonical_id = rows[0].sale_group_id or str(rows[0].id)
    return rows[0], rows, int(amount), canonical_id


@router.post("/gateway/create")
@router.post("/gateway/mock/create")
async def create_gateway_payment(
    request: Request,
    provider: str = Form(""),
    source_type: str = Form(...),
    source_id: str = Form(...),
    amount: int = Form(None),
    payment_method: str = Form(None),
    method: str = Form(None),
):
    _require_app_token_header(request)
    normalized_provider = _normalize_provider(_resolve_requested_provider(provider))
    normalized_type = _normalize_source_type(source_type)
    normalized_method = _normalize_method(payment_method or method)

    with db.Session() as session:
        primary, rows, db_amount, canonical_id = _find_payment_source(session, normalized_type, source_id)
        requested_amount = int(float(amount if amount is not None else db_amount))
        if db_amount <= 0:
            raise HTTPException(status_code=400, detail="Total pembayaran harus lebih dari 0.")
        if requested_amount != db_amount:
            raise HTTPException(status_code=400, detail="Total pembayaran tidak sesuai dengan transaksi.")

        try:
            payment = create_payment(normalized_provider, normalized_type, canonical_id, db_amount, normalized_method)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=_safe_gateway_error(exc)) from exc
        for row in rows:
            row.payment_provider = payment["payment_provider"]
            row.payment_reference = payment["payment_reference"]
            row.payment_url = payment["payment_url"]
            row.payment_channel = payment["payment_channel"]
            row.payment_expired_at = payment["payment_expired_at"]
            row.payment_gateway_status = payment["payment_gateway_status"]
            row.payment_status = payment["payment_status"]
            row.payment_method = payment["payment_method"]
            row.amount_paid = 0
            row.paid_at = None
        session.commit()
        result = _serialize_payment(primary, normalized_type, canonical_id, db_amount)

    db.log_audit("gateway_payment_created", normalized_type, canonical_id, "Gateway payment dibuat.", result)
    return {"status": "success", "payment": result}


@router.get("/gateway/status/{payment_reference}")
@router.get("/gateway/mock/status/{payment_reference}")
def get_gateway_status(request: Request, payment_reference: str, simulate: str = Query("")):
    _require_app_token_header(request)
    normalized_reference = str(payment_reference or "").strip()
    if not normalized_reference:
        raise HTTPException(status_code=400, detail="Referensi pembayaran wajib diisi.")

    from database import HerbalTransaction, Visit

    with db.Session() as session:
        visit = session.query(Visit).filter(Visit.payment_reference == normalized_reference).first()
        rows = []
        source_type = "visit"
        source_id = ""
        amount = 0
        primary = visit
        if visit:
            source_id = str(visit.id)
            herbal_total = (
                session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0))
                .filter(HerbalTransaction.visit_id == visit.id, HerbalTransaction.transaction_type == "sale")
                .scalar()
            )
            amount = int(float(getattr(visit, "final_price", None) or visit.price or 0) + float(herbal_total or 0))
            rows = [visit]
        else:
            rows = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.payment_reference == normalized_reference)
                .order_by(HerbalTransaction.id.asc())
                .all()
            )
            if not rows:
                raise HTTPException(status_code=404, detail="Pembayaran gateway tidak ditemukan.")
            primary = rows[0]
            source_type = "herbal"
            source_id = rows[0].sale_group_id or str(rows[0].id)
            amount = int(sum(float(row.total_price or 0) for row in rows))

        old_status = getattr(primary, "payment_status", None) or "paid"
        provider = getattr(primary, "payment_provider", None) or "manual"
        simulation = str(simulate or "").strip().lower()
        if simulation:
            gateway_status_map = (
                {"paid": "settlement", "expired": "expire", "failed": "failure"}
                if provider == "midtrans"
                else {"paid": "paid", "expired": "expired", "failed": "failed"}
            )
            if simulation not in gateway_status_map:
                raise HTTPException(status_code=400, detail="Simulasi status tidak valid.")
            gateway_status = gateway_status_map[simulation]
            payment_status = map_gateway_status(provider, gateway_status)
            update_result = _apply_gateway_status_update(session, rows, source_type, source_id, normalized_reference, old_status, gateway_status, payment_status, amount)
        elif provider == "midtrans":
            try:
                gateway_result = check_payment_status(provider, normalized_reference)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=_safe_gateway_error(exc)) from exc
            gateway_status = gateway_result["payment_gateway_status"]
            payment_status = gateway_result["payment_status"]
            update_result = _apply_gateway_status_update(session, rows, source_type, source_id, normalized_reference, old_status, gateway_status, payment_status, amount)
        elif not is_available_gateway_provider(provider):
            raise HTTPException(status_code=400, detail="Provider pembayaran pada invoice ini belum didukung.")

        result = _serialize_payment(primary, source_type, source_id, amount)
    response = {"status": "success", "payment": result}
    if 'update_result' in locals() and update_result.get("ignored"):
        response.update({"ignored": True, "reason": update_result.get("reason")})
    return response


@router.get("/gateway/pay/{payment_reference}", response_class=HTMLResponse)
@router.get("/gateway/mock/pay/{payment_reference}", response_class=HTMLResponse)
def mock_payment_page(payment_reference: str):
    safe_reference = str(payment_reference or "").strip()
    return f"""
    <!doctype html>
    <html lang="id">
    <head><meta charset="utf-8"><title>Link Pembayaran</title></head>
    <body style="font-family:Arial,sans-serif;margin:40px;color:#0f172a;">
        <h1>Link Pembayaran</h1>
        <p>Halaman percobaan untuk referensi pembayaran:</p>
        <strong>{safe_reference}</strong>
        <p style="color:#64748b;">Tidak ada koneksi ke penyedia pembayaran eksternal.</p>
    </body>
    </html>
    """
