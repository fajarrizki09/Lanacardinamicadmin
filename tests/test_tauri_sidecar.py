import socket
import unittest
from unittest.mock import mock_open, patch

import sidecar_main
from sidecar_main import APP_HOST, find_available_port, normalize_runtime_dir, parse_args


class TestTauriSidecarLauncher(unittest.TestCase):
    def test_explicit_port_is_parsed(self):
        args = parse_args(
            [
                "--port",
                "8123",
                "--shutdown-token",
                "desktop-secret",
                "--runtime-dir",
                "C:/runtime",
            ]
        )

        self.assertEqual(args.port, 8123)
        self.assertEqual(args.shutdown_token, "desktop-secret")
        self.assertEqual(args.runtime_dir, "C:/runtime")

    def test_invalid_port_is_rejected(self):
        with self.assertRaises(SystemExit):
            parse_args(["--port", "70000"])

    def test_port_selection_skips_occupied_loopback_port(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind((APP_HOST, 0))
        listener.listen(1)
        occupied_port = listener.getsockname()[1]
        try:
            selected_port = find_available_port(occupied_port, max_attempts=2)
        finally:
            listener.close()

        self.assertNotEqual(selected_port, occupied_port)

    def test_windowed_sidecar_replaces_missing_console_streams(self):
        stream_open = mock_open()
        with (
            patch.object(sidecar_main.sys, "stdout", None),
            patch.object(sidecar_main.sys, "stderr", None),
            patch.object(sidecar_main, "open", stream_open, create=True),
        ):
            sidecar_main._ensure_background_streams()

            self.assertIsNotNone(sidecar_main.sys.stdout)
            self.assertIsNotNone(sidecar_main.sys.stderr)

        self.assertEqual(stream_open.call_count, 2)

    def test_windows_extended_runtime_path_is_normalized_for_node_children(self):
        self.assertEqual(
            normalize_runtime_dir(r"\\?\C:\Users\Test\AppData\Local\Lancar Dynamic Admin\runtime"),
            r"C:\Users\Test\AppData\Local\Lancar Dynamic Admin\runtime",
        )
        self.assertEqual(
            normalize_runtime_dir(r"\\?\UNC\server\share\runtime"),
            r"\\server\share\runtime",
        )


if __name__ == "__main__":
    unittest.main()
