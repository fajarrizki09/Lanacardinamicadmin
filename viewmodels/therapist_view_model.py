from PySide6.QtCore import QObject, Signal


class TherapistViewModel(QObject):
    data_changed = Signal()
    error = Signal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    # ---------- QUERY ----------
    def get_all_therapists(self, active_only=False):
        """
        Samakan API dengan Database:
        get_all_therapists(active_only=True/False)
        """
        return self.db.get_all_therapists(active_only=active_only)

    # ---------- COMMAND ----------
    def add_therapist(self, name, gender, specialization):
        name = name.strip()
        if not name:
            raise ValueError("Nama terapis tidak boleh kosong")

        # Cegah duplikat nama
        existing = self.db.get_all_therapists(active_only=False)
        if any(t.name.lower() == name.lower() for t in existing):
            raise ValueError("Nama terapis sudah ada")

        self.db.add_therapist(name, gender, specialization)
        self.data_changed.emit()

    def deactivate_therapist(self, therapist_id):
        if therapist_id is None:
            raise ValueError("Terapis tidak valid")

        self.db.delete_therapist(therapist_id)
        self.data_changed.emit()
