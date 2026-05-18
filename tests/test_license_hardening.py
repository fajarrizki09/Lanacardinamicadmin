import json
import os
import unittest
import urllib.error
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from helpers.license import (
    LICENSE_ERROR_MESSAGE,
    LICENSE_STATUS_NETWORK_ERROR,
    LICENSE_STATUS_OK,
    _call_license_api,
    _extract_license_response,
    _is_offline_grace_valid,
    _is_recent_valid_check,
    _parse_expiry_datetime,
    generate_device_id,
    generate_hardware_fingerprint_hash,
    get_or_create_device_id,
    report_error_feedback,
    save_license_key,
    verify_license,
)


class TestLicenseParserHardening(unittest.TestCase):
    def test_status_active_without_explicit_valid_is_invalid(self):
        is_valid, data, message = _extract_license_response({"status": "active"})

        self.assertFalse(is_valid)
        self.assertEqual(data["status"], "active")
        self.assertEqual(message, LICENSE_ERROR_MESSAGE)

    def test_root_valid_false_overrides_active_status(self):
        result = {"ok": True, "valid": False, "status": "active"}
        is_valid, data, message = _extract_license_response(result)

        self.assertFalse(is_valid)
        self.assertEqual(data["status"], "active")
        self.assertEqual(message, LICENSE_ERROR_MESSAGE)

    def test_success_false_overrides_data_valid(self):
        result = {"success": False, "data": {"valid": True, "status": "active"}}
        is_valid, data, message = _extract_license_response(result)

        self.assertFalse(is_valid)
        self.assertEqual(data["status"], "active")
        self.assertEqual(message, LICENSE_ERROR_MESSAGE)

    def test_data_valid_true_is_valid_contract(self):
        result = {"data": {"valid": True, "status": "active"}}
        is_valid, data, message = _extract_license_response(result)

        self.assertTrue(is_valid)
        self.assertEqual(data["status"], "active")
        self.assertEqual(message, "License valid.")

    def test_expiry_date_only_valid_until_end_of_day(self):
        expiry = _parse_expiry_datetime("2026-05-19")

        self.assertEqual(expiry.strftime("%Y-%m-%d %H:%M:%S"), "2026-05-19 23:59:59")

    def test_expiry_midnight_timestamp_treated_as_full_day(self):
        expiry = _parse_expiry_datetime("2026-05-19T00:00:00.000Z")

        self.assertEqual(expiry.strftime("%Y-%m-%d %H:%M:%S"), "2026-05-19 23:59:59")

    @patch("helpers.license._now", return_value=1000)
    def test_recent_cache_rejects_expired_license(self, _mock_now):
        settings = {
            "last_license_valid": True,
            "last_license_check": 990,
            "license_expired_at": "2000-01-01",
        }

        self.assertFalse(_is_recent_valid_check(settings))

    @patch("helpers.license._now", return_value=1000)
    def test_recent_cache_rejects_missing_expiry(self, _mock_now):
        settings = {
            "last_license_valid": True,
            "last_license_check": 990,
        }

        self.assertFalse(_is_recent_valid_check(settings))

    @patch("helpers.license._now", return_value=1000)
    def test_offline_grace_rejects_expired_license(self, _mock_now):
        settings = {
            "last_license_valid": True,
            "last_online_valid_at": 990,
            "license_expired_at": "2000-01-01",
        }

        self.assertFalse(_is_offline_grace_valid(settings))

    @patch("helpers.license._now", return_value=1000)
    def test_offline_grace_rejects_missing_expiry(self, _mock_now):
        settings = {
            "last_license_valid": True,
            "last_online_valid_at": 990,
        }

        self.assertFalse(_is_offline_grace_valid(settings))

    def test_network_error_with_expired_cache_is_not_offline_ok(self):
        settings = {
            "license_key": "LICENSE-SECRET-123456",
            "last_license_valid": True,
            "last_online_valid_at": 9999999999,
            "license_expired_at": "2000-01-01",
        }
        with patch("helpers.license.is_license_invalid", return_value=False), \
            patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.get_or_create_device_id", return_value="device-id-1234567890"), \
            patch("helpers.license._is_settings_hash_valid", return_value=True), \
            patch("helpers.license._call_license_api", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(
                verify_license(exit_on_fail=False, show_message=False),
                LICENSE_STATUS_NETWORK_ERROR,
            )

    def test_network_error_with_missing_expiry_is_not_offline_ok(self):
        settings = {
            "license_key": "LICENSE-SECRET-123456",
            "last_license_valid": True,
            "last_online_valid_at": 9999999999,
        }
        with patch("helpers.license.is_license_invalid", return_value=False), \
            patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.get_or_create_device_id", return_value="device-id-1234567890"), \
            patch("helpers.license._is_settings_hash_valid", return_value=True), \
            patch("helpers.license._call_license_api", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(
                verify_license(exit_on_fail=False, show_message=False),
                LICENSE_STATUS_NETWORK_ERROR,
            )


class TestLicenseActivationFlow(unittest.TestCase):
    def test_get_or_create_device_id_existing(self):
        settings = {"device_id": "a" * 32}
        device_id = get_or_create_device_id(settings)
        self.assertEqual(device_id, "a" * 32)

    def test_get_or_create_device_id_new(self):
        settings = {}
        with patch("helpers.license.save_settings") as mock_save:
            device_id = get_or_create_device_id(settings)

        self.assertEqual(len(device_id), 32)
        self.assertEqual(settings["device_id"], device_id)
        mock_save.assert_called_once()

    def test_generate_device_id_reuses_saved_device_id(self):
        stable_device_id = "stabledeviceid1234567890abcdefgh"
        with patch("helpers.license._load_settings", return_value={"device_id": stable_device_id}), \
            patch("helpers.license.save_settings") as mock_save:
            first = generate_device_id()
            second = generate_device_id()

        self.assertEqual(first, stable_device_id)
        self.assertEqual(second, stable_device_id)
        mock_save.assert_not_called()

    def test_hardware_fingerprint_resilience(self):
        def side_effect(cmd, **kwargs):
            if isinstance(cmd, str) and "wmic" in cmd:
                raise Exception("Failed")
            return "Microsoft Windows [Version 10.0.19041.1]"

        with patch("subprocess.check_output", side_effect=side_effect), \
            patch("uuid.getnode", side_effect=Exception("Failed")):
            hardware_hash = generate_hardware_fingerprint_hash()

        self.assertTrue(len(hardware_hash) > 0)

    def test_verify_license_force_online_skips_recent_cache(self):
        settings = {
            "license_key": "LICENSE-SECRET-123456",
            "clinic_id": "CLINIC-OLD",
            "last_license_valid": True,
            "last_license_check": 9999999999,
            "last_online_valid_at": 9999999999,
            "license_expired_at": "2999-01-01",
        }
        with patch("helpers.license.is_license_invalid", return_value=False), \
            patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.get_or_create_device_id", return_value="device-id-1234567890"), \
            patch("helpers.license._is_settings_hash_valid", return_value=True), \
            patch("helpers.license._save_runtime_settings"), \
            patch(
                "helpers.license._call_license_api",
                return_value={"ok": True, "valid": True, "status": "active", "expired_at": "2999-01-01"},
            ) as mock_call:
            status = verify_license(exit_on_fail=False, show_message=False, force_online=True)

        self.assertEqual(status, LICENSE_STATUS_OK)
        mock_call.assert_called_once()

    def test_verify_license_passes_normalized_clinic_id_to_license_api(self):
        settings = {
            "license_key": "LICENSE-SECRET-123456",
            "clinic_id": "CLINIC-OLD",
        }
        with patch("helpers.license.is_license_invalid", return_value=False), \
            patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.get_or_create_device_id", return_value="device-id-1234567890"), \
            patch("helpers.license._is_settings_hash_valid", return_value=False), \
            patch("helpers.license._save_runtime_settings"), \
            patch(
                "helpers.license._call_license_api",
                return_value={"ok": True, "valid": True, "status": "active", "expired_at": "2999-01-01"},
            ) as mock_call:
            status = verify_license(
                exit_on_fail=False,
                show_message=False,
                force_online=True,
                clinic_id="CLINIC-NORMALIZED",
            )

        self.assertEqual(status, LICENSE_STATUS_OK)
        self.assertEqual(mock_call.call_args.kwargs["clinic_id"], "CLINIC-NORMALIZED")

    def test_verify_license_force_online_network_error_is_not_success(self):
        settings = {
            "license_key": "LICENSE-SECRET-123456",
            "last_license_valid": True,
            "last_license_check": 9999999999,
            "last_online_valid_at": 9999999999,
            "license_expired_at": "2999-01-01",
        }
        with patch("helpers.license.is_license_invalid", return_value=False), \
            patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.get_or_create_device_id", return_value="device-id-1234567890"), \
            patch("helpers.license._is_settings_hash_valid", return_value=True), \
            patch("helpers.license._call_license_api", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(
                verify_license(exit_on_fail=False, show_message=False, force_online=True),
                LICENSE_STATUS_NETWORK_ERROR,
            )

    def test_save_license_key_resets_old_runtime_license_cache(self):
        settings = {
            "license_key": "OLD-LICENSE",
            "clinic_id": "OLD-CLINIC",
            "license_status": "active",
            "license_expired_at": "2999-01-01",
            "license_clinic_name": "Old Clinic",
            "last_license_valid": True,
            "last_license_check": 123,
            "last_online_valid_at": 456,
            "last_server_time": "2999-01-01 00:00:00",
            "settings_hash": "old-hash",
            "last_license_error": "old error",
            "clinic_name": "Keep Clinic Profile",
        }
        with patch("helpers.license._load_settings", return_value=settings), \
            patch("helpers.license.clear_license_invalid"), \
            patch("helpers.license._save_runtime_settings") as mock_save:
            save_license_key("NEW-LICENSE", clinic_id="NEW-CLINIC")

        saved = mock_save.call_args.args[0]
        self.assertEqual(saved["license_key"], "NEW-LICENSE")
        self.assertEqual(saved["clinic_id"], "NEW-CLINIC")
        self.assertEqual(saved["clinic_name"], "Keep Clinic Profile")
        self.assertFalse(saved["last_license_valid"])
        self.assertEqual(saved["last_license_check"], 0)
        self.assertEqual(saved["last_online_valid_at"], 0)
        self.assertNotIn("license_status", saved)
        self.assertNotIn("license_expired_at", saved)
        self.assertNotIn("last_server_time", saved)
        self.assertNotIn("settings_hash", saved)

    def test_call_license_api_sends_hardware_fingerprint_hash_only(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"ok": True, "valid": True}).encode("utf-8")
        response.__exit__.return_value = False

        captured = {}

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return response

        with patch("helpers.license.generate_hardware_fingerprint_hash", return_value="HASHED-FINGERPRINT"), \
            patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = _call_license_api(
                "https://license.example/api",
                "LICENSE-SECRET-123456",
                "device-id-1234567890",
                clinic_id="CLINIC-NORMALIZED",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(captured["payload"]["clinic_id"], "CLINIC-NORMALIZED")
        self.assertEqual(captured["payload"]["hardware_fingerprint_hash"], "HASHED-FINGERPRINT")
        self.assertNotIn("hostname", json.dumps(captured["payload"]).lower())


class TestLicenseErrorFeedbackSanitization(unittest.TestCase):
    @patch("helpers.license._post_license_api", return_value={"ok": True})
    @patch("helpers.license._load_settings")
    def test_report_error_feedback_redacts_sensitive_payload(self, mock_load_settings, mock_post):
        mock_load_settings.return_value = {
            "license_api_url": "https://license.example/api",
            "license_key": "LIC-SECRET-1234567890",
            "clinic_id": "CLINIC-001",
            "license_clinic_name": "Klinik Test",
            "device_id": "DEVICE-SECRET-1234567890",
        }

        err = RuntimeError(
            "failed license_key=LIC-SECRET-1234567890 token=LOCAL-TOKEN-1234567890 admin_pin=1234"
        )

        self.assertTrue(
            report_error_feedback(
                err,
                source="api:POST:/admin_pin/reset/confirm?reset_token=RESET-TOKEN-1234567890",
                context="x_api_key=PAYMENT-SECRET-1234567890 reset_pin=9876",
            )
        )

        payload = mock_post.call_args.args[1]
        payload_text = json.dumps(payload)

        self.assertNotIn("LIC-SECRET-1234567890", payload_text)
        self.assertNotIn("DEVICE-SECRET-1234567890", payload_text)
        self.assertNotIn("LOCAL-TOKEN-1234567890", payload_text)
        self.assertNotIn("RESET-TOKEN-1234567890", payload_text)
        self.assertNotIn("PAYMENT-SECRET-1234567890", payload_text)
        self.assertNotIn("admin_pin=1234", payload_text)
        self.assertNotIn("reset_pin=9876", payload_text)
        self.assertEqual(payload["stack"], "")
        self.assertEqual(payload["license_key"], "LIC-...7890")
        self.assertEqual(payload["device_id"], "DEVI...7890")
        self.assertIn("[redacted]", payload["message"])
        self.assertIn("[redacted]", payload["source"])
        self.assertIn("[redacted]", payload["context"])

    @patch("helpers.license._post_license_api", return_value={"ok": True})
    @patch("helpers.license._load_settings")
    def test_api_exception_handler_reports_sanitized_feedback(self, mock_load_settings, mock_post):
        import api.main as api_main

        mock_load_settings.return_value = {
            "license_api_url": "https://license.example/api",
            "license_key": "LIC-SECRET-1234567890",
            "clinic_id": "CLINIC-001",
            "license_clinic_name": "Klinik Test",
            "device_id": "DEVICE-SECRET-1234567890",
        }
        request = SimpleNamespace(method="POST", url=SimpleNamespace(path="/patients"))
        error = RuntimeError("boom license_key=LIC-SECRET-1234567890 token=LOCAL-TOKEN-1234567890 admin_pin=1234")

        response = asyncio.run(api_main.unhandled_exception_handler(request, error))

        self.assertEqual(response.status_code, 500)
        self.assertIn("Terjadi kesalahan", response.body.decode("utf-8"))
        payload = mock_post.call_args.args[1]
        payload_text = json.dumps(payload)
        self.assertEqual(payload["stack"], "")
        self.assertNotIn("LIC-SECRET-1234567890", payload_text)
        self.assertNotIn("DEVICE-SECRET-1234567890", payload_text)
        self.assertNotIn("LOCAL-TOKEN-1234567890", payload_text)
        self.assertNotIn("admin_pin=1234", payload_text)
        self.assertIn("[redacted]", payload["message"])

    def test_public_route_exemption_stays_limited(self):
        import api.main as api_main

        self.assertTrue(api_main._is_local_token_exempt_path("/license"))
        self.assertTrue(api_main._is_local_token_exempt_path("/static/modules/license.js"))
        self.assertTrue(api_main._is_local_token_exempt_path("/payments/gateway/pay/PAY-123"))
        self.assertTrue(api_main._is_local_token_exempt_path("/payments/gateway/mock/pay/PAY-123"))
        self.assertFalse(api_main._is_local_token_exempt_path("/patients"))
        self.assertFalse(api_main._is_local_token_exempt_path("/settings"))
        self.assertFalse(api_main._is_local_token_exempt_path("/admin_pin/change"))
        self.assertFalse(api_main._is_local_token_exempt_path("/payments/gateway/status/PAY-123"))

    def test_license_template_uses_json_config_script(self):
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api", "templates", "license.html"))
        with open(template_path, encoding="utf-8") as template_file:
            template = template_file.read()

        self.assertIn('id="app-config"', template)
        self.assertIn('type="application/json"', template)
        self.assertIn("| tojson", template)
        self.assertIn("JSON.parse", template)
        self.assertIn("cache_buster | default(1)", template)
        self.assertNotIn("window._initialLicense = {{ license | tojson }}", template)

    def test_license_ui_does_not_render_raw_license_key_or_html_message(self):
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api", "static", "modules", "license.js"))
        with open(script_path, encoding="utf-8") as script_file:
            script = script_file.read()

        self.assertIn("function escapeHtml", script)
        self.assertIn("escapeHtml(data.message)", script)
        self.assertNotIn("data.license_key", script)
        self.assertNotIn("innerHTML = error", script)
        self.assertNotIn("innerHTML = data.message", script)


if __name__ == "__main__":
    unittest.main()
