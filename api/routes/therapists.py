import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Form, Query, Request
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license

router = APIRouter()

@router.get("/therapists")
def get_therapists(active_only: bool = Query(False)):
    try:
        return db.get_all_therapists(active_only=active_only)
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat data terapis. Hubungi admin.")

def _parse_bool(value):
    return str(value or "").strip().lower() in ("true", "1", "on", "yes", "ya")

def _parse_service_ids(value):
    text = str(value or "").strip()
    if not text:
        return []
    try:
        raw_items = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("Daftar layanan terapis tidak valid.")
    if not isinstance(raw_items, list):
        raise ValueError("Daftar layanan terapis tidak valid.")
    service_ids = []
    for raw_id in raw_items:
        try:
            service_id = int(raw_id)
        except (TypeError, ValueError):
            raise ValueError("Daftar layanan terapis tidak valid.")
        if service_id > 0 and service_id not in service_ids:
            service_ids.append(service_id)
    return service_ids

@router.post("/add_therapist")
async def add_therapist(
    request: Request,
    name: str = Form(...),
    gender: str = Form(...),
    specialization: str = Form(""),
    can_handle_any_gender: str = Form("false"),
    service_ids: Optional[str] = Form(None),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama terapis wajib diisi.")
        if gender not in ("Laki-laki", "Perempuan"):
            raise ValueError("Jenis kelamin terapis tidak valid.")
        db.add_therapist(
            name.strip(),
            gender,
            specialization,
            _parse_bool(can_handle_any_gender),
            None if service_ids is None else _parse_service_ids(service_ids),
        )
        return {"status": "success", "message": "Terapis baru berhasil didaftarkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_therapist")
async def update_therapist(
    request: Request,
    therapist_id: int = Form(...),
    name: str = Form(...),
    gender: str = Form(...),
    specialization: str = Form(""),
    is_active: str = Form("true"),
    can_handle_any_gender: str = Form("false"),
    service_ids: Optional[str] = Form(None),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if not name.strip():
            raise ValueError("Nama terapis wajib diisi.")
        if gender not in ("Laki-laki", "Perempuan"):
            raise ValueError("Jenis kelamin terapis tidak valid.")
        active = _parse_bool(is_active)
        db.update_therapist(
            therapist_id,
            name.strip(),
            gender,
            specialization,
            active,
            _parse_bool(can_handle_any_gender),
            None if service_ids is None else _parse_service_ids(service_ids),
        )
        return {"status": "success", "message": "Terapis berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/toggle_therapist")
async def toggle_therapist(request: Request, therapist_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        t = db.get_therapist(therapist_id)
        if not t:
            raise HTTPException(status_code=404, detail="Terapis tidak ditemukan.")
        db.update_therapist(therapist_id, t.name, t.gender, t.specialization, not t.is_active, t.can_handle_any_gender)
        return {"status": "success", "is_active": not t.is_active}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_therapist")
async def delete_therapist(request: Request, therapist_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        t = db.get_therapist(therapist_id)
        if not t:
            raise HTTPException(status_code=404, detail="Terapis tidak ditemukan.")
        db.delete_therapist(therapist_id)
        return {"status": "success", "message": "Terapis berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        if "riwayat kunjungan" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
