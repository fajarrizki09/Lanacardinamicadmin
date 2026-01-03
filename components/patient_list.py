from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem,
    QPushButton, QLineEdit
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
        layout = QVBoxLayout(self)

        # 🔍 Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari nama atau nomor HP...")
        search_layout.addWidget(self.search_input)

        # 📋 List pasien
        self.patient_list = QListWidget()
        self.patient_list.setMinimumHeight(300)
        self.patient_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.patient_list.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        item = self.patient_list.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Edit Pasien")
        delete_action = menu.addAction("🗑️ Hapus Pasien")
        
        action = menu.exec_(self.patient_list.mapToGlobal(pos))
        if action == edit_action:
            self.update_btn.click()
        elif action == delete_action:
            self.delete_btn.click()

        # 🔘 Tombol
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

    def update_list(self, patients_data):
        """
        patients_data:
        list of tuple -> (id, name, phone, gender, address, total_visits)
        """
        self.patient_list.clear()

        for patient_data in patients_data:
            if len(patient_data) < 3:
                continue

            patient_id = patient_data[0]
            name = patient_data[1]
            phone = patient_data[2]
            gender = patient_data[3] if len(patient_data) > 3 else ""
            address = patient_data[4] if len(patient_data) > 4 else ""
            # total_visits is at index 5
            total_visits = patient_data[5] if len(patient_data) > 5 else 0

            item = QListWidgetItem()
            widget = PatientItemWidget(
                name=name,
                phone=phone,
                total_visits=total_visits,
                gender=gender,
                address=address
            )

            item.setSizeHint(widget.sizeHint())

            # ⬅️ SIMPAN SEMUA DATA PASIEN
            item.setData(Qt.UserRole, patient_data)

            self.patient_list.addItem(item)
            self.patient_list.setItemWidget(item, widget)

    def get_selected_patient(self):
        item = self.patient_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None
