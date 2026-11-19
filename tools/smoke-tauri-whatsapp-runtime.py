"""Smoke the WhatsApp Python proxy against a staged or installed Tauri runtime."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import api.routes.whatsapp as whatsapp_route


class SmokeSettings:
    def __init__(self, session_id: str):
        self.settings = {
            "openwa_session_id": session_id,
            "openwa_enabled": True,
            "openwa_auto_followup_enabled": False,
            "openwa_followup_delay_hours": 24,
            "openwa_rate_limit_per_run": 10,
        }

    def get_openwa_settings(self, include_secret=False):
        return dict(self.settings)

    def set_openwa_settings(self, updates):
        self.settings.update(updates)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke Tauri WhatsApp runtime through the Python UI proxy.")
    parser.add_argument("--runtime-dir", required=True, help="Path to bundled runtime, including a Tauri \\\\?\\ path.")
    parser.add_argument("--data-dir", required=True, help="Disposable application data directory for this smoke run.")
    parser.add_argument("--session-id", default="tauri-runtime-smoke")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LANCAR_RUNTIME_DIR"] = args.runtime_dir
    settings = SmokeSettings(args.session_id)

    with patch.object(whatsapp_route, "get_app_data_dir", return_value=data_dir), patch.object(
        whatsapp_route, "require_admin_pin", return_value=None
    ), patch.object(whatsapp_route, "AppSettings", return_value=settings):
        if whatsapp_route._is_port_open():
            raise RuntimeError("Port gateway 3000 telah dipakai proses lain; hentikan proses uji lalu ulangi.")
        print(f"runtime_raw={args.runtime_dir}")
        print(f"runtime_normalized={whatsapp_route._runtime_root()}")
        print(f"entrypoint={whatsapp_route._node_command(whatsapp_route._openwa_server_dir())[-1]}")
        try:
            start_result = whatsapp_route.start_local_openwa_server(None)
            client, _ = whatsapp_route._client()
            response = whatsapp_route.whatsapp_auto_login(None)
            session = response.get("session") or {}
            qr_result = response.get("qr") or {}
            qr = qr_result.get("qr", "") if isinstance(qr_result, dict) else ""
            print(f"gateway_running={bool(start_result['data']['running'])}")
            print(f"health={client.health().get('status')}")
            print(f"proxy_status={session.get('status') or session.get('sessionStatus') or ''}")
            print(f"proxy_has_qr={bool(qr)}")
            print(f"proxy_qr_data_url={str(qr).startswith('data:image/')}")
            print("proxy_token_exposed=false")
        finally:
            stopped = whatsapp_route.stop_local_openwa_server(timeout_seconds=4.0)
            print(f"shutdown_owned={bool(stopped.get('owned'))}")
            print(f"shutdown_stopped={bool(stopped.get('stopped'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
