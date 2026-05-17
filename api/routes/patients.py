from fastapi import APIRouter, HTTPException, Request, Form
from typing import Optional
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license
from helpers.payment_rules import allocate_payment_amounts, normalize_visit_payment
import json
import threading
import time
from datetime import datetime

router = APIRouter()

_VISIT_IDEMPOTENCY_TTL_SECONDS = 10 * 60
_visit_idempotency_lock = threading.Lock()
_visit_idempotency_cache = {}


def _cleanup_visit_idempotency_cache(now=None):
    now = now or time.monotonic()
    expired_keys = [
        key for key, entry in _visit_idempotency_cache.items()
        if now - float(entry.get("created_at") or 0) > _VISIT_IDEMPOTENCY_TTL_SECONDS
    ]
    for key in expired_keys:
        _visit_idempotency_cache.pop(key, None)


def _reserve_visit_idempotency_key(raw_key):
    key = str(raw_key or "").strip()
    if not key:
        return "", "none", None
    key = key[:128]
    now = time.monotonic()
    with _visit_idempotency_lock:
        _cleanup_visit_idempotency_cache(now)
        existing = _visit_idempotency_cache.get(key)
        if existing:
            return key, existing.get("state"), existing.get("response")
        _visit_idempotency_cache[key] = {"state": "pending", "created_at": now, "response": None}
        return key, "reserved", None


def _complete_visit_idempotency_key(key, response):
    if not key:
        return
    with _visit_idempotency_lock:
        _visit_idempotency_cache[key] = {
            "state": "done",
            "created_at": time.monotonic(),
            "response": dict(response),
        }


def _release_visit_idempotency_key(key):
    if not key:
        return
    with _visit_idempotency_lock:
        entry = _visit_idempotency_cache.get(key)
        if entry and entry.get("state") == "pending":
            _visit_idempotency_cache.pop(key, None)

def _validated_visit_therapist_id(session, patient, therapist_id, therapist_cache=None):
    from database import Therapist
    if therapist_cache is None:
        therapist_cache = {}

    if not therapist_id:
        cache_key = ("auto", patient.gender)
        if cache_key in therapist_cache:
            if therapist_cache[cache_key] is None:
                raise ValueError("Belum ada terapis aktif yang bisa menangani pasien ini. Tambahkan terapis sesuai gender atau aktifkan opsi lintas gender.")
            return therapist_cache[cache_key]

        matching_therapist = session.query(Therapist).filter(
            Therapist.is_active == True,
            (Therapist.gender == patient.gender) | (Therapist.can_handle_any_gender == True),
        ).first()
        if not matching_therapist:
            therapist_cache[cache_key] = None
            raise ValueError("Belum ada terapis aktif yang bisa menangani pasien ini. Tambahkan terapis sesuai gender atau aktifkan opsi lintas gender.")
        # Auto-assign ke terapis pertama yang cocok jika tidak dipilih manual
        therapist_cache[cache_key] = matching_therapist.id
        return matching_therapist.id

    cache_key = ("manual", therapist_id)
    if cache_key in therapist_cache:
        therapist = therapist_cache[cache_key]
    else:
        therapist = session.get(Therapist, int(therapist_id))
        therapist_cache[cache_key] = therapist

    if not therapist:
        raise ValueError("Terapis tidak ditemukan atau tidak aktif.")
    if not therapist.is_active:
        raise ValueError("Terapis tidak ditemukan atau tidak aktif.")
    if therapist.gender != patient.gender and not therapist.can_handle_any_gender:
        raise ValueError("Terapis tidak sesuai dengan jenis kelamin pasien. Pilih terapis lain atau aktifkan opsi lintas gender pada data terapis.")
    return therapist.id

def _normalize_visit_service_id(service_id):
    if not str(service_id or "").strip():
        return None
    try:
        return int(service_id)
    except (TypeError, ValueError):
        raise ValueError("Layanan tidak ditemukan.")

def _validated_visit_service(session, service_id):
    from database import Service
    normalized_service_id = _normalize_visit_service_id(service_id)
    if not normalized_service_id:
        return None
    service = session.get(Service, normalized_service_id)
    if not service:
        raise ValueError("Layanan tidak ditemukan.")
    if not service.is_active:
        raise ValueError("Layanan nonaktif tidak bisa dipakai untuk kunjungan baru.")
    return service

def _validate_patient_gender(gender):
    if gender not in ("Laki-laki", "Perempuan"):
        raise ValueError("Jenis kelamin pasien tidak valid.")
    return gender

def _validate_optional_phone(phone):
    phone = str(phone or "").strip()
    if not phone:
        return ""
    if not phone.isdigit() or not phone.startswith("08") or not 10 <= len(phone) <= 13:
        raise ValueError("Nomor HP harus diawali 08 dan berisi 10-13 digit.")
    return phone

def _resolve_patient_update_phone(submitted_phone, current_phone):
    phone = _validate_optional_phone(submitted_phone)
    current_phone = str(current_phone or "").strip()
    if phone:
        return phone
    if current_phone.startswith("TEMP-"):
        return current_phone
    raise ValueError("Nomor HP tidak boleh kosong.")

def _parse_bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "ya", "y", "on")

def _get_quantity_value(data, required=False, default=None):
    for key in ("quantity", "point_count", "points"):
        value = data.get(key)
        if value is not None and str(value).strip() != "":
            try:
                quantity = int(float(value))
            except (TypeError, ValueError):
                raise ValueError("Jumlah layanan harus berupa angka.")
            if quantity < 1:
                raise ValueError("Jumlah layanan minimal 1.")
            return quantity
    if required:
        raise ValueError("Jumlah layanan minimal 1.")
    return default

def _get_price_value(data):
    value = data.get("final_price", data.get("price"))
    if value is None or str(value).strip() == "":
        raise ValueError("Harga kunjungan wajib diisi.")
    price = float(value)
    if price < 0:
        raise ValueError("Harga kunjungan tidak boleh kurang dari 0.")
    return price

def _parse_herbal_items(value):
    text = str(value or "").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("Data pembelian herbal tidak valid.")
    if not isinstance(data, list):
        raise ValueError("Data pembelian herbal tidak valid.")
    items = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Data pembelian herbal tidak valid.")
        try:
            herbal_id = int(item.get("herbal_id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            raise ValueError("Data pembelian herbal tidak valid.")
        if quantity <= 0:
            raise ValueError("Jumlah pembelian herbal harus lebih dari 0.")
        items.append({"herbal_id": herbal_id, "quantity": quantity})
    return items

@router.get("/patients")
def get_patients():
    try:
        # We might still need all patients for simple dropdowns if not converted yet,
        # but realistically, autocomplete is better. For now we keep this to not break 
        # existing simple selects if they exist.
        patients = db.get_all_patients()
        therapists = db.get_all_therapists(active_only=True)
        return {"patients": patients, "therapists": therapists}
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat data pasien. Hubungi admin.")

@router.get("/patients_paginated")
def get_patients_paginated(
    draw: int = 1,
    start: int = 0,
    length: int = 10,
    search: str = "",
    order_col: int = 0,
    order_dir: str = "asc"
):
    try:
        result = db.get_patients_paginated(
            start=start,
            length=length,
            search_val=search,
            order_col_idx=order_col,
            order_dir=order_dir
        )
        result["draw"] = draw
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat data pasien (paginasi). Hubungi admin.")

@router.get("/visit_form_options")
def get_visit_form_options():
    try:
        from settings import AppSettings

        app_settings = AppSettings()
        services = db.get_all_services(active_only=True)
        return {
            "services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "unit_label": s.unit_label,
                    "default_quantity": s.default_quantity,
                    "price_per_unit": s.price_per_unit,
                    "notes_template": s.notes_template,
                    "is_active": s.is_active,
                }
                for s in services
            ],
            "price_per_point": app_settings.get_price_per_point(),
            "free_visit_reasons": app_settings.get_free_visit_reasons(),
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat opsi form. Hubungi admin.")

@router.get("/patient_detail/{patient_id}")
def get_patient_detail(patient_id: int):
    try:
        patient = db.get_patient_detail(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
        return patient
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat detail pasien. Hubungi admin.")

@router.post("/add_patient")
async def add_patient(name: str = Form(...), phone: str = Form(""), address: str = Form(""), gender: str = Form("Laki-laki")):
    try:
        require_valid_license()
        if not name.strip():
            raise HTTPException(status_code=400, detail="Nama tidak boleh kosong")

        gender = _validate_patient_gender(gender)
        phone = _validate_optional_phone(phone)
        if not phone:
            phone = "TEMP-" + datetime.now().strftime("%H%M%S%f")[:10]

        if db.patient_phone_exists(phone):
            raise HTTPException(status_code=400, detail=f"Nomor HP {phone} sudah terdaftar untuk pasien lain.")

        db.add_patient(name.strip(), phone, address.strip(), gender)
        return {"status": "success", "message": "Pasien baru berhasil didaftarkan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_patient")
async def update_patient(
    patient_id: int = Form(...),
    name: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    gender: str = Form("Laki-laki")
):
    try:
        require_valid_license()
        from datetime import datetime as dt
        if not name.strip():
            raise HTTPException(status_code=400, detail="Nama tidak boleh kosong.")
        gender = _validate_patient_gender(gender)
        phone = _validate_optional_phone(phone)
        if not phone:
            raise HTTPException(status_code=400, detail="Nomor HP tidak boleh kosong.")
        if db.patient_phone_exists(phone, exclude_patient_id=patient_id):
            raise HTTPException(status_code=400, detail=f"Nomor HP {phone} sudah dipakai pasien lain.")
        old_patient = db.get_patient_detail(patient_id) or {}
        db.update_patient(patient_id, name.strip(), phone, address.strip(), gender)
        db.log_audit("patient_updated", "patient", patient_id, "Data pasien diperbarui.", {
            "name": name.strip(),
            "phone": phone,
            "gender": gender,
            "old_name": old_patient.get("name"),
            "old_phone": old_patient.get("phone"),
        })
        return {"status": "success", "message": "Data pasien berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_patient_full")
async def update_patient_full(request: Request):
    try:
        require_valid_license()
        from datetime import datetime as dt
        form = await request.form()
        _patient_id_raw = form.get("patient_id")
        if not _patient_id_raw:
            raise HTTPException(status_code=400, detail="patient_id wajib diisi.")
        patient_id = int(_patient_id_raw)
        name = form.get("name", "").strip()
        phone = form.get("phone", "").strip()
        address = form.get("address", "").strip()
        gender = form.get("gender", "Laki-laki")
        visits_json = form.get("visits", "[]")

        if not name:
            raise HTTPException(status_code=400, detail="Nama tidak boleh kosong.")
        gender = _validate_patient_gender(gender)

        from database import Patient, Visit
        visits_data = json.loads(visits_json)
        with db.Session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                raise ValueError("Pasien tidak ditemukan.")

            phone = _resolve_patient_update_phone(phone, patient.phone)
            if db.patient_phone_exists(phone, exclude_patient_id=patient_id):
                raise HTTPException(status_code=400, detail=f"Nomor HP {phone} sudah dipakai pasien lain.")

            patient.name = name
            patient.phone = phone
            patient.address = address
            patient.gender = gender

            therapist_cache = {}
            for v_data in visits_data:
                v = session.get(Visit, int(v_data['id']))
                if v and v.patient_id == patient_id:
                    price = _get_price_value(v_data) if ("price" in v_data or "final_price" in v_data) else float(v.price or 0)
                    is_free_visit = _parse_bool_value(v_data.get('is_free_visit'), bool(v.is_free_visit))
                    free_visit_reason = str(v_data.get('free_visit_reason') or "").strip() if is_free_visit else None
                    if price == 0 and not is_free_visit:
                        raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis.")
                    if is_free_visit and price != 0:
                        raise ValueError("Kunjungan gratis harus memakai harga 0.")
                    if is_free_visit and not free_visit_reason:
                        raise ValueError("Alasan kunjungan gratis wajib diisi.")
                    point_count = _get_quantity_value(v_data, default=v.point_count)
                    if point_count is not None:
                        v.point_count = point_count
                    v.price = max(0, price)
                    if "medical_notes" in v_data or "notes" in v_data:
                        v.medical_notes = v_data.get('medical_notes', v_data.get('notes', ''))
                    if "therapist_id" in v_data:
                        v.therapist_id = _validated_visit_therapist_id(session, patient, v_data.get('therapist_id'), therapist_cache)
                    if "service_id" in v_data:
                        raw_service_id = v_data.get("service_id")
                        v.service_id = int(raw_service_id) if raw_service_id not in (None, "") else None
                    if "service_name" in v_data:
                        v.service_name = str(v_data.get("service_name") or "").strip() or "Bekam"
                    if "discount_rule_id" in v_data:
                        raw_rule_id = v_data.get("discount_rule_id")
                        v.discount_rule_id = int(raw_rule_id) if raw_rule_id not in (None, "") else None
                    if "discount_rule_name" in v_data:
                        v.discount_rule_name = str(v_data.get("discount_rule_name") or "").strip() or None
                    if "discount_applied" in v_data:
                        v.discount_applied = _parse_bool_value(v_data.get("discount_applied"))
                    v.is_free_visit = is_free_visit
                    v.free_visit_reason = free_visit_reason
                    if is_free_visit:
                        v.discount_applied = False
                        v.discount_rule_id = None
                        v.discount_rule_name = None
                    if v_data.get('date'):
                        try:
                            v.date = dt.fromisoformat(v_data['date'])
                        except ValueError:
                            raise ValueError("Tanggal kunjungan tidak valid.")
            session.commit()

        db.log_audit("patient_updated", "patient", patient_id, "Data pasien dan kunjungan diperbarui.", {
            "name": name,
            "phone": phone,
            "gender": gender,
            "visit_count": len(visits_data),
        })
        return {"status": "success", "message": "Data pasien & kunjungan berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_patient")
async def delete_patient(request: Request, patient_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        old_patient = db.get_patient_detail(patient_id) or {}
        db.delete_patient(patient_id)
        db.log_audit("patient_deleted", "patient", patient_id, "Pasien dihapus.", {
            "name": old_patient.get("name"),
            "phone": old_patient.get("phone"),
            "visit_count": old_patient.get("visits_count"),
        })
        return {"status": "success", "message": "Pasien berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_visit")
async def add_visit(
    patient_id: int = Form(...), 
    point_count: int = Form(...), 
    price: int = Form(...),
    therapist_id: int = Form(None),
    service_id: str = Form(""),
    service_name: str = Form(""),
    medical_notes: str = Form(""),
    discount_applied: bool = Form(False),
    discount_rule_id: str = Form(""),
    is_free_visit: bool = Form(False),
    free_visit_reason: str = Form(""),
    voucher_code: str = Form(""),
    manual_price_used: bool = Form(False),
    herbal_items: str = Form(""),
    payment_status: str = Form("unpaid"),
    payment_method: str = Form(""),
    amount_paid: Optional[int] = Form(None),
    idempotency_key: str = Form("")
):
    reserved_idempotency_key = ""
    try:
        require_valid_license()
        if point_count < 1:
            raise ValueError("Jumlah layanan minimal 1.")
        idempotency_key_value, idempotency_state, idempotency_response = _reserve_visit_idempotency_key(idempotency_key)
        if idempotency_state == "reserved":
            reserved_idempotency_key = idempotency_key_value
        if idempotency_state == "pending":
            raise HTTPException(status_code=409, detail="Kunjungan sedang diproses. Tunggu sebentar sebelum mencoba lagi.")
        if idempotency_state == "done":
            response = dict(idempotency_response or {"status": "success", "message": "Kunjungan sudah dicatat."})
            response["idempotent_replay"] = True
            return response
        from database import Patient, Therapist
        from settings import AppSettings
        normalized_service_id = _normalize_visit_service_id(service_id)
        parsed_herbal_items = _parse_herbal_items(herbal_items)
        app_settings = AppSettings()
        patient_name_for_audit = ""
        therapist_name_for_audit = ""
        unit_label_for_audit = "titik"
        with db.Session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                raise ValueError("Pasien tidak ditemukan.")
            patient_name_for_audit = patient.name
            validated_therapist_id = _validated_visit_therapist_id(session, patient, therapist_id)
            if validated_therapist_id:
                therapist = session.get(Therapist, validated_therapist_id)
                therapist_name_for_audit = therapist.name if therapist else ""
            service = _validated_visit_service(session, normalized_service_id)
            if service:
                service_name = service.name
                unit_label_for_audit = service.unit_label or "sesi"
            if not manual_price_used and not is_free_visit:
                if service and service.name.strip().lower() != "bekam":
                    price = float(service.price_per_unit or 0) * point_count
                else:
                    price = float(app_settings.get_price_per_point() or 0) * point_count
            elif str(service_name or "").strip().lower() != "bekam":
                unit_label_for_audit = unit_label_for_audit or "sesi"

        db.add_visit(
            patient_id,
            price,
            point_count=point_count,
            therapist_id=validated_therapist_id,
            service_id=normalized_service_id,
            service_name=service_name,
            discount_percentage=app_settings.get_discount_percentage(),
            min_visits_for_discount=app_settings.get_min_visits_for_discount(),
            medical_notes=medical_notes,
            inventory_config=app_settings.get_inventory_config(),
            is_free_visit=is_free_visit,
            free_visit_reason=free_visit_reason,
            manual_price_used=manual_price_used,
            voucher_code=voucher_code,
            discount_rule_id=int(discount_rule_id) if str(discount_rule_id or "").strip() else None,
            herbal_items=parsed_herbal_items,
            payment_status=payment_status,
            payment_method=payment_method,
            amount_paid=amount_paid,
        )
        db.log_audit(
            "visit_created",
            "visit",
            None,
            "Kunjungan baru dicatat.",
            {
                "patient_id": patient_id,
                "patient_name": patient_name_for_audit,
                "service_name": service_name or "Bekam",
                "therapist_name": therapist_name_for_audit,
                "quantity": point_count,
                "unit_label": unit_label_for_audit,
                "price": price,
                "is_free_visit": is_free_visit,
                "free_visit_reason": free_visit_reason if is_free_visit else "",
                "herbal_count": len(parsed_herbal_items),
            },
        )

        response = {"status": "success", "message": "Kunjungan berhasil dicatat."}
        _complete_visit_idempotency_key(reserved_idempotency_key, response)
        return response
    except HTTPException:
        _release_visit_idempotency_key(reserved_idempotency_key)
        raise
    except Exception as e:
        _release_visit_idempotency_key(reserved_idempotency_key)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update_visit")
async def update_visit(
    visit_id: int = Form(...),
    point_count: int = Form(...),
    price: float = Form(...),
    medical_notes: str = Form(""),
    therapist_id: int = Form(None),
    service_id: str = Form(""),
    service_name: str = Form(""),
    discount_applied: bool = Form(False),
    discount_rule_id: str = Form(""),
    discount_rule_name: str = Form(""),
    is_free_visit: bool = Form(False),
    free_visit_reason: str = Form(""),
    date: str = Form(""),
    payment_status: str = Form("paid"),
    payment_method: str = Form("cash"),
    amount_paid: Optional[int] = Form(None)
):
    try:
        require_valid_license()
        from database import HerbalTransaction, Visit
        with db.Session() as session:
            v = session.get(Visit, visit_id)
            if not v:
                raise HTTPException(status_code=404, detail="Kunjungan tidak ditemukan.")
            patient_id_for_audit = v.patient_id
            patient_name_for_audit = v.patient.name if getattr(v, "patient", None) else ""
            old_price = float(v.price or 0)
            old_quantity = int(v.point_count or 0)
            if price < 0:
                raise ValueError("Harga kunjungan tidak boleh kurang dari 0.")
            if price == 0 and not is_free_visit:
                raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis.")
            if is_free_visit and price != 0:
                raise ValueError("Kunjungan gratis harus memakai harga 0.")
            normalized_free_reason = free_visit_reason.strip() if is_free_visit else None
            if is_free_visit and not normalized_free_reason:
                raise ValueError("Alasan kunjungan gratis wajib diisi.")
            if point_count < 1:
                raise ValueError("Jumlah layanan minimal 1.")
            v.point_count   = point_count
            v.price         = price
            v.medical_notes = medical_notes
            v.therapist_id  = _validated_visit_therapist_id(session, v.patient, therapist_id)
            v.service_id = int(service_id) if str(service_id or "").strip() else None
            v.service_name = str(service_name or "").strip() or "Bekam"
            v.discount_applied = bool(discount_applied) and not is_free_visit
            v.discount_rule_id = int(discount_rule_id) if str(discount_rule_id or "").strip() and not is_free_visit else None
            v.discount_rule_name = str(discount_rule_name or "").strip() if not is_free_visit else None
            v.is_free_visit = is_free_visit
            v.free_visit_reason = normalized_free_reason

            linked_herbal_sales = (
                session.query(HerbalTransaction)
                .filter(
                    HerbalTransaction.visit_id == visit_id,
                    HerbalTransaction.transaction_type == "sale",
                )
                .order_by(HerbalTransaction.id.asc())
                .all()
            )
            herbal_total = sum(float(row.total_price or 0) for row in linked_herbal_sales)

            # Payment status updates
            payment = normalize_visit_payment(
                float(price or 0) + herbal_total,
                payment_status=payment_status,
                payment_method=payment_method,
                amount_paid=amount_paid,
                paid_at=v.paid_at,
                is_free_visit=is_free_visit,
                payment_provider=getattr(v, "payment_provider", None) or "manual",
            )
            component_payments = allocate_payment_amounts(
                payment["amount_paid"],
                [price] + [row.total_price for row in linked_herbal_sales],
            )
            v.payment_status = payment["payment_status"]
            v.payment_method = payment["payment_method"]
            v.amount_paid = component_payments[0] if component_payments else 0
            v.paid_at = payment["paid_at"]
            for row, paid_amount in zip(linked_herbal_sales, component_payments[1:]):
                row.payment_status = payment["payment_status"]
                row.payment_method = payment["payment_method"]
                row.amount_paid = paid_amount
                row.paid_at = payment["paid_at"]
            if date:
                try:
                    v.date = datetime.fromisoformat(date)
                except ValueError:
                    raise ValueError("Tanggal kunjungan tidak valid.")
            session.commit()
        db.log_audit("visit_updated", "visit", visit_id, "Kunjungan diperbarui.", {
            "patient_id": patient_id_for_audit,
            "patient_name": patient_name_for_audit,
            "service_name": service_name or "Bekam",
            "quantity": point_count,
            "old_quantity": old_quantity,
            "price": price,
            "old_price": old_price,
            "is_free_visit": is_free_visit,
            "free_visit_reason": normalized_free_reason or "",
        })
        return {"status": "success", "message": "Kunjungan berhasil diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/delete_visit")
async def delete_visit(request: Request, visit_id: int = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        from database import HerbalTransaction, Visit
        with db.Session() as session:
            v = session.get(Visit, visit_id)
            if not v:
                raise HTTPException(status_code=404, detail="Kunjungan tidak ditemukan.")
            herbal_count = (
                session.query(HerbalTransaction.id)
                .filter(HerbalTransaction.visit_id == visit_id)
                .count()
            )
            if (
                float(v.price or 0) > 0
                or int(v.point_count or 0) > 0
                or bool(v.invoice_path)
                or bool(v.service_id)
                or herbal_count > 0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Kunjungan sudah menjadi transaksi/laporan sehingga tidak boleh dihapus permanen. Gunakan void invoice atau koreksi tercatat.",
                )
            session.delete(v)
            session.commit()
        db.log_audit("visit_deleted", "visit", visit_id, "Kunjungan kosong dihapus.", {"visit_id": visit_id})
        return {"status": "success", "message": "Kunjungan kosong berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
