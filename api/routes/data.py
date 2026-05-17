from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import io, json
from datetime import datetime
from api.admin_pin import require_admin_pin
from api.database_manager import db
from api.license_guard import require_valid_license
from utils.app_paths import get_app_data_dir
import os

router = APIRouter()


def _is_blank(value):
    return value is None or str(value).strip() in ("", "-")


def _clean_text(value, default=""):
    if _is_blank(value):
        return default
    return str(value).strip()


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("ya", "yes", "true", "1", "y")


def _parse_optional_bool(value):
    if _is_blank(value):
        return None
    text_value = str(value).strip().lower()
    if text_value in ("ya", "yes", "true", "1", "y"):
        return True
    if text_value in ("tidak", "no", "false", "0", "n"):
        return False
    return None


def _parse_date(value):
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        return value
    text_value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(text_value, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        return None


def _parse_int(value, default=0):
    if _is_blank(value):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default

def _parse_positive_quantity(value, row_label, default_if_blank=1):
    if _is_blank(value):
        return default_if_blank
    try:
        quantity = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f"{row_label}: jumlah layanan/quantity harus berupa angka.")
    if quantity < 1:
        raise ValueError(f"{row_label}: jumlah layanan/quantity minimal 1.")
    return quantity


def _parse_float(value, default=0):
    if _is_blank(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _import_json_data(data):
    from database import VisitData

    therapists_imported = 0
    existing_therapists = {t.name.lower(): t for t in db.get_all_therapists(active_only=False)}
    for t in data.get("therapists", []):
        name = _clean_text(t.get("name"))
        if name and name.lower() not in existing_therapists:
            db.add_therapist(
                name,
                t.get("gender", "Laki-laki"),
                t.get("specialization", ""),
                _parse_bool(t.get("can_handle_any_gender", False)),
            )
            therapists_imported += 1
            existing_therapists[name.lower()] = True

    t_name_map = {t.name.lower(): t.id for t in db.get_all_therapists(active_only=False)}

    patients_imported = 0
    visits_imported = 0

    from database import Patient
    with db.Session() as session:
        existing_phones = {r[0] for r in session.query(Patient.phone).all() if r[0]}

    for patient_index, p in enumerate(data.get("patients", []), start=1):
        phone = _clean_text(p.get("phone"))
        name = _clean_text(p.get("name"))
        if not phone or not name or phone in existing_phones:
            continue
        existing_phones.add(phone)

        visit_objs = []
        for visit_index, v in enumerate(p.get("visits", []), start=1):
            row_label = f"Pasien #{patient_index} kunjungan #{visit_index}"
            vdate = _parse_date(v.get("date"))
            if not vdate:
                continue
            therapist_name = _clean_text(v.get("therapist_name")).lower()
            tid = t_name_map.get(therapist_name)
            is_free_visit = _parse_bool(v.get("is_free_visit"))
            price = 0 if is_free_visit else _parse_float(v.get("price"))
            point_count = _parse_positive_quantity(v.get("quantity", v.get("point_count")), row_label)
            free_visit_reason = _clean_text(v.get("free_visit_reason"), None)
            if is_free_visit and not free_visit_reason:
                raise ValueError(f"{row_label}: alasan kunjungan gratis wajib diisi.")
            visit_objs.append(VisitData(
                id=None,
                date=vdate,
                price=price,
                discount_applied=False if is_free_visit else _parse_bool(v.get("discount_applied")),
                point_count=point_count,
                therapist_id=tid,
                service_id=_parse_int(v.get("service_id"), None),
                service_name=_clean_text(v.get("service_name"), None),
                is_free_visit=is_free_visit,
                free_visit_reason=free_visit_reason,
                discount_rule_id=_parse_int(v.get("discount_rule_id"), None),
                discount_rule_name=_clean_text(v.get("discount_rule_name"), None),
            ))

        db.add_patient(name, phone, p.get("address", ""), p.get("gender", "Laki-laki"), visit_objs)
        patients_imported += 1
        visits_imported += len(visit_objs)

    return patients_imported, visits_imported, therapists_imported


def _import_xlsx_data(content: bytes):
    from database import VisitData
    from settings import AppSettings

    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl tidak terinstall. Jalankan: pip install openpyxl")

    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="File Excel kosong.")

    header = [str(c).strip().lower() if c is not None else "" for c in rows[0]]
    aliases = {
        "nama pasien": "name",
        "nama": "name",
        "name": "name",
        "telepon": "phone",
        "phone": "phone",
        "no hp": "phone",
        "nomor hp": "phone",
        "alamat": "address",
        "address": "address",
        "gender": "gender",
        "jenis kelamin": "gender",
        "tanggal kunjungan": "date",
        "tanggal": "date",
        "date": "date",
        "terapis": "therapist",
        "therapist": "therapist",
        "jumlah layanan": "point_count",
        "jumlah titik": "point_count",
        "titik": "point_count",
        "point_count": "point_count",
        "quantity": "point_count",
        "qty": "point_count",
        "jumlah": "point_count",
        "harga": "price",
        "price": "price",
        "diskon": "discount",
        "discount": "discount",
        "catatan": "medical_notes",
        "keterangan": "medical_notes",
        "medical_notes": "medical_notes",
        "kunjungan gratis": "is_free_visit",
        "gratis": "is_free_visit",
        "is_free_visit": "is_free_visit",
        "alasan gratis": "free_visit_reason",
        "catatan gratis": "free_visit_reason",
        "free_visit_reason": "free_visit_reason",
    }
    columns = [aliases.get(c, c) for c in header]

    required = {"name", "phone"}
    if not required.issubset(set(columns)):
        raise HTTPException(status_code=400, detail="Excel wajib memiliki kolom: Nama Pasien dan Telepon.")

    therapists_imported = 0
    therapist_map = {t.name.lower(): t.id for t in db.get_all_therapists(active_only=False)}
    patients = {}
    app_settings = AppSettings()
    discount_interval = max(1, int(app_settings.get_min_visits_for_discount() or 5))

    for row_number, raw_row in enumerate(rows[1:], start=2):
        row = {columns[i]: raw_row[i] if i < len(raw_row) else None for i in range(len(columns))}
        name = _clean_text(row.get("name"))
        phone = _clean_text(row.get("phone"))
        if not name or not phone:
            continue

        patient = patients.setdefault(phone, {
            "name": name,
            "phone": phone,
            "address": _clean_text(row.get("address")),
            "gender": _clean_text(row.get("gender"), "Laki-laki"),
            "visits": [],
        })
        if not patient["address"]:
            patient["address"] = _clean_text(row.get("address"))
        if not patient["gender"]:
            patient["gender"] = _clean_text(row.get("gender"), "Laki-laki")

        vdate = _parse_date(row.get("date"))
        if not vdate:
            continue

        therapist_name = _clean_text(row.get("therapist"))
        therapist_id = None
        if therapist_name:
            therapist_key = therapist_name.lower()
            therapist_id = therapist_map.get(therapist_key)
            if therapist_id is None:
                therapist_id = db.add_therapist(therapist_name, patient["gender"], "")
                therapist_map[therapist_key] = therapist_id
                therapists_imported += 1

        is_free_visit = _parse_bool(row.get("is_free_visit"))
        point_count = _parse_positive_quantity(row.get("point_count"), f"Baris Excel {row_number}")
        free_visit_reason = _clean_text(row.get("free_visit_reason"), None)
        if is_free_visit and not free_visit_reason:
            raise ValueError(f"Baris Excel {row_number}: alasan kunjungan gratis wajib diisi.")
        patient["visits"].append({
            "date": vdate,
            "price": 0 if is_free_visit else _parse_float(row.get("price")),
            "discount_override": _parse_optional_bool(row.get("discount")),
            "point_count": point_count,
            "therapist_id": therapist_id,
            "medical_notes": _clean_text(row.get("medical_notes"), None),
            "is_free_visit": is_free_visit,
            "free_visit_reason": free_visit_reason,
        })

    from database import Patient
    with db.Session() as session:
        existing_phones = {r[0] for r in session.query(Patient.phone).all() if r[0]}

    patients_imported = 0
    visits_imported = 0
    for patient in patients.values():
        if patient["phone"] in existing_phones:
            continue
        existing_phones.add(patient["phone"])
        visit_objs = []
        sorted_visits = sorted(patient["visits"], key=lambda visit: visit["date"])
        for index, visit in enumerate(sorted_visits, start=1):
            inferred_discount = (index >= discount_interval)
            discount_applied = visit["discount_override"] if visit["discount_override"] is not None else inferred_discount
            if visit["is_free_visit"]:
                discount_applied = False
            visit_objs.append(VisitData(
                id=None,
                date=visit["date"],
                price=visit["price"],
                discount_applied=discount_applied,
                point_count=visit["point_count"],
                therapist_id=visit["therapist_id"],
                medical_notes=visit["medical_notes"],
                is_free_visit=visit["is_free_visit"],
                free_visit_reason=visit["free_visit_reason"],
            ))
        db.add_patient(
            patient["name"],
            patient["phone"],
            patient["address"],
            patient["gender"] or "Laki-laki",
            visit_objs,
        )
        patients_imported += 1
        visits_imported += len(visit_objs)

    return patients_imported, visits_imported, therapists_imported

def _build_patient_export(format: str = "xlsx"):
    patients = db.get_all_patients()
    therapists = db.get_all_therapists(active_only=False)
    t_dict = {t.id: t.name for t in therapists}
    export_date = datetime.now().strftime('%Y%m%d')

    if format == "json":
        data = {
            "metadata": {"version": "1.0", "export_date": datetime.now().isoformat(), "app": "Lancar Dynamic Admin"},
            "therapists": [{
                "id": t.id,
                "name": t.name,
                "gender": t.gender,
                "specialization": t.specialization,
                "is_active": t.is_active,
                "can_handle_any_gender": t.can_handle_any_gender,
            } for t in therapists],
            "patients": [{
                "name": p.name, "phone": p.phone, "address": p.address, "gender": p.gender,
                "visits": [{
                    "date": v.date.isoformat() if hasattr(v.date, 'isoformat') else str(v.date),
                    "price": float(v.price or 0),
                    "final_price": float(v.price or 0),
                    "discount_applied": v.discount_applied,
                    "point_count": v.point_count,
                    "quantity": v.point_count,
                    "therapist_id": v.therapist_id,
                    "therapist_name": t_dict.get(v.therapist_id, ""),
                    "is_free_visit": getattr(v, "is_free_visit", False),
                    "free_visit_reason": getattr(v, "free_visit_reason", None),
                    "discount_rule_id": getattr(v, "discount_rule_id", None),
                    "discount_rule_name": getattr(v, "discount_rule_name", None),
                } for v in p.visits]
            } for p in patients]
        }
        return (
            f"data_pasien_{export_date}.json",
            json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8'),
            "application/json",
        )

    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl tidak terinstall. Jalankan: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Pasien"
    ws.append(["Nama Pasien", "Telepon", "Alamat", "Gender", "Tanggal Kunjungan", "Terapis", "Jumlah Layanan", "Harga", "Diskon", "Nama Diskon", "Catatan Gratis"])

    for p in patients:
        if not p.visits:
            ws.append([p.name, p.phone, p.address, p.gender, "-", "-", 0, 0, "-", "-", "-"])
        for v in p.visits:
            date_str = v.date.strftime("%Y-%m-%d %H:%M") if hasattr(v.date, 'strftime') else str(v.date)
            free_reason = getattr(v, "free_visit_reason", None) if getattr(v, "is_free_visit", False) else "-"
            ws.append([p.name, p.phone, p.address, p.gender, date_str, t_dict.get(v.therapist_id, "-"), v.point_count, float(v.price or 0), "Ya" if v.discount_applied else "Tidak", getattr(v, "discount_rule_name", None) or "-", free_reason])

    output = io.BytesIO()
    wb.save(output)
    return (
        f"data_pasien_{export_date}.xlsx",
        output.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _date_export_value(value):
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _sheet_rows_to_json(headers, rows):
    return [
        {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
        for row in rows
    ]


def _operational_export_sections(kind="all"):
    from database import (
        AuditLog,
        Herbal,
        HerbalTransaction,
        Inventory,
        InventoryTransaction,
        Patient,
        Service,
        ServiceInventoryUsage,
        Therapist,
        Visit,
    )
    from settings import AppSettings
    from sqlalchemy.orm import joinedload

    kind = str(kind or "all").strip().lower()
    if kind not in {"all", "patients", "herbals", "inventory", "audit_logs"}:
        kind = "all"

    sections = []
    with db.Session() as session:
        if kind in {"all", "patients"}:
            patients = session.query(Patient).order_by(Patient.name.asc()).all()
            sections.append((
                "Pasien",
                ["ID", "Nama", "Telepon", "Gender", "Alamat", "Tanggal Daftar"],
                [
                    [p.id, p.name, p.phone, p.gender, p.address, _date_export_value(getattr(p, "created_at", None))]
                    for p in patients
                ],
            ))

            visits = (
                session.query(Visit)
                .options(joinedload(Visit.patient), joinedload(Visit.therapist), joinedload(Visit.service))
                .order_by(Visit.date.desc())
                .all()
            )
            sections.append((
                "Kunjungan",
                ["ID", "Tanggal", "Pasien", "Telepon", "Layanan", "Terapis", "Quantity", "Harga", "Diskon", "Gratis", "Alasan Gratis", "Status Invoice"],
                [
                    [
                        v.id,
                        _date_export_value(v.date),
                        v.patient.name if v.patient else "",
                        v.patient.phone if v.patient else "",
                        (v.service.name if v.service else None) or v.service_name or "Layanan",
                        v.therapist.name if v.therapist else "",
                        int(v.point_count or 0),
                        float(v.price or 0),
                        "Ya" if v.discount_applied else "Tidak",
                        "Ya" if getattr(v, "is_free_visit", False) else "Tidak",
                        getattr(v, "free_visit_reason", None) or "",
                        getattr(v, "invoice_status", None) or "active",
                    ]
                    for v in visits
                ],
            ))

        if kind == "all":
            therapists = session.query(Therapist).order_by(Therapist.name.asc()).all()
            sections.append((
                "Terapis",
                ["ID", "Nama", "Gender", "Spesialisasi", "Aktif", "Bisa Lintas Gender"],
                [[
                    t.id,
                    t.name,
                    t.gender,
                    t.specialization,
                    "Ya" if t.is_active else "Tidak",
                    "Ya" if t.can_handle_any_gender else "Tidak",
                ] for t in therapists],
            ))

            services = session.query(Service).order_by(Service.name.asc()).all()
            sections.append((
                "Layanan",
                ["ID", "Nama", "Satuan", "Quantity Default", "Harga per Unit", "Aktif", "Catatan"],
                [[s.id, s.name, s.unit_label, int(s.default_quantity or 0), float(s.price_per_unit or 0), "Ya" if s.is_active else "Tidak", s.notes_template or ""] for s in services],
            ))

            usage_rows = (
                session.query(ServiceInventoryUsage)
                .options(joinedload(ServiceInventoryUsage.service), joinedload(ServiceInventoryUsage.inventory))
                .order_by(ServiceInventoryUsage.id.asc())
                .all()
            )
            sections.append((
                "Pemakaian Stok Layanan",
                ["ID", "Layanan", "Item Inventory", "Quantity"],
                [[u.id, u.service.name if u.service else "", u.inventory.item_name if u.inventory else "", int(u.quantity or 0)] for u in usage_rows],
            ))

        if kind in {"all", "inventory"}:
            inventory = session.query(Inventory).order_by(Inventory.item_name.asc()).all()
            sections.append((
                "Inventory",
                ["ID", "Item", "Quantity", "Unit", "Minimum", "Aktif", "Terakhir Update"],
                [[i.id, i.item_name, int(i.quantity or 0), i.unit, int(i.min_stock or 0), "Ya" if i.is_active else "Tidak", _date_export_value(i.last_updated)] for i in inventory],
            ))

            inventory_tx = (
                session.query(InventoryTransaction)
                .options(joinedload(InventoryTransaction.inventory))
                .order_by(InventoryTransaction.date.desc())
                .all()
            )
            sections.append((
                "Transaksi Inventory",
                ["ID", "Tanggal", "Item", "Perubahan", "Jenis", "Catatan"],
                [[tx.id, _date_export_value(tx.date), tx.inventory.item_name if tx.inventory else "", int(tx.change or 0), tx.transaction_type, tx.note or ""] for tx in inventory_tx],
            ))

        if kind in {"all", "herbals"}:
            herbals = session.query(Herbal).order_by(Herbal.name.asc()).all()
            sections.append((
                "Herbal",
                ["ID", "Nama", "Stok", "Harga", "Unit", "Aktif", "Terakhir Update"],
                [[h.id, h.name, int(h.stock or 0), float(h.price or 0), h.unit, "Ya" if h.is_active else "Tidak", _date_export_value(h.last_updated)] for h in herbals],
            ))

            herbal_tx = (
                session.query(HerbalTransaction)
                .options(joinedload(HerbalTransaction.herbal), joinedload(HerbalTransaction.visit).joinedload(Visit.patient))
                .order_by(HerbalTransaction.date.desc())
                .all()
            )
            sections.append((
                "Transaksi Herbal",
                ["ID", "Tanggal", "Herbal", "Quantity", "Total", "Jenis", "Pasien", "Sale Group", "Status Invoice", "Catatan"],
                [
                    [
                        tx.id,
                        _date_export_value(tx.date),
                        tx.herbal.name if tx.herbal else "",
                        int(tx.quantity or 0),
                        float(tx.total_price or 0),
                        tx.transaction_type,
                        tx.visit.patient.name if tx.visit and tx.visit.patient else "",
                        tx.sale_group_id or "",
                        tx.invoice_status or "",
                        tx.note or "",
                    ]
                    for tx in herbal_tx
                ],
            ))

        if kind in {"all", "audit_logs"}:
            audit_rows = session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(5000).all()
            sections.append((
                "Audit Log",
                ["ID", "Waktu", "Actor", "Action", "Entity", "Entity ID", "Deskripsi", "Metadata"],
                [[a.id, _date_export_value(a.created_at), a.actor, a.action, a.entity_type, a.entity_id or "", a.description or "", a.metadata_json or ""] for a in audit_rows],
            ))

    if kind == "all":
        safe_settings = AppSettings().get_all_settings()
        sections.append((
            "Settings Aman",
            ["Key", "Value"],
            [[key, json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value] for key, value in sorted(safe_settings.items())],
        ))

    return sections


def _build_operational_export(format: str = "xlsx", kind: str = "all"):
    export_date = datetime.now().strftime('%Y%m%d')
    kind = str(kind or "all").strip().lower()
    kind_slug = {
        "all": "semua_data",
        "patients": "pasien_kunjungan",
        "herbals": "herbal",
        "inventory": "inventory",
        "audit_logs": "audit_log",
    }.get(kind, "semua_data")
    sections = _operational_export_sections(kind)

    if format == "json":
        payload = {
            "metadata": {
                "version": "1.0",
                "export_date": datetime.now().isoformat(),
                "app": "Lancar Dynamic Admin",
                "kind": kind,
            },
            "sections": {
                title: _sheet_rows_to_json(headers, rows)
                for title, headers, rows in sections
            },
        }
        return (
            f"export_{kind_slug}_{export_date}.json",
            json.dumps(payload, indent=4, ensure_ascii=False).encode("utf-8"),
            "application/json",
        )

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl tidak terinstall. Jalankan: pip install openpyxl")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    header_fill = PatternFill("solid", fgColor="EAF3EF")
    for title, headers, rows in sections:
        ws = wb.create_sheet(title[:31])
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
        if rows:
            for row in rows:
                ws.append(row)
        else:
            ws.append(["Tidak ada data."])
        for column in ws.columns:
            letter = get_column_letter(column[0].column)
            width = max(len(str(cell.value or "")) for cell in column) + 2
            ws.column_dimensions[letter].width = min(max(width, 10), 44)

    output = io.BytesIO()
    wb.save(output)
    return (
        f"export_{kind_slug}_{export_date}.xlsx",
        output.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/export")
def export_data(request: Request, format: str = "xlsx", kind: str = "all"):
    try:
        require_valid_license()
        require_admin_pin(request)
        filename, content, media_type = _build_operational_export(format, kind)
        return StreamingResponse(io.BytesIO(content), media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/save")
def save_export_data(request: Request, format: str = "xlsx", kind: str = "all"):
    try:
        require_valid_license()
        require_admin_pin(request)
        filename, content, _media_type = _build_operational_export(format, kind)
        export_dir = os.path.join(get_app_data_dir(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(export_dir, filename))
        with open(file_path, "wb") as output_file:
            output_file.write(content)
        return {
            "status": "success",
            "message": "File export berhasil dibuat.",
            "filename": filename,
            "path": file_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_data(request: Request):
    try:
        require_valid_license()
        require_admin_pin(request)
        form = await request.form()
        file_blob = form.get("file")
        if not file_blob:
            raise HTTPException(status_code=400, detail="Tidak ada file yang diterima.")

        content = await file_blob.read()
        filename = getattr(file_blob, "filename", "") or ""

        if filename.lower().endswith(".xlsx"):
            patients_imported, visits_imported, therapists_imported = _import_xlsx_data(content)
        elif filename.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            patients_imported, visits_imported, therapists_imported = _import_json_data(data)
        else:
            raise HTTPException(status_code=400, detail="Format file tidak didukung. Gunakan .json atau .xlsx.")

        return {
            "status": "success",
            "message": f"Berhasil: {patients_imported} pasien, {visits_imported} kunjungan, {therapists_imported} terapis diimpor."
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Format file JSON tidak valid.")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import gagal: {e}")
