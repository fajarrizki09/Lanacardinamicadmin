from fastapi import APIRouter, HTTPException, Form, Request
from typing import Optional
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license
from helpers.ttl_cache import TTLCache
from helpers.exceptions import ValidationError, StockError, IdempotencyError
import json
import threading
import time
import hashlib
import logging
import uuid

router = APIRouter()

# Idempotency / concurrency protection with TTL cache (prevents memory leaks)
_herbal_idempotency_cache = TTLCache(maxsize=1000, ttl_seconds=600, cleanup_interval=60)
_logger = logging.getLogger("lancar.herbals")

def _reserve_herbal_idempotency_key(raw_key):
    """Reserve idempotency key using TTL cache."""
    key = str(raw_key or "").strip()
    if not key:
        return "", "none", None
    key = key[:128]
    
    existing = _herbal_idempotency_cache.get(key)
    if existing:
        return key, existing.get("state"), existing.get("response")
    
    _herbal_idempotency_cache.set(key, {"state": "pending", "response": None})
    return key, "reserved", None

def _complete_herbal_idempotency_key(key, response):
    """Mark idempotency key as complete."""
    if not key:
        return
    _herbal_idempotency_cache.set(key, {"state": "done", "response": dict(response)})

def _release_herbal_idempotency_key(key):
    """Release pending idempotency key."""
    if not key:
        return
    existing = _herbal_idempotency_cache.get(key)
    if existing and existing.get("state") == "pending":
        _herbal_idempotency_cache.delete(key)

# Simple process-wide lock to avoid concurrent stock updates in the same process
_herbal_sale_lock = threading.Lock()

def _herbal_meta(herbal_id):
    try:
        return next((item for item in db.get_all_herbals() if int(item.get("id")) == int(herbal_id)), {}) or {}
    except Exception:
        return {}

def _parse_sale_items(value):
    """Parse and validate herbal sale items."""
    text = str(value or "").strip()
    if not text:
        raise ValidationError("Minimal pilih satu herbal untuk dijual.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        _logger.error(f"JSON decode error in sale items: {e}")
        raise ValidationError("Data penjualan herbal tidak valid.")
    if not isinstance(data, list) or not data:
        raise ValidationError("Minimal pilih satu herbal untuk dijual.")
    items = []
    for item in data:
        if not isinstance(item, dict):
            raise ValidationError("Data penjualan herbal tidak valid.")
        try:
            herbal_id = int(item.get("herbal_id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError) as e:
            _logger.error(f"Invalid herbal item data: {e}")
            raise ValidationError("Data penjualan herbal tidak valid.")
        if quantity <= 0:
            raise ValidationError("Jumlah penjualan herbal harus lebih dari 0.")
        items.append({"herbal_id": herbal_id, "quantity": quantity})
    return items

@router.get("/herbals")
def get_herbals():
    """Get all herbals."""
    try:
        return db.get_all_herbals()
    except Exception as e:
        _logger.error(f"Failed to get herbals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gagal memuat data herbal. Hubungi admin.")

@router.get("/herbals/transactions")
def get_herbal_transactions(
    page: int = 1,
    page_size: int = 100,
    search: str = "",
    date_from: str = "",
    date_to: str = "",
    transaction_type: str = "",
):
    try:
        from datetime import datetime
        from sqlalchemy.orm import joinedload
        from database import HerbalTransaction

        page = max(1, int(page or 1))
        page_size = min(250, max(10, int(page_size or 100)))
        search_text = str(search or "").strip().lower()
        tx_type = str(transaction_type or "").strip()

        def parse_date(value):
            text = str(value or "").strip()
            if not text:
                return None
            try:
                return datetime.fromisoformat(text)
            except ValueError:
                return datetime.fromisoformat(f"{text}T00:00:00")

        with db.Session() as session:
            query = session.query(HerbalTransaction).options(joinedload(HerbalTransaction.herbal))
            start_date = parse_date(date_from)
            end_date = parse_date(date_to)
            if start_date:
                query = query.filter(HerbalTransaction.date >= start_date)
            if end_date:
                query = query.filter(HerbalTransaction.date <= end_date)
            if tx_type:
                query = query.filter(HerbalTransaction.transaction_type == tx_type)
            rows = (
                query
                .order_by(HerbalTransaction.date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            data = []
            for row in rows:
                herbal_name = row.herbal.name if row.herbal else "Herbal"
                if search_text and search_text not in herbal_name.lower() and search_text not in str(row.note or "").lower():
                    continue
                data.append({
                    "id": row.id,
                    "date": row.date.isoformat() if row.date else None,
                    "herbal_id": row.herbal_id,
                    "herbal_name": herbal_name,
                    "visit_id": row.visit_id,
                    "sale_group_id": row.sale_group_id,
                    "quantity": int(row.quantity or 0),
                    "total_price": float(row.total_price or 0),
                    "transaction_type": row.transaction_type,
                    "invoice_path": row.invoice_path,
                    "note": row.note,
                })
            return {"page": page, "page_size": page_size, "data": data}
    except Exception as e:
        _logger.exception("Failed to load herbal transactions")
        raise HTTPException(status_code=500, detail=f"Gagal memuat riwayat transaksi herbal: {str(e)[:100]}")

@router.post("/herbals/sale")
async def add_herbal_sale(
    request: Request,
    buyer_name: str = Form(""),
    patient_id: str = Form(""),
    items: str = Form(""),
    payment_status: str = Form("paid"),
    payment_method: str = Form("cash"),
    payment_provider: str = Form("manual"),
    amount_paid: Optional[int] = Form(None),
    idempotency_key: str = Form("")
):
    try:
        require_valid_license()

        # Resolve idempotency key: prefer header, then form, then fallback hash
        header_key = str(request.headers.get("X-Idempotency-Key", "")).strip()
        form_key = str(idempotency_key or "").strip()
        if header_key:
            key_source = header_key
        elif form_key:
            key_source = form_key
        else:
            # Use UUID + timestamp for better uniqueness guarantee
            fallback_raw = f"{buyer_name}|{patient_id}|{items}|{uuid.uuid4().hex[:8]}"
            key_source = hashlib.sha256(fallback_raw.encode()).hexdigest()[:64]

        reserved_idempotency_key = ""
        idempotency_key_value, idempotency_state, idempotency_response = _reserve_herbal_idempotency_key(key_source)
        if idempotency_state == "reserved":
            reserved_idempotency_key = idempotency_key_value
        if idempotency_state == "pending":
            raise HTTPException(status_code=409, detail="Penjualan sedang diproses. Tunggu sebentar sebelum mencoba lagi.")
        if idempotency_state == "done":
            response = dict(idempotency_response or {"status": "success", "message": "Penjualan herbal sudah dicatat."})
            response["idempotent_replay"] = True
            return response

        parsed_items = _parse_sale_items(items)
        normalized_patient_id = int(patient_id) if str(patient_id or "").strip() else None
        from datetime import datetime

        # Serialize stock updates in-process to avoid race on SQLite
        try:
            with _herbal_sale_lock:
                sale = db.add_herbal_sale(
                    parsed_items,
                    buyer_name=buyer_name,
                    patient_id=normalized_patient_id,
                    payment_status=payment_status,
                    payment_method=payment_method,
                    payment_provider=payment_provider,
                    amount_paid=amount_paid if payment_status != 'unpaid' else 0,
                    paid_at=datetime.now().isoformat() if payment_status in ['paid', 'partial'] else None
                )

            response = {
                "status": "success",
                "message": "Penjualan herbal berhasil disimpan.",
                "sale": sale,
            }
            db.log_audit("herbal_sale_created", "herbal_sale", sale.get("sale_group_id"), "Penjualan herbal dicatat.", {
                "buyer_name": buyer_name.strip() or "-",
                "patient_id": normalized_patient_id,
                "item_count": len(parsed_items),
                "total": sale.get("total"),
            })
            _complete_herbal_idempotency_key(reserved_idempotency_key, response)
            return response
        except Exception as e:
            # release idempotency if key was reserved
            try:
                _release_herbal_idempotency_key(reserved_idempotency_key)
            except Exception:
                pass
            # translate known validation errors
            if isinstance(e, ValueError):
                raise HTTPException(status_code=400, detail=str(e))
            _logger.exception("Unexpected error in add_herbal_sale")
            raise HTTPException(status_code=500, detail="Gagal menyimpan penjualan herbal. Hubungi admin.")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _logger.exception("Unhandled error while processing herbal sale request")
        raise HTTPException(status_code=500, detail="Gagal memproses permintaan. Silakan hubungi admin.")

@router.post("/update_herbal")
async def update_herbal(
    request: Request,
    herbal_id: int = Form(...),
    change: int = Form(...),
    reason: str = Form(""),
    multiplier: int = Form(1),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if multiplier < 1:
            raise ValueError("Multiplier minimal 1.")
        total_change = int(change or 0) * multiplier
        reason_text = reason.strip() or ("Herbal masuk" if total_change > 0 else "Herbal keluar")
        before = _herbal_meta(herbal_id)
        success = db.update_herbal_stock(
            herbal_id,
            total_change,
            transaction_type="stock_in" if total_change > 0 else "stock_out",
            note=reason_text,
            correction_reason=reason_text,
        )
        if not success:
            raise ValueError("Herbal not found")
        after = _herbal_meta(herbal_id)
        db.log_audit("herbal_stock_corrected", "herbal", herbal_id, "Stok herbal dikoreksi.", {
            "name": before.get("name") or after.get("name"),
            "change": total_change,
            "stock_before": before.get("stock"),
            "stock_after": after.get("stock"),
            "unit": before.get("unit") or after.get("unit"),
            "reason": reason_text,
        })
        return {"status": "success", "message": "Stok herbal berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/herbals/return")
async def return_herbal_sale(request: Request, transaction_id: int = Form(...), quantity: int = Form(...), reason: str = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        result = db.return_herbal_sale(transaction_id, quantity, reason)
        db.log_audit("herbal_return_created", "herbal_transaction", transaction_id, "Retur penjualan herbal dicatat.", {
            "quantity": quantity,
            "reason": reason,
            "total": result.get("total_price") if isinstance(result, dict) else None,
        })
        return {
            "status": "success",
            "message": "Retur penjualan berhasil dicatat dan stok dikembalikan.",
            "return": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/correction_logs")
def get_correction_logs(request: Request, limit: int = 100, action_type: str = ""):
    try:
        require_admin_pin(request)
        return db.get_correction_logs(limit=limit, action_type=action_type)
    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("Failed to load correction logs")
        raise HTTPException(status_code=500, detail=f"Gagal memuat log koreksi: {str(e)[:100]}")

@router.post("/add_herbal")
async def add_herbal(
    request: Request,
    name: str = Form(...),
    unit: str = Form("pcs"),
    price: float = Form(0),
    stock: int = Form(0),
    cost_price: float = Form(0),
    package_unit: str = Form(""),
    package_size: int = Form(1),
    min_stock: int = Form(5),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama herbal wajib diisi.")
        if price < 0:
            raise ValueError("Harga herbal tidak boleh negatif.")
        if cost_price < 0:
            raise ValueError("Harga modal herbal tidak boleh negatif.")
        if stock < 0:
            raise ValueError("Stok herbal tidak boleh negatif.")
        if min_stock < 0:
            raise ValueError("Stok minimum tidak boleh negatif.")
        herbal_id = db.add_herbal(name, unit, price, stock, cost_price, package_unit.strip() or None, package_size, min_stock)
        db.log_audit("herbal_created", "herbal", herbal_id, "Herbal baru ditambahkan.", {
            "name": name.strip(),
            "unit": unit,
            "package_unit": package_unit.strip(),
            "package_size": package_size,
            "cost_price": cost_price,
            "price": price,
            "stock": stock,
            "min_stock": min_stock,
        })
        return {"status": "success", "message": "Herbal baru berhasil didaftarkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/edit_herbal")
async def edit_herbal(
    request: Request,
    herbal_id: int = Form(...),
    name: str = Form(...),
    unit: str = Form("pcs"),
    price: float = Form(0),
    stock: int = Form(0),
    cost_price: float = Form(0),
    package_unit: str = Form(""),
    package_size: int = Form(1),
    min_stock: int = Form(5),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama herbal wajib diisi.")
        if price < 0:
            raise ValueError("Harga herbal tidak boleh negatif.")
        if cost_price < 0:
            raise ValueError("Harga modal herbal tidak boleh negatif.")
        if stock < 0:
            raise ValueError("Stok herbal tidak boleh negatif.")
        if min_stock < 0:
            raise ValueError("Stok minimum tidak boleh negatif.")
        before = _herbal_meta(herbal_id)
        success = db.update_herbal(herbal_id, name, unit, price, stock, cost_price, package_unit.strip() or None, package_size, min_stock)
        if not success:
            raise ValueError("Herbal not found")
        db.log_audit("herbal_updated", "herbal", herbal_id, "Data herbal diperbarui.", {
            "name": name.strip(),
            "old_name": before.get("name"),
            "unit": unit,
            "package_unit": package_unit.strip(),
            "package_size": package_size,
            "cost_price": cost_price,
            "price": price,
            "old_price": before.get("price"),
            "stock": stock,
            "stock_before": before.get("stock"),
            "min_stock": min_stock,
        })
        return {"status": "success", "message": "Data herbal berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_herbal")
async def delete_herbal(request: Request, herbal_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        before = _herbal_meta(herbal_id)
        success = db.delete_herbal(herbal_id)
        if not success:
            raise ValueError("Herbal not found")
        db.log_audit("herbal_deactivated", "herbal", herbal_id, "Herbal dinonaktifkan.", {
            "name": before.get("name"),
            "stock": before.get("stock"),
            "unit": before.get("unit"),
            "price": before.get("price"),
        })
        return {"status": "success", "message": "Herbal berhasil dinonaktifkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
