import logging
import os
import tempfile
import unittest

from database import Database, Herbal, Inventory


class Batch2ADatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test_data.db")
        self.db = Database(f"sqlite:///{self.db_path}")

    def tearDown(self):
        self.db.engine.dispose()
        for name, logger in logging.Logger.manager.loggerDict.items():
            if not (name.startswith("lancar.migration.") or name.startswith("lancar.audit.")) or not hasattr(logger, "handlers"):
                continue
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
        self.tmp.cleanup()

    def test_low_stock_count_counts_active_inventory_and_herbal_once(self):
        self.db.add_inventory_item("Kassa Low", "pcs", min_stock=5, initial_qty=5)
        self.db.add_inventory_item("Kassa Safe", "pcs", min_stock=5, initial_qty=6)
        self.db.add_herbal("Madu Low", "botol", price=25000, stock=2, min_stock=2)
        self.db.add_herbal("Madu Safe", "botol", price=25000, stock=3, min_stock=2)

        with self.db.Session() as session:
            inactive_inventory = Inventory(item_name="Kassa Inactive", quantity=0, unit="pcs", min_stock=5, is_active=False)
            inactive_herbal = Herbal(name="Madu Inactive", stock=0, unit="botol", price=25000, min_stock=5, is_active=False)
            session.add_all([inactive_inventory, inactive_herbal])
            session.commit()

        analytics = self.db.get_analytics_data(period="all")

        self.assertEqual(analytics["low_stock_count"], 2)

    def test_ensure_performance_indexes_reports_already_ok_when_indexes_exist(self):
        with self.db.Session() as session:
            changed = self.db._ensure_performance_indexes(session)

        self.assertFalse(changed)

    def test_update_herbal_stock_change_writes_correction_log(self):
        herbal_id = self.db.add_herbal("Temulawak", "botol", price=30000, stock=4, min_stock=1)

        updated = self.db.update_herbal(
            herbal_id,
            "Temulawak",
            "botol",
            price=30000,
            stock=7,
            cost_price=10000,
            min_stock=1,
        )

        logs = self.db.get_correction_logs(action_type="stock_correction")
        self.assertTrue(updated)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["herbal_id"], herbal_id)
        self.assertEqual(logs[0]["quantity_change"], 3)
        self.assertEqual(logs[0]["stock_before"], 4)
        self.assertEqual(logs[0]["stock_after"], 7)
        self.assertEqual(logs[0]["reason"], "Koreksi stok herbal manual")


if __name__ == "__main__":
    unittest.main()
