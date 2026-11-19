import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta

from fastapi import HTTPException

import api.routes.crm as crm_route
from database import Database, VisitData
from helpers.crm_analysis_helper import build_crm_patients
from tests.api_test_utils import app_headers, client, db, form_headers


def unique_phone(suffix):
    return f"08{time.time_ns() % 10_000_000_000:010d}{suffix}"


class TestCRMLabels(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Database(f"sqlite:///{os.path.join(self.tmp.name, 'crm_labels.db')}")

    def tearDown(self):
        self.db.engine.dispose()
        self.tmp.cleanup()

    def _patient_row(self, patient_id):
        with self.db.Session() as session:
            return next(row for row in build_crm_patients(session) if row["id"] == patient_id)

    def test_high_value_segment_label_is_admin_friendly(self):
        patient_id = self.db.add_patient(
            "Pasien Prioritas Label",
            unique_phone("01"),
            visits=[
                VisitData(
                    id=None,
                    date=datetime.now(),
                    price=1_000_000,
                    discount_applied=False,
                    point_count=1,
                    service_name="Bekam",
                )
            ],
        )

        row = self._patient_row(patient_id)

        self.assertEqual(row["segment"], "high_value")
        self.assertEqual(row["segment_label"], "Pasien Prioritas")

    def test_dormant_segment_label_is_admin_friendly(self):
        patient_id = self.db.add_patient(
            "Pasien Lama Tidak Datang",
            unique_phone("02"),
            visits=[
                VisitData(
                    id=None,
                    date=datetime.now() - timedelta(days=130),
                    price=100_000,
                    discount_applied=False,
                    point_count=1,
                    service_name="Bekam",
                )
            ],
        )

        row = self._patient_row(patient_id)

        self.assertEqual(row["segment"], "dormant")
        self.assertEqual(row["segment_label"], "Lama Tidak Datang")


class TestCRMApiSafety(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_generic_crm_exception_uses_safe_message(self):
        original = crm_route.build_crm_summary

        def explode(_session):
            raise RuntimeError("C:\\secret\\clinic.db SQL failed")

        crm_route.build_crm_summary = explode
        try:
            with self.assertRaises(HTTPException) as raised:
                crm_route.get_crm_summary()
            response = self.client.get("/crm/summary", headers=app_headers())
        finally:
            crm_route.build_crm_summary = original

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "Gagal memuat data follow-up pasien. Silakan coba lagi.")
        self.assertEqual(response.status_code, 500)
        detail = response.json()["detail"]
        self.assertNotIn("secret", detail)
        self.assertNotIn("SQL", detail)

    def test_crm_special_voucher_requires_admin_pin(self):
        patient_id = db.add_patient("Pasien Voucher PIN CRM", unique_phone("03"))

        response = self.client.post(
            f"/crm/patient/{patient_id}/vouchers",
            data={
                "name": "Voucher PIN",
                "voucher_code": "PIN10",
                "discount_type": "percent",
                "discount_value": "10",
            },
            headers=form_headers(),
        )

        self.assertEqual(response.status_code, 403)

    def test_crm_voucher_invalid_discount_rejected_400(self):
        patient_id = db.add_patient("Pasien Voucher Invalid CRM", unique_phone("04"))

        response = self.client.post(
            f"/crm/patient/{patient_id}/vouchers",
            data={
                "name": "Voucher Invalid",
                "voucher_code": "BAD101",
                "discount_type": "percent",
                "discount_value": "101",
            },
            headers=form_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Nilai diskon tidak valid.")

    def test_contact_preference_requires_admin_pin(self):
        patient_id = db.add_patient("Pasien Preferensi CRM", unique_phone("05"))

        response = self.client.post(
            f"/crm/patient/{patient_id}/contact-preference",
            data={
                "boleh_reminder_kontrol": "false",
                "boleh_promo": "true",
                "jangan_dihubungi": "true",
                "catatan_kontak": "Hubungi hanya sore.",
            },
            headers=form_headers(),
        )
        self.assertEqual(response.status_code, 403)

        # Second try with correct pin should succeed
        success_response = self.client.post(
            f"/crm/patient/{patient_id}/contact-preference",
            data={
                "boleh_reminder_kontrol": "false",
                "boleh_promo": "true",
                "jangan_dihubungi": "true",
                "catatan_kontak": "Hubungi hanya sore.",
            },
            headers=form_headers(pin="1234"),
        )
        self.assertEqual(success_response.status_code, 200)

        read_response = self.client.get(
            f"/crm/patient/{patient_id}/contact-preference",
            headers=app_headers(),
        )

        self.assertEqual(read_response.status_code, 200)
        data = read_response.json()
        self.assertFalse(data["boleh_reminder_kontrol"])
        self.assertTrue(data["boleh_promo"])
        self.assertTrue(data["jangan_dihubungi"])
        self.assertEqual(data["catatan_kontak"], "Hubungi hanya sore.")

    def test_mark_whatsapp_contacted_accepts_json_without_existing_message_log(self):
        patient_id = db.add_patient("Pasien Followup Manual CRM", unique_phone("06"))

        response = self.client.post(
            f"/crm/patient/{patient_id}/mark-whatsapp-contacted",
            json={"follow_up_date": "2026-06-01"},
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["followup_status"], "contacted")

        history = self.client.get(
            f"/crm/patient/{patient_id}/followups",
            headers=app_headers(),
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[0]["status"], "contacted")
        self.assertEqual(history.json()[0]["follow_up_date"], "2026-06-01")

    def test_mark_whatsapp_contacted_invalid_json_returns_safe_error(self):
        patient_id = db.add_patient("Pasien Followup Invalid CRM", unique_phone("07"))

        response = self.client.post(
            f"/crm/patient/{patient_id}/mark-whatsapp-contacted",
            content="{",
            headers={**app_headers(), "Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "Data yang dikirim tidak valid. Periksa kembali input.")


if __name__ == "__main__":
    unittest.main()
