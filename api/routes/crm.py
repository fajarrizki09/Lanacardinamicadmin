from fastapi import APIRouter, Form, HTTPException, Query, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db
from database import Patient
from helpers.crm_analysis_helper import (
    build_crm_conversion_report,
    build_crm_daily_tasks,
    build_crm_patients,
    build_followup_message,
    build_patient_message_logs,
    build_crm_tag_options,
    confirm_crm_whatsapp_log,
    create_crm_whatsapp_log,
    build_crm_summary,
    build_patient_followup_history,
    get_patient_active_vouchers,
    get_voucher_for_crm_message,
    get_patient_contact_preference,
    get_patient_tags,
    mark_whatsapp_contacted,
    save_followup_outcome,
    save_patient_contact_preference,
    save_patient_followup,
    save_patient_tags,
)

router = APIRouter(prefix="/crm")

CRM_LOAD_ERROR = "Gagal memuat data follow-up pasien. Silakan coba lagi."
CRM_SAVE_ERROR = "Gagal menyimpan data follow-up pasien. Silakan coba lagi."
CRM_VOUCHER_ERROR = "Gagal menyimpan voucher khusus pasien. Silakan coba lagi."
CRM_WHATSAPP_ERROR = "Gagal memproses WhatsApp follow-up. Silakan coba lagi."


def _internal_error(message=CRM_LOAD_ERROR):
    raise HTTPException(status_code=500, detail=message)


@router.get("/summary")
def get_crm_summary():
    try:
        with db.Session() as session:
            return build_crm_summary(session)
    except Exception:
        _internal_error()


@router.get("/patients")
def get_crm_patients(
    segment: str = Query(""),
    status: str = Query(""),
    search: str = Query(""),
    tag_type: str = Query(""),
    tag: str = Query(""),
):
    try:
        with db.Session() as session:
            return build_crm_patients(session, segment=segment, status=status, search=search, tag_type=tag_type, tag=tag)
    except Exception:
        _internal_error()


@router.get("/tag-options")
def get_crm_tag_options():
    try:
        with db.Session() as session:
            return build_crm_tag_options(session)
    except Exception:
        _internal_error()


@router.get("/daily-tasks")
def get_crm_daily_tasks():
    try:
        with db.Session() as session:
            return build_crm_daily_tasks(session)
    except Exception:
        _internal_error()


@router.get("/conversion-report")
def get_crm_conversion_report(start_date: str = Query(""), end_date: str = Query("")):
    try:
        with db.Session() as session:
            return build_crm_conversion_report(session, start_date=start_date or None, end_date=end_date or None)
    except Exception:
        _internal_error("Gagal memuat laporan booking follow-up. Silakan coba lagi.")


@router.get("/patient/{patient_id}")
def get_crm_patient(patient_id: int):
    try:
        with db.Session() as session:
            rows = build_crm_patients(session)
            for row in rows:
                if row["id"] == patient_id:
                    return row
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
    except HTTPException:
        raise
    except Exception:
        _internal_error()


@router.get("/patient/{patient_id}/message")
def get_crm_patient_message(patient_id: int, template: str = Query("kontrol")):
    try:
        with db.Session() as session:
            rows = build_crm_patients(session)
            for row in rows:
                if row["id"] == patient_id:
                    return build_followup_message(row, template=template)
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
    except HTTPException:
        raise
    except Exception:
        _internal_error("Gagal membuat pesan follow-up pasien. Silakan coba lagi.")


@router.post("/patient/{patient_id}/whatsapp-link")
async def create_crm_patient_whatsapp_link(
    request: Request,
    patient_id: int,
    template_type: str = Form("routine"),
    custom_message: str = Form(""),
    override_lock: bool = Form(False),
    mark_opened: bool = Form(False),
    voucher_rule_id: str = Form(""),
    allow_general_voucher: bool = Form(False),
):
    try:
        # require_admin_pin(request)  # Relaxed for operator flow
        with db.Session() as session:
            rows = build_crm_patients(session)
            for row in rows:
                if row["id"] == patient_id:
                    voucher = get_voucher_for_crm_message(
                        session,
                        patient_id,
                        voucher_rule_id,
                        allow_general=allow_general_voucher,
                    ) if str(voucher_rule_id or "").strip() else None
                    return create_crm_whatsapp_log(
                        session,
                        row,
                        template_type=template_type,
                        custom_message=custom_message or None,
                        override_lock=override_lock,
                        mark_opened=mark_opened,
                        voucher=voucher,
                    )
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_WHATSAPP_ERROR)


@router.post("/patient/{patient_id}/whatsapp-confirm")
async def confirm_crm_patient_whatsapp(
    request: Request,
    patient_id: int,
    log_id: str = Form(""),
    follow_up_date: str = Form(""),
):
    try:
        # require_admin_pin(request)  # Relaxed for operator flow
        with db.Session() as session:
            return confirm_crm_whatsapp_log(
                session,
                patient_id,
                log_id=log_id or None,
                follow_up_date=follow_up_date or None,
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_WHATSAPP_ERROR)


@router.post("/patient/{patient_id}/mark-whatsapp-contacted")
async def mark_crm_patient_whatsapp_contacted(
    request: Request,
    patient_id: int,
    follow_up_date: str = Form(""),
):
    try:
        # require_admin_pin(request)  # Relaxed for operator flow
        with db.Session() as session:
            followup_id = mark_whatsapp_contacted(session, patient_id, follow_up_date or None)
        return {"status": "success", "id": followup_id, "message": "Aktivitas WhatsApp dicatat sebagai sudah dihubungi."}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_WHATSAPP_ERROR)


@router.get("/patient/{patient_id}/message-logs")
def get_crm_patient_message_logs(patient_id: int):
    try:
        with db.Session() as session:
            return build_patient_message_logs(session, patient_id, limit=10)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        _internal_error("Gagal memuat riwayat WhatsApp pasien. Silakan coba lagi.")


@router.get("/patient/{patient_id}/vouchers")
def get_crm_patient_vouchers(patient_id: int):
    try:
        with db.Session() as session:
            return get_patient_active_vouchers(session, patient_id, include_general=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        _internal_error("Gagal memuat voucher pasien. Silakan coba lagi.")


@router.post("/patient/{patient_id}/vouchers")
async def create_crm_patient_voucher(
    request: Request,
    patient_id: int,
    name: str = Form(""),
    voucher_code: str = Form(""),
    discount_type: str = Form("fixed"),
    discount_value: str = Form(""),
    usage_limit: str = Form(""),
    per_patient_limit: str = Form("1"),
    end_date: str = Form(""),
):
    try:
        require_admin_pin(request)
        with db.Session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                raise ValueError("Pasien tidak ditemukan.")
        from datetime import datetime
        parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d") if str(end_date or "").strip() else None
        name = str(name or "").strip()
        voucher_code = str(voucher_code or "").strip()
        if not name or not voucher_code:
            raise ValueError("Nama voucher dan kode voucher wajib diisi.")
        if not str(discount_value or "").strip():
            raise ValueError("Nilai diskon voucher wajib diisi.")
        try:
            parsed_discount_value = float(discount_value)
        except (TypeError, ValueError):
            raise ValueError("Nilai diskon voucher harus berupa angka.")
        data = {
            "name": name,
            "type": "voucher",
            "discount_type": discount_type,
            "discount_value": parsed_discount_value,
            "voucher_code": voucher_code,
            "usage_limit": int(usage_limit) if str(usage_limit or "").strip() else None,
            "per_patient_limit": int(per_patient_limit) if str(per_patient_limit or "").strip() else 1,
            "end_date": parsed_end_date,
            "is_active": True,
            "priority": 10,
            "target_patient_ids": [patient_id],
        }
        if data["discount_type"] not in {"fixed", "percent"}:
            raise ValueError("Jenis diskon tidak valid.")
        if data["discount_value"] < 0 or (data["discount_type"] == "percent" and data["discount_value"] > 100):
            raise ValueError("Nilai diskon tidak valid.")
        rule_id = db.add_discount_rule(data)
        db.log_audit(
            "crm_special_voucher_created",
            "discount_rule",
            rule_id,
            "Voucher khusus pasien dibuat dari CRM.",
            {
                "patient_id": patient_id,
                "name": data["name"],
                "discount_type": data["discount_type"],
                "discount_value": data["discount_value"],
                "voucher_code": data["voucher_code"],
                "usage_limit": data["usage_limit"],
                "per_patient_limit": data["per_patient_limit"],
                "end_date": parsed_end_date.isoformat() if parsed_end_date else "",
            },
        )
        with db.Session() as session:
            vouchers = get_patient_active_vouchers(session, patient_id, include_general=True)
        return {"status": "success", "message": "Voucher khusus berhasil dibuat.", "rule_id": rule_id, "vouchers": vouchers}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        _internal_error(CRM_VOUCHER_ERROR)


@router.get("/patient/{patient_id}/followups")
def get_crm_patient_followups(patient_id: int):
    try:
        with db.Session() as session:
            return build_patient_followup_history(session, patient_id, limit=10)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        _internal_error("Gagal memuat riwayat follow-up pasien. Silakan coba lagi.")


@router.get("/patient/{patient_id}/tags")
def get_crm_patient_tags(patient_id: int):
    try:
        with db.Session() as session:
            return get_patient_tags(session, patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        _internal_error("Gagal memuat tag pasien. Silakan coba lagi.")


@router.post("/patient/{patient_id}/tags")
async def update_crm_patient_tags(request: Request, patient_id: int, tags: str = Form("")):
    try:
        require_admin_pin(request)
        import json
        try:
            parsed = json.loads(tags or "[]")
        except json.JSONDecodeError:
            raise ValueError("Format tag pasien tidak valid.")
        with db.Session() as session:
            return save_patient_tags(session, patient_id, parsed)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_SAVE_ERROR)


@router.get("/patient/{patient_id}/contact-preference")
def get_crm_patient_contact_preference(patient_id: int):
    try:
        with db.Session() as session:
            return get_patient_contact_preference(session, patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        _internal_error("Gagal memuat izin kontak pasien. Silakan coba lagi.")


@router.post("/patient/{patient_id}/contact-preference")
async def update_crm_patient_contact_preference(
    request: Request,
    patient_id: int,
    boleh_reminder_kontrol: bool = Form(True),
    boleh_promo: bool = Form(True),
    jangan_dihubungi: bool = Form(False),
    catatan_kontak: str = Form(""),
):
    try:
        require_admin_pin(request)
        with db.Session() as session:
            return save_patient_contact_preference(session, patient_id, {
                "boleh_reminder_kontrol": boleh_reminder_kontrol,
                "boleh_promo": boleh_promo,
                "jangan_dihubungi": jangan_dihubungi,
                "catatan_kontak": catatan_kontak,
            })
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_SAVE_ERROR)


@router.post("/patient/{patient_id}/followup-outcome")
async def update_crm_followup_outcome(
    request: Request,
    patient_id: int,
    outcome: str = Form(...),
    note: str = Form(""),
    follow_up_date: str = Form(""),
):
    try:
        # require_admin_pin(request)  # Relaxed for operator flow
        with db.Session() as session:
            return save_followup_outcome(session, patient_id, outcome, note, follow_up_date or None)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_SAVE_ERROR)


@router.post("/followup")
async def create_crm_followup(
    request: Request,
    patient_id: int = Form(...),
    status: str = Form("contacted"),
    note: str = Form(""),
    follow_up_date: str = Form(""),
):
    try:
        # require_admin_pin(request)  # Relaxed for operator flow
        with db.Session() as session:
            followup_id = save_patient_followup(session, patient_id, status, note, follow_up_date or None)
        return {"status": "success", "id": followup_id, "message": "Follow-up CRM tersimpan."}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        _internal_error(CRM_SAVE_ERROR)
