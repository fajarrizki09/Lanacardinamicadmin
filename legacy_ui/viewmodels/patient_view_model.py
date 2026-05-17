from PySide6.QtCore import QObject, Signal

from database import VisitData


class PatientViewModel(QObject):
    data_changed = Signal()

    def __init__(self, db):
        super().__init__()
        self.db = db

    def add_patient(self, name, phone, address="", gender="Laki-laki"):
        patient_id = self.db.add_patient(name, phone, address, gender)
        self.data_changed.emit()
        return patient_id

    def get_patients(self):
        return self.db.get_patients()

    def get_patient_with_visits(self, patient_id):
        return self.db.get_patient_with_visits(patient_id)

    def update_patient(self, patient_id, name, phone, address="", gender="Laki-laki"):
        self.db.update_patient(patient_id, name, phone, address, gender)
        self.data_changed.emit()

    def update_patient_visits(self, patient_id, visits):
        visit_data_list = [
            VisitData(
                id=visit.get("id"),
                date=visit.get("date"),
                price=visit.get("price", 0),
                discount_applied=visit.get("discount_applied", False),
                point_count=visit.get("point_count", 0),
                therapist_id=visit.get("therapist_id"),
                medical_notes=visit.get("medical_notes"),
            )
            for visit in visits
        ]
        self.db.update_patient_visits(patient_id, visit_data_list)
        self.data_changed.emit()

    def delete_patient(self, patient_id):
        self.db.delete_patient(patient_id)
        self.data_changed.emit()

    def delete_visit(self, patient_id, visit_id):
        current_visits = self.db.get_visits(patient_id)
        updated_visits = []
        for visit in current_visits:
            if visit["id"] != visit_id:
                updated_visits.append(VisitData(
                    id=visit["id"],
                    date=visit["date"],
                    price=visit["price"],
                    discount_applied=visit["discount_applied"],
                    point_count=visit.get("point_count", 0),
                    therapist_id=visit.get("therapist_id"),
                    medical_notes=visit.get("medical_notes"),
                ))

        self.db.update_patient_visits(patient_id, updated_visits)
        self.data_changed.emit()
