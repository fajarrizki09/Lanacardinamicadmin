import logging
import os
import tempfile
import unittest

from database import Database
from helpers.owner_report_helper import build_owner_report_summary


class IsolatedP3DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "p3_polish.db")
        self.db = Database(f"sqlite:///{self.db_path}")

    def tearDown(self):
        if hasattr(self, "db"):
            self.db.engine.dispose()
        for name, logger in logging.Logger.manager.loggerDict.items():
            if not (name.startswith("lancar.migration.") or name.startswith("lancar.audit.")) or not hasattr(logger, "handlers"):
                continue
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
        self.tmp.cleanup()

    def patient_and_therapist(self):
        patient_id = self.db.add_patient("Pasien P3", "081277700001")
        therapist_id = self.db.add_therapist("Terapis P3", "Perempuan", "Umum")
        return patient_id, therapist_id


class TestP3Polish(IsolatedP3DatabaseTestCase):
    def test_owner_report_includes_top_service_categories(self):
        patient_id, therapist_id = self.patient_and_therapist()
        therapy_id = self.db.add_service(
            "Terapi P3",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=100000,
            service_category="therapy",
        )
        consult_id = self.db.add_service(
            "Konsultasi P3",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=50000,
            service_category="consultation",
        )

        self.db.add_visit(patient_id, 100000, quantity=1, therapist_id=therapist_id, service_id=therapy_id)
        self.db.add_visit(patient_id, 50000, quantity=1, therapist_id=therapist_id, service_id=consult_id)

        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="all")

        categories = {row["name"]: row for row in report["top_service_categories"]}
        self.assertEqual(categories["therapy"]["visits"], 1)
        self.assertEqual(categories["therapy"]["revenue"], 100000)
        self.assertEqual(categories["consultation"]["visits"], 1)
        self.assertEqual(categories["consultation"]["revenue"], 50000)

    def test_owner_report_pending_revenue_summary_is_consistent(self):
        patient_id, therapist_id = self.patient_and_therapist()
        herbal_id = self.db.add_herbal("Herbal Pending P3", "botol", 40000, stock=5, cost_price=10000)

        self.db.add_visit(
            patient_id,
            100000,
            quantity=1,
            therapist_id=therapist_id,
            service_name="Partial P3",
            payment_status="partial",
            amount_paid=30000,
        )
        self.db.add_visit(
            patient_id,
            80000,
            quantity=1,
            therapist_id=therapist_id,
            service_name="Unpaid P3",
            payment_status="unpaid",
            payment_method="transfer",
        )
        self.db.add_herbal_sale(
            [{"herbal_id": herbal_id, "quantity": 1}],
            buyer_name="Pembeli Pending",
            payment_status="partial",
            payment_method="cash",
            amount_paid=10000,
        )

        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="all")

        summary = report["summary"]
        self.assertEqual(summary["pending_visit_revenue"], 150000)
        self.assertEqual(summary["pending_herbal_revenue"], 30000)
        self.assertEqual(summary["pending_revenue"], 180000)
        self.assertEqual(summary["visit_revenue"], 30000)
        self.assertEqual(summary["herbal_revenue"], 10000)


if __name__ == "__main__":
    unittest.main()
