from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QSpinBox
)
from datetime import datetime
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import Qt, QRegularExpression
from utils.styles import STYLES

class VisitSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Kunjungan Pasien")
        self.parent = parent
        self.current_patient_gender = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        points_layout = QHBoxLayout()
        self.points_input = QSpinBox()
        self.points_input.setRange(1, 50)
        self.points_input.setValue(13)
        self.points_input.setSuffix(" titik")
        self.points_input.setFixedWidth(120)
        self.points_input.valueChanged.connect(self.update_price_from_points)
        points_layout.addWidget(QLabel("Jumlah Titik:"))
        points_layout.addWidget(self.points_input)
        points_layout.addStretch()
        
        price_layout = QHBoxLayout()
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Harga kunjungan (Rp)")
        self.price_input.setText("130000")
        self.price_input.setReadOnly(True)
        self.price_input.setFixedWidth(150)
        self.price_input.setStyleSheet("background-color: #f0f0f0;")
        price_layout.addWidget(QLabel("Harga Total:"))
        price_layout.addWidget(self.price_input)
        price_layout.addWidget(QLabel("(otomatis)"))
        price_layout.addStretch()
        
        therapist_layout = QHBoxLayout()
        self.therapist_combo = QComboBox()
        self.therapist_combo.setMinimumWidth(200)
        therapist_layout.addWidget(QLabel("Terapis:"))
        therapist_layout.addWidget(self.therapist_combo)
        therapist_layout.addStretch()
        
        self.visit_btn = QPushButton("Catat Kunjungan")
        self.visit_btn.setStyleSheet(STYLES["visit_button"])
        
        self.visit_table = QTableWidget(0, 5)
        self.visit_table.setHorizontalHeaderLabels(["Tanggal", "Terapis", "Titik", "Harga", "Diskon"])
        self.visit_table.setMinimumHeight(250)
        self.visit_table.setAlternatingRowColors(True)
        
        self.total_info_label = QLabel("Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0")
        self.total_info_label.setAlignment(Qt.AlignRight)
        self.total_info_label.setStyleSheet("font-weight: bold;")
        
        layout.addLayout(points_layout)
        layout.addLayout(price_layout)
        layout.addLayout(therapist_layout)
        layout.addWidget(self.visit_btn)
        layout.addWidget(self.visit_table)
        layout.addWidget(self.total_info_label)
        self.setLayout(layout)
    
    def update_price_from_points(self):
        if self.parent and hasattr(self.parent, 'settings'):
            point_count = self.points_input.value()
            price = self.parent.settings.calculate_price_from_points(point_count)
            self.price_input.setText(str(price))
    
    def set_patient_gender(self, gender):
        self.current_patient_gender = gender
        
    def load_therapists(self, therapists):
        self.therapist_combo.clear()
        self.therapist_combo.addItem("-- Pilih Terapis --", None)
        for therapist in therapists:
            gender_icon = "👨" if therapist.gender == "Laki-laki" else "👩"
            display_name = f"{gender_icon} {therapist.name}"
            if therapist.specialization:
                display_name += f" ({therapist.specialization})"
            self.therapist_combo.addItem(display_name, therapist.id)
    
    def get_selected_therapist_id(self):
        return self.therapist_combo.currentData()
        
    def load_visits(self, visits, therapists_dict=None):
        self.visit_table.setRowCount(len(visits))
        total = 0
        total_points = 0
        
        for row, visit in enumerate(visits):
            if isinstance(visit, dict):
                date = visit['date']
                price = visit['price']
                discount_applied = visit['discount_applied']
                point_count = visit.get('point_count', 0)
                therapist_id = visit.get('therapist_id')
            else:
                date = visit.date
                price = visit.price
                discount_applied = visit.discount_applied
                point_count = visit.point_count if hasattr(visit, 'point_count') else 0
                therapist_id = visit.therapist_id if hasattr(visit, 'therapist_id') else None

            if isinstance(date, str):
                date_obj = datetime.fromisoformat(date)
            else:
                date_obj = date
            date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            
            therapist_name = "-"
            if therapist_id and therapists_dict and therapist_id in therapists_dict:
                therapist_name = therapists_dict[therapist_id].name

            self.visit_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.visit_table.setItem(row, 1, QTableWidgetItem(therapist_name))
            self.visit_table.setItem(row, 2, QTableWidgetItem(f"{point_count}"))
            self.visit_table.setItem(row, 3, QTableWidgetItem(f"Rp {price:,}"))
            self.visit_table.setItem(row, 4, QTableWidgetItem("✅" if discount_applied else "-"))
            total += price
            total_points += point_count

        self.total_info_label.setText(f"Total kunjungan: {len(visits)} | Total titik: {total_points} | Total pemasukan: Rp {total:,}")
        
    def get_visit_price(self):
        try:
            return int(self.price_input.text())
        except ValueError:
            return None
    
    def get_point_count(self):
        return self.points_input.value()
