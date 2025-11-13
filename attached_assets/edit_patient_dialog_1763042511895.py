from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QMenu, QComboBox, QTextEdit, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QPoint
from datetime import datetime
import re

class EditPatientDialog(QDialog):
    def __init__(self, patient, visits, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Edit Pasien & Riwayat")
        self.resize(600, 500)
        self.patient = patient
        self.visits = visits
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_group = QGroupBox("Data Pasien")
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit(self.patient.name)
        self.phone_input = QLineEdit(self.patient.phone)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Laki-laki", "Perempuan"])
        current_gender = self.patient.gender if hasattr(self.patient, 'gender') else 'Laki-laki'
        self.gender_combo.setCurrentText(current_gender)
        
        self.address_input = QTextEdit()
        address = self.patient.address if hasattr(self.patient, 'address') else ''
        self.address_input.setPlainText(address)
        self.address_input.setMaximumHeight(80)
        
        form_layout.addRow("Nama:", self.name_input)
        form_layout.addRow("Nomor HP:", self.phone_input)
        form_layout.addRow("Jenis Kelamin:", self.gender_combo)
        form_layout.addRow("Alamat:", self.address_input)
        
        form_group.setLayout(form_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tanggal", "Harga", "Diskon"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(200)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.load_table()
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Simpan")
        self.cancel_btn = QPushButton("❌ Batal")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(form_group)
        layout.addWidget(QLabel("Riwayat Kunjungan:"))
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)

    def load_table(self):
        self.visits.sort(key=lambda v: v['date'] if isinstance(v, dict) else v.date, reverse=True)
        self.table.setRowCount(len(self.visits))

        for row, visit in enumerate(self.visits):
            if isinstance(visit, dict):
                date = visit['date']
                price = visit['price']
                discount_applied = visit['discount_applied']
            else:
                date = visit.date
                price = visit.price
                discount_applied = visit.discount_applied
                
            if isinstance(date, str):
                date_obj = datetime.fromisoformat(date)
            else:
                date_obj = date
            date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            price_str = f"Rp {price:,}".replace(",", ".")
            discount_str = "✅" if discount_applied else "-"

            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(price_str))
            self.table.setItem(row, 2, QTableWidgetItem(discount_str))

    def delete_selected_visit(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.visits.pop(selected_row)
            self.load_table()

    def show_context_menu(self, pos: QPoint):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu()
        delete_action = menu.addAction("🗑️ Hapus Riwayat Ini")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == delete_action:
            self.delete_selected_visit()

    def get_data(self):
        new_name = self.name_input.text().strip()
        new_phone = self.phone_input.text().strip()
        new_gender = self.gender_combo.currentText()
        new_address = self.address_input.toPlainText().strip()
        
        updated_visits = []
        for row in range(self.table.rowCount()):
            date_item = self.table.item(row, 0)
            price_item = self.table.item(row, 1)
            discount_item = self.table.item(row, 2)

            if not all([date_item, price_item, discount_item]):
                continue

            date_str = date_item.text().strip()
            price_str = re.sub(r"[^\d]", "", price_item.text())
            discount_str = discount_item.text().strip()

            try:
                if isinstance(self.visits[row], dict):
                    visit_data = {
                        'id': self.visits[row].get('id'),
                        'date': datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"),
                        'price': int(price_str),
                        'discount_applied': discount_str in ["✅", "Y", "YES", "TRUE", "1"]
                    }
                    updated_visits.append(visit_data)
            except Exception as e:
                print(f"Gagal parsing row {row}: {e}")

        return new_name, new_phone, new_address, new_gender, updated_visits
