from PySide6.QtCore import QThread, Signal

class VisitThread(QThread):
    visit_done = Signal(float, float, bool)
    visit_failed = Signal(str)

    def __init__(self, db, patient_id, point_count, therapist_id=None, settings=None, 
                 invoice_path=None, medical_notes=None, inventory_config=None, manual_price=None):
        super().__init__()
        self.db = db
        self.patient_id = patient_id
        self.point_count = point_count
        self.therapist_id = therapist_id
        self.settings = self.settings = settings
        self.invoice_path = invoice_path
        self.medical_notes = medical_notes
        self.inventory_config = inventory_config
        self.manual_price = manual_price

    def run(self):
        try:
            discount_percentage = 0
            min_visits = 5
            price_per_point = 10000
            
            if self.settings:
                discount_percentage = self.settings.get_discount_percentage()
                min_visits = self.settings.get_min_visits_for_discount()
                price_per_point = self.settings.get_price_per_point()
            
            if self.manual_price is not None:
                normal_price = float(self.manual_price)
            else:
                normal_price = float(self.point_count * price_per_point)
            
            final_price, discount_applied = self.db.add_visit(
                self.patient_id, 
                normal_price,
                point_count=self.point_count,
                therapist_id=self.therapist_id,
                discount_percentage=discount_percentage,
                min_visits_for_discount=min_visits,
                invoice_path=self.invoice_path,
                medical_notes=self.medical_notes,
                inventory_config=self.inventory_config
            )
            
            self.visit_done.emit(normal_price, final_price, discount_applied)
        except Exception as e:
            self.visit_failed.emit(str(e))
