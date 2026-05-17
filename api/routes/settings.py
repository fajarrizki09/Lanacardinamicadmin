from datetime import datetime
import os
import json
import re

from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
import sys
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license
from helpers.backup_helper import BackupHelper
from utils.app_paths import get_app_data_dir

router = APIRouter()

LOGO_MAX_BYTES = 2 * 1024 * 1024
LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _detect_logo_extension(filename, content, content_type=""):
    ext = os.path.splitext(filename or "")[1].lower()
    content_type = (content_type or "").lower()
    if ext not in LOGO_EXTENSIONS:
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = ".png"
        elif content.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
            ext = ".webp"
        elif content_type == "image/png":
            ext = ".png"
        elif content_type in {"image/jpeg", "image/jpg"}:
            ext = ".jpg"
        elif content_type == "image/webp":
            ext = ".webp"
    if ext not in LOGO_EXTENSIONS:
        raise ValueError("Format logo tidak didukung. Gunakan PNG, JPG, JPEG, atau WebP.")
    return ".jpg" if ext == ".jpeg" else ext


def _save_logo_upload(filename, content, content_type=""):
    if not content:
        raise ValueError("File logo kosong.")
    if len(content) > LOGO_MAX_BYTES:
        raise ValueError("Ukuran logo maksimal 2 MB.")
    ext = _detect_logo_extension(filename, content, content_type)
    logo_dir = os.path.join(get_app_data_dir(), "assets", "logos")
    os.makedirs(logo_dir, exist_ok=True)
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", os.path.splitext(filename or "clinic_logo")[0]).strip("_")
    if not safe_stem:
        safe_stem = "clinic_logo"
    logo_path = os.path.join(logo_dir, f"{safe_stem[:40]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
    with open(logo_path, "wb") as logo_file:
        logo_file.write(content)
    return logo_path


def _parse_optional_float(value):
    text = str(value or "").strip()
    if not text:
        return None
    return float(text)


def _parse_optional_int(value):
    text = str(value or "").strip()
    if not text:
        return None
    parsed = int(text)
    return parsed if parsed > 0 else None


def _parse_optional_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%d")


def _discount_rule_payload(rule):
    def _date_value(value):
        return value.strftime("%Y-%m-%d") if value else ""

    return {
        "id": rule.id,
        "name": rule.name,
        "type": rule.type,
        "discount_type": rule.discount_type,
        "discount_value": rule.discount_value,
        "condition_value": rule.condition_value,
        "voucher_code": rule.voucher_code or "",
        "start_date": _date_value(rule.start_date),
        "end_date": _date_value(rule.end_date),
        "is_active": rule.is_active,
        "priority": rule.priority,
        "created_at": rule.created_at.strftime("%Y-%m-%d %H:%M:%S") if rule.created_at else "",
        "usage_limit": rule.usage_limit,
        "per_patient_limit": rule.per_patient_limit,
        "usage_count": getattr(rule, "usage_count", 0),
        "target_patient_ids": getattr(rule, "target_patient_ids", []),
        "target_patient_names": getattr(rule, "target_patient_names", []),
    }


def _discount_preview_payload(rule, price):
    final_price = db._apply_discount_value(float(price or 0), rule)
    return {
        **_discount_rule_payload(rule),
        "final_price": round(final_price, 2),
        "discount_amount": round(max(0, float(price or 0) - final_price), 2),
    }


def _attach_discount_rule_metadata(session, rules):
    if not rules:
        return rules
    from database import Patient, VoucherPatientTarget, VoucherUsage
    from sqlalchemy import func

    rule_ids = [rule.id for rule in rules]
    usage_rows = (
        session.query(VoucherUsage.discount_rule_id, func.count(VoucherUsage.id))
        .filter(VoucherUsage.discount_rule_id.in_(rule_ids))
        .group_by(VoucherUsage.discount_rule_id)
        .all()
    )
    usage_by_rule = {rule_id: int(count or 0) for rule_id, count in usage_rows}
    target_rows = (
        session.query(VoucherPatientTarget.discount_rule_id, VoucherPatientTarget.patient_id, Patient.name)
        .join(Patient, Patient.id == VoucherPatientTarget.patient_id)
        .filter(VoucherPatientTarget.discount_rule_id.in_(rule_ids))
        .order_by(Patient.name.asc())
        .all()
    )
    targets_by_rule = {}
    names_by_rule = {}
    for rule_id, patient_id, patient_name in target_rows:
        targets_by_rule.setdefault(rule_id, []).append(patient_id)
        names_by_rule.setdefault(rule_id, []).append(patient_name)
    for rule in rules:
        rule.usage_count = usage_by_rule.get(rule.id, 0)
        rule.target_patient_ids = targets_by_rule.get(rule.id, [])
        rule.target_patient_names = names_by_rule.get(rule.id, [])
    return rules


def _backup_helper():
    base_dir = get_app_data_dir()
    return BackupHelper(
        db_path=os.path.join(base_dir, "data.db"),
        backup_dir=os.path.join(base_dir, "backups"),
        max_backups=10,
        log_dir=os.path.join(base_dir, "logs"),
    )


def _backup_payload(path):
    backup_dir = _backup_helper().backup_dir
    stat = os.stat(path)
    return {
        "name": os.path.basename(path),
        "path": os.path.relpath(path, backup_dir).replace("\\", "/"),
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def _resolve_backup_path(relative_path):
    backup_root = os.path.abspath(_backup_helper().backup_dir)
    target = os.path.abspath(os.path.join(backup_root, str(relative_path or "")))
    if os.path.commonpath([backup_root, target]) != backup_root:
        raise ValueError("Path backup tidak valid.")
    if not target.lower().endswith(".db"):
        raise ValueError("File backup harus berformat .db.")
    return target

@router.get("/settings")
def get_settings():
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        s = AppSettings()
        return s.get_all_settings()
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat pengaturan. Coba lagi atau hubungi admin.")


@router.post("/settings/logo")
async def upload_settings_logo(request: Request):
    try:
        require_valid_license()
        require_admin_pin(request)
        form = await request.form()
        file_blob = form.get("logo")
        if not file_blob:
            raise ValueError("Pilih file logo terlebih dahulu.")
        content = await file_blob.read()
        filename = getattr(file_blob, "filename", "") or "clinic_logo"
        content_type = getattr(file_blob, "content_type", "") or ""
        logo_path = _save_logo_upload(filename, content, content_type)
        return {
            "status": "success",
            "message": "Logo klinik berhasil dipilih.",
            "path": logo_path,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal upload logo. Pastikan file valid dan coba lagi.")


@router.get("/first_run/status")
def first_run_status():
    from settings import AppSettings
    s = AppSettings()
    return {
        "completed": s.is_first_run_completed(),
        "settings": s.get_all_settings(),
    }


@router.post("/first_run/complete")
async def complete_first_run(
    clinic_name: str = Form(""),
    clinic_address: str = Form(""),
    clinic_phone: str = Form(""),
    clinic_logo_path: str = Form(""),
    invoice_prefix: str = Form("INV"),
    services: str = Form("[]"),
    skipped: bool = Form(False),
):
    try:
        require_valid_license()
        from settings import AppSettings
        s = AppSettings()
        parsed_services = []
        if not skipped:
            if not clinic_name.strip():
                raise ValueError("Nama klinik wajib diisi.")
            parsed_services = json.loads(services or "[]")
            if not isinstance(parsed_services, list) or not parsed_services:
                raise ValueError("Minimal isi satu layanan awal.")

        s.complete_first_run(
            {
                "clinic_name": clinic_name,
                "clinic_address": clinic_address,
                "clinic_phone": clinic_phone,
                "clinic_logo_path": clinic_logo_path,
                "invoice_prefix": invoice_prefix or "INV",
            },
            skipped=skipped,
        )
        created_services = 0
        existing_names = {service.name.lower() for service in db.get_all_services(active_only=False)}
        for service in parsed_services[:3]:
            name = str((service or {}).get("name") or "").strip()
            if not name or name.lower() in existing_names:
                continue
            db.add_service(
                name,
                unit_label=str((service or {}).get("unit_label") or "sesi").strip() or "sesi",
                default_quantity=max(1, int((service or {}).get("default_quantity") or 1)),
                price_per_unit=max(0, float((service or {}).get("price_per_unit") or 0)),
            )
            created_services += 1
        db.log_audit(
            "first_run_completed" if not skipped else "first_run_skipped",
            "settings",
            "first_run",
            "Setup awal disimpan." if not skipped else "Setup awal dilewati.",
            {"created_services": created_services},
        )
        return {"status": "success", "message": "Setup awal berhasil disimpan." if not skipped else "Setup awal dilewati."}
    except HTTPException:
        raise
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise


@router.post("/demo_data/seed")
async def seed_demo_data(request: Request):
    try:
        require_valid_license()
        require_admin_pin(request)
        result = db.seed_demo_data()
        return {"status": "success", **result}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise


@router.post("/demo_data/clear")
async def clear_demo_data(request: Request):
    try:
        require_valid_license()
        require_admin_pin(request)
        return db.clear_demo_data()
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise


@router.get("/free_visit_reasons")
def get_free_visit_reasons():
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        return {"items": AppSettings().get_free_visit_reasons()}
    except Exception:
        raise HTTPException(status_code=500, detail="Gagal memuat alasan kunjungan gratis. Hubungi admin.")


@router.post("/free_visit_reasons")
async def save_free_visit_reasons(request: Request, reasons: str = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        items = [line.strip() for line in str(reasons or "").splitlines()]
        s = AppSettings()
        s.set_free_visit_reasons(items)
        return {
            "status": "success",
            "message": "Alasan kunjungan gratis berhasil disimpan.",
            "items": s.get_free_visit_reasons(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/backups")
def get_backups(request: Request):
    try:
        require_admin_pin(request)
        helper = _backup_helper()
        files = helper._list_backup_files()
        files = sorted(files, key=os.path.getmtime, reverse=True)
        total_size = sum(os.path.getsize(path) for path in files)
        return {
            "status": helper.get_status(),
            "items": [_backup_payload(path) for path in files],
            "count": len(files),
            "total_size": total_size,
            "backup_dir": os.path.abspath(helper.backup_dir),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/create")
async def create_backup_now(request: Request):
    try:
        require_valid_license()
        require_admin_pin(request)
        helper = _backup_helper()
        path = helper.create_backup(daily=False)
        if not path:
            raise ValueError(helper.get_status().get("message") or "Backup gagal dibuat.")
        db.log_audit("backup_created", "backup", None, "Backup database dibuat.", {"path": os.path.basename(path)})
        return {"status": "success", "message": "Backup database berhasil dibuat.", "backup": _backup_payload(path)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backups/restore")
async def restore_backup(request: Request, relative_path: str = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        path = _resolve_backup_path(relative_path)
        helper = _backup_helper()
        db.engine.dispose()
        status = helper.restore_backup(path)
        db.engine.dispose()
        if not status.get("success"):
            raise ValueError(status.get("message") or "Restore backup gagal.")
        db.log_audit("backup_restored", "backup", None, "Database direstore dari backup.", {"path": os.path.basename(path)})
        return {
            "status": "success",
            "message": "Backup berhasil direstore. Silakan reload atau restart aplikasi agar data terbaru terbaca sempurna.",
            "backup": status,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discount_rules")
def get_discount_rules():
    try:
        return [_discount_rule_payload(rule) for rule in db.get_discount_rules()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discount_rules/simulate")
def simulate_discount_rules(
    price: float = 100000,
    visit_count: int = 0,
    patient_id: int = 0,
    voucher_code: str = "",
    manual_price_used: bool = False,
):
    try:
        if price <= 0:
            return {"selected": None, "matches": [], "message": "Harga 0 atau gratis tidak memakai diskon otomatis."}
        now = datetime.now()
        with db.Session() as session:
            from database import DiscountRule, Patient
            effective_visit_count = int(visit_count or 0)
            if int(patient_id or 0) > 0:
                patient = session.get(Patient, int(patient_id))
                if patient:
                    effective_visit_count = sum(
                        1 for visit in patient.visits
                        if db._is_active_visit_for_discount_count(visit)
                    )
            rules = (
                session.query(DiscountRule)
                .filter(DiscountRule.is_active == True)
                .order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc())
                .all()
            )
            _attach_discount_rule_metadata(session, rules)
            matches = [
                _discount_preview_payload(rule, price)
                for rule in rules
                if db._rule_matches(
                    rule,
                    effective_visit_count,
                    manual_price_used=manual_price_used,
                    voucher_code=voucher_code,
                    current_dt=now,
                    session=session,
                    patient_id=int(patient_id or 0) or None,
                )
            ]
        selected = matches[0] if matches else None
        if selected and len(matches) > 1:
            message = "Ada beberapa diskon cocok. Sistem hanya memakai aturan teratas berdasarkan prioritas."
        elif selected:
            message = "Diskon ini akan dipakai untuk kunjungan baru."
        else:
            message = "Tidak ada diskon aktif yang cocok dengan simulasi."
        return {"selected": selected, "matches": matches, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discount_rules")
async def save_discount_rule(
    request: Request,
    rule_id: int = Form(0),
    name: str = Form(...),
    type: str = Form(...),
    discount_type: str = Form(...),
    discount_value: float = Form(...),
    condition_value: str = Form(""),
    voucher_code: str = Form(""),
    usage_limit: str = Form(""),
    per_patient_limit: str = Form(""),
    target_patient_ids: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    is_active: str = Form("on"),
    priority: int = Form(100),
):
    try:
        require_valid_license()
        require_admin_pin(request)
        if type not in {"visit_count", "voucher", "manual", "period"}:
            raise ValueError("Tipe aturan diskon tidak valid.")
        if discount_type not in {"percent", "fixed"}:
            raise ValueError("Jenis diskon tidak valid.")
        if discount_value < 0:
            raise ValueError("Nilai diskon tidak boleh negatif.")
        if discount_type == "percent" and discount_value > 100:
            raise ValueError("Diskon persen maksimal 100%.")
        if type == "visit_count" and not _parse_optional_float(condition_value):
            raise ValueError("Diskon jumlah kunjungan wajib memiliki nilai kondisi.")
        if type == "voucher" and not voucher_code.strip():
            raise ValueError("Voucher wajib memiliki kode voucher.")
        if type == "period" and not (start_date.strip() or end_date.strip()):
            raise ValueError("Diskon periode wajib memiliki tanggal mulai atau selesai.")
        parsed_start_date = _parse_optional_date(start_date)
        parsed_end_date = _parse_optional_date(end_date)
        parsed_usage_limit = _parse_optional_int(usage_limit) if type == "voucher" else None
        parsed_per_patient_limit = _parse_optional_int(per_patient_limit) if type == "voucher" else None
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise ValueError("Tanggal mulai tidak boleh setelah tanggal selesai.")

        data = {
            "name": name.strip(),
            "type": type,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "condition_value": _parse_optional_float(condition_value),
            "voucher_code": voucher_code.strip(),
            "start_date": parsed_start_date,
            "end_date": parsed_end_date,
            "usage_limit": parsed_usage_limit,
            "per_patient_limit": parsed_per_patient_limit,
            "target_patient_ids": [
                item.strip()
                for item in str(target_patient_ids or "").split(",")
                if item.strip()
            ] if type == "voucher" else [],
            "is_active": str(is_active).lower() in {"1", "true", "yes", "on"},
            "priority": priority,
        }
        if not data["name"]:
            raise ValueError("Nama aturan diskon wajib diisi.")

        if int(rule_id or 0) > 0:
            ok = db.update_discount_rule(rule_id, data)
            if not ok:
                raise ValueError("Aturan diskon tidak ditemukan.")
            db.log_audit("discount_rule_updated", "discount_rule", rule_id, "Aturan diskon diperbarui.", {
                "name": data["name"],
                "type": data["type"],
                "discount_type": data["discount_type"],
                "discount_value": data["discount_value"],
                "condition_value": data["condition_value"],
                "voucher_code": data["voucher_code"],
                "is_active": data["is_active"],
                "priority": data["priority"],
            })
            message = "Aturan diskon berhasil diperbarui."
        else:
            new_rule_id = db.add_discount_rule(data)
            db.log_audit("discount_rule_created", "discount_rule", new_rule_id, "Aturan diskon ditambahkan.", {
                "name": data["name"],
                "type": data["type"],
                "discount_type": data["discount_type"],
                "discount_value": data["discount_value"],
                "condition_value": data["condition_value"],
                "voucher_code": data["voucher_code"],
                "is_active": data["is_active"],
                "priority": data["priority"],
            })
            message = "Aturan diskon berhasil ditambahkan."
        return {"status": "success", "message": message}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discount_rules/{rule_id}/toggle")
async def toggle_discount_rule(request: Request, rule_id: int, is_active: bool = Form(...)):
    try:
        require_valid_license()
        require_admin_pin(request)
        ok = db.set_discount_rule_active(rule_id, is_active)
        if not ok:
            raise HTTPException(status_code=404, detail="Aturan diskon tidak ditemukan.")
        db.log_audit("discount_rule_toggled", "discount_rule", rule_id, "Status aturan diskon diperbarui.", {
            "is_active": is_active,
        })
        return {"status": "success", "message": "Status aturan diskon diperbarui."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discount_rules/{rule_id}/delete")
async def delete_discount_rule(request: Request, rule_id: int):
    try:
        require_valid_license()
        require_admin_pin(request)
        ok = db.delete_discount_rule(rule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Aturan diskon tidak ditemukan.")
        action_message = "Aturan diskon dinonaktifkan karena sudah pernah dipakai." if ok == "deactivated" else "Aturan diskon dihapus."
        db.log_audit("discount_rule_deleted", "discount_rule", rule_id, "Aturan diskon dihapus.", {
            "rule_id": rule_id,
            "result": ok,
        })
        return {"status": "success", "message": action_message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/settings")
async def update_settings(
    request: Request,
    base_price: int = Form(100000),
    price_per_point: int = Form(10000),
    discount_percentage: int = Form(50),
    min_visits_for_discount: int = Form(5),
    clinic_name: str = Form("Lancar Dynamic Admin"),
    clinic_tagline: str = Form("Clinic Management System"),
    clinic_address: str = Form(""),
    clinic_phone: str = Form(""),
    clinic_email: str = Form(""),
    clinic_website: str = Form(""),
    clinic_logo_path: str = Form(""),
    invoice_footer: str = Form("Semoga menjadi wasilah ikhtiar kesembuhan yang berkah."),
    admin_label: str = Form("Admin Klinik,"),
    payment_gateway_enabled: str = Form(""),
    payment_gateway_default_provider: str = Form("gateway_mock"),
    payment_gateway_environment: str = Form("sandbox"),
    midtrans_server_key: str = Form(""),
    midtrans_client_key: str = Form(""),
    midtrans_merchant_id: str = Form(""),
    xendit_secret_key: str = Form(""),
    duitku_merchant_code: str = Form(""),
    duitku_api_key: str = Form("")
):
    try:
        require_valid_license()
        require_admin_pin(request)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from settings import AppSettings
        s = AppSettings()
        s.set_base_price(base_price)
        s.set_price_per_point(price_per_point)
        s.set_discount_percentage(discount_percentage)
        s.set_min_visits_for_discount(min_visits_for_discount)
        s.save_custom_invoice_settings({
            "clinic_name": clinic_name,
            "clinic_tagline": clinic_tagline,
            "clinic_address": clinic_address,
            "clinic_phone": clinic_phone,
            "clinic_email": clinic_email,
            "clinic_website": clinic_website,
            "clinic_logo_path": clinic_logo_path,
            "invoice_footer": invoice_footer,
            "admin_label": admin_label
        })
        s.set_payment_gateway_settings({
            "payment_gateway_enabled": str(payment_gateway_enabled).lower() in {"1", "true", "yes", "on"},
            "payment_gateway_default_provider": payment_gateway_default_provider,
            "payment_gateway_environment": payment_gateway_environment,
            "midtrans_server_key": midtrans_server_key,
            "midtrans_client_key": midtrans_client_key,
            "midtrans_merchant_id": midtrans_merchant_id,
            "xendit_secret_key": xendit_secret_key,
            "duitku_merchant_code": duitku_merchant_code,
            "duitku_api_key": duitku_api_key,
        })
        db.log_audit("settings_updated", "settings", "clinic", "Pengaturan klinik diperbarui.", {
            "clinic_name": clinic_name,
            "clinic_phone": clinic_phone,
            "base_price": base_price,
            "price_per_point": price_per_point,
            "discount_percentage": discount_percentage,
            "min_visits_for_discount": min_visits_for_discount,
            "payment_gateway_enabled": str(payment_gateway_enabled).lower() in {"1", "true", "yes", "on"},
            "payment_gateway_default_provider": payment_gateway_default_provider,
            "payment_gateway_environment": payment_gateway_environment,
        })
        return {"status": "success", "message": "Pengaturan berhasil disimpan."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
