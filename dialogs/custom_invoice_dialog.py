from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt
from utils.styles import STYLES

class CustomInvoiceDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kustomisasi Cetak Invoice")
        self.setMinimumWidth(400)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        group = QGroupBox("Informasi Header & Footer")
        form = QFormLayout(group)
        
        self.clinic_name = QLineEdit(self.settings.get("clinic_name", "Klinik Bekam Sunnah Pro"))
        self.clinic_tagline = QLineEdit(self.settings.get("clinic_tagline", "Professional Cupping Therapy"))
        self.footer_msg = QLineEdit(self.settings.get("invoice_footer", "Semoga menjadi wasilah kesembuhan yang berkah."))
        self.admin_label = QLineEdit(self.settings.get("admin_label", "Admin Klinik,"))

        form.addRow("Nama Klinik:", self.clinic_name)
        form.addRow("Tagline:", self.clinic_tagline)
        form.addRow("Pesan Footer:", self.footer_msg)
        form.addRow("Label Admin:", self.admin_label)
        
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Simpan")
        save_btn.setStyleSheet(STYLES["add_button"])
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Batal")
        cancel_btn.setStyleSheet(STYLES["action_button"])
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "clinic_name": self.clinic_name.text(),
            "clinic_tagline": self.clinic_tagline.text(),
            "invoice_footer": self.footer_msg.text(),
            "admin_label": self.admin_label.text()
        }
