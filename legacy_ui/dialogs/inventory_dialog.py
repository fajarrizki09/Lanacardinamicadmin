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
        # Parameter db dipertahankan untuk kompatibilitas constructor lama.
        # Akses data stok diarahkan lewat InventoryStore.
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- SISI KIRI (AKSI / TRANSAKSI) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet(STYLES.get("card", "") + "padding: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        self.transaction_form = InventoryTransactionForm()
        self.transaction_form.submit_btn.clicked.connect(self.process_transaction)
        
        left_layout.addWidget(self.transaction_form)
        left_layout.addStretch()
        
        # Add basic CRUD at the bottom of left panel
        crud_group = QFrame()
        crud_group.setStyleSheet("border-top: 1px solid #eee; padding-top: 15px;")
        crud_layout = QHBoxLayout(crud_group)
        self.add_item_btn = QPushButton("➕ Item Baru")
        self.edit_item_btn = QPushButton("📝 Edit")
        self.del_item_btn = QPushButton("🗑️ Hapus")
        
        for btn in [self.add_item_btn, self.edit_item_btn, self.del_item_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            if btn == self.del_item_btn:
                btn.setStyleSheet(STYLES.get("delete_button", "") + "font-size: 11px; padding: 8px;")
            else:
                btn.setStyleSheet(STYLES.get("update_button", "") + "font-size: 11px; padding: 8px;")
            crud_layout.addWidget(btn)
            
        self.add_item_btn.clicked.connect(self.on_add_item)
        self.edit_item_btn.clicked.connect(self.on_edit_item)
        self.del_item_btn.clicked.connect(self.on_delete_item)

        left_layout.addWidget(crud_group)
        
        # --- SISI KANAN (INFORMASI / MONITORING) ---
        right_panel = QFrame()
        right_panel.setStyleSheet(STYLES.get("card", "") + "padding: 10px;")
        right_layout = QVBoxLayout(right_panel)
        
        header_row = QHBoxLayout()
        header_lbl = QLabel("Monitoring Stok Alat")
        header_lbl.setStyleSheet(STYLES.get("inventory_header", ""))
        
        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari alat...")
        self.search_input.setStyleSheet(STYLES.get("search_input", ""))
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_table)
        
        header_row.addWidget(header_lbl)
        header_row.addStretch()
        header_row.addWidget(self.search_input)
        
        self.table_view = QTableView()
        self.table_view.setStyleSheet("""
            QTableView { border: none; gridline-color: #f0f3f6; }
            QHeaderView::section { 
                background: #f8fafc; 
                padding: 12px; 
                border: none; 
                border-bottom: 2px solid #eee; 
                font-weight: bold;
                font-size: 13px;
                min-height: 45px;
            }
            QTableView::item { padding: 10px; }
        """)
        self.table_view.verticalHeader().setDefaultSectionSize(45)
        self.model = InventoryTableModel(headers=["ID", "Nama Alat", "Stok", "Satuan", "Kemasan", "Min Stok"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.clicked.connect(self.on_item_selected_view)
        
        right_layout.addLayout(header_row)
        right_layout.addWidget(self.table_view)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def on_item_selected_view(self, index):
        if not index.isValid(): return
        item = self.model._data[index.row()]
        self.transaction_form.set_item(
            item["id"],
            item["item_name"],
            item.get("unit"),
            item.get("package_unit"),
            item.get("package_size", 1),
        )

    def filter_table(self, text):
        if not hasattr(self, 'all_items'): return
        filtered = [i for i in self.all_items if text.lower() in i["item_name"].lower()]
        self.model.update_data(filtered)

    def process_transaction(self):
        data = self.transaction_form.get_data()
        if not data["item_id"]:
            QMessageBox.warning(self, "Peringatan", "Pilih item dari daftar di kanan terlebih dahulu.")
            return
            
        converted_qty = int(data["qty"] * data.get("unit_multiplier", 1))
        qty = converted_qty if data["type"] == "IN" else -converted_qty
        note = data.get("notes") or f"{data['qty']} {data.get('unit_label', data.get('base_unit', 'unit'))}"
        success, message = self.store.update_stock(
            data["item_id"],
            qty,
            transaction_type=("stock_in" if data["type"] == "IN" else "stock_out"),
            note=note,
        )
        if not success:
            QMessageBox.warning(self, "Stok Tidak Cukup", message)
            return
        QMessageBox.information(self, "Sukses", message)
        self.transaction_form.item_name_display.clear()

    def on_add_item(self):
        from dialogs.inventory_form_dialog import InventoryFormDialog
        dlg = InventoryFormDialog(self)
        if dlg.exec_():
            d = dlg.get_data()
            if d["name"]:
                self.store.add_inventory_item(
                    d["name"], d["unit"], d["min_stock"], d["stock"], d["package_unit"], d["package_size"]
                )

    def on_edit_item(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        from dialogs.inventory_form_dialog import InventoryFormDialog
        dlg = InventoryFormDialog(self, {
            "name": item["item_name"],
            "unit": item["unit"],
            "package_unit": item.get("package_unit", ""),
            "package_size": item.get("package_size", 1),
            "stock": item["quantity"],
            "min_stock": item["min_stock"],
        })
        if dlg.exec_():
            d = dlg.get_data()
            self.store.update_inventory_item(
                item["id"], d["name"], d["stock"], d["unit"], d["min_stock"], d["package_unit"], d["package_size"]
            )

    def on_delete_item(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        if QMessageBox.question(self, "Hapus", f"Hapus '{item['item_name']}'?") == QMessageBox.Yes:
            self.store.delete_inventory_item(item["id"])
