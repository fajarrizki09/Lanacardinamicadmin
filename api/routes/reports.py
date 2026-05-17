import io
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from api.admin_pin import require_admin_pin
from api.database_manager import db
from helpers.report_excel_helper import build_report_excel

router = APIRouter(prefix="/reports")


@router.get("/export_excel")
def export_excel_report(
    request: Request,
    report_type: str = Query("owner_summary"),
    period: str = Query("month"),
    year: int | None = Query(None),
    month: int | None = Query(None),
    date_from: str = Query(""),
    date_to: str = Query(""),
    new_patient_source: str = Query("first_visit"),
):
    try:
        require_admin_pin(request)
        with db.Session() as session:
            filename, content = build_report_excel(
                session,
                report_type=report_type,
                period=period,
                year=year,
                month=month,
                date_from=date_from or None,
                date_to=date_to or None,
                new_patient_source=new_patient_source,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    encoded_name = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
        "Cache-Control": "no-store",
    }
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
