from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QPushButton, QLabel, QComboBox, QDateEdit
)
from PySide6.QtCore import QDate, Qt
from utils.styles import STYLES

class InventoryTransactionForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.item_name_display = QLineEdit()
        self.item_name_display.setReadOnly(True)
        self.item_name_display.setPlaceholderText("Pilih item dari daftar di kanan ->")
        self.item_name_display.setStyleSheet("background-color: #f8f9fa; font-weight: bold;")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Barang Masuk (Stok Bertambah)", "Barang Keluar (Stok Berkurang)"])

        self.unit_combo = QComboBox()
        
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 9999)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Keterangan (misal: Pembelian, Penggunaan...)")

        form.addRow("Item:", self.item_name_display)
        form.addRow("Tipe:", self.type_combo)
        form.addRow("Jumlah:", self.qty_input)
        form.addRow("Satuan:", self.unit_combo)
        form.addRow("Tanggal:", self.date_input)
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        self.submit_btn = QPushButton("Submit Transaksi")
        self.submit_btn.setStyleSheet(STYLES["add_button"])
        self.submit_btn.setHeight = 45 # Custom height logic handled by CSS usually
        layout.addWidget(self.submit_btn)
        layout.addStretch()

    def set_item(self, item_id, item_name, unit=None, package_unit=None, package_size=1):
        self.selected_item_id = item_id
        self.selected_unit = unit or "pcs"
        self.selected_package_unit = package_unit or ""
        self.selected_package_size = max(1, int(package_size or 1))
        self.item_name_display.setText(item_name)
        self.unit_combo.clear()
        self.unit_combo.addItem(self.selected_unit, 1)
        if self.selected_package_unit and self.selected_package_unit != self.selected_unit:
            self.unit_combo.addItem(
                f"{self.selected_package_unit} (1 = {self.selected_package_size} {self.selected_unit})",
                self.selected_package_size,
            )
        self.qty_input.setValue(1)
        self.notes_input.clear()
        self.qty_input.setFocus()

    def get_data(self):
        return {
            "item_id": getattr(self, "selected_item_id", None),
            "type": "IN" if self.type_combo.currentIndex() == 0 else "OUT",
            "qty": self.qty_input.value(),
            "unit_multiplier": self.unit_combo.currentData() or 1,
            "unit_label": self.unit_combo.currentText(),
            "base_unit": getattr(self, "selected_unit", "pcs"),
            "date": self.date_input.date().toPython(),
            "notes": self.notes_input.text()
        }
