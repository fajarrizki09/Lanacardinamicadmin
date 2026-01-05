from PySide6.QtCore import QObject, Signal, Qt, QAbstractTableModel
from datetime import datetime

class InventoryStore(QObject):
    """Single Source of Truth for Inventory & Herbal Data"""
    data_changed = Signal()  # Emitted when any data changes
    item_updated = Signal(int)  # Emitted when a specific item changes

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._inventory_cache = []
        self._herbal_cache = []
        self.refresh_cache()

    def refresh_cache(self):
        self._inventory_cache = self.db.get_all_inventory()
        self._herbal_cache = self.db.get_all_herbals()
        self.data_changed.emit()

    def get_inventory(self):
        return self._inventory_cache

    def get_herbals(self):
        return self._herbal_cache

    def update_stock(self, item_id, qty, is_herbal=False):
        if is_herbal:
            self.db.update_herbal_stock(item_id, qty)
        else:
            self.db.update_stock(item_id, qty)
        self.refresh_cache()

class InventoryTableModel(QAbstractTableModel):
    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data or []
        self._headers = headers or ["ID", "Nama", "Stok", "Satuan", "Status"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        item = self._data[row]

        if role == Qt.DisplayRole:
            # Mapping based on typical dict keys from DB
            keys = list(item.keys())
            if col < len(keys):
                val = item[keys[col]]
                if isinstance(val, (int, float)) and "price" in keys[col].lower():
                    return f"Rp {val:,}"
                return str(val)
        
        if role == Qt.ForegroundRole and col == 1: # Stock status logic
            qty = item.get("quantity") or item.get("stock") or 0
            min_stock = item.get("min_stock", 5)
            if qty <= 0: return Qt.red
            if qty <= min_stock: return Qt.darkYellow
            return Qt.darkGreen

        return None

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()
