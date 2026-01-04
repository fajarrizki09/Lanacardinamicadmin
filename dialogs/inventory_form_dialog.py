from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QPushButton, QLabel
)
from utils.styles import STYLES

class InventoryFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Form Stok Alat")
        self.setMinimumWidth(350)
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("pcs / pack / unit")
        
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)
        
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 9999)

        if self.data:
            self.name_input.setText(self.data.get('name', ''))
            self.unit_input.setText(self.data.get('unit', ''))
            self.stock_input.setValue(self.data.get('stock', 0))
            self.min_stock_input.setValue(self.data.get('min_stock', 10))

        form.addRow("Nama Alat:", self.name_input)
        form.addRow("Satuan:", self.unit_input)
        form.addRow("Stok Saat Ini:", self.stock_input)
        form.addRow("Minimal Stok:", self.min_stock_input)
        
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Simpan")
        save_btn.setStyleSheet(STYLES["add_button"])
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Batal")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "unit": self.unit_input.text(),
            "stock": self.stock_input.value(),
            "min_stock": self.min_stock_input.value()
        }
