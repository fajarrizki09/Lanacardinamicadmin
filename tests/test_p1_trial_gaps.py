import os
import logging
import tempfile
import unittest

from fastapi import HTTPException

from database import Database, Inventory
from helpers.invoice_helper import InvoiceHelper
from api.routes.invoices import void_invoice_endpoint


class IsolatedP1DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "p1_trial.db")
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


class TestP1TrialGaps(IsolatedP1DatabaseTestCase):
    def test_service_pricing_fields_are_persisted(self):
        service_id = self.db.add_service(
            "Paket Fixed Trial",
            unit_label="sesi",
            default_quantity=2,
            price_per_unit=50000,
            notes_template="Catatan",
            pricing_type="fixed",
            service_category="therapy",
            fixed_price=90000,
            allow_manual_price=False,
        )

        service = self.db.get_service(service_id)

        self.assertEqual(service.pricing_type, "fixed")
        self.assertEqual(service.service_category, "therapy")
        self.assertEqual(service.fixed_price, 90000)
        self.assertFalse(service.allow_manual_price)

    def test_auto_deduct_skips_non_consumable_inventory(self):
        service_id = self.db.add_service("Terapi Auto Deduct", unit_label="sesi", default_quantity=1, price_per_unit=75000)
        consumable_id = self.db.add_inventory_item("Kassa Trial", "pcs", 1, 5, item_type="consumable")
        non_consumable_id = self.db.add_inventory_item("Bed Trial", "unit", 1, 1, item_type="non_consumable")
        self.db.update_service(
            service_id,
            "Terapi Auto Deduct",
            "sesi",
            1,
            75000,
            "",
            True,
            [
                {"inventory_id": consumable_id, "quantity": 2},
                {"inventory_id": non_consumable_id, "quantity": 1},
            ],
        )
        patient_id = self.db.add_patient("Pasien P1", "081200000001")
        therapist_id = self.db.add_therapist("Terapis P1", "Laki-laki", "Umum")

        self.db.add_visit(patient_id, therapist_id, 75000, 1, service_id=service_id, service_name="Terapi Auto Deduct")

        with self.db.Session() as session:
            consumable = session.get(Inventory, consumable_id)
            non_consumable = session.get(Inventory, non_consumable_id)
            self.assertEqual(consumable.quantity, 3)
            self.assertEqual(non_consumable.quantity, 1)

    def test_invoice_filename_is_sanitized_and_stays_inside_output_dir(self):
        output_dir = os.path.join(self.tmp.name, "invoices")
        helper = InvoiceHelper(output_dir)

        path = helper.generate_invoice(
            patient_name="../Pasien:Risky",
            date="2026-05-18",
            points=1,
            price=10000,
            invoice_number="../INV:Risky",
        )

        self.assertEqual(os.path.commonpath([helper.output_dir, os.path.abspath(path)]), helper.output_dir)
        self.assertEqual(os.path.basename(path), "INVRisky_PasienRisky.pdf")

    def test_void_route_rejects_blank_reason_before_db_call(self):
        class RequestStub:
            headers = {"X-Admin-PIN": "123456"}
            cookies = {}

        original_require_valid_license = void_invoice_endpoint.__globals__["require_valid_license"]
        original_require_admin_pin = void_invoice_endpoint.__globals__["require_admin_pin"]
        original_db = void_invoice_endpoint.__globals__["db"]

        class DbStub:
            called = False

            def void_visit_invoice(self, visit_id, reason):
                self.called = True

        stub_db = DbStub()
        void_invoice_endpoint.__globals__["require_valid_license"] = lambda: None
        void_invoice_endpoint.__globals__["require_admin_pin"] = lambda request: None
        void_invoice_endpoint.__globals__["db"] = stub_db
        try:
            with self.assertRaises(HTTPException) as ctx:
                import asyncio

                asyncio.run(void_invoice_endpoint(RequestStub(), "visit", visit_id=1, reason="   "))
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertFalse(stub_db.called)
        finally:
            void_invoice_endpoint.__globals__["require_valid_license"] = original_require_valid_license
            void_invoice_endpoint.__globals__["require_admin_pin"] = original_require_admin_pin
            void_invoice_endpoint.__globals__["db"] = original_db


if __name__ == "__main__":
    unittest.main()
