from __future__ import annotations

import os
import platform
import subprocess
from urllib.parse import urlparse

from utils.app_paths import get_app_data_dir

ALLOWED_HTTPS_EXTERNAL_HOSTS = {
    "app.sandbox.midtrans.com",
    "wa.me",
}
ALLOWED_LOCAL_EXTERNAL_TARGETS = {
    ("http", "127.0.0.1", 3000),
}


def _support_settings():
    try:
        from settings import AppSettings
        settings = AppSettings().get_all_settings()
    except Exception:
        settings = {}
    return {
        "support_name": str(os.getenv("SUPPORT_NAME") or settings.get("support_name") or "Support Lancar Dynamic").strip(),
        "support_whatsapp": str(os.getenv("SUPPORT_WHATSAPP") or settings.get("support_whatsapp") or "").strip(),
        "support_email": str(os.getenv("SUPPORT_EMAIL") or settings.get("support_email") or "").strip(),
    }


def get_support_app_info(db=None):
    base_dir = get_app_data_dir()
    backup_dir = os.path.join(base_dir, "backups")
    logs_dir = os.path.join(base_dir, "logs")
    exports_dir = os.path.join(base_dir, "exports")
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)

    try:
        from version import APP_VERSION
    except Exception:
        APP_VERSION = ""

    database_path = ""
    if db is not None:
        try:
            database_path = db.get_database_path() or ""
        except Exception:
            database_path = ""

    license_status = {}
    try:
        from helpers.license import get_license_status_summary
        raw_license = get_license_status_summary()
        license_status = {
            "valid": bool(raw_license.get("valid")),
            "status": str(raw_license.get("status") or ""),
            "expired_at": str(raw_license.get("expired_at") or ""),
            "clinic_id": str(raw_license.get("clinic_id") or ""),
            "clinic_name": str(raw_license.get("clinic_name") or ""),
        }
    except Exception:
        license_status = {"valid": False, "status": ""}

    return {
        "app_version": APP_VERSION,
        "database_path": os.path.abspath(database_path) if database_path else "",
        "backup_dir": os.path.abspath(backup_dir),
        "logs_dir": os.path.abspath(logs_dir),
        "exports_dir": os.path.abspath(exports_dir),
        "license": license_status,
        "support": _support_settings(),
    }


def folder_path_for_kind(kind, db=None):
    info = get_support_app_info(db)
    mapping = {
        "backup": info["backup_dir"],
        "backups": info["backup_dir"],
        "log": info["logs_dir"],
        "logs": info["logs_dir"],
        "export": info["exports_dir"],
        "exports": info["exports_dir"],
        "data": os.path.dirname(info["database_path"]) if info.get("database_path") else get_app_data_dir(),
    }
    key = str(kind or "").strip().lower()
    if key not in mapping:
        raise ValueError("Folder tidak dikenal.")
    path = os.path.abspath(mapping[key])
    os.makedirs(path, exist_ok=True)
    return path


def open_local_folder(kind, db=None):
    path = folder_path_for_kind(kind, db)
    system = platform.system().lower()
    if system == "windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
    return path


def validate_external_url(url):
    value = str(url or "").strip()
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.username or parsed.password:
        raise ValueError("URL eksternal tidak diizinkan.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL eksternal tidak diizinkan.") from exc
    if parsed.scheme == "https" and hostname in ALLOWED_HTTPS_EXTERNAL_HOSTS and port in (None, 443):
        return value
    if (parsed.scheme, hostname, port) in ALLOWED_LOCAL_EXTERNAL_TARGETS:
        return value
    raise ValueError("URL eksternal tidak diizinkan.")


def open_external_url(url):
    safe_url = validate_external_url(url)
    system = platform.system().lower()
    if system == "windows":
        os.startfile(safe_url)  # type: ignore[attr-defined]
    elif system == "darwin":
        subprocess.Popen(["open", safe_url])
    else:
        subprocess.Popen(["xdg-open", safe_url])
    return safe_url
