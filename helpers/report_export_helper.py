from datetime import datetime
import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


class ReportExportHelper:
    """Export laporan operasional tanpa mencampur logic laporan ke UI."""

    def __init__(self, db, settings_source=None):
        self.db = db
        self.settings_source = settings_source

    def get_clinic_profile(self):
        if self.settings_source and hasattr(self.settings_source, "get_clinic_profile"):
            return self.settings_source.get_clinic_profile()
        if self.settings_source and hasattr(self.settings_source, "get_custom_invoice_settings"):
            return self.settings_source.get_custom_invoice_settings()
        return {
            "clinic_name": "Lancar Dynamic Admin",
            "clinic_tagline": "Professional Cupping Therapy",
            "clinic_address": "",
            "clinic_phone": "",
            "clinic_email": "",
            "clinic_website": "",
            "clinic_logo_path": "",
        }

    def _format_visit_date(self, value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M")
        return str(value) if value else "-"

    def _matches_month(self, value, target_month):
        if not target_month:
            return True
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m") == target_month
        return str(value).startswith(target_month)

    def build_patient_visit_rows(self, target_month=None):
        patients = self.db.get_all_patients()
        therapists = self.db.get_all_therapists(active_only=False)
        therapist_names = {t.id: t.name for t in therapists}
        rows = []

        for patient in patients:
            visits = patient.visits
            if target_month:
                visits = [v for v in visits if self._matches_month(v.date, target_month)]

            if not visits and not target_month:
                rows.append({
                    "Nama Pasien": patient.name,
                    "Telepon": patient.phone,
                    "Gender": patient.gender,
                    "Tanggal Kunjungan": "-",
                    "Layanan": "-",
                    "Terapis": "-",
                    "Jumlah": 0,
                    "Harga": 0,
                    "Diskon": "-",
                    "Nama Diskon": "-",
                    "Catatan Gratis": "-",
                })
                continue

            for visit in visits:
                rows.append({
                    "Nama Pasien": patient.name,
                    "Telepon": patient.phone,
                    "Gender": patient.gender,
                    "Tanggal Kunjungan": self._format_visit_date(visit.date),
                    "Layanan": getattr(visit, "service_name", None) or "Bekam",
                    "Terapis": therapist_names.get(visit.therapist_id, "-"),
                    "Jumlah": visit.point_count,
                    "Harga": float(visit.price or 0),
                    "Status Invoice": getattr(visit, "invoice_status", None) or "active",
                    "Alasan Void": getattr(visit, "void_reason", None) or "-",
                    "Diskon": "Ya" if visit.discount_applied else "Tidak",
                    "Nama Diskon": getattr(visit, "discount_rule_name", None) or "-",
                    "Catatan Gratis": visit.free_visit_reason if getattr(visit, "is_free_visit", False) else "-",
                })

        return rows

    def export_patient_visit_excel(self, file_path, target_month=None):
        rows = self.build_patient_visit_rows(target_month=target_month)
        if not rows:
            raise ValueError("Tidak ada data laporan untuk periode tersebut.")

        profile = self.get_clinic_profile()
        info_rows = [
            ["Nama Klinik", profile.get("clinic_name", "")],
            ["Tagline", profile.get("clinic_tagline", "")],
            ["Alamat", profile.get("clinic_address", "")],
            ["Kontak", profile.get("clinic_phone", "")],
            ["Email", profile.get("clinic_email", "")],
            ["Website", profile.get("clinic_website", "")],
            ["Logo", profile.get("clinic_logo_path", "")],
            ["Dibuat", datetime.now().strftime("%d %b %Y %H:%M")],
        ]
        with pd.ExcelWriter(file_path) as writer:
            pd.DataFrame(info_rows, columns=["Profil", "Nilai"]).to_excel(
                writer, sheet_name="Laporan", index=False, header=False
            )
            pd.DataFrame(rows).to_excel(writer, sheet_name="Laporan", index=False, startrow=len(info_rows) + 2)
        return file_path

    def export_patient_visit_pdf(self, file_path, target_month=None):
        rows = self.build_patient_visit_rows(target_month=target_month)
        if not rows:
            raise ValueError("Tidak ada data laporan untuk periode tersebut.")

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=1.2 * cm, leftMargin=1.2 * cm)
        styles = getSampleStyleSheet()
        profile = self.get_clinic_profile()
        title = "Laporan Pasien & Kunjungan"
        if target_month:
            title += f" - {target_month}"

        clinic_lines = [
            profile.get("clinic_tagline", ""),
            profile.get("clinic_address", ""),
            " | ".join([p for p in [
                profile.get("clinic_phone", ""),
                profile.get("clinic_email", ""),
                profile.get("clinic_website", ""),
            ] if p]),
        ]
        clinic_lines = [line for line in clinic_lines if line]

        story = []
        logo_path = profile.get("clinic_logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=3.2 * cm, height=1.6 * cm)
                logo.hAlign = "CENTER"
                story.append(logo)
            except Exception:
                pass
        story.extend([
            Paragraph(profile.get("clinic_name", "Lancar Dynamic Admin"), styles["Title"]),
            Paragraph("<br/>".join(clinic_lines), styles["Normal"]),
            Spacer(1, 0.2 * cm),
            Paragraph(title, styles["Heading2"]),
            Paragraph(f"Dibuat: {datetime.now().strftime('%d %b %Y %H:%M')}", styles["Normal"]),
            Spacer(1, 0.35 * cm),
        ])

        table_data = [["Pasien", "Telepon", "Tanggal", "Layanan", "Terapis", "Jumlah", "Harga", "Diskon"]]
        for row in rows:
            table_data.append([
                row["Nama Pasien"],
                row["Telepon"],
                row["Tanggal Kunjungan"],
                row["Layanan"],
                row["Terapis"],
                str(row["Jumlah"]),
                f"Rp {row['Harga']:,.0f}",
                row["Nama Diskon"],
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e5df")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f6")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        doc.build(story)
        return file_path
