from __future__ import annotations

import io
import re
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import joinedload

from database import AuditLog, Herbal, HerbalTransaction, Inventory, Patient, Service, Therapist, Visit
from helpers.owner_report_helper import _between, _period_range, build_owner_report_summary


REPORT_LABELS = {
    "owner_summary": "Laporan Owner",
    "visits": "Laporan Kunjungan",
    "patients": "Laporan Pasien",
    "herbals": "Laporan Herbal",
    "inventory": "Laporan Inventori",
    "audit_logs": "Laporan Audit Log",
}


def safe_excel_filename(report_type, period_label):
    base = {
        "owner_summary": "laporan_owner",
        "visits": "laporan_kunjungan",
        "patients": "laporan_pasien",
        "herbals": "laporan_herbal",
        "inventory": "laporan_inventori",
        "audit_logs": "laporan_audit",
    }.get(str(report_type or "").strip(), "laporan")
    suffix = re.sub(r"[^A-Za-z0-9._-]+", "-", str(period_label or datetime.now().strftime("%Y-%m"))).strip("-")
    return f"{base}_{suffix or datetime.now().strftime('%Y-%m')}.xlsx"


def _date_text(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _add_title(ws, title, period_text):
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Periode: {period_text}"
    ws["A3"] = f"Tanggal export: {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def _append_table(ws, start_row, headers, rows):
    header_fill = PatternFill("solid", fgColor="EAF3EF")
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(start_row, col, header)
        cell.font = Font(bold=True)
        cell.fill = header_fill

    if not rows:
        ws.cell(start_row + 1, 1, "Tidak ada data untuk periode ini.")
        return start_row + 2

    for row_index, row in enumerate(rows, start=start_row + 1):
        for col_index, value in enumerate(row, start=1):
            cell = ws.cell(row_index, col_index, value)
            if isinstance(value, (int, float)) and any(word in str(headers[col_index - 1]).lower() for word in ("rp", "pendapatan", "revenue", "harga", "total")):
                cell.number_format = '#,##0'
    return start_row + len(rows) + 1


def _autosize(ws):
    for column in ws.columns:
        max_len = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            max_len = max(max_len, len(str(cell.value or "")))
        ws.column_dimensions[column_letter].width = min(max(max_len + 2, 10), 42)


def _workbook_bytes(wb):
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def _period_label(period_info):
    start = period_info.get("date_from") or ""
    end = period_info.get("date_to") or ""
    if start and end and start[:7] == end[:7]:
        return start[:7]
    return f"{start or 'awal'}_sd_{end or 'akhir'}"


def _period_text(start, end):
    return f"{start.strftime('%Y-%m-%d') if start else '-'} s/d {end.strftime('%Y-%m-%d') if end else '-'}"


def build_report_excel(session, report_type="owner_summary", period="month", year=None, month=None, date_from=None, date_to=None, new_patient_source="first_visit"):
    report_type = str(report_type or "owner_summary").strip().lower()
    if report_type not in REPORT_LABELS:
        raise ValueError("Jenis laporan tidak dikenal.")

    start, end = _period_range(period, year=year, month=month, date_from=date_from, date_to=date_to)
    wb = Workbook()
    ws = wb.active
    ws.title = REPORT_LABELS[report_type][:31]
    _add_title(ws, REPORT_LABELS[report_type], _period_text(start, end))

    if report_type == "owner_summary":
        report = build_owner_report_summary(
            session,
            period=period,
            year=year,
            month=month,
            date_from=date_from,
            date_to=date_to,
            new_patient_source=new_patient_source,
        )
        summary = report["summary"]
        _append_table(ws, 5, ["Metrik", "Nilai"], [
            ["Total Pendapatan", summary["total_revenue"]],
            ["Pendapatan Kunjungan", summary["visit_revenue"]],
            ["Pendapatan Herbal", summary["herbal_revenue"]],
            ["Total Kunjungan", summary["total_visits"]],
            ["Pasien Unik", summary["unique_patients"]],
            ["Pasien Baru", summary["new_patients"]],
            ["Pasien Aktif", summary["active_patients"]],
            ["Pasien Perlu Follow-up", summary["patients_need_followup"]],
            ["Pasien Lama Tidak Datang", summary["dormant_patients"]],
            ["Follow-up WhatsApp", summary["total_whatsapp_followups"]],
            ["Follow-up Booking", summary["followup_booked"]],
        ])

        row = 19
        row = _append_table(ws, row, ["Top Layanan", "Kunjungan", "Pendapatan"], [
            [item["name"], item["visits"], item["revenue"]] for item in report.get("top_services", [])
        ]) + 2
        row = _append_table(ws, row, ["Top Herbal", "Qty", "Pendapatan"], [
            [item["name"], item["quantity"], item["revenue"]] for item in report.get("top_herbals", [])
        ]) + 2
        _append_table(ws, row, ["Pasien Loyal", "Kunjungan", "Pendapatan", "Terakhir"], [
            [item["name"], item["visits"], item["revenue"], item["last_visit"]] for item in report.get("top_loyal_patients", [])
        ])
        filename = safe_excel_filename(report_type, _period_label(report["period"]))

    elif report_type == "visits":
        rows = (
            _between(
                session.query(Visit).options(joinedload(Visit.patient), joinedload(Visit.therapist), joinedload(Visit.service)),
                Visit.date,
                start,
                end,
            )
            .order_by(Visit.date.desc())
            .all()
        )
        _append_table(ws, 5, ["Tanggal", "Pasien", "Telepon", "Layanan", "Terapis", "Quantity", "Harga", "Status Invoice"], [
            [
                _date_text(row.date),
                row.patient.name if row.patient else "",
                row.patient.phone if row.patient else "",
                (row.service.name if row.service else None) or row.service_name or "Layanan",
                row.therapist.name if row.therapist else "",
                int(row.point_count or 0),
                float(row.price or 0),
                row.invoice_status or "active",
            ]
            for row in rows
        ])
        filename = safe_excel_filename(report_type, _period_text(start, end))

    elif report_type == "patients":
        rows = _between(session.query(Patient).options(joinedload(Patient.visits)), Patient.created_at, start, end).order_by(Patient.created_at.desc()).all()
        _append_table(ws, 5, ["Tanggal Daftar", "Nama", "Telepon", "Gender", "Alamat", "Jumlah Kunjungan"], [
            [_date_text(row.created_at), row.name, row.phone, row.gender, row.address, len(row.visits or [])]
            for row in rows
        ])
        filename = safe_excel_filename(report_type, _period_text(start, end))

    elif report_type == "herbals":
        rows = (
            _between(
                session.query(HerbalTransaction).options(joinedload(HerbalTransaction.herbal)),
                HerbalTransaction.date,
                start,
                end,
            )
            .order_by(HerbalTransaction.date.desc())
            .all()
        )
        _append_table(ws, 5, ["Tanggal", "Herbal", "Jenis", "Qty", "Total", "Status Invoice"], [
            [_date_text(row.date), row.herbal.name if row.herbal else "Herbal", row.transaction_type, int(row.quantity or 0), float(row.total_price or 0), row.invoice_status or ""]
            for row in rows
        ])
        filename = safe_excel_filename(report_type, _period_text(start, end))

    elif report_type == "inventory":
        rows = session.query(Inventory).order_by(Inventory.item_name.asc()).all()
        _append_table(ws, 5, ["Item", "Unit", "Stok", "Minimum", "Status"], [
            [row.item_name, row.unit, int(row.quantity or 0), int(row.min_stock or 0), "Aktif" if row.is_active else "Nonaktif"]
            for row in rows
        ])
        filename = safe_excel_filename(report_type, datetime.now().strftime("%Y-%m-%d"))

    else:
        rows = _between(session.query(AuditLog), AuditLog.created_at, start, end).order_by(AuditLog.created_at.desc()).limit(1000).all()
        _append_table(ws, 5, ["Waktu", "Actor", "Action", "Entity", "Entity ID", "Keterangan"], [
            [_date_text(row.created_at), row.actor, row.action, row.entity_type, row.entity_id or "", row.description or ""]
            for row in rows
        ])
        filename = safe_excel_filename(report_type, _period_text(start, end))

    _autosize(ws)
    return filename, _workbook_bytes(wb)
