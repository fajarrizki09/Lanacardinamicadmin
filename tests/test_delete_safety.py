import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(__file__))
from api_test_utils import app_headers, client, db
from database import Herbal, Inventory, Service, Therapist, Visit


class TestDeleteSafety(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def _patient_with_visit(self, suffix):
        patient_id = db.add_patient(f"Delete Safety Patient {suffix}", f"08129998{suffix:05d}", gender="Laki-laki")
        therapist_id = db.add_therapist(f"Delete Safety Therapist {suffix}", "Laki-laki")
        db.add_visit(patient_id, price=100000, point_count=1, therapist_id=therapist_id, service_name="Bekam")
        visit_id = db.get_visits(patient_id)[0]["id"]
        return patient_id, visit_id

    def test_delete_patient_with_visit_is_rejected_and_patient_remains(self):
        patient_id, _visit_id = self._patient_with_visit(1)

        response = self.client.post(
            "/delete_patient",
            data={"patient_id": patient_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tidak boleh dihapus permanen", response.json()["detail"])
        self.assertIsNotNone(db.get_patient_detail(patient_id))

    def test_delete_visit_transaction_is_rejected_and_visit_remains(self):
        _patient_id, visit_id = self._patient_with_visit(2)

        response = self.client.post(
            "/delete_visit",
            data={"visit_id": visit_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tidak boleh dihapus permanen", response.json()["detail"])
        with db.Session() as session:
            self.assertIsNotNone(session.get(Visit, visit_id))

    def test_delete_herbal_deactivates_without_hard_delete(self):
        herbal_id = db.add_herbal("Delete Safety Herbal", "botol", 20000, stock=3)

        response = self.client.post(
            "/delete_herbal",
            data={"herbal_id": herbal_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            herbal = session.get(Herbal, herbal_id)
            self.assertIsNotNone(herbal)
            self.assertFalse(herbal.is_active)

    def test_delete_inventory_deactivates_without_hard_delete(self):
        item_id = db.add_inventory_item("Delete Safety Inventory", "pcs", 1, initial_qty=5)

        response = self.client.post(
            "/delete_inventory",
            data={"item_id": item_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            item = session.get(Inventory, item_id)
            self.assertIsNotNone(item)
            self.assertFalse(item.is_active)

    def test_void_invoice_keeps_visit_record(self):
        patient_id, visit_id = self._patient_with_visit(3)
        db.update_visit_invoice_path(visit_id, "invoices/test-delete-safety.pdf")

        response = self.client.post(
            "/void_invoice",
            data={"invoice_type": "visit", "visit_id": visit_id, "reason": "Test void invoice"},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertIsNotNone(visit)
            self.assertEqual(visit.invoice_status, "void")
            self.assertEqual(visit.patient_id, patient_id)

    def test_delete_unused_therapist_hard_deletes_record(self):
        therapist_id = db.add_therapist("Delete Safety Unused Therapist", "Laki-laki")

        response = self.client.post(
            "/delete_therapist",
            data={"therapist_id": therapist_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            self.assertIsNone(session.get(Therapist, therapist_id))

    def test_delete_therapist_with_visit_is_rejected_and_history_remains(self):
        patient_id, _visit_id = self._patient_with_visit(4)
        visit = db.get_visits(patient_id)[0]
        therapist_id = visit["therapist_id"]

        response = self.client.post(
            "/delete_therapist",
            data={"therapist_id": therapist_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("Gunakan Nonaktifkan", response.json()["detail"])
        with db.Session() as session:
            self.assertIsNotNone(session.get(Therapist, therapist_id))
            self.assertIsNotNone(session.get(Visit, visit["id"]))

    def test_delete_unused_service_hard_deletes_record(self):
        service_id = db.add_service("Delete Safety Unused Service", "sesi", 1, 50000)

        response = self.client.post(
            "/delete_service",
            data={"service_id": service_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            self.assertIsNone(session.get(Service, service_id))

    def test_delete_service_with_visit_is_rejected_and_history_remains(self):
        patient_id = db.add_patient("Delete Safety Service Patient", "081277770004", gender="Laki-laki")
        service_id = db.add_service("Delete Safety Used Service", "sesi", 1, 60000)
        db.add_visit(patient_id, price=60000, point_count=1, service_id=service_id, service_name="Delete Safety Used Service")
        visit_id = db.get_visits(patient_id)[0]["id"]

        response = self.client.post(
            "/delete_service",
            data={"service_id": service_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("Gunakan Nonaktifkan", response.json()["detail"])
        with db.Session() as session:
            self.assertIsNotNone(session.get(Service, service_id))
            self.assertIsNotNone(session.get(Visit, visit_id))

    def test_therapist_active_filter_hides_and_shows_inactive_records(self):
        active_id = db.add_therapist("Delete Safety Active Filter Therapist", "Laki-laki")
        inactive_id = db.add_therapist("Delete Safety Inactive Filter Therapist", "Laki-laki")
        inactive = db.get_therapist(inactive_id)
        db.update_therapist(inactive_id, inactive.name, inactive.gender, inactive.specialization, False, inactive.can_handle_any_gender)

        active_response = self.client.get("/therapists?active_only=true", headers=app_headers(pin="1234"))
        all_response = self.client.get("/therapists", headers=app_headers(pin="1234"))

        self.assertEqual(active_response.status_code, 200)
        self.assertEqual(all_response.status_code, 200)
        active_ids = {row["id"] for row in active_response.json()}
        all_ids = {row["id"] for row in all_response.json()}
        self.assertIn(active_id, active_ids)
        self.assertNotIn(inactive_id, active_ids)
        self.assertIn(inactive_id, all_ids)

    def test_service_active_filter_hides_and_shows_inactive_records(self):
        active_id = db.add_service("Delete Safety Active Filter Service", "sesi", 1, 50000)
        inactive_id = db.add_service("Delete Safety Inactive Filter Service", "sesi", 1, 50000)
        inactive = db.get_service(inactive_id)
        db.update_service(
            inactive_id,
            inactive.name,
            inactive.unit_label,
            inactive.default_quantity,
            inactive.price_per_unit,
            inactive.notes_template,
            False,
            inactive.inventory_usage,
        )

        active_response = self.client.get("/services?active_only=true", headers=app_headers(pin="1234"))
        all_response = self.client.get("/services", headers=app_headers(pin="1234"))

        self.assertEqual(active_response.status_code, 200)
        self.assertEqual(all_response.status_code, 200)
        active_ids = {row["id"] for row in active_response.json()}
        all_ids = {row["id"] for row in all_response.json()}
        self.assertIn(active_id, active_ids)
        self.assertNotIn(inactive_id, active_ids)
        self.assertIn(inactive_id, all_ids)

    def test_toggle_therapist_and_service_status_still_work(self):
        therapist_id = db.add_therapist("Delete Safety Toggle Therapist", "Laki-laki")
        service_id = db.add_service("Delete Safety Toggle Service", "sesi", 1, 50000)

        therapist_response = self.client.post(
            "/toggle_therapist",
            data={"therapist_id": therapist_id},
            headers=app_headers(pin="1234"),
        )
        service_response = self.client.post(
            "/toggle_service",
            data={"service_id": service_id},
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(therapist_response.status_code, 200)
        self.assertEqual(service_response.status_code, 200)
        self.assertFalse(db.get_therapist(therapist_id).is_active)
        self.assertFalse(db.get_service(service_id).is_active)


if __name__ == "__main__":
    unittest.main()
