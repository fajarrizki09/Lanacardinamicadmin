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
        self.setWindowTitle("📊 Manajemen Stok Alat (Inventory)")
        self.setMinimumSize(1100, 600)
        self.init_ui()
        self.store.data_changed.connect(self.refresh_ui)
        self.refresh_ui()

    def refresh_ui(self):
        items = self.store.get_inventory()
        self.all_items = items
        self.model.update_data(items)
        # Fallback for search
        self.filter_table(self.search_input.text())

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
        
        self.table_view = QTableView()
        self.model = InventoryTableModel(headers=["ID", "Nama Alat", "Stok", "Satuan", "Min Stok"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.clicked.connect(self.on_item_selected_view)
        
        right_layout.addWidget(header_lbl)
        right_layout.addWidget(self.search_input)
        right_layout.addWidget(self.table_view)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def on_item_selected_view(self, index):
        if not index.isValid(): return
        item = self.model._data[index.row()]
        self.transaction_form.set_item(item["id"], item["item_name"])

    def filter_table(self, text):
        if not hasattr(self, 'all_items'): return
        filtered = [i for i in self.all_items if text.lower() in i["item_name"].lower()]
        self.model.update_data(filtered)

    def process_transaction(self):
        data = self.transaction_form.get_data()
        if not data["item_id"]:
            QMessageBox.warning(self, "Peringatan", "Pilih item dari daftar di kanan terlebih dahulu.")
            return
            
        qty = data["qty"] if data["type"] == "IN" else -data["qty"]
        self.store.update_stock(data["item_id"], qty)
        QMessageBox.information(self, "Sukses", f"Transaksi berhasil. Stok diperbarui.")
        self.transaction_form.item_name_display.clear()

    def on_add_item(self):
        from dialogs.inventory_form_dialog import InventoryFormDialog
        dlg = InventoryFormDialog(self)
        if dlg.exec_():
            d = dlg.get_data()
            if d["name"]:
                self.db.add_inventory_item(d["name"], d["unit"], d["stock"], d["min_stock"])
                self.store.refresh_cache()

    def on_edit_item(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        from dialogs.inventory_form_dialog import InventoryFormDialog
        dlg = InventoryFormDialog(self, {"name": item["item_name"], "unit": item["unit"], "stock": item["quantity"], "min_stock": item["min_stock"]})
        if dlg.exec_():
            d = dlg.get_data()
            self.db.update_inventory_item(item["id"], d["name"], d["unit"], d["min_stock"])
            diff = d["stock"] - item["quantity"]
            if diff != 0: self.db.update_stock(item["id"], diff)
            self.store.refresh_cache()

    def on_delete_item(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        if QMessageBox.question(self, "Hapus", f"Hapus '{item['item_name']}'?") == QMessageBox.Yes:
            self.db.delete_inventory_item(item["id"])
            self.store.refresh_cache()
