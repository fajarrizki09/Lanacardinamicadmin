from fastapi import APIRouter, HTTPException, Request
from api.admin_pin import require_admin_pin
from api.database_manager import db

router = APIRouter()

SAFE_DASHBOARD_STATS = {
    "total_patients": 0,
    "total_visits": 0,
    "visits_today": 0,
    "total_herbal_sales": 0,
    "total_transactions": 0,
    "total_income": 0,
    "current_period_income": 0,
    "low_stock_inventory": 0,
    "out_of_stock_herbals": 0,
    "low_stock_items": [],
    "out_of_stock_items": [],
    "recent_transactions": [],
    "discount_summary": {},
}


def _safe_dashboard_stats(data):
    safe = dict(SAFE_DASHBOARD_STATS)
    if isinstance(data, dict):
        safe.update({key: value for key, value in data.items() if value is not None})

    for key in (
        "total_patients",
        "total_visits",
        "visits_today",
        "total_herbal_sales",
        "total_transactions",
        "low_stock_inventory",
        "out_of_stock_herbals",
    ):
        safe[key] = int(safe.get(key) or 0)

    for key in ("total_income", "current_period_income"):
        safe[key] = float(safe.get(key) or 0)

    for key in ("low_stock_items", "out_of_stock_items", "recent_transactions"):
        if not isinstance(safe.get(key), list):
            safe[key] = []
    if not isinstance(safe.get("discount_summary"), dict):
        safe["discount_summary"] = {}

    return safe


def _date_text(value):
    return value.strftime("%Y-%m-%d") if value else ""


def _rule_payload(rule):
    return {
        "id": rule.id,
        "name": rule.name,
        "type": rule.type,
        "discount_type": rule.discount_type,
        "discount_value": float(rule.discount_value or 0),
        "condition_value": float(rule.condition_value) if rule.condition_value is not None else None,
        "voucher_code": rule.voucher_code or "",
        "start_date": _date_text(rule.start_date),
        "end_date": _date_text(rule.end_date),
        "is_active": bool(rule.is_active),
        "priority": int(rule.priority or 100),
        "created_at": rule.created_at.strftime("%Y-%m-%d %H:%M:%S") if rule.created_at else "",
    }


def _discount_dashboard_summary():
    rules = db.get_discount_rules(active_only=False)
    active = [rule for rule in rules if rule.is_active]
    vouchers = [rule for rule in active if rule.type == "voucher"]
    visit_rules = [rule for rule in active if rule.type == "visit_count"]
    sorted_by_created = sorted(rules, key=lambda rule: rule.created_at or 0, reverse=True)
    newest = sorted_by_created[0] if sorted_by_created else None
    previous = sorted_by_created[1] if len(sorted_by_created) > 1 else None
    next_rule = sorted(active, key=lambda rule: (rule.priority, rule.created_at or 0))[0] if active else None

    return {
        "active_count": len(active),
        "active_voucher_count": len(vouchers),
        "active_visit_count": len(visit_rules),
        "newest": _rule_payload(newest) if newest else None,
        "previous": _rule_payload(previous) if previous else None,
        "top_priority": _rule_payload(next_rule) if next_rule else None,
        "active_items": [_rule_payload(rule) for rule in sorted(active, key=lambda rule: (rule.priority, rule.created_at or 0))[:5]],
    }


@router.get("/dashboard_stats")
def get_dashboard_stats():
    try:
        stats = _safe_dashboard_stats(db.get_dashboard_stats())
        stats["discount_summary"] = _discount_dashboard_summary()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
def get_analytics(request: Request, period: str = "6m"):
    try:
        require_admin_pin(request)
        return db.get_analytics_data(period=period)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
