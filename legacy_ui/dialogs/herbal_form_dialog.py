from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QComboBox
)
from utils.styles import STYLES

UNIT_OPTIONS = ["botol", "pcs", "box", "saset", "pack", "strip", "tablet", "kapsul", "dus"]

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
        self.unit_input = QComboBox()
        self.unit_input.setEditable(True)
        self.unit_input.addItems(UNIT_OPTIONS)

        self.package_unit_input = QComboBox()
        self.package_unit_input.setEditable(True)
        self.package_unit_input.addItems([""] + UNIT_OPTIONS)

        self.package_size_input = QSpinBox()
        self.package_size_input.setRange(1, 9999)
        self.package_size_input.setValue(1)

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 10000000)
        self.cost_input.setPrefix("Rp ")
        self.cost_input.setGroupSeparatorShown(True)
        self.cost_input.setDecimals(0)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10000000)
        self.price_input.setPrefix("Rp ")
        self.price_input.setGroupSeparatorShown(True)
        self.price_input.setDecimals(0)
        
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 9999)
        self.min_stock_input.setValue(5)

        if self.data:
            self.name_input.setText(self.data.get('name', ''))
            self.unit_input.setCurrentText(self.data.get('unit', 'botol'))
            self.package_unit_input.setCurrentText(self.data.get('package_unit', ''))
            self.package_size_input.setValue(self.data.get('package_size', 1))
            self.cost_input.setValue(self.data.get('cost_price', 0))
            self.price_input.setValue(self.data.get('price', 0))
            self.stock_input.setValue(self.data.get('stock', 0))
            self.min_stock_input.setValue(self.data.get('min_stock', 5))

        form.addRow("Nama Herbal:", self.name_input)
        form.addRow("Satuan Dasar:", self.unit_input)
        form.addRow("Satuan Kemasan:", self.package_unit_input)
        form.addRow("Isi per Kemasan:", self.package_size_input)
        form.addRow("Harga Modal:", self.cost_input)
        form.addRow("Harga Jual:", self.price_input)
        form.addRow("Stok Awal:", self.stock_input)
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
            "unit": self.unit_input.currentText().strip(),
            "package_unit": self.package_unit_input.currentText().strip(),
            "package_size": self.package_size_input.value(),
            "cost_price": self.cost_input.value(),
            "price": self.price_input.value(),
            "stock": self.stock_input.value(),
            "min_stock": self.min_stock_input.value()
        }
