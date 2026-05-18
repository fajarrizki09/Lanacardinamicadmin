from datetime import datetime, time

from sqlalchemy import case, or_

from helpers.revenue_rules import active_invoice_filter, revenue_case


def build_dashboard_stats(session, models):
    """Bangun data dashboard dari session database aktif."""

    func = models["func"]
    Patient = models["Patient"]
    Therapist = models["Therapist"]
    Visit = models["Visit"]
    Inventory = models["Inventory"]
    Herbal = models["Herbal"]
    HerbalTransaction = models["HerbalTransaction"]

    standalone_herbal_sale_filter = (
        HerbalTransaction.transaction_type == "sale",
        HerbalTransaction.visit_id.is_(None),
    )
    herbal_return_filter = HerbalTransaction.transaction_type.in_(["return", "retur"])
    active_visit_status = active_invoice_filter(Visit)
    active_herbal_status = active_invoice_filter(HerbalTransaction)
    total_patients = session.query(func.count(Patient.id)).scalar() or 0
    total_visits = session.query(func.count(Visit.id)).scalar() or 0
    total_herbal_sales = session.query(func.count(HerbalTransaction.id)).filter(*standalone_herbal_sale_filter).scalar() or 0
    linked_herbal_total_expr = (
        session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0))
        .filter(HerbalTransaction.visit_id == Visit.id, HerbalTransaction.transaction_type == "sale")
        .correlate(Visit)
        .scalar_subquery()
    )
    linked_herbal_paid_expr = (
        session.query(func.coalesce(func.sum(func.coalesce(HerbalTransaction.amount_paid, 0)), 0))
        .filter(HerbalTransaction.visit_id == Visit.id, HerbalTransaction.transaction_type == "sale")
        .correlate(Visit)
        .scalar_subquery()
    )
    visit_total_expr = func.coalesce(func.nullif(Visit.final_price, 0), Visit.price, 0) + linked_herbal_total_expr
    visit_paid_expr = func.coalesce(Visit.amount_paid, 0) + linked_herbal_paid_expr
    visit_income_expr = case(
        (Visit.payment_method == "free", 0),
        (or_(Visit.payment_status == "paid", Visit.payment_status.is_(None)), visit_total_expr),
        (Visit.payment_status == "partial", visit_paid_expr),
        else_=0,
    )
    herbal_income_expr = revenue_case(HerbalTransaction, HerbalTransaction.total_price)

    visit_income = session.query(func.coalesce(func.sum(visit_income_expr), 0)).filter(active_visit_status).scalar() or 0
    herbal_income = session.query(func.coalesce(func.sum(herbal_income_expr), 0)).filter(*standalone_herbal_sale_filter, active_herbal_status).scalar() or 0
    herbal_returns = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)).filter(herbal_return_filter, HerbalTransaction.visit_id.is_(None)).scalar() or 0
    net_herbal_income = max(0, float(herbal_income or 0) - float(herbal_returns or 0))
    today_start = datetime.combine(datetime.now().date(), time.min)
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    visits_today = session.query(func.count(Visit.id))\
        .filter(Visit.date >= today_start).scalar() or 0
    current_visit_income = session.query(func.coalesce(func.sum(visit_income_expr), 0))\
        .filter(Visit.date >= month_start, active_visit_status).scalar() or 0
    current_herbal_income = session.query(func.coalesce(func.sum(herbal_income_expr), 0))\
        .filter(HerbalTransaction.date >= month_start, *standalone_herbal_sale_filter, active_herbal_status).scalar() or 0
    current_herbal_returns = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0))\
        .filter(HerbalTransaction.date >= month_start, herbal_return_filter, HerbalTransaction.visit_id.is_(None)).scalar() or 0
    current_net_herbal_income = max(0, float(current_herbal_income or 0) - float(current_herbal_returns or 0))

    low_stock_inventory = session.query(func.count(Inventory.id))\
        .filter(Inventory.quantity <= Inventory.min_stock, Inventory.is_active == True).scalar() or 0
    out_of_stock_herbals = session.query(func.count(Herbal.id))\
        .filter(Herbal.stock <= 0, Herbal.is_active == True).scalar() or 0

    low_stock_items = session.query(Inventory.item_name, Inventory.quantity, Inventory.unit, Inventory.min_stock)\
        .filter(Inventory.quantity <= Inventory.min_stock, Inventory.is_active == True)\
        .order_by(Inventory.quantity.asc(), Inventory.item_name.asc())\
        .limit(5).all()
    out_of_stock_items = session.query(Herbal.name, Herbal.stock, Herbal.unit)\
        .filter(Herbal.stock <= 0, Herbal.is_active == True)\
        .order_by(Herbal.name.asc())\
        .limit(5).all()

    recent_transactions = []
    recent_visits = session.query(
        Visit.date,
        Visit.price,
        Patient.name.label("patient_name"),
        Therapist.name.label("therapist_name"),
    ).outerjoin(Patient, Patient.id == Visit.patient_id)\
     .outerjoin(Therapist, Therapist.id == Visit.therapist_id)\
     .order_by(Visit.date.desc()).limit(5).all()

    for visit in recent_visits:
        recent_transactions.append({
            "type": "visit",
            "date_obj": visit.date,
            "date": visit.date.strftime("%d %b %Y %H:%M") if hasattr(visit.date, "strftime") else str(visit.date),
            "title": visit.patient_name or "Pasien tidak diketahui",
            "subtitle": visit.therapist_name or "Terapis belum diisi",
            "amount": float(visit.price or 0),
        })

    recent_herbals = session.query(
        HerbalTransaction.date,
        HerbalTransaction.quantity,
        HerbalTransaction.total_price,
        Herbal.name.label("herbal_name"),
    ).outerjoin(Herbal, Herbal.id == HerbalTransaction.herbal_id)\
        .filter(*standalone_herbal_sale_filter)\
     .order_by(HerbalTransaction.date.desc()).limit(5).all()

    for sale in recent_herbals:
        recent_transactions.append({
            "type": "herbal",
            "date_obj": sale.date,
            "date": sale.date.strftime("%d %b %Y %H:%M") if hasattr(sale.date, "strftime") else str(sale.date),
            "title": sale.herbal_name or "Herbal tidak diketahui",
            "subtitle": f"Penjualan herbal ({int(sale.quantity or 0)} item)",
            "amount": float(sale.total_price or 0),
        })

    recent_transactions.sort(key=lambda item: item.get("date_obj") or datetime.min, reverse=True)
    recent_transactions = recent_transactions[:5]
    for item in recent_transactions:
        item.pop("date_obj", None)

    return {
        "total_patients": total_patients,
        "total_visits": total_visits,
        "visits_today": int(visits_today or 0),
        "total_herbal_sales": total_herbal_sales,
        "total_transactions": total_visits + total_herbal_sales,
        "total_income": float(visit_income or 0) + net_herbal_income,
        "current_period_income": float(current_visit_income or 0) + current_net_herbal_income,
        "gross_herbal_sales": float(herbal_income or 0),
        "herbal_returns": float(herbal_returns or 0),
        "net_herbal_sales": net_herbal_income,
        "active_invoice_total": float(visit_income or 0) + float(herbal_income or 0),
        "low_stock_inventory": low_stock_inventory,
        "out_of_stock_herbals": out_of_stock_herbals,
        "low_stock_items": [
            {
                "name": item.item_name,
                "quantity": int(item.quantity or 0),
                "unit": item.unit,
                "min_stock": int(item.min_stock or 0),
            }
            for item in low_stock_items
        ],
        "out_of_stock_items": [
            {
                "name": item.name,
                "quantity": int(item.stock or 0),
                "unit": item.unit,
            }
            for item in out_of_stock_items
        ],
        "recent_transactions": recent_transactions,
    }
