from datetime import datetime, time

from fastapi import APIRouter, HTTPException, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db


router = APIRouter()


def _parse_date(value, end_of_day=False):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.fromisoformat(f"{text}T00:00:00")
    if end_of_day and parsed.time() == time.min:
        parsed = datetime.combine(parsed.date(), time.max)
    return parsed


@router.get("/audit_logs")
def get_audit_logs(
    request: Request,
    action: str = "",
    entity_type: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 100,
):
    try:
        require_admin_pin(request)
        return db.get_audit_logs(
            action=action,
            entity_type=entity_type,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to, end_of_day=True),
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
