from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, QLabel
)
from utils.styles import STYLES

class HerbalFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("🌿 Form Herbal")
        self.setMinimumWidth(350)
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("botol / box / pcs")
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10000000)
        self.price_input.setPrefix("Rp ")
        self.price_input.setGroupSeparatorShown(True)
        self.price_input.setDecimals(0)
        
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)

        if self.data:
            self.name_input.setText(self.data.get('name', ''))
            self.unit_input.setText(self.data.get('unit', ''))
            self.price_input.setValue(self.data.get('price', 0))
            self.stock_input.setValue(self.data.get('stock', 0))

        form.addRow("Nama Herbal:", self.name_input)
        form.addRow("Satuan:", self.unit_input)
        form.addRow("Harga Jual:", self.price_input)
        form.addRow("Stok Awal:", self.stock_input)
        
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
            "price": self.price_input.value(),
            "stock": self.stock_input.value()
        }
