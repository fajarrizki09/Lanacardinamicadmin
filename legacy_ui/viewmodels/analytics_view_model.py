class AnalyticsViewModel:
    """Jalur data analytics agar dialog tidak query database langsung."""

    def __init__(self, db):
        self.db = db

    def get_analytics_data(self, period="6m"):
        data = self.db.get_analytics_data(period=period) or {}
        return {
            "total_patients": int(data.get("total_patients", 0) or 0),
            "total_visits": int(data.get("total_visits", 0) or 0),
            "total_transactions": int(data.get("total_transactions", data.get("total_visits", 0)) or 0),
            "total_income": float(data.get("total_income", 0) or 0),
            "net_visit_revenue": float(data.get("net_visit_revenue", 0) or 0),
            "net_herbal_sales": float(data.get("net_herbal_sales", 0) or 0),
            "herbal_cogs": float(data.get("herbal_cogs", 0) or 0),
            "gross_profit": float(data.get("gross_profit", 0) or 0),
            "avg_income": float(data.get("avg_income", 0) or 0),
            "monthly_labels": data.get("monthly_labels") or [],
            "monthly_visits": data.get("monthly_visits") or [],
            "monthly_income": data.get("monthly_income") or [],
        }

    def get_inventory_status(self):
        inventory = self.db.get_all_inventory() or []
        herbals = self.db.get_all_herbals() or []
        low_stock_count = sum(1 for item in inventory if item.get("quantity", 0) <= item.get("min_stock", 0))
        low_stock_count += sum(1 for item in herbals if item.get("stock", 0) <= item.get("min_stock", 5))
        return {
            "inventory": inventory,
            "herbals": herbals,
            "low_stock_count": low_stock_count,
        }
