from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QInputDialog, QMessageBox, QFrame, QSpinBox,
    QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from utils.styles import STYLES
from components.inventory_transaction_form import InventoryTransactionForm

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, 
    QMessageBox, QFrame, QLineEdit, QPushButton
)
from viewmodels.inventory_store import InventoryTableModel

class InventoryDialog(QDialog):
    def __init__(self, db, store, parent=None):
        super().__init__(parent)
        self.db = db
        self.store = store
        self.init_ui()
        self.store.data_changed.connect(self.refresh_ui)
        self.refresh_ui()

    def init_ui(self):
        # ... setup layout ...
        self.table_view = QTableView()
        self.model = InventoryTableModel(headers=["ID", "Nama Alat", "Stok", "Satuan", "Min Stok"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # ...

    def init_ui(self):
        # Main Horizontal Layout for Split View
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- SISI KIRI (AKSI / TRANSAKSI) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(400)
        left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #dcdde1;")
        left_layout = QVBoxLayout(left_panel)
        
        self.transaction_form = InventoryTransactionForm()
        self.transaction_form.submit_btn.clicked.connect(self.process_transaction)
        
        # Add basic CRUD at the bottom of left panel
        crud_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("➕ Item Baru")
        self.edit_item_btn = QPushButton("📝 Edit")
        self.del_item_btn = QPushButton("🗑️ Hapus")
        
        for btn in [self.add_item_btn, self.edit_item_btn, self.del_item_btn]:
            btn.setStyleSheet("padding: 5px; font-size: 11px;")
            crud_layout.addWidget(btn)
            
        self.add_item_btn.clicked.connect(self.on_add_item)
        self.edit_item_btn.clicked.connect(self.on_edit_item)
        self.del_item_btn.clicked.connect(self.on_delete_item)

        left_layout.addWidget(self.transaction_form)
        left_layout.addLayout(crud_layout)
        
        # --- SISI KANAN (INFORMASI / MONITORING) ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #f8f9fa;")
        right_layout = QVBoxLayout(right_panel)
        
        header_lbl = QLabel("Monitoring Stok Real-time")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        
        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari alat...")
        self.search_input.textChanged.connect(self.filter_table)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nama Item", "Stok", "Satuan", "Min", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.itemClicked.connect(self.on_item_selected)
        
        right_layout.addWidget(header_lbl)
        right_layout.addWidget(self.search_input)
        right_layout.addWidget(self.table)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def refresh_data(self):
        items = self.db.get_all_inventory()
        self.all_items = items # For filtering
        self.update_table(items)

    def update_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name_item = QTableWidgetItem(item["item_name"])
            name_item.setData(Qt.UserRole, item["id"])
            
            qty_item = QTableWidgetItem(str(item["quantity"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            
            unit_item = QTableWidgetItem(item["unit"])
            unit_item.setTextAlignment(Qt.AlignCenter)
            
            min_item = QTableWidgetItem(str(item["min_stock"]))
            min_item.setTextAlignment(Qt.AlignCenter)
            
            status_text = "✅ Aman"
            status_color = "#27ae60"
            if item["quantity"] <= item["min_stock"]:
                status_text = "⚠️ Menipis"
                status_color = "#e67e22"
            if item["quantity"] <= 0:
                status_text = "🚨 Habis"
                status_color = "#e74c3c"
                
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QBrush(QColor("white")))
            status_item.setBackground(QBrush(QColor(status_color)))
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, qty_item)
            self.table.setItem(row, 2, unit_item)
            self.table.setItem(row, 3, min_item)
            self.table.setItem(row, 4, status_item)
            self.table.setRowHeight(row, 40)

    def on_item_selected(self, item):
        row = item.row()
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        self.transaction_form.set_item(item_id, name)

    def filter_table(self, text):
        filtered = [i for i in self.all_items if text.lower() in i["item_name"].lower()]
        self.update_table(filtered)

    def process_transaction(self):
        data = self.transaction_form.get_data()
        if not data["item_id"]:
            QMessageBox.warning(self, "Peringatan", "Pilih item dari daftar di kanan terlebih dahulu.")
            return
            
        qty = data["qty"] if data["type"] == "IN" else -data["qty"]
        
        # Update DB
        self.db.update_stock(data["item_id"], qty)
        
        # UI Refresh
        self.refresh_data()
        QMessageBox.information(self, "Sukses", f"Transaksi berhasil. Stok diperbarui.")
        self.transaction_form.item_name_display.clear()
        self.transaction_form.selected_item_id = None

    def on_add_item(self):
        from dialogs.inventory_form_dialog import InventoryFormDialog
        dlg = InventoryFormDialog(self)
        if dlg.exec_():
            d = dlg.get_data()
            if d["name"]:
                self.db.add_inventory_item(d["name"], d["unit"], d["stock"], d["min_stock"])
                self.refresh_data()

    def on_edit_item(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        items = self.db.get_all_inventory()
        curr = next((i for i in items if i['id'] == item_id), None)
        if curr:
            from dialogs.inventory_form_dialog import InventoryFormDialog
            dlg = InventoryFormDialog(self, {"name": curr["item_name"], "unit": curr["unit"], "stock": curr["quantity"], "min_stock": curr["min_stock"]})
            if dlg.exec_():
                d = dlg.get_data()
                self.db.update_inventory_item(item_id, d["name"], d["unit"], d["min_stock"])
                diff = d["stock"] - curr["quantity"]
                if diff != 0: self.db.update_stock(item_id, diff)
                self.refresh_data()

    def on_delete_item(self):
        row = self.table.currentRow()
        if row < 0: return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        if QMessageBox.question(self, "Hapus", f"Hapus '{name}'?") == QMessageBox.Yes:
            self.db.delete_inventory_item(item_id)
            self.refresh_data()
