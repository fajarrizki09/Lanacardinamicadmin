import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from settings import AppSettings


SENSITIVE_KEYS = {
    "admin_pin_hash",
    "admin_pin_salt",
    "admin_pin_reset_token",
    "admin_pin_reset_request_id",
    "license_key",
    "license_api_url",
    "clinic_id",
    "device_id",
    "settings_hash",
    "last_online_valid_at",
    "last_license_check",
    "last_license_valid",
    "last_server_time",
    "license_status",
    "license_expired_at",
    "license_clinic_name",
    "midtrans_server_key",
    "xendit_secret_key",
    "duitku_api_key",
}


class TestSettingsSecurity(unittest.TestCase):
    def test_default_settings_path_prefers_appdata_runtime_store(self):
        with patch("helpers.secure_settings.get_app_data_dir", return_value=r"C:\Users\Test\AppData\Roaming\LancarDinamicAdmin"):
            from helpers.secure_settings import get_settings_path

            self.assertEqual(
                get_settings_path(),
                r"C:\Users\Test\AppData\Roaming\LancarDinamicAdmin\settings.json",
            )

    def test_get_all_settings_filters_sensitive_keys_and_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            payload = {
                "clinic_name": "Klinik Test",
                "clinic_address": "Jl. Aman",
                "clinic_phone": "081234567890",
                "base_price": 120000,
                "invoice_prefix": "KT",
                "admin_pin_hash": "hash",
                "admin_pin_salt": "salt",
                "admin_pin_reset_token": "RESET-TOKEN-SECRET",
                "admin_pin_reset_request_id": "REQ-SECRET",
                "license_key": "secret",
                "license_api_url": "https://license.example",
                "clinic_id": "CLN-SECRET",
                "device_id": "device",
                "settings_hash": "settings-hash",
                "last_online_valid_at": 1,
                "last_license_check": 2,
                "last_license_valid": True,
                "last_server_time": "2026-05-09T00:00:00Z",
                "license_status": "ok",
                "license_expired_at": "2026-05-09",
                "license_clinic_name": "Hidden Clinic",
                "license_cache_extra": "hidden",
                "last_license_extra": "hidden",
                "last_online_extra": "hidden",
                "last_server_extra": "hidden",
                "payment_gateway_default_provider": "midtrans",
                "payment_gateway_environment": "sandbox",
                "midtrans_server_key": "SB-MIDTRANS-SECRET",
                "midtrans_client_key": "CLIENT-KEY",
                "midtrans_merchant_id": "MERCHANT-ID",
                "xendit_secret_key": "XENDIT-SECRET",
                "duitku_merchant_code": "DUITKU-CODE",
                "duitku_api_key": "DUITKU-SECRET",
            }
            with open(settings_path, "w", encoding="utf-8") as settings_file:
                json.dump(payload, settings_file)

            public_settings = AppSettings(settings_path).get_all_settings()

        for key in SENSITIVE_KEYS:
            self.assertNotIn(key, public_settings)
        for key in public_settings:
            self.assertFalse(key.startswith("admin_pin_reset_"), key)
            self.assertFalse(key.startswith("license_"), key)
            self.assertFalse(key.startswith("last_license_"), key)
            self.assertFalse(key.startswith("last_online_"), key)
            self.assertFalse(key.startswith("last_server_"), key)

        self.assertEqual(public_settings["clinic_name"], "Klinik Test")
        self.assertEqual(public_settings["clinic_address"], "Jl. Aman")
        self.assertEqual(public_settings["clinic_phone"], "081234567890")
        self.assertEqual(public_settings["base_price"], 120000)
        self.assertEqual(public_settings["invoice_prefix"], "KT")
        self.assertEqual(public_settings["payment_gateway_default_provider"], "midtrans")
        self.assertEqual(public_settings["payment_gateway_environment"], "sandbox")
        self.assertEqual(public_settings["midtrans_client_key"], "CLIENT-KEY")
        self.assertEqual(public_settings["midtrans_merchant_id"], "MERCHANT-ID")
        self.assertEqual(public_settings["duitku_merchant_code"], "DUITKU-CODE")
        self.assertTrue(public_settings["admin_pin_set"])

    def test_payment_gateway_settings_can_be_saved_and_sensitive_fields_are_filtered(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            settings = AppSettings(settings_path)
            settings.set_payment_gateway_settings({
                "payment_gateway_enabled": True,
                "payment_gateway_default_provider": "midtrans",
                "payment_gateway_environment": "production",
                "midtrans_server_key": "MIDTRANS-SECRET",
                "midtrans_client_key": "MIDTRANS-CLIENT",
                "midtrans_merchant_id": "MIDTRANS-MERCHANT",
                "xendit_secret_key": "XENDIT-SECRET",
                "duitku_merchant_code": "DUITKU-MERCHANT",
                "duitku_api_key": "DUITKU-SECRET",
            })

            public_settings = settings.get_all_settings()

        self.assertTrue(public_settings["payment_gateway_enabled"])
        self.assertEqual(public_settings["payment_gateway_default_provider"], "midtrans")
        self.assertEqual(public_settings["payment_gateway_supported_providers"], ["gateway_mock", "midtrans"])
        self.assertEqual(public_settings["payment_gateway_available_providers"], ["gateway_mock", "midtrans"])
        self.assertEqual(public_settings["payment_gateway_coming_soon_providers"], ["doku", "duitku", "tripay", "xendit"])
        self.assertEqual(public_settings["payment_gateway_provider_registry"]["xendit"]["status"], "coming_soon")
        self.assertEqual(public_settings["payment_gateway_environment"], "production")
        self.assertEqual(public_settings["midtrans_client_key"], "MIDTRANS-CLIENT")
        self.assertEqual(public_settings["midtrans_merchant_id"], "MIDTRANS-MERCHANT")
        self.assertEqual(public_settings["duitku_merchant_code"], "DUITKU-MERCHANT")
        self.assertNotIn("midtrans_server_key", public_settings)
        self.assertNotIn("xendit_secret_key", public_settings)
        self.assertNotIn("duitku_api_key", public_settings)

    def test_unsupported_gateway_provider_cannot_be_saved_or_exposed_as_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            settings = AppSettings(settings_path)
            for provider in ("xendit", "duitku", "doku", "tripay"):
                with self.subTest(provider=provider):
                    with self.assertRaises(ValueError):
                        settings.set_payment_gateway_settings({
                            "payment_gateway_enabled": True,
                            "payment_gateway_default_provider": provider,
                            "payment_gateway_environment": "sandbox",
                        })

            settings.settings["payment_gateway_default_provider"] = "duitku"
            public_settings = settings.get_all_settings()

        self.assertEqual(settings.get_payment_gateway_default_provider(), "gateway_mock")
        self.assertEqual(public_settings["payment_gateway_default_provider"], "gateway_mock")

    def test_settings_ui_shows_coming_soon_providers_as_info_only(self):
        source = Path("api/static/modules/settings.js").read_text(encoding="utf-8")

        self.assertIn("comingSoonProviders", source)
        self.assertIn("Segera Hadir", source)
        self.assertIn('value="gateway_mock"', source)
        self.assertIn('value="midtrans"', source)
        self.assertNotIn('option value="xendit"', source)
        self.assertNotIn('option value="duitku"', source)
        self.assertNotIn('option value="doku"', source)
        self.assertNotIn('option value="tripay"', source)

    def test_default_settings_store_encrypts_sensitive_runtime_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = os.path.join(tmp, "settings.json")
            project_defaults_path = os.path.join(tmp, "project_settings.json")
            with patch("helpers.secure_settings.get_settings_path", return_value=settings_path), patch(
                "helpers.secure_settings._project_settings_path",
                return_value=project_defaults_path,
            ):
                settings = AppSettings()
                settings.set_admin_pin("1234")
                settings.settings["license_key"] = "LICENSE-SECRET-123456"
                settings.settings["clinic_id"] = "CLINIC-SECRET"
                settings.settings["admin_pin_reset_token"] = "RESET-TOKEN-SECRET"
                settings.settings["midtrans_server_key"] = "MIDTRANS-SECRET"
                settings.settings["xendit_secret_key"] = "XENDIT-SECRET"
                settings.settings["duitku_api_key"] = "DUITKU-SECRET"
                settings.save()

                with open(settings_path, "r", encoding="utf-8") as settings_file:
                    raw = json.load(settings_file)

                raw_text = json.dumps(raw)
                self.assertTrue(str(raw["admin_pin_hash"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["admin_pin_salt"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["license_key"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["admin_pin_reset_token"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["midtrans_server_key"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["xendit_secret_key"]).startswith("enc:v1:"))
                self.assertTrue(str(raw["duitku_api_key"]).startswith("enc:v1:"))
                self.assertNotIn("1234", raw_text)
                self.assertNotIn("LICENSE-SECRET-123456", raw_text)
                self.assertNotIn("RESET-TOKEN-SECRET", raw_text)
                self.assertNotIn("CLINIC-SECRET", raw_text)
                self.assertNotIn("MIDTRANS-SECRET", raw_text)
                self.assertNotIn("XENDIT-SECRET", raw_text)
                self.assertNotIn("DUITKU-SECRET", raw_text)

                reloaded = AppSettings()
                self.assertTrue(reloaded.verify_admin_pin("1234"))
                self.assertEqual(reloaded.settings["license_key"], "LICENSE-SECRET-123456")
                self.assertEqual(reloaded.settings["admin_pin_reset_token"], "RESET-TOKEN-SECRET")
                self.assertEqual(reloaded.settings["clinic_id"], "CLINIC-SECRET")
                self.assertEqual(reloaded.settings["midtrans_server_key"], "MIDTRANS-SECRET")
                self.assertEqual(reloaded.settings["xendit_secret_key"], "XENDIT-SECRET")
                self.assertEqual(reloaded.settings["duitku_api_key"], "DUITKU-SECRET")


if __name__ == "__main__":
    unittest.main()
