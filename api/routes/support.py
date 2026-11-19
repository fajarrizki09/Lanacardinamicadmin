from fastapi import APIRouter, Form, HTTPException, Query, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db
from helpers.support_helper import get_support_app_info, open_external_url, open_local_folder

router = APIRouter(prefix="/support")


@router.get("/app_info")
def support_app_info(request: Request):
    require_admin_pin(request)
    return get_support_app_info(db)


@router.post("/open_folder")
def support_open_folder(request: Request, kind: str = Query(...)):
    try:
        require_admin_pin(request)
        path = open_local_folder(kind, db)
        return {"status": "success", "path": path}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/open_external_url")
def support_open_external_url(url: str = Form(...)):
    try:
        target = open_external_url(url)
        return {"status": "success", "url": target}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
