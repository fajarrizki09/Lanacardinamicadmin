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

    def add_inventory_item(self, name, unit, min_stock, initial_qty=0, package_unit=None, package_size=1):
        item_id = self.db.add_inventory_item(name, unit, min_stock, initial_qty, package_unit, package_size)
        self.refresh_cache()
        return item_id

    def update_inventory_item(self, item_id, name, quantity, unit, min_stock, package_unit=None, package_size=1):
        result = self.db.update_inventory_item(item_id, name, quantity, unit, min_stock, package_unit, package_size)
        self.refresh_cache()
        return result

    def delete_inventory_item(self, item_id):
        result = self.db.delete_inventory_item(item_id)
        self.refresh_cache()
        return result

    def add_herbal(self, name, unit, price, stock=0, cost_price=0, package_unit=None, package_size=1, min_stock=5):
        item_id = self.db.add_herbal(name, unit, price, stock, cost_price, package_unit, package_size, min_stock)
        self.refresh_cache()
        return item_id

    def update_herbal(self, item_id, name, unit, price, stock, cost_price=0, package_unit=None, package_size=1, min_stock=5):
        result = self.db.update_herbal(item_id, name, unit, price, stock, cost_price, package_unit, package_size, min_stock)
        self.refresh_cache()
        return result

    def delete_herbal(self, item_id):
        result = self.db.delete_herbal(item_id)
        self.refresh_cache()
        return result

    def update_stock(self, item_id, qty, is_herbal=False, transaction_type=None, note=None):
        # Logic layer validation
        current_data = self.get_herbals() if is_herbal else self.get_inventory()
        item = next((i for i in current_data if i['id'] == item_id), None)

        if not item:
            return False, "Item stok tidak ditemukan. Silakan refresh data dan pilih ulang item."

        current_qty = item.get('stock') if is_herbal else item.get('quantity')
        if current_qty is not None and current_qty + qty < 0:
            item_name = item.get('name', item.get('item_name'))
            return False, f"Stok {item_name} tidak cukup. Tersedia {current_qty}, perlu {abs(qty)}."

        try:
            if is_herbal:
                self.db.update_herbal_stock(item_id, qty, transaction_type=transaction_type, note=note)
            else:
                self.db.update_stock(item_id, qty, transaction_type=transaction_type, note=note)
            self.refresh_cache()
            return True, "Stok berhasil diperbarui."
        except ValueError as exc:
            return False, str(exc)

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
            key_map = {
                "ID": "id",
                "Nama": "name",
                "Nama Herbal": "name",
                "Nama Alat": "item_name",
                "Stok": "stock_display",
                "Satuan": "unit",
                "Kemasan": "package_display",
                "Min Stok": "min_stock",
                "Harga": "price",
                "Modal": "cost_price",
                "Margin": "margin",
            }
            header = self._headers[col] if col < len(self._headers) else ""
            key = key_map.get(header)
            if header == "Kemasan":
                package_unit = item.get("package_unit")
                package_size = item.get("package_size", 1)
                unit = item.get("unit", "")
                return f"1 {package_unit} = {package_size} {unit}" if package_unit else "-"
            if key:
                val = item.get(key, "")
                if header == "Stok" and not val:
                    val = item.get("quantity", item.get("stock", ""))
                if isinstance(val, (int, float)) and key in {"price", "cost_price", "margin"}:
                    return f"Rp {val:,.0f}".replace(",", ".")
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
