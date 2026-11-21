import logging
import os
import tempfile
import unittest
from pathlib import Path

from database import Database, Visit
from db_dataclasses import VisitData
from helpers.payment_rules import normalize_visit_payment


class IsolatedP2DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "p2_hardening.db")
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


class TestP2Hardening(IsolatedP2DatabaseTestCase):
    def test_visit_quantity_alias_writes_point_count(self):
        patient_id = self.db.add_patient("Pasien Quantity Alias", "081288800001")
        therapist_id = self.db.add_therapist("Terapis Quantity Alias", "Laki-laki", "Umum")

        self.db.add_visit(patient_id, 150000, quantity=3, therapist_id=therapist_id, service_name="Terapi Quantity")

        with self.db.Session() as session:
            visit = session.query(Visit).order_by(Visit.id.desc()).first()
            self.assertEqual(visit.point_count, 3)
            self.assertEqual(visit.quantity, 3)
            visit.quantity = 4
            session.commit()

        with self.db.Session() as session:
            visit = session.query(Visit).order_by(Visit.id.desc()).first()
            self.assertEqual(visit.point_count, 4)
            self.assertEqual(visit.quantity, 4)

    def test_visit_data_quantity_alias_syncs_with_point_count(self):
        from datetime import datetime

        from_point_count = VisitData(id=1, date=datetime.now(), price=10000, point_count=2)
        from_quantity = VisitData(id=2, date=datetime.now(), price=10000, point_count=0, quantity=5)

        self.assertEqual(from_point_count.quantity, 2)
        self.assertEqual(from_quantity.point_count, 5)

    def test_refunded_payment_status_is_supported_and_has_zero_revenue(self):
        payment = normalize_visit_payment(
            100000,
            payment_status="refunded",
            payment_method="transfer",
            amount_paid=100000,
        )

        self.assertEqual(payment["payment_status"], "refunded")
        self.assertEqual(payment["payment_method"], "transfer")
        self.assertEqual(payment["amount_paid"], 0)
        self.assertIsNone(payment["paid_at"])

    def test_refunded_payment_status_rejects_free_method(self):
        with self.assertRaisesRegex(ValueError, "Gratis"):
            normalize_visit_payment(100000, payment_status="refunded", payment_method="free")

    def test_shared_types_source_exists_for_frontend_contracts(self):
        root = Path(__file__).resolve().parents[1]
        shared_types = root / "api" / "static" / "ts" / "types.ts"
        content = shared_types.read_text(encoding="utf-8")

        self.assertIn("type AdminVisit", content)
        self.assertIn("type AdminServiceModel", content)
        self.assertIn("type AdminInventoryModel", content)
        self.assertIn("type PaymentStatus", content)
        self.assertIn("'refunded'", content)

    def test_dom_helper_has_unsafe_html_guard(self):
        root = Path(__file__).resolve().parents[1]
        dom_ts = root / "api" / "static" / "ts" / "dom.ts"
        content = dom_ts.read_text(encoding="utf-8")

        self.assertIn("assertEscapedHtml", content)
        self.assertIn("LANCAR_RAW_HTML_PATTERNS", content)
        self.assertIn("/<script\\b/i", content)
        self.assertIn("/\\son[a-z]+\\s*=/i", content)

    def test_known_dataset_badges_escape_values_before_inner_html(self):
        root = Path(__file__).resolve().parents[1]
        inventory_ts = (root / "api" / "static" / "ts" / "inventory.ts").read_text(encoding="utf-8")
        herbals_ts = (root / "api" / "static" / "ts" / "herbals.ts").read_text(encoding="utf-8")

        self.assertIn("<strong>${escapeHtml(item.item_name || item.name || '-')}</strong>", inventory_ts)
        self.assertIn("${escapeHtml(unit)} &middot; ${escapeHtml(inventoryItemTypeLabel(item.item_type))}", inventory_ts)
        self.assertIn('data-inventory-action="edit" data-id="${i.id}"', inventory_ts)
        self.assertIn("function editInventoryFromCache", inventory_ts)
        self.assertIn('data-inventory-action="delete" data-id="${i.id}"', inventory_ts)
        self.assertIn("function deleteInventoryFromCache", inventory_ts)
        self.assertIn("<strong>${escapeHtml(item.name)}</strong>", herbals_ts)
        self.assertIn("${escapeHtml(item.unit)} &middot; ${formatRupiah(item.price)}", herbals_ts)
        self.assertIn('data-herbal-action="edit" data-id="${h.id}"', herbals_ts)
        self.assertIn("function editHerbalFromCache", herbals_ts)
        self.assertIn('data-herbal-action="delete" data-id="${h.id}"', herbals_ts)
        self.assertIn("function deleteHerbalFromCache", herbals_ts)


if __name__ == "__main__":
    unittest.main()
