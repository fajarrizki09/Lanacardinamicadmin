from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QTextEdit
)
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression

class PatientForm(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Tambah Pasien")
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama pasien")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Nomor HP (kosongkan untuk no sementara)")
        
        self.name_input.setFixedWidth(200)
        self.phone_input.setFixedWidth(180)
        
        # Hapus validator ketat agar mendukung nomor sementara manual jika perlu atau dikosongkan
        # regex = QRegularExpression(r"^\d{10,15}$")
        # self.phone_input.setValidator(QRegularExpressionValidator(regex))
        
        row1.addWidget(QLabel("Nama:"))
        row1.addWidget(self.name_input)
        row1.addSpacing(10)
        row1.addWidget(QLabel("No HP:"))
        row1.addWidget(self.phone_input)
        row1.addStretch()
        
        row2 = QHBoxLayout()
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Laki-laki", "Perempuan"])
        self.gender_combo.setFixedWidth(150)
        
        row2.addWidget(QLabel("Jenis Kelamin:"))
        row2.addWidget(self.gender_combo)
        row2.addStretch()
        
        row3 = QHBoxLayout()
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Alamat lengkap...")
        self.address_input.setMaximumHeight(60)
        
        row3.addWidget(QLabel("Alamat:"))
        row3.addWidget(self.address_input)
        
        row4 = QHBoxLayout()
        self.add_btn = QPushButton("Tambah Pasien")
        self.add_btn.setToolTip("Tambah pasien baru ke database")
        row4.addStretch()
        row4.addWidget(self.add_btn)
        
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addLayout(row4)
        self.setLayout(layout)
        
    def get_inputs(self):
        return (
            self.name_input.text().strip(),
            self.phone_input.text().strip(),
            self.address_input.toPlainText().strip(),
            self.gender_combo.currentText()
        )
        
    def clear_inputs(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.gender_combo.setCurrentIndex(0)
