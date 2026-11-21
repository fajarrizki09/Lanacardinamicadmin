class SettingsViewModel:
    """Wrapper tipis agar dialog pengaturan tidak mengakses storage settings langsung."""

    def __init__(self, settings, db=None):
        self.settings = settings
        self.db = db

    def get_price_settings(self):
        return {
            "price_per_point": self.settings.get_price_per_point(),
            "base_price": self.settings.get_base_price(),
            "discount_percentage": self.settings.get_discount_percentage(),
            "min_visits_for_discount": self.settings.get_min_visits_for_discount(),
        }

    def save_price_settings(self, price_per_point, base_price, discount_percentage, min_visits):
        self.settings.set_price_per_point(price_per_point)
        self.settings.set_base_price(base_price)
        self.settings.set_discount_percentage(discount_percentage)
        self.settings.set_min_visits_for_discount(min_visits)

    def get_custom_invoice_settings(self):
        return self.settings.get_custom_invoice_settings()

    def save_custom_invoice_settings(self, data):
        self.settings.save_custom_invoice_settings(data)

    def get_clinic_profile(self):
        if hasattr(self.settings, "get_clinic_profile"):
            return self.settings.get_clinic_profile()
        return self.settings.get_custom_invoice_settings()

    def save_clinic_profile(self, data):
        if hasattr(self.settings, "save_clinic_profile"):
            self.settings.save_clinic_profile(data)
        else:
            self.settings.save_custom_invoice_settings(data)

    def get_inventory_config(self):
        return self.settings.get_inventory_config()

    def set_inventory_config(self, config):
        self.settings.set_inventory_config(config)

    def get_price_per_point(self):
        return self.settings.get_price_per_point()

    def calculate_price_from_points(self, point_count):
        return self.settings.calculate_price_from_points(point_count)

    def get_database_path(self):
        if self.db and hasattr(self.db, "get_database_path"):
            return self.db.get_database_path()
        return "data.db"

    def get_backup_config(self):
        if hasattr(self.settings, "get_backup_config"):
            return self.settings.get_backup_config()
        return {
            "auto_enabled": True,
            "interval": "daily",
            "max_files": 10,
            "last_backup_time": None,
            "last_backup_status": "Belum pernah backup",
        }

    def save_backup_config(self, auto_enabled=True, interval="daily", max_files=10):
        if hasattr(self.settings, "set_backup_config"):
            self.settings.set_backup_config(auto_enabled, interval, max_files)

    def save_backup_status(self, status, backup_time=None):
        if hasattr(self.settings, "set_backup_status"):
            self.settings.set_backup_status(status, backup_time)

    def get_discount_rules(self):
        if not self.db:
            return []
        return self.db.get_discount_rules()

    def add_discount_rule(self, data):
        if not self.db:
            raise ValueError("Database belum tersedia untuk aturan diskon.")
        return self.db.add_discount_rule(data)

    def update_discount_rule(self, rule_id, data):
        if not self.db:
            raise ValueError("Database belum tersedia untuk aturan diskon.")
        return self.db.update_discount_rule(rule_id, data)

    def set_discount_rule_active(self, rule_id, is_active):
        if not self.db:
            raise ValueError("Database belum tersedia untuk aturan diskon.")
        return self.db.set_discount_rule_active(rule_id, is_active)

    def delete_discount_rule(self, rule_id):
        if not self.db:
            raise ValueError("Database belum tersedia untuk aturan diskon.")
        return self.db.delete_discount_rule(rule_id)
