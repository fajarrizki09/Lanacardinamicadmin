from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QInputDialog, QMessageBox, QFrame, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from utils.styles import STYLES

class InventoryDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Manajemen Stok Alat (Inventory)")
        self.setMinimumSize(700, 500)
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header Info
        header_lbl = QLabel("Monitoring Stok Bahan & Alat Bekam")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header_lbl)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nama Item", "Stok Saat Ini", "Satuan", "Min. Stok", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                gridline-color: #f5f8fa;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        
        add_item_btn = QPushButton("➕ Tambah Item Baru")
        add_item_btn.setStyleSheet(STYLES["add_button"])
        add_item_btn.clicked.connect(self.on_add_item)
        
        add_stock_btn = QPushButton("📦 Tambah Stok")
        add_stock_btn.setStyleSheet(STYLES["update_button"])
        add_stock_btn.clicked.connect(self.on_add_stock)
        
        use_stock_btn = QPushButton("📉 Gunakan Stok")
        use_stock_btn.setStyleSheet(STYLES["delete_button"])
        use_stock_btn.clicked.connect(self.on_use_stock)
        
        edit_item_btn = QPushButton("📝 Edit")
        edit_item_btn.setStyleSheet(STYLES["update_button"])
        edit_item_btn.clicked.connect(self.on_edit_item)
        
        delete_item_btn = QPushButton("🗑️ Hapus")
        delete_item_btn.setStyleSheet(STYLES["delete_button"])
        delete_item_btn.clicked.connect(self.on_delete_item)
        
        btn_layout.addWidget(add_item_btn)
        btn_layout.addWidget(edit_item_btn)
        btn_layout.addWidget(delete_item_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(use_stock_btn)
        btn_layout.addWidget(add_stock_btn)
        
        layout.addLayout(btn_layout)

    def refresh_data(self):
        items = self.db.get_all_inventory()
        
        # Seed default items if empty
        if not items:
            self.db.add_inventory_item("Pisau Bedah", "pcs", 10, 50)
            self.db.add_inventory_item("Kop Bekam (Cup)", "pcs", 20, 100)
            self.db.add_inventory_item("Minyak Zaitun", "botol", 5, 10)
            self.db.add_inventory_item("Tisu / Alcohol Swab", "box", 10, 50)
            items = self.db.get_all_inventory()

        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            # Item Name
            name_item = QTableWidgetItem(item["item_name"])
            name_item.setData(Qt.UserRole, item["id"])
            
            # Quantity
            qty_item = QTableWidgetItem(str(item["quantity"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            
            # Unit
            unit_item = QTableWidgetItem(item["unit"])
            unit_item.setTextAlignment(Qt.AlignCenter)
            
            # Min Stock
            min_item = QTableWidgetItem(str(item["min_stock"]))
            min_item.setTextAlignment(Qt.AlignCenter)
            
            # Status
            status_text = "✅ Aman"
            status_color = "#27ae60"
            if item["quantity"] <= item["min_stock"]:
                status_text = "⚠️ Stok Menipis!"
                status_color = "#e67e22"
            if item["quantity"] <= 0:
                status_text = "🚨 Habis!"
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
            
            self.table.setRowHeight(row, 45)

    def on_edit_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Item", "Silakan pilih item yang ingin diedit.")
            return
            
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        current_name = self.table.item(row, 0).text()
        current_unit = self.table.item(row, 2).text()
        current_min = int(self.table.item(row, 3).text())
        
        name, ok = QInputDialog.getText(self, "Edit Item", "Nama Alat/Bahan:", text=current_name)
        if ok and name:
            unit, ok = QInputDialog.getText(self, "Edit Item", "Satuan:", text=current_unit)
            if ok and unit:
                min_s, ok = QInputDialog.getInt(self, "Edit Item", "Minimal Stok:", current_min, 1)
                if ok:
                    self.db.update_inventory_item(item_id, name, unit, min_s)
                    self.refresh_data()

    def on_delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Item", "Silakan pilih item yang ingin dihapus.")
            return
            
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        
        confirm = QMessageBox.question(
            self, "Hapus Item",
            f"Yakin ingin menghapus '{name}' dari inventori?\nData stok akan hilang selamanya.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.delete_inventory_item(item_id)
            self.refresh_data()

    def on_add_item(self):
        name, ok = QInputDialog.getText(self, "Tambah Item", "Nama Alat/Bahan:")
        if ok and name:
            unit, ok = QInputDialog.getText(self, "Tambah Item", "Satuan (pcs, box, dll):")
            if ok and unit:
                min_s, ok = QInputDialog.getInt(self, "Tambah Item", "Minimal Stok (Peringatan):", 10, 1)
                if ok:
                    self.db.add_inventory_item(name, unit, min_s)
                    self.refresh_data()

    def on_add_stock(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Item", "Silakan pilih item di tabel terlebih dahulu.")
            return
        
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        
        qty, ok = QInputDialog.getInt(self, "Tambah Stok", f"Jumlah penambahan {name}:", 1, 1, 10000)
        if ok:
            self.db.update_stock(item_id, qty)
            self.refresh_data()

    def on_use_stock(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Item", "Silakan pilih item di tabel terlebih dahulu.")
            return
        
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        current_qty = int(self.table.item(row, 1).text())
        
        qty, ok = QInputDialog.getInt(self, "Gunakan Stok", f"Jumlah penggunaan {name}:", 1, 1, current_qty)
        if ok:
            self.db.update_stock(item_id, -qty)
            self.refresh_data()
