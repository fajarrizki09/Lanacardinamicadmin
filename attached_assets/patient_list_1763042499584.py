from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLineEdit, QLabel
)
from PySide6.QtCore import Qt
from components.patient_item_widget import PatientItemWidget
from utils.styles import STYLES

class PatientList(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Daftar Pasien")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari nama atau nomor HP...")
        search_layout.addWidget(self.search_input)
        
        self.patient_list = QListWidget()
        self.patient_list.setMinimumHeight(300)
        
        button_layout = QHBoxLayout()
        self.update_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Hapus")
        
        self.update_btn.setStyleSheet(STYLES["update_button"])
        self.delete_btn.setStyleSheet(STYLES["delete_button"])
        
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(search_layout)
        layout.addWidget(self.patient_list)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def update_list(self, patients_data):
        self.patient_list.clear()
        for patient_data in patients_data:
            if len(patient_data) >= 3:
                patient_id, name, phone = patient_data[:3]
                gender = patient_data[3] if len(patient_data) > 3 else ''
                total_visits = 0
                
                item = QListWidgetItem()
                widget = PatientItemWidget(name, phone, total_visits, gender)
                item.setSizeHint(widget.sizeHint())
                item.setData(Qt.UserRole, patient_data)
                self.patient_list.addItem(item)
                self.patient_list.setItemWidget(item, widget)

    def get_selected_patient(self):
        current_item = self.patient_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
