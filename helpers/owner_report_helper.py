from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import case, func, or_

from database import CRMWhatsAppLog, Herbal, HerbalTransaction, Patient, PatientFollowup, Service, Visit
from helpers.crm_analysis_helper import build_crm_patients
from helpers.revenue_rules import active_invoice_filter, revenue_case


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.strptime(text, "%Y-%m-%d")


def _period_range(period="month", year=None, month=None, date_from=None, date_to=None):
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start or end:
        if start and not end:
            end = datetime.now()
        if end and not start:
            start = datetime.min
        return start, end.replace(hour=23, minute=59, second=59, microsecond=999999)

    now = datetime.now()
    selected_year = int(year or now.year)
    selected_month = int(month or now.month)
    if str(period or "").lower() == "year":
        start = datetime(selected_year, 1, 1)
        end = datetime(selected_year, 12, 31, 23, 59, 59, 999999)
        return start, end

    start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        next_month = datetime(selected_year + 1, 1, 1)
    else:
        next_month = datetime(selected_year, selected_month + 1, 1)
    end = next_month - timedelta(microseconds=1)
    return start, end


def _between(query, column, start, end):
    if start:
        query = query.filter(column >= start)
    if end:
        query = query.filter(column <= end)
    return query


def _money(value):
    return round(float(value or 0), 2)


def build_owner_report_summary(
    session,
    period="month",
    year=None,
    month=None,
    date_from=None,
    date_to=None,
    new_patient_source="first_visit",
):
    start, end = _period_range(period, year=year, month=month, date_from=date_from, date_to=date_to)
    new_patient_source = str(new_patient_source or "first_visit").strip().lower()
    if new_patient_source not in {"registration", "first_visit"}:
        new_patient_source = "first_visit"
    active_visit_status = active_invoice_filter(Visit)
    active_herbal_status = active_invoice_filter(HerbalTransaction)
    receivable_statuses = ("unpaid", "pending", "partial")
    herbal_sale_filter = HerbalTransaction.transaction_type == "sale"
    herbal_return_filter = HerbalTransaction.transaction_type.in_(["return", "retur"])

    visit_total_expr = func.coalesce(func.nullif(Visit.final_price, 0), Visit.price, 0)
    visit_paid_expr = func.coalesce(Visit.amount_paid, 0)
    visit_revenue_expr = case(
        (Visit.payment_method == "free", 0),
        (or_(Visit.payment_status == "paid", Visit.payment_status.is_(None)), visit_total_expr),
        (Visit.payment_status == "partial", visit_paid_expr),
        else_=0,
    )
    herbal_revenue_expr = revenue_case(HerbalTransaction, HerbalTransaction.total_price)
    visit_query = _between(session.query(Visit), Visit.date, start, end).filter(active_visit_status)
    total_visits = int(visit_query.count() or 0)
    total_visit_revenue = _money(visit_query.with_entities(func.coalesce(func.sum(visit_revenue_expr), 0)).scalar())
    unique_patients = int(visit_query.with_entities(func.count(func.distinct(Visit.patient_id))).scalar() or 0)

    if new_patient_source == "registration":
        new_patients = int(
            _between(session.query(Patient), Patient.created_at, start, end)
            .with_entities(func.count(Patient.id))
            .scalar()
            or 0
        )
    else:
        first_visit_subquery = (
            session.query(Visit.patient_id.label("patient_id"), func.min(Visit.date).label("first_visit"))
            .group_by(Visit.patient_id)
            .subquery()
        )
        new_patients = int(
            session.query(func.count(first_visit_subquery.c.patient_id))
            .filter(first_visit_subquery.c.first_visit >= start, first_visit_subquery.c.first_visit <= end)
            .scalar()
            or 0
        )

    herbal_sales_query = _between(
        session.query(func.coalesce(func.sum(herbal_revenue_expr), 0)),
        HerbalTransaction.date,
        start,
        end,
    ).filter(herbal_sale_filter, active_herbal_status)
    herbal_returns_query = _between(
        session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)),
        HerbalTransaction.date,
        start,
        end,
    ).filter(herbal_return_filter, HerbalTransaction.visit_id.is_(None))
    total_herbal_revenue = max(0, _money(herbal_sales_query.scalar()) - _money(herbal_returns_query.scalar()))
    total_revenue = _money(total_visit_revenue + total_herbal_revenue)

    pending_visit_expr = case(
        (Visit.payment_status == 'partial', visit_total_expr - func.coalesce(Visit.amount_paid, 0)),
        (Visit.payment_status.in_(["unpaid", "pending"]), visit_total_expr),
        else_=0,
    )
    pending_herbal_expr = case(
        (HerbalTransaction.payment_status == 'partial', HerbalTransaction.total_price - func.coalesce(HerbalTransaction.amount_paid, 0)),
        (HerbalTransaction.payment_status.in_(["unpaid", "pending"]), HerbalTransaction.total_price),
        else_=0,
    )
    pending_visit_revenue = _money(
        visit_query
        .filter(Visit.payment_status.in_(receivable_statuses))
        .with_entities(func.coalesce(func.sum(pending_visit_expr), 0))
        .scalar()
    )
    pending_herbal_revenue = _money(
        _between(
            session.query(func.coalesce(func.sum(pending_herbal_expr), 0)),
            HerbalTransaction.date,
            start,
            end,
        )
        .filter(herbal_sale_filter, active_herbal_status, HerbalTransaction.payment_status.in_(receivable_statuses))
        .scalar()
    )

    crm_rows = build_crm_patients(session)
    active_segments = {"active", "loyal", "high_value", "high_value_at_risk"}
    needs_followup_segments = {"needs_followup", "dormant", "high_value_at_risk"}
    active_patients = sum(1 for row in crm_rows if row.get("segment") in active_segments)
    need_followup_rows = [
        row for row in crm_rows
        if row.get("segment") in needs_followup_segments or row.get("followup_due_status") == "overdue"
    ]
    dormant_rows = [
        row for row in crm_rows
        if row.get("segment") == "dormant" or int(row.get("days_since_last_visit") or 0) >= 60
    ]

    top_services = [
        {
            "name": row.name or "Layanan",
            "visits": int(row.visits or 0),
            "revenue": _money(row.revenue),
        }
        for row in (
            _between(
                session.query(
                    func.coalesce(Service.name, Visit.service_name, "Layanan").label("name"),
                    func.count(Visit.id).label("visits"),
                    func.coalesce(func.sum(visit_revenue_expr), 0).label("revenue"),
                ).outerjoin(Service, Service.id == Visit.service_id),
                Visit.date,
                start,
                end,
            )
            .filter(active_visit_status)
            .group_by("name")
            .order_by(func.count(Visit.id).desc(), func.coalesce(func.sum(visit_revenue_expr), 0).desc())
            .limit(5)
            .all()
        )
    ]

    top_service_categories = [
        {
            "name": row.category or "Tanpa Kategori",
            "visits": int(row.visits or 0),
            "revenue": _money(row.revenue),
        }
        for row in (
            _between(
                session.query(
                    func.coalesce(Service.service_category, "uncategorized").label("category"),
                    func.count(Visit.id).label("visits"),
                    func.coalesce(func.sum(visit_revenue_expr), 0).label("revenue"),
                ).outerjoin(Service, Service.id == Visit.service_id),
                Visit.date,
                start,
                end,
            )
            .filter(active_visit_status)
            .group_by("category")
            .order_by(func.coalesce(func.sum(visit_revenue_expr), 0).desc(), func.count(Visit.id).desc())
            .limit(5)
            .all()
        )
    ]

    top_herbals = [
        {
            "name": row.name or "Herbal",
            "quantity": int(row.quantity or 0),
            "revenue": _money(row.revenue),
        }
        for row in (
            _between(
                session.query(
                    Herbal.name.label("name"),
                    func.coalesce(func.sum(HerbalTransaction.quantity), 0).label("quantity"),
                    func.coalesce(func.sum(herbal_revenue_expr), 0).label("revenue"),
                ).outerjoin(Herbal, Herbal.id == HerbalTransaction.herbal_id),
                HerbalTransaction.date,
                start,
                end,
            )
            .filter(herbal_sale_filter, active_herbal_status)
            .group_by(Herbal.name)
            .order_by(func.coalesce(func.sum(herbal_revenue_expr), 0).desc())
            .limit(5)
            .all()
        )
    ]

    top_loyal_patients = [
        {
            "id": row.get("id"),
            "name": row.get("name"),
            "phone": row.get("phone"),
            "visits": int(row.get("total_visits") or 0),
            "revenue": _money(row.get("total_spent")),
            "last_visit": row.get("last_visit") or "",
        }
        for row in sorted(crm_rows, key=lambda item: (-(item.get("total_visits") or 0), -(item.get("total_spent") or 0)))[:5]
    ]

    whatsapp_query = _between(session.query(CRMWhatsAppLog), CRMWhatsAppLog.created_at, start, end)
    followup_query = _between(session.query(PatientFollowup), PatientFollowup.created_at, start, end)
    total_whatsapp = int(whatsapp_query.count() or 0)
    total_whatsapp_confirmed = int(whatsapp_query.filter(CRMWhatsAppLog.status == "confirmed_sent").count() or 0)
    total_booked = int(
        followup_query
        .filter(PatientFollowup.outcome.in_(["booked", "booking_ulang"]))
        .with_entities(PatientFollowup.patient_id)
        .distinct()
        .count()
        or 0
    )

    return {
        "period": {
            "type": period or "month",
            "date_from": start.strftime("%Y-%m-%d") if start and start != datetime.min else "",
            "date_to": end.strftime("%Y-%m-%d") if end else "",
            "new_patient_source": new_patient_source,
        },
        "summary": {
            "total_revenue": total_revenue,
            "visit_revenue": total_visit_revenue,
            "herbal_revenue": total_herbal_revenue,
            "total_visits": total_visits,
            "unique_patients": unique_patients,
            "new_patients": new_patients,
            "active_patients": active_patients,
            "patients_need_followup": len({row.get("id") for row in need_followup_rows}),
            "dormant_patients": len({row.get("id") for row in dormant_rows}),
            "total_whatsapp_followups": total_whatsapp,
            "total_whatsapp_confirmed": total_whatsapp_confirmed,
            "followup_booked": total_booked,
            "pending_revenue": _money(pending_visit_revenue + pending_herbal_revenue),
            "pending_visit_revenue": pending_visit_revenue,
            "pending_herbal_revenue": pending_herbal_revenue,
        },
        "top_services": top_services,
        "top_service_categories": top_service_categories,
        "top_herbals": top_herbals,
        "top_loyal_patients": top_loyal_patients,
        "patients_need_followup": need_followup_rows[:8],
    }
