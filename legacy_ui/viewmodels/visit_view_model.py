from PySide6.QtCore import QObject, Signal
from threads.visit_thread import VisitThread
from database import VisitData
from typing import List
from datetime import datetime, timedelta, time

class VisitViewModel(QObject):
    visit_added = Signal(float, float, bool, str)
    visit_failed = Signal(str)

    def __init__(self, db, settings):
        super().__init__()
        self.db = db
        self.settings = settings
        self._visit_cache = {}
        self._current_thread = None

    def add_visit(self, patient_id, point_count, therapist_id=None, invoice_path=None,
                  medical_notes=None, manual_price=None, is_free_visit=False,
                  free_visit_reason=None, voucher_code=None, service_id=None,
                  service_name=None):
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.wait()

        inventory_config = self.settings.get_inventory_config()

        self._current_thread = VisitThread(
            self.db, patient_id, point_count, therapist_id, self.settings, invoice_path,
            medical_notes, inventory_config, manual_price, is_free_visit, free_visit_reason,
            voucher_code, service_id, service_name
        )
        self._current_thread.patient_id = patient_id
        self._current_thread.visit_done.connect(self._on_visit_done)
        self._current_thread.visit_failed.connect(self._on_visit_failed)
        self._current_thread.start()

    def _on_visit_done(self, normal_price, discounted_price, discount_applied, discount_rule_name):
        if hasattr(self._current_thread, 'patient_id'):
            patient_id = self._current_thread.patient_id
            self.invalidate_cache(patient_id)

        self.visit_added.emit(normal_price, discounted_price, discount_applied, discount_rule_name)

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
                service_id=v_dict.get('service_id'),
                service_name=v_dict.get('service_name') or 'Bekam',
                invoice_path=v_dict.get('invoice_path'),
                medical_notes=v_dict.get('medical_notes', '-'),
                is_free_visit=v_dict.get('is_free_visit', False),
                free_visit_reason=v_dict.get('free_visit_reason'),
                discount_rule_id=v_dict.get('discount_rule_id'),
                discount_rule_name=v_dict.get('discount_rule_name')
            ))

        self._visit_cache[patient_id] = visits
        return visits

    def get_summary_text(self, visits: List[VisitData]) -> str:
        total = sum(float(v.price) for v in visits)
        total_points = sum(v.point_count for v in visits)
        summary = f"Total kunjungan: {len(visits)} | Total satuan: {total_points} | Total pemasukan: Rp {total:,.0f}"
        return summary

    def filter_visits_by_period(self, visits: List[VisitData], start_date=None, end_date=None) -> List[VisitData]:
        start_dt = self._coerce_datetime(start_date, start_of_day=True)
        end_dt = self._coerce_datetime(end_date, start_of_day=False)

        filtered = []
        for visit in visits:
            visit_date = self._coerce_datetime(visit.date)
            if not visit_date:
                continue
            if start_dt and visit_date < start_dt:
                continue
            if end_dt and visit_date > end_dt:
                continue
            filtered.append(visit)
        return filtered

    def build_visit_report(self, visits: List[VisitData], start_date=None, end_date=None):
        filtered = self.filter_visits_by_period(visits, start_date=start_date, end_date=end_date)
        total_income = sum(float(v.price or 0) for v in filtered)
        total_points = sum(int(v.point_count or 0) for v in filtered)
        discounted_count = sum(1 for v in filtered if v.discount_applied)
        return {
            "visits": filtered,
            "total_visits": len(filtered),
            "total_points": total_points,
            "total_income": total_income,
            "discounted_count": discounted_count,
            "average_income": total_income / len(filtered) if filtered else 0,
        }

    def build_patient_visit_report(self, patient_id, start_date=None, end_date=None):
        visits = self.get_visits_for_patient(patient_id)
        return self.build_visit_report(visits, start_date=start_date, end_date=end_date)

    def get_period_bounds(self, period="month"):
        today = datetime.now()
        if period == "today":
            return datetime.combine(today.date(), time.min), datetime.combine(today.date(), time.max)
        if period == "7d":
            return today - timedelta(days=6), today
        if period == "30d":
            return today - timedelta(days=29), today
        if period == "month":
            return today.replace(day=1, hour=0, minute=0, second=0, microsecond=0), today
        return None, None

    def _coerce_datetime(self, value, start_of_day=True):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            day_time = time.min if start_of_day else time.max
            return datetime.combine(value, day_time)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def invalidate_cache(self, patient_id=None):
        if patient_id:
            if patient_id in self._visit_cache:
                del self._visit_cache[patient_id]
        else:
            self._visit_cache.clear()
