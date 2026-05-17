from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class PatientItemWidget(QWidget):
    def __init__(self, name, phone, total_visits, gender='', address='', parent=None):
        super().__init__(parent)
        self.name = name
        self.phone = phone
        self.total_visits = total_visits
        self.gender = gender
        self.address = address
        self.name_label = QLabel()
        self.phone_label = QLabel()
        self.address_label = QLabel()
        self.visit_label = QLabel()
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        
        gender_icon = "👨" if self.gender == "Laki-laki" else "👩" if self.gender == "Perempuan" else ""
        self.name_label.setText(f"<b>{gender_icon} {self.name}</b>")
        self.phone_label.setText(f"📱 {self.phone}")
        self.address_label.setText(f"🏠 {self.address if self.address else '-'}")
        self.address_label.setWordWrap(True)
        self.visit_label.setText(f"🩺 Kunjungan: {self.total_visits}x")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.phone_label)
        layout.addWidget(self.address_label)
        layout.addWidget(self.visit_label)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)

        self.setStyleSheet("""
            PatientItemWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 4px;
                padding: 4px;
                background: #f9f9f9;
            }
            PatientItemWidget:hover {
                background: #e3f2fd;
                border: 1px solid #2196F3;
            }
        """)
