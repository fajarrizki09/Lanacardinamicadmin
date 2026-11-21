import base64
import hashlib
import hmac
import json
import logging
import traceback
import os
import platform
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, time as datetime_time

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
except ImportError:
    QApplication = None
    QMessageBox = None

from helpers.secure_settings import load_settings, save_settings
from utils.app_paths import get_app_data_dir


_DEFAULT_LICENSE_API_URL_PARTS = (
    "aHR0cHM6Ly9tYW5h",
    "Z2VtZW50LWxpc2Vuc2",
    "kudmVyY2VsLmFwcC9h",
    "cGkvZ2Fz",
)


def _default_license_api_url() -> str:
    encoded = "".join(_DEFAULT_LICENSE_API_URL_PARTS)
    return base64.b64decode(encoded.encode("ascii")).decode("utf-8")


DEFAULT_LICENSE_API_URL = _default_license_api_url()
APP_NAME = "LancarDinamicAdmin"
try:
    from version import APP_VERSION
except Exception:
    APP_VERSION = "1.7"
CACHE_TTL_SECONDS = 6 * 60 * 60
OFFLINE_GRACE_SECONDS = 7 * 24 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 10
LICENSE_ERROR_MESSAGE = "Lisensi tidak valid atau sudah expired"
ONLINE_VERIFY_REQUIRED_MESSAGE = "Lisensi perlu diverifikasi online kembali."
INVALID_SYSTEM_TIME_MESSAGE = "Waktu sistem tidak valid. Periksa tanggal/jam komputer."
POPUP_COOLDOWN_SECONDS = 5 * 60
LICENSE_STATUS_OK = "ok"
LICENSE_STATUS_INVALID = "invalid"
LICENSE_STATUS_NETWORK_ERROR = "network_error"
PIN_RESET_TOKEN_SETTING = "admin_pin_reset_token"
PIN_RESET_REQUEST_ID_SETTING = "admin_pin_reset_request_id"
last_popup_time = 0.0
license_invalid = False
last_license_message = ""
_popup_lock = threading.Lock()
_license_state_lock = threading.Lock()


class LicenseNetworkError(Exception):
    pass


def mark_license_invalid() -> None:
    global license_invalid
    with _license_state_lock:
        license_invalid = True


def is_license_invalid() -> bool:
    with _license_state_lock:
        return license_invalid


def clear_license_invalid() -> None:
    global license_invalid
    with _license_state_lock:
        license_invalid = False


def get_last_license_message() -> str:
    return last_license_message


def _set_last_license_message(message: str) -> None:
    global last_license_message
    last_license_message = str(message or "").strip()


def _load_settings() -> dict:
    return load_settings()


def _settings_hash_source(settings: dict) -> str:
    return "|".join([
        str(settings.get("license_key", "")).strip(),
        str(settings.get("last_online_valid_at") or 0),
        str(settings.get("device_id", "")).strip(),
    ])


def _create_settings_hash(settings: dict) -> str:
    return hashlib.sha256(_settings_hash_source(settings).encode("utf-8")).hexdigest()


def _update_settings_hash(settings: dict) -> None:
    if not settings.get("device_id"):
        settings["device_id"] = generate_device_id()
    settings["settings_hash"] = _create_settings_hash(settings)


def _is_settings_hash_valid(settings: dict, device_id: str) -> bool:
    stored_hash = str(settings.get("settings_hash", "")).strip()
    if not stored_hash:
        return False

    hash_settings = settings.copy()
    hash_settings["device_id"] = device_id
    expected_hash = _create_settings_hash(hash_settings)
    return hmac.compare_digest(stored_hash, expected_hash)


def _save_runtime_settings(settings: dict) -> None:
    _update_settings_hash(settings)
    save_settings(settings)


def get_saved_license_key() -> str:
    return str(_load_settings().get("license_key", "")).strip()


def get_saved_clinic_id() -> str:
    return str(_load_settings().get("clinic_id", "")).strip()


def get_license_status_summary() -> dict:
    settings = _load_settings()
    license_key = str(settings.get("license_key", "")).strip()
    masked_key = ""
    if license_key:
        masked_key = license_key if len(license_key) <= 10 else f"{license_key[:7]}...{license_key[-4:]}"

    return {
        "status": str(settings.get("license_status", "") or "").strip(),
        "valid": bool(settings.get("last_license_valid")),
        "expired_at": str(settings.get("license_expired_at", "") or "").strip(),
        "clinic_id": str(settings.get("clinic_id", "") or "").strip(),
        "clinic_name": str(settings.get("license_clinic_name", "") or settings.get("clinic_name", "") or "").strip(),
        "license_key": masked_key,
        "last_check": settings.get("last_license_check") or 0,
        "message": get_last_license_message(),
    }


def _reset_license_runtime_settings(settings: dict) -> None:
    for field in (
        "license_key",
        "clinic_id",
        "license_status",
        "license_expired_at",
        "license_clinic_name",
        "last_license_valid",
        "last_license_check",
        "last_online_valid_at",
        "last_server_time",
        "settings_hash",
        "last_license_error",
    ):
        settings.pop(field, None)
    settings["last_license_valid"] = False
    settings["last_license_check"] = 0
    settings["last_online_valid_at"] = 0


def save_license_key(license_key: str, api_url: str = "", clinic_id: str = "") -> None:
    settings = _load_settings()
    _reset_license_runtime_settings(settings)

    settings["license_key"] = str(license_key or "").strip()
    if clinic_id:
        settings["clinic_id"] = str(clinic_id).strip()
    if api_url:
        settings["license_api_url"] = str(api_url).strip()

    clear_license_invalid()
    _save_runtime_settings(settings)


def generate_hardware_fingerprint_hash() -> str:
    import subprocess
    import uuid

    bits = [
        socket.gethostname(),
        platform.system(),
        platform.release(),
        platform.version(),
        platform.machine(),
        platform.processor(),
    ]

    try:
        mac = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        if mac and mac != "00:00:00:00:00:00":
            bits.append(mac)
    except Exception:
        pass

    if platform.system() == "Windows":
        for command, header in (
            ("wmic diskdrive get serialnumber", "SerialNumber"),
            ("wmic cpu get processorid", "ProcessorId"),
        ):
            try:
                result = subprocess.check_output(
                    command,
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).decode().split("\n")
                bits.extend(part.strip() for part in result if part.strip() and header not in part)
            except Exception:
                pass

    raw = "|".join(str(part) for part in bits if part)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_or_create_device_id(settings: dict) -> str:
    device_id = str(settings.get("device_id") or "").strip()
    if device_id and len(device_id) >= 32:
        return device_id

    import uuid
    new_id = str(uuid.uuid4()).replace("-", "")
    settings["device_id"] = new_id
    try:
        save_settings(settings)
    except Exception as exc:
        logging.warning("Failed to save newly generated device_id: %s", exc)
    return new_id


def generate_device_id() -> str:
    settings = _load_settings()
    return get_or_create_device_id(settings)


def _now() -> int:
    return int(time.time())


def _is_recent_valid_check(settings: dict) -> bool:
    if not settings.get("last_license_valid"):
        return False

    if not _is_cached_license_unexpired(settings):
        return False

    try:
        checked_at = int(settings.get("last_license_check") or 0)
    except (TypeError, ValueError):
        return False

    return checked_at > 0 and (_now() - checked_at) < CACHE_TTL_SECONDS


def _is_offline_grace_valid(settings: dict) -> bool:
    if not settings.get("last_license_valid"):
        return False

    if not _is_cached_license_unexpired(settings):
        return False

    try:
        online_valid_at = int(settings.get("last_online_valid_at") or 0)
    except (TypeError, ValueError):
        return False

    return online_valid_at > 0 and (_now() - online_valid_at) <= OFFLINE_GRACE_SECONDS


def _parse_server_time(value: object) -> datetime | None:
    server_time = str(value or "").strip()
    if not server_time:
        return None

    for date_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(server_time[:19], date_format)
        except ValueError:
            continue
    return None


def _parse_expiry_datetime(value: object) -> datetime | None:
    expiry_text = str(value or "").strip()
    if not expiry_text:
        return None

    if expiry_text.endswith("Z"):
        expiry_text = expiry_text[:-1]
    if "+" in expiry_text:
        expiry_text = expiry_text.split("+", 1)[0]

    date_only = expiry_text[:10]
    time_part = expiry_text[10:].strip()
    if len(expiry_text) == 10:
        try:
            return datetime.combine(datetime.strptime(date_only, "%Y-%m-%d").date(), datetime_time.max)
        except ValueError:
            return None
    normalized_time_part = time_part.lstrip("T")
    if normalized_time_part.startswith("00:00:00"):
        time_part = "00:00:00"
    if time_part in {"", "T00:00:00", "00:00:00"}:
        try:
            return datetime.combine(datetime.strptime(date_only, "%Y-%m-%d").date(), datetime_time.max)
        except ValueError:
            return None

    return _parse_server_time(expiry_text)


def _is_cached_license_unexpired(settings: dict) -> bool:
    expiry = _parse_expiry_datetime(settings.get("license_expired_at"))
    if expiry is not None:
        return datetime.now() <= expiry

    status = str(settings.get("license_status") or "").lower().strip()
    return status in {"active", "ok", "valid", "lifetime", "permanent"}

def _is_local_time_before_last_server_time(settings: dict) -> bool:
    last_server_time = _parse_server_time(settings.get("last_server_time"))
    if last_server_time is None:
        return False

    return datetime.now() < last_server_time


def _show_blocking_popup(message: str = LICENSE_ERROR_MESSAGE) -> None:
    global last_popup_time

    now = time.monotonic()
    with _popup_lock:
        if now - last_popup_time < POPUP_COOLDOWN_SECONDS:
            return
        last_popup_time = now

    if QApplication is None or QMessageBox is None:
        logging.error("License access blocked: %s", message)
        return

    if QApplication.instance() is None:
        QApplication(sys.argv)

    QMessageBox.critical(None, "Lisensi", message)


def _exit_with_license_error(message: str = LICENSE_ERROR_MESSAGE) -> None:
    _show_blocking_popup(message)
    sys.exit(1)


def _call_license_api(api_url: str, license_key: str, device_id: str, clinic_id: str = "") -> dict:
    if not clinic_id:
        settings = _load_settings()
        clinic_id = str(settings.get("clinic_id", "")).strip()

    payload = {
        "action": "verify_license",
        "license_key": license_key,
        "clinic_id": clinic_id,
        "device_id": device_id,
        "hardware_fingerprint_hash": generate_hardware_fingerprint_hash(),
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "os_name": platform.system(),
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def _post_license_api(api_url: str, payload: dict, timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def _license_identity_payload(settings: dict, action: str) -> dict:
    device_id = str(settings.get("device_id") or generate_device_id()).strip()
    return {
        "action": action,
        "clinic_id": str(settings.get("clinic_id", "")).strip(),
        "clinic_name": str(settings.get("license_clinic_name") or settings.get("clinic_name") or "").strip(),
        "license_key": str(settings.get("license_key", "")).strip(),
        "device_id": device_id,
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "os_name": platform.system(),
    }


def _parse_pin_reset_response(result: dict) -> tuple[bool, str, dict]:
    if not isinstance(result, dict):
        return False, "Respons pusat lisensi tidak valid.", {}

    data = result.get("data")
    if not isinstance(data, dict):
        data = {}

    approved = result.get("approved")
    if not isinstance(approved, bool):
        approved = data.get("approved")
    if isinstance(approved, bool):
        success = approved
    else:
        success = bool(result.get("success") or result.get("ok") or data.get("success"))

    message = (
        str(result.get("message") or "").strip()
        or str(data.get("message") or "").strip()
        or str(result.get("error") or "").strip()
        or str(data.get("error") or "").strip()
        or ("Reset PIN disetujui pusat lisensi." if success else "Reset PIN belum disetujui pusat lisensi.")
    )
    return success, message, data


def _sanitize_pin_reset_message(message: str) -> str:
    return _sanitize_feedback_text(message, max_length=240) or "Respons pusat lisensi tidak valid."


def _save_pin_reset_token(settings: dict, token: str, request_id: str) -> None:
    settings[PIN_RESET_TOKEN_SETTING] = token
    settings[PIN_RESET_REQUEST_ID_SETTING] = request_id
    _save_runtime_settings(settings)


def _clear_pin_reset_token(settings: dict) -> None:
    settings.pop(PIN_RESET_TOKEN_SETTING, None)
    settings.pop(PIN_RESET_REQUEST_ID_SETTING, None)
    _save_runtime_settings(settings)


def request_admin_pin_reset() -> dict:
    settings = _load_settings()
    api_url = str(settings.get("license_api_url", DEFAULT_LICENSE_API_URL)).strip() or DEFAULT_LICENSE_API_URL
    payload = _license_identity_payload(settings, "request_admin_pin_reset")
    if not payload["license_key"]:
        raise ValueError("Lisensi belum terpasang. Aktivasi lisensi dulu sebelum reset PIN.")
    if not payload["clinic_id"]:
        raise ValueError("Clinic ID belum tersimpan. Aktivasi lisensi dulu sebelum reset PIN.")

    try:
        result = _post_license_api(api_url, payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError) as parse_exc:
            raise LicenseNetworkError("Pusat lisensi menolak permintaan reset PIN.") from parse_exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise LicenseNetworkError("Pusat lisensi tidak dapat dihubungi untuk meminta reset PIN.") from exc

    success, message, data = _parse_pin_reset_response(result)
    message = _sanitize_pin_reset_message(message)
    if not success:
        raise ValueError(message)
    reset_token = str(data.get("reset_token") or result.get("reset_token") or "").strip()
    if not reset_token:
        raise ValueError("Pusat lisensi tidak mengirim token reset yang valid.")
    reset_request_id = str(data.get("reset_request_id") or data.get("id") or result.get("reset_request_id") or result.get("id") or "").strip()
    _save_pin_reset_token(settings, reset_token, reset_request_id)
    return {
        "status": "success",
        "message": message,
        "reset_request_id": reset_request_id,
    }


def confirm_admin_pin_reset(reset_token: str, reset_pin: str = "") -> dict:
    pin_code = str(reset_pin or "").strip()
    if not pin_code:
        raise ValueError("Kode reset lisensi wajib diisi.")

    settings = _load_settings()
    token = str(settings.get(PIN_RESET_TOKEN_SETTING) or reset_token or "").strip()
    if not token:
        raise ValueError("Kode reset belum siap. Klik Minta Kode Reset ulang.")
    api_url = str(settings.get("license_api_url", DEFAULT_LICENSE_API_URL)).strip() or DEFAULT_LICENSE_API_URL
    payload = _license_identity_payload(settings, "confirm_admin_pin_reset")
    payload["reset_token"] = token
    payload["reset_pin"] = pin_code
    if not payload["license_key"]:
        raise ValueError("Lisensi belum terpasang. Aktivasi lisensi dulu sebelum reset PIN.")
    if not payload["clinic_id"]:
        raise ValueError("Clinic ID belum tersimpan. Aktivasi lisensi dulu sebelum reset PIN.")

    try:
        result = _post_license_api(api_url, payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError) as parse_exc:
            raise LicenseNetworkError("Pusat lisensi menolak kode reset PIN.") from parse_exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise LicenseNetworkError("Pusat lisensi tidak dapat dihubungi untuk memverifikasi kode reset.") from exc

    success, message, data = _parse_pin_reset_response(result)
    message = _sanitize_pin_reset_message(message)
    if not success:
        raise ValueError(message)
    _clear_pin_reset_token(settings)
    return {
        "status": "success",
        "message": message,
        "reset_request_id": str(data.get("reset_request_id") or data.get("id") or result.get("reset_request_id") or result.get("id") or "").strip(),
    }


def _extract_license_response(result: dict) -> tuple[bool, dict, str]:
    if not isinstance(result, dict):
        return False, {}, "License API response tidak valid."

    data = result.get("data")
    if not isinstance(data, dict):
        data = {}

    license_info = result.get("license")
    if not isinstance(license_info, dict):
        license_info = {}

    status = str(
        license_info.get("status")
        or data.get("status")
        or result.get("status")
        or ""
    ).lower().strip()
    expired_at_str = str(
        license_info.get("expires_at")
        or license_info.get("expired_at")
        or data.get("expired_at")
        or result.get("expired_at")
        or ""
    ).strip()

    root_ok = result.get("ok")
    root_success = result.get("success")
    root_valid = result.get("valid")
    data_valid = data.get("valid")
    explicit_failure = (
        root_ok is False
        or root_success is False
        or root_valid is False
        or data_valid is False
    )
    explicit_valid = root_valid is True or data_valid is True
    status_is_active = status in {"active", "ok", "valid", "lifetime", "permanent"}
    is_valid = bool((explicit_valid or status_is_active) and not explicit_failure)

    if is_valid and expired_at_str:
        expiry = _parse_expiry_datetime(expired_at_str)
        if expiry is not None and datetime.now() > expiry:
            is_valid = False
            status = "expired"

    merged_data = {
        **data,
        "valid": is_valid,
    }
    if status:
        merged_data.setdefault("status", status)
    if expired_at_str:
        merged_data.setdefault("expired_at", expired_at_str)
    if license_info:
        merged_data.setdefault("clinic_id", license_info.get("clinic_id", ""))

    message = (
        str(result.get("message") or "").strip()
        or str(result.get("error") or "").strip()
        or str(data.get("message") or "").strip()
        or str(data.get("error") or "").strip()
        or ("License valid." if is_valid else LICENSE_ERROR_MESSAGE)
    )
    return is_valid, merged_data, message


_FEEDBACK_SECRET_KEY_PATTERN = re.compile(
    r'(?i)\b([A-Za-z0-9_-]*(?:license[_-]?key|api[_-]?key|secret|token|pin|password|admin[_-]?pin)[A-Za-z0-9_-]*)\b'
    r'(\s*[:=]\s*)'
    r'(["\']?)[^,\s"\'&]+(["\']?)'
)
_FEEDBACK_AUTH_PATTERN = re.compile(r"(?i)\b(Bearer|Token|Basic)\s+[A-Za-z0-9._~+/=-]+")
_FEEDBACK_LONG_SECRET_PATTERN = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9._-]{15,}\b")


def _mask_feedback_secret(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}...{text[-4:]}"


def _sanitize_feedback_text(value: object, max_length: int = 500) -> str:
    text = str(value or "")
    if not text:
        return ""

    text = _FEEDBACK_SECRET_KEY_PATTERN.sub(r"\1\2\3[redacted]\4", text)
    text = _FEEDBACK_AUTH_PATTERN.sub(r"\1 [redacted]", text)
    text = _FEEDBACK_LONG_SECRET_PATTERN.sub("[redacted]", text)
    text = text.replace("\r", " ").replace("\n", " ")
    return text[:max_length].strip()


def report_error_feedback(
    error: BaseException | str,
    source: str = "",
    severity: str = "error",
    context: str = "",
) -> bool:
    settings = _load_settings()
    api_url = str(settings.get("license_api_url", DEFAULT_LICENSE_API_URL)).strip() or DEFAULT_LICENSE_API_URL
    device_id = str(settings.get("device_id") or generate_device_id()).strip()

    if isinstance(error, BaseException):
        error_type = error.__class__.__name__
        message = _sanitize_feedback_text(str(error))
    else:
        error_type = "ApplicationError"
        message = _sanitize_feedback_text(error)

    payload = {
        "action": "report_feedback",
        "severity": _sanitize_feedback_text(severity, max_length=40),
        "clinic_id": _sanitize_feedback_text(settings.get("clinic_id"), max_length=120),
        "clinic_name": _sanitize_feedback_text(settings.get("license_clinic_name") or settings.get("clinic_name"), max_length=160),
        "license_key": _mask_feedback_secret(settings.get("license_key")),
        "device_id": _mask_feedback_secret(device_id),
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "os_name": platform.system(),
        "error_type": error_type,
        "message": message or error_type,
        "source": _sanitize_feedback_text(source, max_length=160),
        "stack": "",
        "context": _sanitize_feedback_text(context, max_length=500),
    }

    try:
        result = _post_license_api(api_url, payload, timeout=6)
        return bool(result.get("success") or result.get("ok"))
    except Exception:
        logging.exception("Failed to report application feedback")
        return False


def _save_license_cache(
    settings: dict,
    is_valid: bool,
    online_valid: bool = False,
    server_time: str = "",
    device_id: str = "",
    license_data: dict | None = None,
) -> None:
    settings["last_license_check"] = _now()
    settings["last_license_valid"] = bool(is_valid)
    settings["device_id"] = device_id or generate_device_id()
    if license_data:
        settings["license_status"] = str(license_data.get("status") or "").strip()
        settings["license_expired_at"] = str(license_data.get("expired_at") or "").strip()
        settings["license_clinic_name"] = str(license_data.get("clinic_name") or "").strip()
        if license_data.get("clinic_id"):
            settings["clinic_id"] = str(license_data.get("clinic_id")).strip()
    if server_time:
        settings["last_server_time"] = server_time
    if online_valid:
        settings["last_online_valid_at"] = settings["last_license_check"]
    _save_runtime_settings(settings)


def verify_license(
    exit_on_fail: bool = True,
    show_message: bool = True,
    raise_network_errors: bool = False,
    force_online: bool = False,
    clinic_id: str = "",
    **kwargs,
) -> str:
    _set_last_license_message("")
    if kwargs:
        try:
            logging.warning(
                "verify_license received unexpected kwargs: %s\nCaller stack:\n%s",
                kwargs,
                "".join(traceback.format_stack(limit=12)),
            )
        except Exception:
            pass
    if is_license_invalid():
        return LICENSE_STATUS_INVALID

    settings = _load_settings()
    license_key = str(settings.get("license_key", "")).strip()
    api_url = str(settings.get("license_api_url", DEFAULT_LICENSE_API_URL)).strip() or DEFAULT_LICENSE_API_URL
    device_id = get_or_create_device_id(settings)
    force_online_verify = not _is_settings_hash_valid(settings, device_id) or force_online

    if _is_local_time_before_last_server_time(settings):
        mark_license_invalid()
        if show_message:
            _show_blocking_popup(INVALID_SYSTEM_TIME_MESSAGE)
        if exit_on_fail:
            sys.exit(1)
        return LICENSE_STATUS_INVALID

    if not force_online_verify and _is_recent_valid_check(settings):
        return LICENSE_STATUS_OK

    if not license_key:
        _save_license_cache(settings, False, device_id=device_id)
        mark_license_invalid()
        if show_message:
            _show_blocking_popup()
        if exit_on_fail:
            sys.exit(1)
        return LICENSE_STATUS_INVALID

    if not clinic_id:
        clinic_id = str(settings.get("clinic_id", "")).strip()

    try:
        result = _call_license_api(api_url, license_key, device_id, clinic_id=clinic_id)
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            _set_last_license_message("License API HTTP response tidak valid.")
            if raise_network_errors:
                raise LicenseNetworkError("License API HTTP response tidak valid.") from exc
            return LICENSE_STATUS_NETWORK_ERROR
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        _set_last_license_message("License API tidak dapat dihubungi.")
        if raise_network_errors:
            raise LicenseNetworkError("License API tidak dapat dihubungi.")
        if not force_online_verify and _is_offline_grace_valid(settings):
            _set_last_license_message("Lisensi aktif dari cache offline.")
            return LICENSE_STATUS_OK
        if settings.get("last_license_valid"):
            if show_message:
                _show_blocking_popup(ONLINE_VERIFY_REQUIRED_MESSAGE)
        return LICENSE_STATUS_NETWORK_ERROR

    is_valid, data, message = _extract_license_response(result)
    _set_last_license_message(message)
    _save_license_cache(
        settings,
        is_valid,
        online_valid=is_valid,
        server_time=str(data.get("server_time") or ""),
        device_id=device_id,
        license_data=data,
    )

    if not is_valid:
        mark_license_invalid()
        if show_message:
            _show_blocking_popup()
        if exit_on_fail:
            sys.exit(1)
        return LICENSE_STATUS_INVALID

    return LICENSE_STATUS_OK
