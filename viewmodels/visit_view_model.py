from PySide6.QtCore import QObject, Signal
from threads.visit_thread import VisitThread
from database import VisitData
from typing import List

class VisitViewModel(QObject):
    visit_added = Signal(float, float, bool)
    visit_failed = Signal(str)

    def __init__(self, db, settings):
        super().__init__()
        self.db = db
        self.settings = settings
        self._visit_cache = {}
        self._current_thread = None

    def add_visit(self, patient_id, point_count, therapist_id=None, invoice_path=None, medical_notes=None):
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.wait()

        inventory_config = self.settings.get_inventory_config()

        self._current_thread = VisitThread(
            self.db, patient_id, point_count, therapist_id, self.settings, invoice_path, medical_notes, inventory_config
        )
        self._current_thread.patient_id = patient_id
        self._current_thread.visit_done.connect(self._on_visit_done)
        self._current_thread.visit_failed.connect(self._on_visit_failed)
        self._current_thread.start()

    def _on_visit_done(self, normal_price, discounted_price, discount_applied):
        if hasattr(self._current_thread, 'patient_id'):
            patient_id = self._current_thread.patient_id
            self.invalidate_cache(patient_id)

        self.visit_added.emit(normal_price, discounted_price, discount_applied)

    def _on_visit_failed(self, message):
        self.visit_failed.emit(message)

    def get_visits_for_patient(self, patient_id):
        if patient_id in self._visit_cache:
            return self._visit_cache[patient_id]

        visits_data = self.db.get_visits(patient_id)
        visits = []
        for v_dict in visits_data:
            visits.append(VisitData(
                id=v_dict['id'],
                date=v_dict['date'],
                price=float(v_dict['price']),
                discount_applied=v_dict['discount_applied'],
                point_count=v_dict.get('point_count', 0),
                therapist_id=v_dict.get('therapist_id'),
                invoice_path=v_dict.get('invoice_path'),
                medical_notes=v_dict.get('medical_notes', '-')
            ))

        self._visit_cache[patient_id] = visits
        return visits

    def get_summary_text(self, visits: List[VisitData]) -> str:
        total = sum(float(v.price) for v in visits)
        total_points = sum(v.point_count for v in visits)
        summary = f"Total kunjungan: {len(visits)} | Total titik: {total_points} | Total pemasukan: Rp {total:,.0f}"
        return summary

    def invalidate_cache(self, patient_id=None):
        if patient_id:
            if patient_id in self._visit_cache:
                del self._visit_cache[patient_id]
        else:
            self._visit_cache.clear()
