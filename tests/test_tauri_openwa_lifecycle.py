import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import api.routes.whatsapp as whatsapp_route
from helpers.openwa_client import OpenWAClient, OpenWAConfig, OpenWAError


class TestTauriOpenWARuntime(unittest.TestCase):
    def tearDown(self):
        whatsapp_route._OPENWA_PROCESS = None
        whatsapp_route._OPENWA_SHUTDOWN_TOKEN = None
        whatsapp_route._OPENWA_API_TOKEN = None
        whatsapp_route._close_openwa_log_stream()

    def test_tauri_runtime_root_controls_packaged_gateway_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            with patch.dict(os.environ, {"LANCAR_RUNTIME_DIR": str(runtime)}):
                self.assertEqual(whatsapp_route._runtime_root(), runtime.resolve())
                self.assertEqual(whatsapp_route._openwa_server_dir(), runtime.resolve() / "openwa_server")

    def test_gateway_session_data_is_written_under_application_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(whatsapp_route, "get_app_data_dir", return_value=tmp):
                env = whatsapp_route._openwa_subprocess_env()

        self.assertEqual(env["WA_GATEWAY_DATA_DIR"], str(Path(tmp) / "whatsapp_gateway"))
        self.assertNotIn("openwa_server", env["WA_GATEWAY_DATA_DIR"])

    def test_gateway_runtime_receives_internal_api_and_shutdown_tokens(self):
        env = whatsapp_route._openwa_subprocess_env("shutdown-token", "api-token")

        self.assertEqual(env["WA_GATEWAY_SHUTDOWN_TOKEN"], "shutdown-token")
        self.assertEqual(env["WA_GATEWAY_API_TOKEN"], "api-token")

    def test_bundled_node_command_uses_absolute_entrypoint_under_install_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "Lancar Dynamic Admin" / "resources" / "runtime"
            node_dir = runtime / "node"
            gateway_dir = runtime / "openwa_server"
            node_dir.mkdir(parents=True)
            gateway_dir.mkdir(parents=True)
            (node_dir / "node.exe").write_text("", encoding="utf-8")
            (gateway_dir / "server.js").write_text("", encoding="utf-8")

            with patch.dict(os.environ, {"LANCAR_RUNTIME_DIR": str(runtime)}), patch.object(
                whatsapp_route.sys, "platform", "win32"
            ):
                command = whatsapp_route._node_command(gateway_dir)

        self.assertEqual(command[0], str((node_dir / "node.exe").resolve()))
        self.assertEqual(command[1], str((gateway_dir / "server.js").resolve()))
        self.assertIn("Lancar Dynamic Admin", command[1])

    def test_tauri_extended_length_runtime_path_is_not_passed_to_node(self):
        raw_runtime = r"\\?\C:\Users\Test\AppData\Local\Lancar Dynamic Admin\runtime"
        with patch.dict(os.environ, {"LANCAR_RUNTIME_DIR": raw_runtime}), patch.object(
            whatsapp_route.sys, "platform", "win32"
        ):
            runtime = str(whatsapp_route._runtime_root())

        self.assertFalse(runtime.startswith("\\\\?\\"))
        self.assertIn("Lancar Dynamic Admin", runtime)

    def test_openwa_client_sends_internal_gateway_token(self):
        client = OpenWAClient(OpenWAConfig(api_token="api-token"))

        self.assertEqual(client._headers()["X-Gateway-Token"], "api-token")

    def test_gateway_api_rejects_browser_origin_and_requires_internal_token(self):
        source = (Path(__file__).resolve().parents[1] / "openwa_server" / "server.js").read_text(encoding="utf-8")

        self.assertIn("const browserRequest = Boolean(req.get('origin') || req.get('referer'));", source)
        self.assertIn("req.get('x-gateway-token') !== API_TOKEN", source)
        self.assertIn("api.use('/api'", source)

    def test_startup_readiness_probe_uses_internal_gateway_token(self):
        fake_client = MagicMock()
        with patch.object(whatsapp_route, "OpenWAClient", return_value=fake_client) as client_factory:
            whatsapp_route._wait_for_local_openwa_ready("owned-token", timeout_seconds=0.1)

        config = client_factory.call_args.args[0]
        self.assertEqual(config.api_token, "owned-token")
        fake_client.health.assert_called_once_with()

    def test_startup_readiness_reports_child_process_exit_before_qr_flow(self):
        process = MagicMock()
        process.poll.return_value = 1

        with self.assertRaises(OpenWAError) as context:
            whatsapp_route._wait_for_local_openwa_ready("owned-token", process=process, timeout_seconds=0.1)

        self.assertIn("berhenti saat startup", str(context.exception))

    def test_windows_gateway_process_does_not_open_console_window(self):
        with patch.object(whatsapp_route.sys, "platform", "win32"):
            flags = whatsapp_route._openwa_creation_flags()

        self.assertTrue(flags & subprocess.CREATE_NEW_PROCESS_GROUP)
        self.assertTrue(flags & subprocess.CREATE_NO_WINDOW)

    def test_gateway_log_is_written_under_application_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(whatsapp_route, "get_app_data_dir", return_value=tmp):
                stream = whatsapp_route._openwa_log_stream()
            try:
                self.assertEqual(Path(stream.name), Path(tmp) / "logs" / "whatsapp_gateway.log")
            finally:
                stream.close()

    def test_owned_gateway_stops_gracefully(self):
        process = MagicMock()
        process.poll.side_effect = [None, 0]
        whatsapp_route._OPENWA_PROCESS = process
        whatsapp_route._OPENWA_SHUTDOWN_TOKEN = "token"

        with patch.object(whatsapp_route, "_request_openwa_shutdown", return_value=True) as request_shutdown:
            result = whatsapp_route.stop_local_openwa_server(timeout_seconds=0.1)

        request_shutdown.assert_called_once_with("token")
        process.terminate.assert_not_called()
        process.wait.assert_called_once_with(timeout=0.1)
        self.assertEqual(result, {"owned": True, "stopped": True, "forced": False})
        self.assertIsNone(whatsapp_route._OPENWA_PROCESS)

    def test_owned_gateway_falls_back_to_process_tree_kill_after_timeout(self):
        process = MagicMock()
        process.pid = 8172
        process.poll.side_effect = [None, 0]
        process.wait.side_effect = [subprocess.TimeoutExpired("node", 0.1), None]
        whatsapp_route._OPENWA_PROCESS = process
        whatsapp_route._OPENWA_SHUTDOWN_TOKEN = "token"

        with patch.object(whatsapp_route, "_request_openwa_shutdown", return_value=True), patch.object(whatsapp_route, "_force_kill_process_tree") as force_kill:
            result = whatsapp_route.stop_local_openwa_server(timeout_seconds=0.1)

        force_kill.assert_called_once_with(process)
        self.assertEqual(result, {"owned": True, "stopped": True, "forced": True})


if __name__ == "__main__":
    unittest.main()
