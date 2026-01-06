from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QPushButton, QLabel, QComboBox, QDateEdit
)
from PySide6.QtCore import QDate
from utils.styles import STYLES

class InventoryTransactionForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("📦 Transaksi Stok")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.item_name_display = QLineEdit()
        self.item_name_display.setReadOnly(True)
        self.item_name_display.setPlaceholderText("Pilih item dari daftar di kanan ->")
        self.item_name_display.setStyleSheet("background-color: #f8f9fa; font-weight: bold;")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Barang Masuk (Stok Bertambah)", "Barang Keluar (Stok Berkurang)"])
        
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 9999)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Keterangan (misal: Pembelian, Penggunaan...)")

        form.addRow("Item:", self.item_name_display)
        form.addRow("Tipe:", self.type_combo)
        form.addRow("Jumlah:", self.qty_input)
        form.addRow("Tanggal:", self.date_input)
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        self.submit_btn = QPushButton("Submit Transaksi")
        self.submit_btn.setStyleSheet(STYLES["add_button"])
        self.submit_btn.setHeight = 45 # Custom height logic handled by CSS usually
        layout.addWidget(self.submit_btn)
        layout.addStretch()

    def set_item(self, item_id, item_name):
        self.selected_item_id = item_id
        self.item_name_display.setText(item_name)
        self.qty_input.setValue(1)
        self.notes_input.clear()
        self.qty_input.setFocus()

    def get_data(self):
        return {
            "item_id": getattr(self, "selected_item_id", None),
            "type": "IN" if self.type_combo.currentIndex() == 0 else "OUT",
            "qty": self.qty_input.value(),
            "date": self.date_input.date().toPython(),
            "notes": self.notes_input.text()
        }
