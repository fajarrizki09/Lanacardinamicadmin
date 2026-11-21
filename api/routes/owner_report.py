from fastapi import APIRouter, Query, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db
from helpers.owner_report_helper import build_owner_report_summary

router = APIRouter(prefix="/owner_report")


@router.get("/summary")
def owner_report_summary(
    request: Request,
    period: str = Query("month"),
    year: int | None = Query(None),
    month: int | None = Query(None),
    date_from: str = Query(""),
    date_to: str = Query(""),
    new_patient_source: str = Query("first_visit"),
):
    require_admin_pin(request)
    with db.Session() as session:
        return build_owner_report_summary(
            session,
            period=period,
            year=year,
            month=month,
            date_from=date_from or None,
            date_to=date_to or None,
            new_patient_source=new_patient_source,
        )
