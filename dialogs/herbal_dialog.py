from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QInputDialog, QMessageBox, QFrame,
    QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from utils.styles import STYLES
from components.inventory_transaction_form import InventoryTransactionForm

class HerbalDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌿 Manajemen Obat Herbal")
        self.setMinimumSize(1100, 600)
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- SISI KIRI (TRANSAKSI) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(400)
        left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #dcdde1;")
        left_layout = QVBoxLayout(left_panel)
        
        self.transaction_form = InventoryTransactionForm()
        self.transaction_form.submit_btn.clicked.connect(self.process_transaction)
        
        crud_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("➕ Herbal Baru")
        self.edit_item_btn = QPushButton("📝 Edit")
        self.del_item_btn = QPushButton("🗑️ Hapus")
        
        for btn in [self.add_item_btn, self.edit_item_btn, self.del_item_btn]:
            btn.setStyleSheet("padding: 5px; font-size: 11px;")
            crud_layout.addWidget(btn)
            
        self.add_item_btn.clicked.connect(self.on_add)
        self.edit_item_btn.clicked.connect(self.on_edit)
        self.del_item_btn.clicked.connect(self.on_delete)

        left_layout.addWidget(self.transaction_form)
        left_layout.addLayout(crud_layout)

        # --- SISI KANAN (MONITORING) ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #f0fff4;") # Light herbal green
        right_layout = QVBoxLayout(right_panel)
        
        header_lbl = QLabel("Monitoring Stok Herbal & Madu")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari herbal...")
        self.search_input.textChanged.connect(self.filter_table)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nama Herbal", "Stok", "Satuan", "Harga", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemClicked.connect(self.on_item_selected)
        
        right_layout.addWidget(header_lbl)
        right_layout.addWidget(self.search_input)
        right_layout.addWidget(self.table)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def refresh_data(self):
        items = self.db.get_all_herbals()
        self.all_items = items
        self.update_table(items)

    def update_table(self, items):
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
            
            status_text = "✅ Aman"
            status_color = "#27ae60"
            if item["stock"] <= 5: # Default threshold
                status_text = "⚠️ Menipis"
                status_color = "#e67e22"
            if item["stock"] <= 0:
                status_text = "🚨 Habis"
                status_color = "#e74c3c"
                
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QBrush(QColor("white")))
            status_item.setBackground(QBrush(QColor(status_color)))
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, stock_item)
            self.table.setItem(row, 2, unit_item)
            self.table.setItem(row, 3, price_item)
            self.table.setItem(row, 4, status_item)
            self.table.setRowHeight(row, 40)

    def on_item_selected(self, item):
        row = item.row()
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        self.transaction_form.set_item(item_id, name)

    def filter_table(self, text):
        filtered = [i for i in self.all_items if text.lower() in i["name"].lower()]
        self.update_table(filtered)

    def process_transaction(self):
        data = self.transaction_form.get_data()
        if not data["item_id"]:
            QMessageBox.warning(self, "Peringatan", "Pilih herbal dari daftar di kanan.")
            return
            
        qty = data["qty"] if data["type"] == "IN" else -data["qty"]
        self.db.update_herbal_stock(data["item_id"], qty)
        self.refresh_data()
        QMessageBox.information(self, "Sukses", "Stok herbal berhasil diperbarui.")
        self.transaction_form.item_name_display.clear()

    def on_add(self):
        from dialogs.herbal_form_dialog import HerbalFormDialog
        dlg = HerbalFormDialog(self)
        if dlg.exec_():
            d = dlg.get_data()
            if d["name"]:
                self.db.add_herbal(d["name"], d["unit"], d["price"])
                if d["stock"] > 0:
                    items = self.db.get_all_herbals()
                    new_id = max([i['id'] for i in items]) if items else None
                    if new_id: self.db.update_herbal_stock(new_id, d["stock"])
                self.refresh_data()

    def on_edit(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        items = self.db.get_all_herbals()
        curr = next((i for i in items if i['id'] == item_id), None)
        if curr:
            from dialogs.herbal_form_dialog import HerbalFormDialog
            dlg = HerbalFormDialog(self, curr)
            if dlg.exec_():
                d = dlg.get_data()
                self.db.update_herbal(item_id, d["name"], d["unit"], d["price"], 0)
                diff = d["stock"] - curr["stock"]
                if diff != 0: self.db.update_herbal_stock(item_id, diff)
                self.refresh_data()

    def on_delete(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        if QMessageBox.question(self, "Hapus", "Hapus herbal?") == QMessageBox.Yes:
            self.db.delete_herbal(item_id)
            self.refresh_data()
