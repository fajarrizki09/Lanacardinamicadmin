import logging
import os
import tempfile
import unittest

from database import Database, HerbalTransaction, Visit
from helpers.owner_report_helper import build_owner_report_summary


class IsolatedP0DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "p0_regression.db")
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

    def create_patient_and_therapist(self):
        patient_id = self.db.add_patient("Pasien P0", "081299900001")
        therapist_id = self.db.add_therapist("Terapis P0", "Laki-laki", "Umum")
        return patient_id, therapist_id

    def latest_visit_id(self):
        with self.db.Session() as session:
            visit = session.query(Visit).order_by(Visit.id.desc()).first()
            return visit.id


class TestP0Regressions(IsolatedP0DatabaseTestCase):
    def test_visit_pricing_breakdown_and_owner_report_uses_final_price(self):
        patient_id, therapist_id = self.create_patient_and_therapist()

        self.db.add_visit(
            patient_id,
            100000,
            point_count=1,
            therapist_id=therapist_id,
            service_name="Terapi Diskon",
            discount_percentage=20,
            min_visits_for_discount=0,
        )
        visit_id = self.latest_visit_id()

        with self.db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(float(visit.original_price), 100000)
            self.assertEqual(float(visit.discount_amount), 20000)
            self.assertEqual(float(visit.final_price), 80000)
            report = build_owner_report_summary(session, period="all")

        self.assertEqual(report["summary"]["visit_revenue"], 80000)
        self.assertEqual(report["summary"]["total_revenue"], 80000)

    def test_visit_rejects_negative_and_zero_without_free_reason(self):
        patient_id, therapist_id = self.create_patient_and_therapist()

        with self.assertRaisesRegex(ValueError, "Harga kunjungan tidak boleh kurang dari 0"):
            self.db.add_visit(patient_id, -1, point_count=1, therapist_id=therapist_id)
        with self.assertRaisesRegex(ValueError, "Harga 0 hanya boleh untuk kunjungan gratis"):
            self.db.add_visit(patient_id, 0, point_count=1, therapist_id=therapist_id)
        with self.assertRaisesRegex(ValueError, "Alasan kunjungan gratis wajib diisi"):
            self.db.add_visit(patient_id, 0, point_count=1, therapist_id=therapist_id, is_free_visit=True)

        self.db.add_visit(
            patient_id,
            0,
            point_count=1,
            therapist_id=therapist_id,
            is_free_visit=True,
            free_visit_reason="Voucher owner",
            payment_method="free",
        )
        visit_id = self.latest_visit_id()
        with self.db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(float(visit.final_price), 0)
            self.assertEqual(visit.free_visit_reason, "Voucher owner")

    def test_herbal_sale_stock_shortage_rolls_back_all_items(self):
        herbal_ok = self.db.add_herbal("Herbal OK P0", "botol", 25000, stock=5, cost_price=10000)
        herbal_short = self.db.add_herbal("Herbal Short P0", "botol", 50000, stock=1, cost_price=20000)

        with self.assertRaisesRegex(ValueError, "Stok herbal tidak cukup"):
            self.db.add_herbal_sale([
                {"herbal_id": herbal_ok, "quantity": 2},
                {"herbal_id": herbal_short, "quantity": 2},
            ])

        herbals = {item["id"]: item for item in self.db.get_all_herbals(active_only=False)}
        self.assertEqual(herbals[herbal_ok]["stock"], 5)
        self.assertEqual(herbals[herbal_short]["stock"], 1)
        with self.db.Session() as session:
            self.assertEqual(session.query(HerbalTransaction).filter(HerbalTransaction.transaction_type == "sale").count(), 0)

    def test_visit_with_herbal_items_reports_service_and_herbal_once(self):
        patient_id, therapist_id = self.create_patient_and_therapist()
        herbal_id = self.db.add_herbal("Herbal Visit P0", "botol", 50000, stock=3, cost_price=20000)

        self.db.add_visit(
            patient_id,
            100000,
            point_count=1,
            therapist_id=therapist_id,
            service_name="Terapi Plus Herbal",
            herbal_items=[{"herbal_id": herbal_id, "quantity": 1}],
        )

        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="all")
            herbal_sales = session.query(HerbalTransaction).filter(HerbalTransaction.transaction_type == "sale").all()

        self.assertEqual(len(herbal_sales), 1)
        self.assertEqual(report["summary"]["visit_revenue"], 100000)
        self.assertEqual(report["summary"]["herbal_revenue"], 50000)
        self.assertEqual(report["summary"]["total_revenue"], 150000)

    def test_partial_free_and_void_revenue_are_not_overcounted(self):
        patient_id, therapist_id = self.create_patient_and_therapist()
        self.db.add_visit(patient_id, 100000, point_count=1, therapist_id=therapist_id, service_name="Paid")
        paid_visit_id = self.latest_visit_id()
        self.db.add_visit(
            patient_id,
            100000,
            point_count=1,
            therapist_id=therapist_id,
            service_name="Partial",
            payment_status="partial",
            amount_paid=30000,
        )
        partial_visit_id = self.latest_visit_id()
        self.db.add_visit(
            patient_id,
            0,
            point_count=1,
            therapist_id=therapist_id,
            service_name="Free",
            is_free_visit=True,
            free_visit_reason="Trial gratis",
            payment_method="free",
        )
        free_visit_id = self.latest_visit_id()
        self.db.add_visit(patient_id, 90000, point_count=1, therapist_id=therapist_id, service_name="Void")
        void_visit_id = self.latest_visit_id()
        self.db.void_visit_invoice(void_visit_id, "Salah input")

        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="all")
            visits = {visit.id: visit for visit in session.query(Visit).all()}

        self.assertEqual(float(visits[paid_visit_id].final_price), 100000)
        self.assertEqual(int(visits[partial_visit_id].amount_paid), 30000)
        self.assertEqual(float(visits[free_visit_id].final_price), 0)
        self.assertEqual(visits[void_visit_id].invoice_status, "void")
        self.assertEqual(report["summary"]["visit_revenue"], 130000)
        self.assertEqual(report["summary"]["total_revenue"], 130000)


if __name__ == "__main__":
    unittest.main()
