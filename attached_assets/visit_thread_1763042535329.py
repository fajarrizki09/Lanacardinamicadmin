from PySide6.QtCore import QThread, Signal

class VisitThread(QThread):
    visit_done = Signal(int, int, bool)
    visit_failed = Signal(str)

    def __init__(self, db, patient_id, price, therapist_id=None, settings=None):
        super().__init__()
        self.db = db
        self.patient_id = patient_id
        self.price = price
        self.therapist_id = therapist_id
        self.settings = settings

    def run(self):
        try:
            discount_percentage = 0
            min_visits = 5
            
            if self.settings:
                discount_percentage = self.settings.get_discount_percentage()
                min_visits = self.settings.get_min_visits_for_discount()
            
            final_price, discount_applied = self.db.add_visit(
                self.patient_id, 
                self.price,
                therapist_id=self.therapist_id,
                discount_percentage=discount_percentage,
                min_visits_for_discount=min_visits
            )
            self.visit_done.emit(self.price, int(final_price), discount_applied)
        except Exception as e:
            self.visit_failed.emit(str(e))
