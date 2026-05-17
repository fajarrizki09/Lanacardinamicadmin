from fastapi import HTTPException

from helpers.license import (
    LICENSE_ERROR_MESSAGE,
    LICENSE_STATUS_OK,
    get_last_license_message,
    verify_license,
)


def require_valid_license():
    status = verify_license(exit_on_fail=False, show_message=False)
    if status != LICENSE_STATUS_OK:
        message = get_last_license_message() or LICENSE_ERROR_MESSAGE
        raise HTTPException(status_code=403, detail=message)
