import logging
import os
import tempfile
import unittest

from database import Database


class Batch2BDatabaseTestCase(unittest.TestCase):
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

    def test_gender_analytics_all_period_without_date_filter(self):
        male_id = self.db.add_patient("Pasien Gender L", "081270000001", gender="Laki-laki")
        female_id = self.db.add_patient("Pasien Gender P", "081270000002", gender="Perempuan")
        self.db.add_visit(male_id, price=100000, point_count=1)
        self.db.add_visit(female_id, price=100000, point_count=1)

        analytics = self.db.get_analytics_data(period="all")

        self.assertEqual(analytics["male_count"], 1)
        self.assertEqual(analytics["female_count"], 1)


if __name__ == "__main__":
    unittest.main()
