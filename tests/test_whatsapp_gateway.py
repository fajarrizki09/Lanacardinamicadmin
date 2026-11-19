import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import api.routes.whatsapp as whatsapp_route
from fastapi import HTTPException
from helpers.openwa_client import OpenWAError, extract_openwa_message_id, phone_to_chat_id
from settings import AppSettings, DEFAULT_OPENWA_BASE_URL


class FakeWhatsAppClient:
    def __init__(self, status=None, qr=None, send_results=None):
        self.status = status or {"status": "connected"}
        self.qr = qr or {}
        self.send_results = list(send_results or [])
        self.sent = []

    def session_status(self, session_id=None):
        return dict(self.status)

    def get_qr(self, session_id=None):
        return dict(self.qr)

    def send_text(self, chat_id, text):
        self.sent.append((chat_id, text))
        result = self.send_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeQueueDb:
    def __init__(self, rows):
        self.rows = rows
        self.sent = []
        self.failed = []

    def get_pending_whatsapp_followups(self, limit=10):
        return self.rows[:limit]

    def mark_whatsapp_followup_sent(self, queue_id, openwa_message_id=""):
        self.sent.append((queue_id, openwa_message_id))
        return True

    def mark_whatsapp_followup_failed(self, queue_id, error_message, max_retry=3):
        self.failed.append((queue_id, error_message, max_retry))
        return True


class TestWhatsAppGatewayPaths(unittest.TestCase):
    def test_packaged_project_root_uses_executable_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe_path = os.path.join(tmp, "LancarDinamicAdmin.exe")
            with patch.object(whatsapp_route.sys, "frozen", True, create=True), patch.object(
                whatsapp_route.sys,
                "executable",
                exe_path,
            ):
                self.assertEqual(whatsapp_route._project_root(), Path(tmp))

    def test_bundled_npm_is_preferred_in_packaged_install_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            node_dir = Path(tmp) / "node"
            node_dir.mkdir()
            npm_cmd = node_dir / "npm.cmd"
            node_exe = node_dir / "node.exe"
            npm_cmd.write_text("@echo off\n", encoding="utf-8")
            node_exe.write_text("", encoding="utf-8")

            with patch.object(whatsapp_route.sys, "frozen", True, create=True), patch.object(
                whatsapp_route.sys,
                "executable",
                str(Path(tmp) / "LancarDinamicAdmin.exe"),
            ), patch.object(whatsapp_route.sys, "platform", "win32"):
                self.assertEqual(whatsapp_route._bundled_node_exe(), node_exe)
                self.assertEqual(whatsapp_route._npm_command(), [str(npm_cmd)])
                env = whatsapp_route._openwa_subprocess_env()
                self.assertTrue(env["PATH"].startswith(str(node_dir)))
                self.assertEqual(env["WA_GATEWAY_PORT"], str(whatsapp_route.WA_GATEWAY_PORT))


class TestWhatsAppGatewayApiHelpers(unittest.TestCase):
    def test_session_status_includes_qr_when_gateway_reports_qr_ready_without_payload(self):
        fake_client = FakeWhatsAppClient(
            status={"status": "qr_ready", "sessionStatus": "qr_ready"},
            qr={"qr": "data:image/png;base64,abc", "sessionStatus": "qr_ready"},
        )

        with patch.object(whatsapp_route, "_client", return_value=(fake_client, {"openwa_session_id": "clinic"})):
            response = whatsapp_route.get_openwa_session_status()

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["qr"], "data:image/png;base64,abc")
        self.assertTrue(response["data"]["hasQr"])

    def test_session_status_surfaces_gateway_auth_failure_instead_of_hiding_qr_error(self):
        fake_client = FakeWhatsAppClient(status={"status": "qr_ready"})
        fake_client.get_qr = MagicMock(side_effect=OpenWAError("OpenWA HTTP 403: Gateway token invalid."))

        with patch.object(whatsapp_route, "_client", return_value=(fake_client, {"openwa_session_id": "clinic"})):
            with self.assertRaises(HTTPException) as context:
                whatsapp_route.get_openwa_session_status()

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("403", str(context.exception.detail))

    def test_qr_proxy_response_does_not_expose_internal_gateway_token(self):
        fake_client = FakeWhatsAppClient(qr={"qr": "data:image/png;base64,abc"})

        with patch.object(whatsapp_route, "_client", return_value=(fake_client, {"openwa_session_id": "clinic"})):
            response = whatsapp_route.get_openwa_session_qr()

        self.assertIn("data:image/png", response["data"]["qr"])
        self.assertNotIn("X-Gateway-Token", repr(response))
        self.assertNotIn("internal-gateway-token", repr(response))

    def test_qr_proxy_logs_reason_without_token_when_gateway_rejects_request(self):
        fake_client = FakeWhatsAppClient()
        fake_client.get_qr = MagicMock(side_effect=OpenWAError("OpenWA HTTP 403: forbidden"))

        with patch.object(whatsapp_route, "_client", return_value=(fake_client, {"openwa_session_id": "clinic"})):
            with self.assertLogs("lancar.whatsapp", level="WARNING") as captured:
                with self.assertRaises(HTTPException):
                    whatsapp_route.get_openwa_session_qr()

        combined = " ".join(captured.output)
        self.assertIn("gateway_auth_rejected", combined)
        self.assertNotIn("forbidden", combined)
        self.assertNotIn("token", combined.lower())

    def test_client_rejects_listening_gateway_without_owned_internal_token(self):
        fake_settings = MagicMock()
        fake_settings.get_openwa_settings.return_value = {"openwa_session_id": "clinic"}
        with patch.object(whatsapp_route, "AppSettings", return_value=fake_settings), patch.object(
            whatsapp_route, "get_local_openwa_api_token", return_value=""
        ), patch.object(whatsapp_route, "_is_port_open", return_value=True):
            with self.assertRaises(OpenWAError) as context:
                whatsapp_route._client()

        self.assertIn("tidak dikelola aplikasi", str(context.exception))

    def test_process_queue_marks_sent_and_failed_rows(self):
        rows = [
            {"id": 1, "chat_id": "628111@s.whatsapp.net", "message": "Pesan satu"},
            {"id": 2, "chat_id": "628222@s.whatsapp.net", "message": "Pesan dua"},
        ]
        fake_db = FakeQueueDb(rows)
        fake_client = FakeWhatsAppClient(
            send_results=[
                {"data": {"messageId": "MSG-1"}},
                OpenWAError("WhatsApp belum terkoneksi."),
            ]
        )

        with patch.object(whatsapp_route, "require_admin_pin", return_value=None), patch.object(
            whatsapp_route,
            "db",
            fake_db,
        ), patch.object(
            whatsapp_route,
            "_client",
            return_value=(fake_client, {"openwa_enabled": True, "openwa_rate_limit_per_run": 10}),
        ):
            response = whatsapp_route.process_whatsapp_queue(request=None)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["count"], 2)
        self.assertEqual(fake_db.sent, [(1, "MSG-1")])
        self.assertEqual(fake_db.failed[0][0], 2)
        self.assertIn("WhatsApp belum terkoneksi", fake_db.failed[0][1])


class TestWhatsAppSettingsAndClient(unittest.TestCase):
    def test_openwa_settings_reset_legacy_remote_urls_and_clamp_queue_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = AppSettings(os.path.join(tmp, "settings.json"))
            settings.set_openwa_settings(
                {
                    "openwa_enabled": "on",
                    "openwa_base_url": "https://example.test/layanan/koneksis/2785",
                    "openwa_session_id": " clinic ",
                    "openwa_auto_followup_enabled": "true",
                    "openwa_followup_delay_hours": "9999",
                    "openwa_rate_limit_per_run": "0",
                }
            )

            cfg = settings.get_openwa_settings()

        self.assertEqual(cfg["openwa_base_url"], DEFAULT_OPENWA_BASE_URL)
        self.assertEqual(cfg["openwa_session_id"], "clinic")
        self.assertEqual(cfg["openwa_followup_delay_hours"], 720)
        self.assertEqual(cfg["openwa_rate_limit_per_run"], 1)

    def test_phone_and_message_id_helpers_match_baileys_gateway_payloads(self):
        self.assertEqual(phone_to_chat_id("0812-3456-7890"), "6281234567890@s.whatsapp.net")
        self.assertEqual(extract_openwa_message_id({"data": {"messageId": "BAILEYS-ID"}}), "BAILEYS-ID")


if __name__ == "__main__":
    unittest.main()
