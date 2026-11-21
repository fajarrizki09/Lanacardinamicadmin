import json
import os
import sys
import uuid
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from api_test_utils import app_headers, client, db
from database import Visit


class TestTherapistServiceCapabilities(unittest.TestCase):
    def setUp(self):
        self.client = client()
        self.suffix = uuid.uuid4().hex[:8]

    def _service(self, label):
        return db.add_service(
            f"{label} {self.suffix}",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=75000,
        )

    def _patient(self, label):
        return db.add_patient(
            f"{label} {self.suffix}",
            f"0812{int(self.suffix[:6], 16) % 100000000:08d}"[:13],
            gender="Laki-laki",
        )

    def _post_visit(self, patient_id, therapist_id, service_id):
        return self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "therapist_id": therapist_id,
                "service_id": service_id,
                "point_count": 1,
                "price": 75000,
                "service_name": "Harus mengikuti layanan",
                "manual_price_used": "true",
            },
            headers=app_headers(),
        )

    def test_therapist_can_store_and_update_multiple_service_capabilities(self):
        first = self._service("Bekam Capability")
        second = self._service("Refleksi Capability")
        response = self.client.post(
            "/add_therapist",
            data={
                "name": f"Terapis Capability {self.suffix}",
                "gender": "Laki-laki",
                "specialization": "Terapi",
                "service_ids": json.dumps([first, second]),
            },
            headers=app_headers(pin="1234"),
        )
        self.assertEqual(response.status_code, 200)

        therapists = self.client.get("/therapists", headers=app_headers()).json()
        therapist = next(item for item in therapists if item["name"] == f"Terapis Capability {self.suffix}")
        self.assertEqual({item["service_id"] for item in therapist["service_capabilities"]}, {first, second})

        updated = self.client.post(
            "/update_therapist",
            data={
                "therapist_id": therapist["id"],
                "name": therapist["name"],
                "gender": therapist["gender"],
                "specialization": therapist["specialization"],
                "is_active": "true",
                "service_ids": json.dumps([second]),
            },
            headers=app_headers(pin="1234"),
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            [item["service_id"] for item in db.get_therapist(therapist["id"]).service_capabilities],
            [second],
        )

    def test_legacy_therapist_without_mapping_does_not_block_visit(self):
        patient_id = self._patient("Pasien Legacy Mapping")
        therapist_id = db.add_therapist(f"Terapis Legacy {self.suffix}", "Laki-laki")
        service_id = self._service("Layanan Legacy")

        response = self._post_visit(patient_id, therapist_id, service_id)

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            self.assertEqual(session.query(Visit).filter(Visit.patient_id == patient_id).count(), 1)

    def test_legacy_update_without_capability_field_preserves_existing_mapping(self):
        service_id = self._service("Layanan Preserve")
        therapist_id = db.add_therapist(
            f"Terapis Preserve {self.suffix}",
            "Laki-laki",
            service_ids=[service_id],
        )

        response = self.client.post(
            "/update_therapist",
            data={
                "therapist_id": therapist_id,
                "name": f"Terapis Preserve Baru {self.suffix}",
                "gender": "Laki-laki",
                "specialization": "Tetap",
                "is_active": "true",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["service_id"] for item in db.get_therapist(therapist_id).service_capabilities],
            [service_id],
        )

    def test_visit_rejects_service_not_mapped_to_therapist(self):
        patient_id = self._patient("Pasien Mismatch Mapping")
        mapped = self._service("Layanan Diizinkan")
        mismatched = self._service("Layanan Ditolak")
        therapist_id = db.add_therapist(
            f"Terapis Terbatas {self.suffix}",
            "Laki-laki",
            service_ids=[mapped],
        )

        response = self._post_visit(patient_id, therapist_id, mismatched)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Layanan tidak sesuai dengan terapis yang dipilih.")

    def test_visit_accepts_service_mapped_to_therapist(self):
        patient_id = self._patient("Pasien Matching Mapping")
        mapped = self._service("Layanan Cocok")
        therapist_id = db.add_therapist(
            f"Terapis Cocok {self.suffix}",
            "Laki-laki",
            service_ids=[mapped],
        )

        response = self._post_visit(patient_id, therapist_id, mapped)

        self.assertEqual(response.status_code, 200)

    def test_inactive_service_cannot_be_assigned_as_new_capability(self):
        service_id = self._service("Layanan Nonaktif Capability")
        service = db.get_service(service_id)
        db.update_service(
            service_id,
            service.name,
            unit_label=service.unit_label,
            default_quantity=service.default_quantity,
            price_per_unit=service.price_per_unit,
            is_active=False,
        )

        response = self.client.post(
            "/add_therapist",
            data={
                "name": f"Terapis Nonaktif {self.suffix}",
                "gender": "Laki-laki",
                "service_ids": json.dumps([service_id]),
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Layanan terapis tidak ditemukan atau tidak aktif.")


if __name__ == "__main__":
    unittest.main()
