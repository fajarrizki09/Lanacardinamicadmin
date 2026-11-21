from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QFormLayout, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt
from utils.styles import STYLES
from viewmodels.settings_view_model import SettingsViewModel

class CustomInvoiceDialog(QDialog):
    def __init__(self, settings_source, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kustomisasi Cetak Invoice")
        self.setMinimumWidth(400)
        if isinstance(settings_source, SettingsViewModel):
            self.settings_vm = settings_source
        else:
            # Kompatibilitas constructor lama: CustomInvoiceDialog(settings, parent)
            self.settings_vm = SettingsViewModel(settings_source)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        group = QGroupBox("Informasi Header & Footer")
        form = QFormLayout(group)
        
        custom = self.settings_vm.get_custom_invoice_settings()
        self.clinic_name = QLineEdit(custom.get("clinic_name", "Klinik Bekam Sunnah Pro"))
        self.clinic_tagline = QLineEdit(custom.get("clinic_tagline", "Professional Cupping Therapy"))
        self.clinic_address = QLineEdit(custom.get("clinic_address", ""))
        self.clinic_phone = QLineEdit(custom.get("clinic_phone", ""))
        self.clinic_email = QLineEdit(custom.get("clinic_email", ""))
        self.clinic_website = QLineEdit(custom.get("clinic_website", ""))
        self.clinic_logo = QLineEdit(custom.get("clinic_logo_path", ""))
        self.footer_msg = QLineEdit(custom.get("invoice_footer", "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah."))
        self.admin_label = QLineEdit(custom.get("admin_label", "Admin Klinik,"))

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.clinic_logo, 1)
        logo_btn = QPushButton("Pilih")
        logo_btn.clicked.connect(self.choose_logo)
        logo_row.addWidget(logo_btn)

        form.addRow("Nama Klinik:", self.clinic_name)
        form.addRow("Tagline:", self.clinic_tagline)
        form.addRow("Alamat:", self.clinic_address)
        form.addRow("Kontak:", self.clinic_phone)
        form.addRow("Email:", self.clinic_email)
        form.addRow("Website:", self.clinic_website)
        form.addRow("Logo:", logo_row)
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

    def choose_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Logo Klinik",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.clinic_logo.setText(file_path)

    def get_data(self):
        return {
            "clinic_name": self.clinic_name.text(),
            "clinic_tagline": self.clinic_tagline.text(),
            "clinic_address": self.clinic_address.text(),
            "clinic_phone": self.clinic_phone.text(),
            "clinic_email": self.clinic_email.text(),
            "clinic_website": self.clinic_website.text(),
            "clinic_logo_path": self.clinic_logo.text(),
            "invoice_footer": self.footer_msg.text(),
            "admin_label": self.admin_label.text()
        }
