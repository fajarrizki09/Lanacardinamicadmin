import json

from fastapi import APIRouter, Form, HTTPException, Query, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license

router = APIRouter()


def _parse_inventory_usage(value):
    text = str(value or "").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("Data pemakaian inventaris layanan tidak valid.")
    if not isinstance(data, list):
        raise ValueError("Data pemakaian inventaris layanan tidak valid.")
    usage = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Data pemakaian inventaris layanan tidak valid.")
        try:
            inventory_id = int(item.get("inventory_id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            raise ValueError("Data pemakaian inventaris layanan tidak valid.")
        if inventory_id <= 0 or quantity <= 0:
            raise ValueError("Inventaris dan jumlah pemakaian harus diisi.")
        usage.append({"inventory_id": inventory_id, "quantity": quantity})
    return usage


@router.get("/services")
def get_services(active_only: bool = Query(False)):
    try:
        return db.get_all_services(active_only=active_only)
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat data layanan. Hubungi admin.")


@router.post("/add_service")
async def add_service(
    request: Request,
    name: str = Form(...),
    unit_label: str = Form("sesi"),
    default_quantity: int = Form(1),
    price_per_unit: float = Form(0),
    notes_template: str = Form(""),
    inventory_usage: str = Form("[]"),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama layanan wajib diisi.")
        if default_quantity < 1:
            raise ValueError("Jumlah default layanan minimal 1.")
        if price_per_unit < 0:
            raise ValueError("Harga layanan tidak boleh negatif.")
        db.add_service(
            name.strip(),
            unit_label.strip() or "sesi",
            default_quantity,
            price_per_unit,
            notes_template,
            _parse_inventory_usage(inventory_usage),
        )
        return {"status": "success", "message": "Layanan berhasil ditambahkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update_service")
async def update_service(
    request: Request,
    service_id: int = Form(...),
    name: str = Form(...),
    unit_label: str = Form("sesi"),
    default_quantity: int = Form(1),
    price_per_unit: float = Form(0),
    notes_template: str = Form(""),
    is_active: str = Form("true"),
    inventory_usage: str = Form("[]"),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama layanan wajib diisi.")
        if default_quantity < 1:
            raise ValueError("Jumlah default layanan minimal 1.")
        if price_per_unit < 0:
            raise ValueError("Harga layanan tidak boleh negatif.")
        active = is_active.lower() in ("true", "1", "on", "yes")
        db.update_service(
            service_id,
            name.strip(),
            unit_label.strip() or "sesi",
            default_quantity,
            price_per_unit,
            notes_template,
            active,
            _parse_inventory_usage(inventory_usage),
        )
        return {"status": "success", "message": "Layanan berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/toggle_service")
async def toggle_service(request: Request, service_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        service = db.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Layanan tidak ditemukan.")
        db.update_service(
            service_id,
            service.name,
            service.unit_label,
            service.default_quantity,
            service.price_per_unit,
            service.notes_template,
            not service.is_active,
            service.inventory_usage,
        )
        return {"status": "success", "is_active": not service.is_active}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete_service")
async def delete_service(request: Request, service_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        service = db.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Layanan tidak ditemukan.")
        db.delete_service(service_id)
        return {"status": "success", "message": "Layanan berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        if "riwayat kunjungan" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
