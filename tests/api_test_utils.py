import atexit
import os
import tempfile


_TEMP_DIR = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TEMP_DIR.name, 'api_test.db')}"


def _cleanup_temp_dir():
    try:
        db.engine.dispose()
    except Exception:
        pass
    _TEMP_DIR.cleanup()


atexit.register(_cleanup_temp_dir)

from fastapi.testclient import TestClient

try:
    import inspect
    import httpx

    if "app" not in inspect.signature(httpx.Client.__init__).parameters:
        _httpx_client_init = httpx.Client.__init__

        def _compatible_httpx_client_init(self, *args, **kwargs):
            kwargs.pop("app", None)
            return _httpx_client_init(self, *args, **kwargs)

        httpx.Client.__init__ = _compatible_httpx_client_init
except Exception:
    pass

import api.admin_pin as admin_pin
import api.license_guard as license_guard
import api.main as api_main
from api.database_manager import db
from helpers.local_token import get_local_app_token


class FakeAdminSettings:
    def has_admin_pin(self):
        return True

    def verify_admin_pin(self, pin):
        return pin == "1234"


def allow_license():
    return True


admin_pin.AppSettings = FakeAdminSettings

original_require_valid_license = api_main.require_valid_license
api_main.app.dependency_overrides[original_require_valid_license] = allow_license
license_guard.require_valid_license = allow_license
api_main.require_valid_license = allow_license

for module_name in (
    "analytics",
    "crm",
    "data",
    "herbals",
    "inventory",
    "invoices",
    "patients",
    "settings",
    "services",
    "therapists",
):
    module = __import__(f"api.routes.{module_name}", fromlist=["dummy"])
    if hasattr(module, "require_valid_license"):
        module.require_valid_license = allow_license


def client():
    return TestClient(api_main.app)


def app_headers(pin=None):
    headers = {"X-App-Token": get_local_app_token()}
    if pin is not None:
        headers["X-Admin-Pin"] = pin
    return headers


def form_headers(pin=None):
    return app_headers(pin=pin)
