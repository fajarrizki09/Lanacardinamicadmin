from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QInputDialog, QMessageBox, QFrame,
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

class HerbalDialog(QDialog):
    def __init__(self, db, store, parent=None):
        super().__init__(parent)
        # Parameter db dipertahankan untuk kompatibilitas constructor lama.
        # Akses data herbal diarahkan lewat InventoryStore.
        self.store = store
        self.setWindowTitle("🌿 Manajemen Obat Herbal")
        self.setMinimumSize(1100, 600)
        self.init_ui()
        self.store.data_changed.connect(self.refresh_ui)
        self.refresh_ui()

    def refresh_ui(self):
        items = self.store.get_herbals()
        self.all_items = items
        self.model.update_data(items)
        self.filter_table(self.search_input.text())

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- SISI KIRI (TRANSAKSI) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet(STYLES.get("card", "") + "padding: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        self.transaction_form = InventoryTransactionForm()
        self.transaction_form.submit_btn.clicked.connect(self.process_transaction)
        
        left_layout.addWidget(self.transaction_form)
        left_layout.addStretch()
        
        crud_group = QFrame()
        crud_group.setStyleSheet("border-top: 1px solid #eee; padding-top: 15px;")
        crud_layout = QHBoxLayout(crud_group)
        self.add_item_btn = QPushButton("➕ Herbal Baru")
        self.edit_item_btn = QPushButton("📝 Edit")
        self.del_item_btn = QPushButton("🗑️ Hapus")
        
        for btn in [self.add_item_btn, self.edit_item_btn, self.del_item_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            if btn == self.del_item_btn:
                btn.setStyleSheet(STYLES.get("delete_button", "") + "font-size: 11px; padding: 8px;")
            else:
                btn.setStyleSheet(STYLES.get("add_button", "") + "font-size: 11px; padding: 8px;")
            crud_layout.addWidget(btn)
            
        self.add_item_btn.clicked.connect(self.on_add)
        self.edit_item_btn.clicked.connect(self.on_edit)
        self.del_item_btn.clicked.connect(self.on_delete)

        left_layout.addWidget(crud_group)

        # --- SISI KANAN (MONITORING) ---
        right_panel = QFrame()
        right_panel.setStyleSheet(STYLES.get("card", "") + "background-color: #f0fff4; padding: 10px;") 
        right_layout = QVBoxLayout(right_panel)
        
        header_row = QHBoxLayout()
        header_lbl = QLabel("Stok Herbal & Madu")
        header_lbl.setStyleSheet(STYLES.get("inventory_header", "") + "color: #27ae60;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari herbal...")
        self.search_input.setStyleSheet(STYLES.get("search_input", ""))
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_table)
        
        header_row.addWidget(header_lbl)
        header_row.addStretch()
        header_row.addWidget(self.search_input)
        
        self.table_view = QTableView()
        self.table_view.setStyleSheet("""
            QTableView { border: none; background-color: transparent; gridline-color: #dcfce7; }
            QHeaderView::section { 
                background: #f0fff4; 
                padding: 12px; 
                border: none; 
                border-bottom: 2px solid #bbf7d0; 
                font-weight: bold;
                font-size: 13px;
                min-height: 45px;
            }
            QTableView::item { padding: 10px; }
        """)
        self.table_view.verticalHeader().setDefaultSectionSize(45)
        self.model = InventoryTableModel(headers=["ID", "Nama Herbal", "Stok", "Satuan", "Kemasan", "Modal", "Harga", "Margin"])
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
            item["name"],
            item.get("unit"),
            item.get("package_unit"),
            item.get("package_size", 1),
        )

    def filter_table(self, text):
        if not hasattr(self, 'all_items'): return
        filtered = [i for i in self.all_items if text.lower() in i["name"].lower()]
        self.model.update_data(filtered)

    def process_transaction(self):
        data = self.transaction_form.get_data()
        if not data["item_id"]:
            QMessageBox.warning(self, "Peringatan", "Pilih herbal dari daftar di kanan.")
            return
            
        converted_qty = int(data["qty"] * data.get("unit_multiplier", 1))
        qty = converted_qty if data["type"] == "IN" else -converted_qty
        note = data.get("notes") or f"{data['qty']} {data.get('unit_label', data.get('base_unit', 'unit'))}"
        success, message = self.store.update_stock(
            data["item_id"],
            qty,
            is_herbal=True,
            transaction_type=("stock_in" if data["type"] == "IN" else "sale"),
            note=note,
        )
        if not success:
            QMessageBox.warning(self, "Stok Tidak Cukup", message)
            return
        QMessageBox.information(self, "Sukses", message)
        self.transaction_form.item_name_display.clear()

    def on_add(self):
        from dialogs.herbal_form_dialog import HerbalFormDialog
        dlg = HerbalFormDialog(self)
        if dlg.exec_():
            d = dlg.get_data()
            if d["name"]:
                self.store.add_herbal(
                    d["name"], d["unit"], d["price"], d["stock"], d["cost_price"],
                    d["package_unit"], d["package_size"], d["min_stock"]
                )

    def on_edit(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        from dialogs.herbal_form_dialog import HerbalFormDialog
        dlg = HerbalFormDialog(self, item)
        if dlg.exec_():
            d = dlg.get_data()
            self.store.update_herbal(
                item["id"], d["name"], d["unit"], d["price"], d["stock"], d["cost_price"],
                d["package_unit"], d["package_size"], d["min_stock"]
            )

    def on_delete(self):
        index = self.table_view.currentIndex()
        if not index.isValid(): return
        item = self.model._data[index.row()]
        if QMessageBox.question(self, "Hapus", f"Hapus '{item['name']}'?") == QMessageBox.Yes:
            self.store.delete_herbal(item["id"])
