from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from utils.styles import STYLES
from datetime import datetime
from viewmodels.settings_view_model import SettingsViewModel
import os

class InvoiceDialog(QDialog):
    def __init__(self, patient_name, visit_date, points, price, therapist_name,
                 settings_source=None, parent=None, discount_rule_name=None, service_name="Bekam"):
        super().__init__(parent)
        self.setWindowTitle(f"Invoice - {patient_name}")
        self.setMinimumSize(450, 600)
        self.patient_name = patient_name
        self.visit_date = visit_date
        self.points = points
        self.price = float(price or 0)
        self.therapist_name = therapist_name
        self.discount_rule_name = discount_rule_name
        self.service_name = service_name or "Bekam"
        if isinstance(settings_source, SettingsViewModel):
            self.settings_vm = settings_source
        elif settings_source:
            # Kompatibilitas constructor lama: InvoiceDialog(..., settings, parent)
            self.settings_vm = SettingsViewModel(settings_source)
        else:
            self.settings_vm = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.setStyleSheet("background-color: white; color: #2c3e50;")

        custom = self.settings_vm.get_custom_invoice_settings() if self.settings_vm else {
            "clinic_name": "Klinik Bekam Sunnah Pro",
            "clinic_tagline": "Professional Cupping Therapy",
            "clinic_address": "",
            "clinic_phone": "",
            "clinic_email": "",
            "clinic_website": "",
            "clinic_logo_path": "",
            "invoice_footer": "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah.",
            "admin_label": "Admin Klinik,"
        }

        # Header Container
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        logo_path = custom.get("clinic_logo_path", "")
        if logo_path and os.path.exists(logo_path):
            logo = QLabel()
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo.setPixmap(pixmap.scaled(160, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                logo.setAlignment(Qt.AlignCenter)
                header_layout.addWidget(logo)
        
        title = QLabel(custom.get("clinic_name", "INVOICE LAYANAN BEKAM").upper())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; margin-bottom: 5px;")
        
        subtitle = QLabel(custom.get("clinic_tagline", ""))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d;")

        details = " | ".join([
            value for value in [
                custom.get("clinic_address", ""),
                custom.get("clinic_phone", ""),
                custom.get("clinic_email", ""),
                custom.get("clinic_website", ""),
            ] if value
        ])
        details_lbl = QLabel(details)
        details_lbl.setAlignment(Qt.AlignCenter)
        details_lbl.setWordWrap(True)
        details_lbl.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #ecf0f1; border: 1px solid #ecf0f1;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        if details:
            header_layout.addWidget(details_lbl)
        header_layout.addWidget(line)
        layout.addWidget(header_frame)

        # Info Section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        patient_lbl = QLabel(f"<b>Kepada:</b> {self.patient_name}")
        date_lbl = QLabel(f"<b>Tanggal:</b> {self.visit_date}")
        patient_lbl.setStyleSheet("font-size: 14px;")
        date_lbl.setStyleSheet("font-size: 14px;")
        
        info_layout.addWidget(patient_lbl)
        info_layout.addWidget(date_lbl)
        layout.addLayout(info_layout)

        # Table Section
        self.table = QTableWidget(3 if self.discount_rule_name else 2, 2)
        self.table.setHorizontalHeaderLabels(["Deskripsi", "Detail"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ecf0f1;
                gridline-color: #ecf0f1;
                font-size: 13px;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #f9f9f9;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #ecf0f1;
                font-weight: bold;
            }
        """)
        self.table.setFixedHeight(120)

        self.table.setItem(0, 0, QTableWidgetItem(self.service_name))
        self.table.setItem(0, 1, QTableWidgetItem(str(self.points)))
        self.table.setItem(1, 0, QTableWidgetItem("Terapis"))
        self.table.setItem(1, 1, QTableWidgetItem(self.therapist_name))
        if self.discount_rule_name:
            self.table.setItem(2, 0, QTableWidgetItem("Diskon"))
            self.table.setItem(2, 1, QTableWidgetItem(self.discount_rule_name))
        
        for r in range(self.table.rowCount()):
            for c in range(2):
                if self.table.item(r, c):
                    self.table.item(r, c).setTextAlignment(Qt.AlignVCenter)

        layout.addWidget(self.table)

        # Total Section
        total_frame = QFrame()
        total_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 15px;")
        total_layout = QHBoxLayout(total_frame)
        
        total_lbl = QLabel("TOTAL PEMBAYARAN")
        total_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        
        amount_lbl = QLabel(f"Rp {self.price:,.0f}")
        amount_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60;")
        
        total_layout.addWidget(total_lbl)
        total_layout.addStretch()
        total_layout.addWidget(amount_lbl)
        layout.addWidget(total_frame)

        # Footer
        footer = QLabel(custom.get("invoice_footer", ""))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 11px; color: #95a5a6; font-style: italic; margin-top: 20px;")
        layout.addWidget(footer)

        # Buttons
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Tutup")
        close_btn.setStyleSheet(STYLES["action_button"])
        close_btn.clicked.connect(self.accept)
        
        print_btn = QPushButton("Cetak PDF")
        print_btn.setStyleSheet(STYLES["add_button"])
        print_btn.clicked.connect(self.on_print)
        
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(print_btn)
        layout.addLayout(btn_layout)

    def on_print(self):
        from helpers.license import is_license_invalid
        if is_license_invalid():
            return

        # Optional: still provide PDF if user wants to print
        from helpers.invoice_helper import InvoiceHelper
        helper = InvoiceHelper()
        custom = self.settings_vm.get_custom_invoice_settings() if self.settings_vm else None
        path = helper.generate_invoice(
            self.patient_name, self.visit_date, 
            self.points, self.price, self.therapist_name,
            custom_settings=custom,
            discount_rule_name=self.discount_rule_name,
            service_name=self.service_name
        )
        import os
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
