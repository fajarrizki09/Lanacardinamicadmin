from PySide6.QtCore import QObject, Signal


class ServiceViewModel(QObject):
    data_changed = Signal()

    def __init__(self, db):
        super().__init__()
        self.db = db

    def get_all_services(self, active_only=False):
        return self.db.get_all_services(active_only=active_only)

    def add_service(self, name, unit_label, default_quantity, price_per_unit, notes_template):
        name = name.strip()
        unit_label = (unit_label or "sesi").strip()
        if not name:
            raise ValueError("Nama layanan tidak boleh kosong")
        if default_quantity <= 0:
            raise ValueError("Jumlah default harus lebih dari 0")
        if price_per_unit < 0:
            raise ValueError("Harga tidak boleh kurang dari 0")

        existing = self.db.get_all_services(active_only=False)
        if any(s.name.lower() == name.lower() for s in existing):
            raise ValueError("Nama layanan sudah ada")

        self.db.add_service(name, unit_label, default_quantity, price_per_unit, notes_template)
        self.data_changed.emit()

    def deactivate_service(self, service_id):
        if service_id is None:
            raise ValueError("Layanan tidak valid")
        self.db.delete_service(service_id)
        self.data_changed.emit()
