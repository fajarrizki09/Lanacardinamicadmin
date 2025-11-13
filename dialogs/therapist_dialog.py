from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QHeaderView
)
from PySide6.QtCore import Qt

class TherapistDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("👨‍⚕️ Kelola Terapis")
        self.resize(600, 500)
        self.init_ui()
        self.load_therapists()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama terapis")
        self.name_input.setFixedWidth(200)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Laki-laki", "Perempuan"])
        self.gender_combo.setFixedWidth(120)
        
        self.specialization_input = QLineEdit()
        self.specialization_input.setPlaceholderText("Spesialisasi (opsional)")
        self.specialization_input.setFixedWidth(150)
        
        self.add_btn = QPushButton("Tambah")
        self.add_btn.clicked.connect(self.add_therapist)
        
        form_layout.addWidget(QLabel("Nama:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Gender:"))
        form_layout.addWidget(self.gender_combo)
        form_layout.addWidget(QLabel("Spesialisasi:"))
        form_layout.addWidget(self.specialization_input)
        form_layout.addWidget(self.add_btn)
        form_layout.addStretch()
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nama", "Gender", "Spesialisasi", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Nonaktifkan")
        self.close_btn = QPushButton("Tutup")
        
        self.delete_btn.clicked.connect(self.deactivate_therapist)
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Daftar Terapis:"))
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        
    def load_therapists(self):
        therapists = self.db.get_all_therapists(active_only=False)
        self.table.setRowCount(len(therapists))
        
        for row, therapist in enumerate(therapists):
            gender_icon = "👨" if therapist.gender == "Laki-laki" else "👩"
            name_item = QTableWidgetItem(f"{gender_icon} {therapist.name}")
            name_item.setData(Qt.UserRole, therapist.id)
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(therapist.gender))
            self.table.setItem(row, 2, QTableWidgetItem(therapist.specialization))
            
            status = "✅ Aktif" if therapist.is_active else "❌ Nonaktif"
            self.table.setItem(row, 3, QTableWidgetItem(status))
    
    def add_therapist(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Nama terapis tidak boleh kosong")
            return
        
        gender = self.gender_combo.currentText()
        specialization = self.specialization_input.text().strip()
        
        try:
            self.db.add_therapist(name, gender, specialization)
            self.name_input.clear()
            self.specialization_input.clear()
            self.load_therapists()
            QMessageBox.information(self, "Berhasil", f"Terapis '{name}' berhasil ditambahkan!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menambahkan terapis:\n{str(e)}")
    
    def deactivate_therapist(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Pilih Terapis", "Silakan pilih terapis yang ingin dinonaktifkan")
            return
        
        therapist_id = self.table.item(selected_row, 0).data(Qt.UserRole)
        therapist_name = self.table.item(selected_row, 0).text()
        
        confirm = QMessageBox.question(
            self, "Konfirmasi",
            f"Nonaktifkan terapis '{therapist_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_therapist(therapist_id)
                self.load_therapists()
                QMessageBox.information(self, "Berhasil", "Terapis berhasil dinonaktifkan")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menonaktifkan terapis:\n{str(e)}")
