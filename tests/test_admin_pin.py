import json
import os
import sys
import tempfile
import unittest

from settings import AppSettings

sys.path.insert(0, os.path.dirname(__file__))
from api_test_utils import app_headers, client


class TestAdminPinSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings_path = os.path.join(self.tmp.name, "settings.json")
        self.settings = AppSettings(file_path=self.settings_path)

    def tearDown(self):
        self.tmp.cleanup()

    def read_raw_settings(self):
        with open(self.settings_path, "r", encoding="utf-8") as settings_file:
            return json.load(settings_file)

    def test_set_pin_first_time_hashes_pin(self):
        self.assertFalse(self.settings.has_admin_pin())

        self.settings.set_admin_pin("1234")

        raw = self.read_raw_settings()
        self.assertTrue(self.settings.has_admin_pin())
        self.assertIn("admin_pin_hash", raw)
        self.assertIn("admin_pin_salt", raw)
        self.assertNotEqual(raw["admin_pin_hash"], "1234")
        self.assertNotIn("1234", json.dumps(raw))

    def test_verify_correct_pin(self):
        self.settings.set_admin_pin("2468")

        self.assertTrue(self.settings.verify_admin_pin("2468"))

    def test_verify_wrong_pin(self):
        self.settings.set_admin_pin("2468")

        self.assertFalse(self.settings.verify_admin_pin("1357"))

    def test_change_pin_requires_current_pin(self):
        self.settings.set_admin_pin("1111")

        with self.assertRaisesRegex(ValueError, "PIN salah"):
            self.settings.change_admin_pin("0000", "2222")

        self.assertTrue(self.settings.verify_admin_pin("1111"))
        self.assertFalse(self.settings.verify_admin_pin("2222"))

        self.settings.change_admin_pin("1111", "2222")

        self.assertFalse(self.settings.verify_admin_pin("1111"))
        self.assertTrue(self.settings.verify_admin_pin("2222"))

    def test_get_all_settings_never_exposes_pin_hash_or_salt(self):
        self.settings.set_admin_pin("9999")

        public_settings = self.settings.get_all_settings()

        self.assertTrue(public_settings["admin_pin_set"])
        self.assertNotIn("admin_pin_hash", public_settings)
        self.assertNotIn("admin_pin_salt", public_settings)

    def test_first_run_default_is_incomplete(self):
        self.assertFalse(self.settings.is_first_run_completed())

        public_settings = self.settings.get_all_settings()
        self.assertFalse(public_settings["first_run_completed"])

    def test_complete_first_run_saves_clinic_profile_and_flag(self):
        self.settings.complete_first_run(
            {
                "clinic_name": "Klinik Test",
                "clinic_address": "Jl. Testing No. 1",
                "clinic_phone": "08123456789",
                "invoice_prefix": "KT",
            }
        )

        public_settings = self.settings.get_all_settings()
        self.assertTrue(self.settings.is_first_run_completed())
        self.assertTrue(public_settings["first_run_completed"])
        self.assertEqual(public_settings["clinic_name"], "Klinik Test")
        self.assertEqual(public_settings["invoice_prefix"], "KT")


class TestAdminPinApiProtection(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_admin_endpoint_without_pin_is_rejected(self):
        response = self.client.get("/backups", headers=app_headers())

        self.assertEqual(response.status_code, 403)

    def test_admin_endpoint_with_valid_pin_is_allowed(self):
        response = self.client.get("/backups", headers=app_headers(pin="1234"))

        self.assertEqual(response.status_code, 200)

    def test_admin_endpoint_with_wrong_pin_is_rejected(self):
        response = self.client.get("/backups", headers=app_headers(pin="0000"))

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
