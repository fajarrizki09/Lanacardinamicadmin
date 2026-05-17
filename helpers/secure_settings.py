import base64
import hashlib
import hmac
import json
import os
import platform
import socket

from utils.app_paths import get_app_data_dir


SENSITIVE_FIELDS = {
    "license_key",
    "license_api_url",
    "clinic_id",
    "license_status",
    "license_expired_at",
    "license_clinic_name",
    "device_id",
    "last_online_valid_at",
    "last_server_time",
    "last_license_valid",
    "last_license_check",
    "settings_hash",
    "midtrans_server_key",
    "xendit_secret_key",
    "duitku_api_key",
}
RUNTIME_ONLY_FIELDS = {
    "admin_pin_hash",
    "admin_pin_salt",
}
ENCRYPTED_FIELDS = SENSITIVE_FIELDS | RUNTIME_ONLY_FIELDS
SECURE_PREFIX = "enc:v1:"


class SecureSettingsError(Exception):
    pass


def get_settings_path() -> str:
    return os.path.join(get_app_data_dir(), "settings.json")


def _project_settings_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))


def _device_key() -> bytes:
    # Use only core, extremely stable fields for encryption key
    # Don't use part of MAC if we want maximum stability against driver updates
    raw = "|".join([
        socket.gethostname(),
        platform.system(),
        platform.machine(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        block = hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        output.extend(block)
        counter += 1
    return bytes(output[:length])


def _xor_bytes(data: bytes, key_bytes: bytes) -> bytes:
    return bytes(left ^ right for left, right in zip(data, key_bytes))


def encrypt_value(value):
    if isinstance(value, str) and value.startswith(SECURE_PREFIX):
        return value

    key = _device_key()
    nonce = os.urandom(16)
    plaintext = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext = _xor_bytes(plaintext, _keystream(key, nonce, len(plaintext)))
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    payload = base64.urlsafe_b64encode(nonce + tag + ciphertext).decode("ascii")
    return f"{SECURE_PREFIX}{payload}"


def decrypt_value(value):
    if not (isinstance(value, str) and value.startswith(SECURE_PREFIX)):
        return value

    try:
        raw = base64.urlsafe_b64decode(value[len(SECURE_PREFIX):].encode("ascii"))
        nonce = raw[:16]
        tag = raw[16:48]
        ciphertext = raw[48:]
        key = _device_key()
        expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise SecureSettingsError("Settings signature mismatch.")
        plaintext = _xor_bytes(ciphertext, _keystream(key, nonce, len(ciphertext)))
        return json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise SecureSettingsError("Encrypted settings value cannot be decrypted.") from exc


def _load_plain_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _decrypt_settings(settings: dict) -> tuple[dict, bool]:
    result = settings.copy()
    corrupt = False

    for field in ENCRYPTED_FIELDS:
        if field not in result:
            continue
        try:
            result[field] = decrypt_value(result[field])
        except SecureSettingsError:
            result.pop(field, None)
            corrupt = True

    if corrupt:
        for field in ENCRYPTED_FIELDS:
            result.pop(field, None)
        result["last_license_valid"] = False
        result["last_license_check"] = 0
        result["last_online_valid_at"] = 0

    return result, corrupt


def is_encrypted_value(value: any) -> bool:
    """Check if a value is in the enc:v1: format."""
    return isinstance(value, str) and value.startswith(SECURE_PREFIX)


def safe_license_display_value(value: any) -> str:
    """Return a display-safe string, masking raw encrypted values."""
    if is_encrypted_value(value):
        return "-"
    if value is None or value == "":
        return "-"
    return str(value).strip()


def load_settings(file_path: str = None) -> dict:
    if file_path is not None:
        try:
            settings, corrupt = _decrypt_settings(_load_plain_json(file_path))
            return settings
        except Exception:
            return {}

    # 1. Load base settings from project root (decrypting as well)
    settings, base_corrupt = _decrypt_settings(_load_plain_json(_project_settings_path()))
    for field in RUNTIME_ONLY_FIELDS:
        settings.pop(field, None)

    # 2. Load and overlay runtime settings from AppData
    try:
        path = get_settings_path()
        if os.path.exists(path):
            raw_runtime = _load_plain_json(path)
            # Try to decrypt. If key changed, this will mark as corrupt and clear SENSITIVE_FIELDS
            runtime_settings, corrupt = _decrypt_settings(raw_runtime)

            settings.update(runtime_settings)

            if corrupt:
                # If settings are corrupt (e.g. key changed), we mark for re-verification
                settings["last_license_error"] = "Data aktivasi lama perlu diverifikasi ulang."
                settings["last_license_valid"] = False
                settings["last_license_check"] = 0
                settings["last_online_valid_at"] = 0
    except Exception:
        # Emergency fallback for totally invalid file structure
        for field in SENSITIVE_FIELDS:
            settings.pop(field, None)
        settings["last_license_error"] = "Data aktivasi lama perlu diverifikasi ulang."
        settings["last_license_valid"] = False
        settings["last_license_check"] = 0
        settings["last_online_valid_at"] = 0
    return settings


def save_settings(settings: dict, file_path: str = None) -> None:
    path = file_path if file_path is not None else get_settings_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    protected = settings.copy()
    for field in ENCRYPTED_FIELDS:
        if field in protected:
            protected[field] = encrypt_value(protected[field])

    with open(path, "w", encoding="utf-8") as settings_file:
        json.dump(protected, settings_file, indent=4, ensure_ascii=False)
