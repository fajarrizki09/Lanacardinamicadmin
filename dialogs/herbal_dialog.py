from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from utils.styles import STYLES

class HerbalDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌿 Manajemen Obat Herbal")
        self.setMinimumSize(800, 500)
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("Daftar Obat Herbal & Madu")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        layout.addWidget(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nama Herbal", "Stok", "Satuan", "Harga Jual", "Aksi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Tambah Herbal")
        add_btn.setStyleSheet(STYLES["add_button"])
        add_btn.clicked.connect(self.on_add)
        
        edit_btn = QPushButton("📝 Edit")
        edit_btn.setStyleSheet(STYLES["update_button"])
        edit_btn.clicked.connect(self.on_edit)

        del_btn = QPushButton("🗑️ Hapus")
        del_btn.setStyleSheet(STYLES["delete_button"])
        del_btn.clicked.connect(self.on_delete)

        stock_btn = QPushButton("📦 Update Stok")
        stock_btn.setStyleSheet(STYLES["add_button"])
        stock_btn.clicked.connect(self.on_update_stock)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(stock_btn)
        layout.addLayout(btn_layout)

    def refresh_data(self):
        items = self.db.get_all_herbals()
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.UserRole, item["id"])
            
            stock_item = QTableWidgetItem(str(item["stock"]))
            stock_item.setTextAlignment(Qt.AlignCenter)
            
            unit_item = QTableWidgetItem(item["unit"])
            unit_item.setTextAlignment(Qt.AlignCenter)
            
            price_item = QTableWidgetItem(f"Rp {item['price']:,}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, stock_item)
            self.table.setItem(row, 2, unit_item)
            self.table.setItem(row, 3, price_item)
            self.table.setRowHeight(row, 45)

    def on_add(self):
        from dialogs.herbal_form_dialog import HerbalFormDialog
        dlg = HerbalFormDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if data["name"]:
                self.db.add_herbal(data["name"], data["unit"], data["price"])
                # Also set initial stock if provided
                if data["stock"] > 0:
                    items = self.db.get_all_herbals()
                    new_id = max([i['id'] for i in items]) if items else None
                    if new_id:
                        self.db.update_herbal_stock(new_id, data["stock"])
                self.refresh_data()

    def on_edit(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        
        # Get current data
        items = self.db.get_all_herbals()
        current_data = next((i for i in items if i['id'] == item_id), None)
        
        if current_data:
            from dialogs.herbal_form_dialog import HerbalFormDialog
            dlg = HerbalFormDialog(self, current_data)
            if dlg.exec_():
                data = dlg.get_data()
                self.db.update_herbal(item_id, data["name"], data["unit"], data["price"], 0)
                self.refresh_data()

    def on_delete(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        if QMessageBox.question(self, "Hapus", "Hapus herbal ini?") == QMessageBox.Yes:
            self.db.delete_herbal(item_id)
            self.refresh_data()

    def on_update_stock(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        val, ok = QInputDialog.getInt(self, "Update Stok", "Tambah/Kurang Stok:", 0, -1000, 1000)
        if ok:
            self.db.update_herbal_stock(item_id, val)
            self.refresh_data()
