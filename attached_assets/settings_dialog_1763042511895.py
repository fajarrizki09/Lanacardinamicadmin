from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QGroupBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("⚙️ Pengaturan Aplikasi")
        self.resize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        price_group = QGroupBox("Harga")
        price_layout = QFormLayout()
        
        self.base_price_input = QSpinBox()
        self.base_price_input.setRange(0, 10000000)
        self.base_price_input.setValue(self.settings.get_base_price())
        self.base_price_input.setSingleStep(10000)
        self.base_price_input.setPrefix("Rp ")
        price_layout.addRow("Harga Dasar:", self.base_price_input)
        price_group.setLayout(price_layout)
        
        discount_group = QGroupBox("Pengaturan Diskon")
        discount_layout = QFormLayout()
        
        self.discount_percentage_input = QSpinBox()
        self.discount_percentage_input.setRange(0, 100)
        self.discount_percentage_input.setValue(self.settings.get_discount_percentage())
        self.discount_percentage_input.setSuffix(" %")
        discount_layout.addRow("Persentase Diskon:", self.discount_percentage_input)
        
        self.min_visits_input = QSpinBox()
        self.min_visits_input.setRange(1, 100)
        self.min_visits_input.setValue(self.settings.get_min_visits_for_discount())
        self.min_visits_input.setSuffix(" kunjungan")
        discount_layout.addRow("Minimum Kunjungan:", self.min_visits_input)
        
        discount_group.setLayout(discount_layout)
        
        info_label = QLabel(
            "💡 <i>Pasien akan mendapat diskon otomatis setelah mencapai jumlah kunjungan minimum.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px;")
        
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Simpan")
        self.cancel_btn = QPushButton("Batal")
        
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(price_group)
        layout.addWidget(discount_group)
        layout.addWidget(info_label)
        layout.addLayout(button_layout)
        
    def save_settings(self):
        self.settings.set_base_price(self.base_price_input.value())
        self.settings.set_discount_percentage(self.discount_percentage_input.value())
        self.settings.set_min_visits_for_discount(self.min_visits_input.value())
        
        QMessageBox.information(
            self, "Berhasil", 
            "Pengaturan berhasil disimpan!\nPerubahan akan diterapkan pada kunjungan berikutnya."
        )
        self.accept()
