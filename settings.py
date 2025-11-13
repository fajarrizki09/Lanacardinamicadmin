import json
import os

class AppSettings:
    def __init__(self, file_path="settings.json"):
        self.file_path = file_path
        self.settings = {
            "base_price": 100000,
            "price_per_point": 10000,
            "discount_percentage": 50,
            "min_visits_for_discount": 5
        }
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
                    if "price_per_point" not in self.settings:
                        self.settings["price_per_point"] = 10000
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_base_price(self):
        return self.settings.get("base_price", 100000)

    def set_base_price(self, price):
        self.settings["base_price"] = price
        self.save()
    
    def get_price_per_point(self):
        return self.settings.get("price_per_point", 10000)
    
    def set_price_per_point(self, price):
        self.settings["price_per_point"] = price
        self.save()
    
    def calculate_price_from_points(self, point_count):
        return point_count * self.get_price_per_point()

    def get_discount_percentage(self):
        return self.settings.get("discount_percentage", 50)

    def set_discount_percentage(self, percentage):
        self.settings["discount_percentage"] = percentage
        self.save()

    def get_min_visits_for_discount(self):
        return self.settings.get("min_visits_for_discount", 5)

    def set_min_visits_for_discount(self, min_visits):
        self.settings["min_visits_for_discount"] = min_visits
        self.save()

    def get_all_settings(self):
        return self.settings.copy()

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save()
