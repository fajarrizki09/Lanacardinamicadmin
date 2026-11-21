from fastapi import HTTPException, Request

from settings import AppSettings


ADMIN_PIN_HEADER = "X-Admin-Pin"


def is_admin_pin_set():
    return AppSettings().has_admin_pin()


def verify_admin_pin(pin):
    return AppSettings().verify_admin_pin(pin)


def require_admin_pin(request: Request):
    settings = AppSettings()
    if not settings.has_admin_pin():
        return
    pin = request.headers.get(ADMIN_PIN_HEADER, "")
    if not settings.verify_admin_pin(pin):
        raise HTTPException(status_code=403, detail="PIN salah.")
