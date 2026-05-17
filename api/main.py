from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from logging.handlers import RotatingFileHandler
import logging
import os
import sys

from api.license_guard import require_valid_license
from api.admin_pin import is_admin_pin_set, require_admin_pin, verify_admin_pin

# Tambahkan direktori parent ke sys.path agar bisa import modul root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.app_paths import get_app_data_dir
from helpers.local_token import get_local_app_token, verify_local_app_token

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
APP_DEBUG = os.getenv("APP_DEBUG", "true").strip().lower() not in ("0", "false", "no", "off")
SHOW_API_DOCS = APP_ENV != "production" and APP_DEBUG
USER_SERVER_ERROR_MESSAGE = "Terjadi kesalahan. Silakan coba lagi atau hubungi admin."
USER_VALIDATION_ERROR_MESSAGE = "Data yang dikirim tidak valid. Periksa kembali input."
TECHNICAL_ERROR_MARKERS = (
    "sqlalchemy",
    "sqlite3",
    "traceback",
    "operationalerror",
    "integrityerror",
    "databaseerror",
    "programmingerror",
    "permissionerror",
    "filenotfounderror",
    "winerror",
    "errno",
    ".py",
    "site-packages",
    "c:\\",
    "/users/",
    "/home/",
)


def _safe_error_detail(detail):
    if isinstance(detail, (list, dict)):
        return USER_VALIDATION_ERROR_MESSAGE
    message = str(detail or "").strip()
    if not message:
        return USER_SERVER_ERROR_MESSAGE

    lowered = message.lower()
    if any(marker in lowered for marker in TECHNICAL_ERROR_MARKERS):
        return USER_SERVER_ERROR_MESSAGE

    return message


def _setup_api_error_logger():
    log_dir = os.path.join(get_app_data_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("lancar.api")
    logger.setLevel(logging.INFO)
    logger.propagate = True

    log_path = os.path.abspath(os.path.join(log_dir, "api_errors.log"))
    if not any(getattr(handler, "baseFilename", None) == log_path for handler in logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    return logger


api_logger = _setup_api_error_logger()

app = FastAPI(
    title="Lancar Dynamic Admin API",
    docs_url="/docs" if SHOW_API_DOCS else None,
    redoc_url="/redoc" if SHOW_API_DOCS else None,
    openapi_url="/openapi.json" if SHOW_API_DOCS else None,
)

# Add GZip Middleware for compressing response data (over 1000 bytes)
app.add_middleware(GZipMiddleware, minimum_size=1000)


def _is_local_token_exempt_path(path):
    return (
        path in {"/", "/license"}
        or path.startswith("/static/")
        or path.startswith("/payments/gateway/pay/")
        or path.startswith("/payments/gateway/mock/pay/")
    )


@app.middleware("http")
async def require_local_app_token(request: Request, call_next):
    if _is_local_token_exempt_path(request.url.path):
        return await call_next(request)

    token = request.headers.get("X-App-Token", "")
    if not verify_local_app_token(token):
        return JSONResponse(status_code=403, content={"detail": "Token aplikasi tidak valid."})

    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        api_logger.error(
            "HTTP %s at %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": USER_SERVER_ERROR_MESSAGE})

    safe_detail = _safe_error_detail(exc.detail)
    if safe_detail != exc.detail:
        api_logger.warning(
            "Sanitized HTTP %s at %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": safe_detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    api_logger.warning(
        "Validation error at %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(status_code=422, content={"detail": USER_VALIDATION_ERROR_MESSAGE})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    api_logger.exception("Unhandled error at %s %s", request.method, request.url.path)
    try:
        from helpers.license import report_error_feedback
        report_error_feedback(
            exc,
            source=f"api:{request.method}:{request.url.path}",
            severity="critical",
            context="Unhandled FastAPI exception",
        )
    except Exception:
        api_logger.exception("Failed to report unhandled API exception to license server.")
    return JSONResponse(status_code=500, content={"detail": USER_SERVER_ERROR_MESSAGE})



current_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, _license=Depends(require_valid_license)):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "show_api_docs": SHOW_API_DOCS,
            "app_token": get_local_app_token(),
        },
    )


@app.get("/license", response_class=HTMLResponse)
def license_page(request: Request):
    from helpers.license import get_license_status_summary

    return templates.TemplateResponse(
        "license.html",
        {
            "request": request,
            "app_token": get_local_app_token(),
            "license": get_license_status_summary(),
        },
    )


@app.get("/health")
def health_check():
    try:
        from version import APP_VERSION
    except Exception:
        APP_VERSION = ""
    return {"status": "ok", "app": "Lancar Dynamic Admin", "version": APP_VERSION}


@app.get("/license_status")
def license_status():
    from helpers.license import get_license_status_summary, verify_license

    status = verify_license(exit_on_fail=False, show_message=False)
    data = get_license_status_summary()
    data["verify_status"] = status
    return data


def _activate_license_payload(license_key: str, clinic_id: str):
    from helpers.license import (
        LICENSE_ERROR_MESSAGE,
        LICENSE_STATUS_OK,
        get_last_license_message,
        get_license_status_summary,
        save_license_key,
        verify_license,
    )

    normalized_key = license_key.strip()
    normalized_clinic_id = clinic_id.strip()
    if not normalized_key:
        raise HTTPException(status_code=400, detail="Kode lisensi tidak boleh kosong.")
    if len(normalized_key) <= 10:
        raise HTTPException(status_code=400, detail="Format lisensi terlalu pendek.")
    if not normalized_clinic_id:
        raise HTTPException(status_code=400, detail="Clinic ID wajib diisi.")

    save_license_key(normalized_key, clinic_id=normalized_clinic_id)
    status = verify_license(exit_on_fail=False, show_message=False, force_online=True, clinic_id=normalized_clinic_id)
    summary = get_license_status_summary()
    summary["verify_status"] = status

    if status != LICENSE_STATUS_OK:
        raise HTTPException(
            status_code=400,
            detail=get_last_license_message() or LICENSE_ERROR_MESSAGE,
        )

    try:
        from api.database_manager import db
        db.log_audit("license_activated", "license", normalized_clinic_id, "Lisensi aplikasi diaktifkan atau diganti.")
    except Exception:
        api_logger.exception("Failed to write license audit log.")

    return {
        "status": "success",
        "message": "Lisensi berhasil diaktifkan.",
        "license": summary,
    }


@app.post("/license/activate")
async def activate_license_from_web(license_key: str = Form(...), clinic_id: str = Form(...)):
    return _activate_license_payload(license_key, clinic_id)


@app.post("/activate_license")
async def activate_license(request: Request, license_key: str = Form(...), clinic_id: str = Form(...)):
    require_admin_pin(request)
    return _activate_license_payload(license_key, clinic_id)


@app.get("/admin_pin/status")
def admin_pin_status():
    return {"pin_set": is_admin_pin_set()}


@app.post("/admin_pin/check")
async def admin_pin_check(pin: str = Form(...)):
    if not verify_admin_pin(pin):
        raise HTTPException(status_code=403, detail="PIN salah.")
    return {"status": "success", "message": "PIN admin valid."}


@app.post("/admin_pin/set")
async def admin_pin_set(pin: str = Form(...)):
    from settings import AppSettings

    settings = AppSettings()
    if settings.has_admin_pin():
        raise HTTPException(status_code=400, detail="PIN admin sudah diset. Gunakan menu ubah PIN.")
    try:
        settings.set_admin_pin(pin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        from api.database_manager import db
        db.log_audit("admin_pin_set", "security", "admin_pin", "PIN admin pertama dibuat.")
    except Exception:
        api_logger.exception("Failed to write admin PIN audit log.")
    return {"status": "success", "message": "PIN admin berhasil disimpan.", "pin_set": True}


@app.post("/admin_pin/change")
async def admin_pin_change(current_pin: str = Form(...), new_pin: str = Form(...)):
    from settings import AppSettings

    settings = AppSettings()
    if not settings.has_admin_pin():
        raise HTTPException(status_code=400, detail="PIN admin belum diset.")
    try:
        settings.change_admin_pin(current_pin, new_pin)
    except ValueError as exc:
        status_code = 403 if str(exc) == "PIN salah." else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
    try:
        from api.database_manager import db
        db.log_audit("admin_pin_changed", "security", "admin_pin", "PIN admin diubah.")
    except Exception:
        api_logger.exception("Failed to write admin PIN audit log.")
    return {"status": "success", "message": "PIN admin berhasil diubah.", "pin_set": True}


@app.post("/admin_pin/reset/request")
async def admin_pin_reset_request():
    from helpers.license import LicenseNetworkError, request_admin_pin_reset

    try:
        result = request_admin_pin_reset()
    except LicenseNetworkError as exc:
        raise HTTPException(status_code=424, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        from api.database_manager import db
        db.log_audit("admin_pin_reset_requested", "security", "admin_pin", "Permintaan reset PIN admin dikirim ke server lisensi.")
    except Exception:
        api_logger.exception("Failed to write admin PIN reset request audit log.")
    return {
        "status": "success",
        "message": result.get("message") or "Permintaan reset PIN dikirim ke server lisensi.",
        "reset_request_id": result.get("reset_request_id", ""),
        "reset_token": result.get("reset_token", ""),
    }


@app.post("/admin_pin/reset/confirm")
async def admin_pin_reset_confirm(reset_token: str = Form(""), reset_pin: str = Form(""), new_pin: str = Form(...)):
    from helpers.license import LicenseNetworkError, confirm_admin_pin_reset
    from settings import AppSettings

    token = str(reset_token or "").strip()
    reset_code = str(reset_pin or "").strip()
    pin = str(new_pin or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token reset PIN belum tersedia. Klik Minta Kode Reset ulang.")
    if not reset_code:
        raise HTTPException(status_code=400, detail="Kode reset dari server lisensi wajib diisi.")
    if not pin.isdigit() or not 4 <= len(pin) <= 8:
        raise HTTPException(status_code=400, detail="PIN admin baru harus berisi 4-8 digit angka.")

    try:
        result = confirm_admin_pin_reset(token, reset_code)
    except LicenseNetworkError as exc:
        raise HTTPException(status_code=424, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    settings = AppSettings()
    try:
        settings.set_admin_pin(pin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        from api.database_manager import db
        db.log_audit("admin_pin_reset_confirmed", "security", "admin_pin", "PIN admin direset melalui server lisensi.")
    except Exception:
        api_logger.exception("Failed to write admin PIN reset confirm audit log.")
    return {
        "status": "success",
        "message": result.get("message") or "PIN admin berhasil direset.",
        "pin_set": True,
    }


# ─── ROUTERS ─────────────────────────────────────────────────────────────────
from api.routes import patients, inventory, herbals, therapists, services, analytics, settings, invoices, data, crm, audit, owner_report, reports, support, payments

admin_dependencies = [Depends(require_valid_license)]

app.include_router(patients.router, dependencies=admin_dependencies)
app.include_router(inventory.router, dependencies=admin_dependencies)
app.include_router(herbals.router, dependencies=admin_dependencies)
app.include_router(therapists.router, dependencies=admin_dependencies)
app.include_router(services.router, dependencies=admin_dependencies)
app.include_router(analytics.router, dependencies=admin_dependencies)
app.include_router(settings.router, dependencies=admin_dependencies)
app.include_router(invoices.router, dependencies=admin_dependencies)
app.include_router(data.router, dependencies=admin_dependencies)
app.include_router(crm.router, dependencies=admin_dependencies)
app.include_router(audit.router, dependencies=admin_dependencies)
app.include_router(owner_report.router, dependencies=admin_dependencies)
app.include_router(reports.router, dependencies=admin_dependencies)
app.include_router(support.router, dependencies=admin_dependencies)
app.include_router(payments.router, dependencies=admin_dependencies)

if __name__ == "__main__":

    import uvicorn
    print("="*60)
    print("INFO: Anda sedang menjalankan backend FastAPI secara mandiri.")
    print("Untuk membuka UI Desktop Terintegrasi otomatis, jalankan file:")
    print("'python main.py' (di folder utama, BUKAN di dalam folder api)")
    print("="*60)

    # Menjalankan server pada port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
