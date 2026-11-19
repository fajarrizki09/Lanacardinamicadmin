"""Backend-only launcher for the Tauri desktop shell.

This process intentionally contains no desktop UI imports. Tauri owns the
window lifecycle while this sidecar keeps the existing FastAPI domain intact.
"""

from __future__ import annotations

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets
import socket
import sys

from fastapi import HTTPException, Request


APP_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def normalize_runtime_dir(runtime_dir: str) -> str:
    """Return a Node-compatible runtime path from Tauri's Windows resource path."""
    normalized = os.path.abspath(str(runtime_dir or "").strip())
    if normalized.startswith("\\\\?\\UNC\\"):
        return "\\\\" + normalized[8:]
    if normalized.startswith("\\\\?\\"):
        return normalized[4:]
    return normalized


def _ensure_background_streams() -> None:
    for stream_name in ("stdout", "stderr"):
        if getattr(sys, stream_name, None) is None:
            setattr(sys, stream_name, open(os.devnull, "w", encoding="utf-8"))


def _setup_sidecar_logging() -> str:
    from utils.app_paths import get_app_data_dir

    log_dir = os.path.join(get_app_data_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.abspath(os.path.join(log_dir, "desktop_sidecar.log"))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(getattr(handler, "baseFilename", None) == log_path for handler in root_logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
        root_logger.addHandler(handler)
    return log_path


def find_available_port(start_port: int = DEFAULT_PORT, max_attempts: int = 20) -> int:
    for offset in range(max_attempts):
        candidate = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            if sock.connect_ex((APP_HOST, candidate)) != 0:
                return candidate
    raise RuntimeError(
        f"Tidak ada port lokal kosong dari {start_port} sampai {start_port + max_attempts - 1}."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lancar Dynamic Admin API sidecar")
    parser.add_argument("--port", type=int, default=0, help="Port loopback yang disediakan shell.")
    parser.add_argument(
        "--shutdown-token",
        default="",
        help="Token internal untuk shutdown graceful oleh desktop shell.",
    )
    parser.add_argument(
        "--runtime-dir",
        default="",
        help="Direktori resource runtime Node/OpenWA yang dibundel Tauri.",
    )
    parser.add_argument(
        "--app-data-dir",
        default="",
        help="Direktori data aplikasi yang dipakai desktop shell.",
    )
    args = parser.parse_args(argv)
    if args.port < 0 or args.port > 65535:
        parser.error("--port harus berada pada rentang 0-65535.")
    return args


def run(
    port: int = 0,
    shutdown_token: str = "",
    runtime_dir: str = "",
    app_data_dir: str = "",
) -> None:
    _ensure_background_streams()
    os.environ["LANCAR_DESKTOP_SHELL"] = "tauri"
    if runtime_dir:
        os.environ["LANCAR_RUNTIME_DIR"] = normalize_runtime_dir(runtime_dir)
    if app_data_dir:
        os.environ["LANCAR_APP_DATA_DIR"] = normalize_runtime_dir(app_data_dir)
    log_path = _setup_sidecar_logging()

    import uvicorn
    from api.main import app as fastapi_app

    selected_port = port or find_available_port()
    logging.info(
        "Starting Tauri API sidecar on %s:%s; runtime=%s; log=%s",
        APP_HOST,
        selected_port,
        os.environ.get("LANCAR_RUNTIME_DIR", ""),
        log_path,
    )
    server = uvicorn.Server(
        uvicorn.Config(
            fastapi_app,
            host=APP_HOST,
            port=selected_port,
            log_level="warning",
            access_log=False,
        )
    )

    if shutdown_token:
        @fastapi_app.post("/_desktop/shutdown", include_in_schema=False)
        async def desktop_shutdown(request: Request):
            if request.headers.get("Origin") or request.headers.get("Referer"):
                raise HTTPException(status_code=403, detail="Shutdown hanya tersedia untuk desktop shell.")
            provided = request.headers.get("X-Shutdown-Token", "")
            if not secrets.compare_digest(provided, shutdown_token):
                raise HTTPException(status_code=403, detail="Token shutdown tidak valid.")
            server.should_exit = True
            return {"status": "shutting_down"}

    try:
        server.run()
    finally:
        try:
            from api.routes.whatsapp import stop_local_openwa_server

            stop_local_openwa_server()
        except Exception:
            logging.exception("Failed to stop WhatsApp gateway during sidecar shutdown.")


def main() -> None:
    args = parse_args()
    run(args.port, args.shutdown_token, args.runtime_dir, args.app_data_dir)


if __name__ == "__main__":
    main()
