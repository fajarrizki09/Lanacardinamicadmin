import json
import os
import hashlib
import hmac
import secrets

from helpers.payment_gateway import (
    get_available_gateway_providers,
    get_coming_soon_gateway_providers,
    get_payment_provider_registry,
)

DEFAULT_FREE_VISIT_REASONS = [
    "promo",
    "keluarga",
    "koreksi",
    "gratis lain-lain",
]

SENSITIVE_SETTINGS_KEYS = {
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

PAYMENT_GATEWAY_PROVIDERS = get_available_gateway_providers()
PAYMENT_GATEWAY_ENVIRONMENTS = {"sandbox", "production"}
DEFAULT_OPENWA_BASE_URL = "http://127.0.0.1:3000/api"
_SECURE_SETTINGS_FUNCS = None


def _secure_settings_funcs():
    global _SECURE_SETTINGS_FUNCS
    if _SECURE_SETTINGS_FUNCS is None:
        from helpers.secure_settings import load_settings, save_settings

        _SECURE_SETTINGS_FUNCS = (load_settings, save_settings)
    return _SECURE_SETTINGS_FUNCS


def _is_sensitive_settings_key(key):
    key_text = str(key or "")
    return (
        key_text in SENSITIVE_SETTINGS_KEYS
        or key_text.startswith("admin_pin_reset_")
        or key_text.startswith("license_")
        or key_text.startswith("last_license_")
        or key_text.startswith("last_online_")
        or key_text.startswith("last_server_")
    )


class AppSettings:
    def __init__(self, file_path="settings.json"):
        self.file_path = None if file_path == "settings.json" else file_path
        self.settings = {
            "clinic_name": "Lancar Dynamic Admin",
            "clinic_tagline": "Clinic Management System",
            "clinic_address": "",
            "clinic_phone": "",
            "clinic_email": "",
            "clinic_website": "",
            "clinic_logo_path": "",
            "base_price": 100000,
            "price_per_point": 10000,
            "discount_percentage": 50,
            "min_visits_for_discount": 5,
            "backup_auto_enabled": True,
            "backup_interval": "daily",
            "backup_max_files": 10,
            "last_backup_time": None,
            "last_backup_status": "Belum pernah backup",
            "free_visit_reasons": DEFAULT_FREE_VISIT_REASONS.copy(),
            "admin_pin_hash": "",
            "admin_pin_salt": "",
            "first_run_completed": False,
            "invoice_prefix": "INV",
            "payment_gateway_enabled": False,
            "payment_gateway_default_provider": "gateway_mock",
            "payment_gateway_environment": "sandbox",
            "midtrans_server_key": "",
            "midtrans_client_key": "",
            "midtrans_merchant_id": "",
            "xendit_secret_key": "",
            "duitku_merchant_code": "",
            "duitku_api_key": "",
            "openwa_enabled": False,
            "openwa_base_url": DEFAULT_OPENWA_BASE_URL,
            "openwa_session_id": "",
            "openwa_auto_followup_enabled": False,
            "openwa_followup_delay_hours": 24,
            "openwa_rate_limit_per_run": 10,
        }
        self.load()

    def load(self):
        try:
            load_settings, _save_settings = _secure_settings_funcs()
            loaded = load_settings(self.file_path)

            if isinstance(loaded, dict):
                self.settings.update(loaded)
            if "price_per_point" not in self.settings:
                self.settings["price_per_point"] = 10000
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save(self):
        try:
            _load_settings, save_settings = _secure_settings_funcs()
            save_settings(self.settings, self.file_path)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_base_price(self):
        return self.settings.get("base_price", 100000)

    def set_base_price(self, price):
        self.settings["base_price"] = price
        self.save()

    def get_price_per_point(self):
        return self.settings.get("price_per_point", 10000)

    def set_price_per_point(self, price):
        self.settings["price_per_point"] = price
        self.save()

    def calculate_price_from_points(self, point_count):
        return point_count * self.get_price_per_point()

    def get_discount_percentage(self):
        return self.settings.get("discount_percentage", 50)

    def set_discount_percentage(self, percentage):
        self.settings["discount_percentage"] = percentage
        self.save()

    def get_min_visits_for_discount(self):
        return self.settings.get("min_visits_for_discount", 5)

    def set_min_visits_for_discount(self, min_visits):
        self.settings["min_visits_for_discount"] = min_visits
        self.save()

    def get_custom_invoice_settings(self):
        return {
            "clinic_name": self.settings.get("clinic_name", "Lancar Dynamic Admin"),
            "clinic_tagline": self.settings.get("clinic_tagline", "Clinic Management System"),
            "clinic_address": self.settings.get("clinic_address", ""),
            "clinic_phone": self.settings.get("clinic_phone", ""),
            "clinic_email": self.settings.get("clinic_email", ""),
            "clinic_website": self.settings.get("clinic_website", ""),
            "clinic_logo_path": self.settings.get("clinic_logo_path", ""),
            "invoice_footer": self.settings.get("invoice_footer", "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah."),
            "admin_label": self.settings.get("admin_label", "Admin Klinik,")
        }

    def save_custom_invoice_settings(self, data):
        self.settings.update(data)
        self.save()

    def get_clinic_profile(self):
        return self.get_custom_invoice_settings()

    def save_clinic_profile(self, data):
        allowed = {
            "clinic_name",
            "clinic_tagline",
            "clinic_address",
            "clinic_phone",
            "clinic_email",
            "clinic_website",
            "clinic_logo_path",
            "invoice_footer",
            "admin_label",
        }
        self.settings.update({k: v for k, v in data.items() if k in allowed})
        self.save()

    def get_all_settings(self):
        data = {
            key: value
            for key, value in self.settings.items()
            if not _is_sensitive_settings_key(key)
        }
        provider = str(data.get("payment_gateway_default_provider") or "gateway_mock").strip().lower()
        data["payment_gateway_default_provider"] = provider if provider in PAYMENT_GATEWAY_PROVIDERS else "gateway_mock"
        data["payment_gateway_supported_providers"] = sorted(PAYMENT_GATEWAY_PROVIDERS)
        data["payment_gateway_available_providers"] = sorted(PAYMENT_GATEWAY_PROVIDERS)
        data["payment_gateway_coming_soon_providers"] = sorted(get_coming_soon_gateway_providers())
        data["payment_gateway_provider_registry"] = get_payment_provider_registry()
        data["first_run_completed"] = self.is_first_run_completed()
        data["admin_pin_set"] = self.has_admin_pin()
        return data

    def set_payment_gateway_settings(self, data):
        provider = str(data.get("payment_gateway_default_provider") or "gateway_mock").strip().lower()
        environment = str(data.get("payment_gateway_environment") or "sandbox").strip().lower()
        if provider not in PAYMENT_GATEWAY_PROVIDERS:
            raise ValueError("Penyedia pembayaran tidak valid.")
        if environment not in PAYMENT_GATEWAY_ENVIRONMENTS:
            raise ValueError("Mode pembayaran tidak valid.")

        self.settings["payment_gateway_enabled"] = bool(data.get("payment_gateway_enabled"))
        self.settings["payment_gateway_default_provider"] = provider
        self.settings["payment_gateway_environment"] = environment
        for key in (
            "midtrans_server_key",
            "midtrans_client_key",
            "midtrans_merchant_id",
            "xendit_secret_key",
            "duitku_merchant_code",
            "duitku_api_key",
        ):
            self.settings[key] = str(data.get(key) or "").strip()
        self.save()

    def get_payment_gateway_default_provider(self):
        provider = str(self.settings.get("payment_gateway_default_provider") or "gateway_mock").strip().lower()
        return provider if provider in PAYMENT_GATEWAY_PROVIDERS else "gateway_mock"

    def get_openwa_settings(self, include_secret=False):
        base_url = str(self.settings.get("openwa_base_url") or DEFAULT_OPENWA_BASE_URL).strip().rstrip("/")
        if "2785" in base_url or "/layanan/" in base_url or "/koneksis" in base_url:
            base_url = DEFAULT_OPENWA_BASE_URL
            self.settings["openwa_base_url"] = base_url
            self.save()
        data = {
            "openwa_enabled": bool(self.settings.get("openwa_enabled", False)),
            "openwa_base_url": base_url,
            "openwa_session_id": str(self.settings.get("openwa_session_id") or "").strip(),
            "openwa_auto_followup_enabled": bool(self.settings.get("openwa_auto_followup_enabled", False)),
            "openwa_followup_delay_hours": int(self.settings.get("openwa_followup_delay_hours") or 24),
            "openwa_rate_limit_per_run": int(self.settings.get("openwa_rate_limit_per_run") or 10),
        }
        return data

    def set_openwa_settings(self, data):
        def _bool(key, default=False):
            return str(data.get(key, default)).strip().lower() in {"1", "true", "yes", "ya", "on"}

        def _int(key, default, min_value, max_value):
            try:
                value = int(data.get(key, default))
            except (TypeError, ValueError):
                value = default
            return max(min_value, min(max_value, value))

        base_url = str(data.get("openwa_base_url") or DEFAULT_OPENWA_BASE_URL).strip().rstrip("/")
        if "2785" in base_url or "/layanan/" in base_url or "/koneksis" in base_url:
            base_url = DEFAULT_OPENWA_BASE_URL
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("OpenWA Base URL harus diawali http:// atau https://")
        self.settings["openwa_enabled"] = _bool("openwa_enabled")
        self.settings["openwa_base_url"] = base_url
        self.settings["openwa_session_id"] = str(data.get("openwa_session_id") or "").strip()
        self.settings["openwa_auto_followup_enabled"] = _bool("openwa_auto_followup_enabled")
        self.settings["openwa_followup_delay_hours"] = _int("openwa_followup_delay_hours", 24, 1, 720)
        self.settings["openwa_rate_limit_per_run"] = _int("openwa_rate_limit_per_run", 10, 1, 100)
        self.save()

    def is_first_run_completed(self):
        if bool(self.settings.get("first_run_completed", False)):
            return True
        clinic_name = str(self.settings.get("clinic_name") or "").strip()
        clinic_address = str(self.settings.get("clinic_address") or "").strip()
        clinic_phone = str(self.settings.get("clinic_phone") or "").strip()
        return clinic_name not in ("", "Lancar Dynamic Admin") or bool(clinic_address or clinic_phone)

    def complete_first_run(self, data=None, skipped=False):
        data = data or {}
        allowed = {
            "clinic_name",
            "clinic_address",
            "clinic_phone",
            "clinic_logo_path",
            "invoice_prefix",
        }
        for key, value in data.items():
            if key in allowed:
                self.settings[key] = str(value or "").strip()
        self.settings["first_run_completed"] = True
        self.settings["first_run_skipped"] = bool(skipped)
        self.save()

    def has_admin_pin(self):
        return bool(str(self.settings.get("admin_pin_hash") or "").strip()) and bool(
            str(self.settings.get("admin_pin_salt") or "").strip()
        )

    def set_admin_pin(self, pin):
        pin_text = str(pin or "").strip()
        if not pin_text.isdigit() or not 4 <= len(pin_text) <= 8:
            raise ValueError("PIN admin harus berisi 4-8 digit.")
        salt = secrets.token_hex(16)
        pin_hash = hashlib.pbkdf2_hmac("sha256", pin_text.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
        self.settings["admin_pin_salt"] = salt
        self.settings["admin_pin_hash"] = pin_hash
        self.save()

    def verify_admin_pin(self, pin):
        if not self.has_admin_pin():
            return True
        pin_text = str(pin or "").strip()
        salt = str(self.settings.get("admin_pin_salt") or "")
        expected = str(self.settings.get("admin_pin_hash") or "")
        candidate = hashlib.pbkdf2_hmac("sha256", pin_text.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
        return hmac.compare_digest(candidate, expected)

    def change_admin_pin(self, current_pin, new_pin):
        if not self.has_admin_pin():
            raise ValueError("PIN admin belum diset.")
        if not self.verify_admin_pin(current_pin):
            raise ValueError("PIN salah.")
        self.set_admin_pin(new_pin)

    def get_free_visit_reasons(self):
        reasons = self.settings.get("free_visit_reasons", DEFAULT_FREE_VISIT_REASONS)
        if not isinstance(reasons, list):
            return DEFAULT_FREE_VISIT_REASONS.copy()
        cleaned = []
        for reason in reasons:
            text = str(reason or "").strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned or DEFAULT_FREE_VISIT_REASONS.copy()

    def set_free_visit_reasons(self, reasons):
        cleaned = []
        for reason in reasons or []:
            text = str(reason or "").strip()
            if text and text not in cleaned:
                cleaned.append(text)
        if not cleaned:
            raise ValueError("Minimal isi satu alasan kunjungan gratis.")
        self.settings["free_visit_reasons"] = cleaned
        self.save()

    def get_inventory_config(self):
        return self.settings.get("inventory_auto_reduction", {
            "Pisau Bedah": 1,
            "Tisu": 2
        })

    def set_inventory_config(self, config):
        self.settings["inventory_auto_reduction"] = config
        self.save()

    def get_backup_config(self):
        return {
            "auto_enabled": bool(self.settings.get("backup_auto_enabled", True)),
            "interval": self.settings.get("backup_interval", "daily"),
            "max_files": int(self.settings.get("backup_max_files", 10) or 10),
            "last_backup_time": self.settings.get("last_backup_time"),
            "last_backup_status": self.settings.get("last_backup_status", "Belum pernah backup"),
        }

    def set_backup_config(self, auto_enabled=True, interval="daily", max_files=10):
        self.settings["backup_auto_enabled"] = bool(auto_enabled)
        self.settings["backup_interval"] = interval or "daily"
        self.settings["backup_max_files"] = int(max_files or 10)
        self.save()

    def set_backup_status(self, status, backup_time=None):
        self.settings["last_backup_status"] = status
        self.settings["last_backup_time"] = backup_time
        self.save()
