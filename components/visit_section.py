from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QSpinBox, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from datetime import datetime
from utils.styles import STYLES


class VisitSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Kunjungan Pasien")
        self.parent = parent
        self.current_patient_gender = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ---- Jumlah Titik ----
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

        # ---- Harga ----
        price_layout = QHBoxLayout()
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Harga kunjungan (Rp)")
        self.price_input.setText("0")
        self.price_input.setReadOnly(True)
        self.price_input.setFixedWidth(150)
        self.price_input.setStyleSheet("background-color: #f0f0f0;")

        price_layout.addWidget(QLabel("Harga Total:"))
        price_layout.addWidget(self.price_input)
        price_layout.addWidget(QLabel("(otomatis)"))
        price_layout.addStretch()

        # ---- Terapis ----
        therapist_layout = QHBoxLayout()
        self.therapist_combo = QComboBox()
        self.therapist_combo.setMinimumWidth(200)

        therapist_layout.addWidget(QLabel("Terapis:"))
        therapist_layout.addWidget(self.therapist_combo)
        therapist_layout.addStretch()

        # ---- Catatan Medis ----
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Catatan Perkembangan Medis:")
        notes_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.medical_notes_input = QLineEdit()
        self.medical_notes_input.setPlaceholderText("Contoh: Keluhan pusing berkurang, titik darah lancar...")
        self.medical_notes_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                color: #2c3e50;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f7fbff;
            }
        """)
        
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.medical_notes_input)

        # ---- Button ----
        self.visit_btn = QPushButton("Catat Kunjungan")
        self.visit_btn.setStyleSheet(STYLES.get("visit_button", ""))

        # ---- Tabel Kunjungan ----
        self.visit_table = QTableWidget(0, 6)
        self.visit_table.setHorizontalHeaderLabels(
            ["Tanggal", "Terapis", "Titik", "Harga", "Catatan Medis", "Diskon"]
        )
        self.visit_table.setMinimumHeight(350)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.visit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.visit_table.setShowGrid(False)
        self.visit_table.setFocusPolicy(Qt.NoFocus)
        self.visit_table.setFrameShape(QTableWidget.NoFrame)
        self.visit_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.visit_table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.visit_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 10px;
                selection-background-color: #f0f7ff;
                selection-color: #2c3e50;
                outline: none;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f5f8fa;
            }
            QTableWidget::item:selected {
                background-color: #eaf2f8;
                border-left: 3px solid #3498db;
            }
            QHeaderView::section {
                background-color: #fdfdfd;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #3498db;
                font-weight: bold;
                color: #2c3e50;
                font-size: 13px;
            }
        """)
        
        header = self.visit_table.horizontalHeader()
        from PySide6.QtWidgets import QHeaderView
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        
        self.visit_table.setColumnWidth(0, 150) # Tanggal
        self.visit_table.setColumnWidth(2, 80)  # Titik
        self.visit_table.setColumnWidth(3, 120) # Harga
        self.visit_table.setColumnWidth(5, 80)  # Diskon
        
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setMinimumSectionSize(100)

        # ---- Info Total ----
        self.total_info_label = QLabel(
            "Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0"
        )
        self.total_info_label.setAlignment(Qt.AlignRight)
        self.total_info_label.setStyleSheet("font-weight: bold;")

        # ---- Layout Assemble ----
        layout.addLayout(points_layout)
        layout.addLayout(price_layout)
        layout.addLayout(therapist_layout)
        layout.addLayout(notes_layout)
        layout.addSpacing(10)
        layout.addWidget(self.visit_btn)
        layout.addWidget(self.visit_table)
        layout.addWidget(self.total_info_label)
        self.setLayout(layout)

        self.update_price_from_points()

    def show_context_menu(self, pos):
        row = self.visit_table.rowAt(pos.y())
        if row < 0:
            return
            
        self.visit_table.selectRow(row)
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ Hapus Kunjungan")
        
        action = menu.exec_(self.visit_table.mapToGlobal(pos))
        if action == delete_action:
            self.delete_visit(row)

    def delete_visit(self, row):
        confirm = QMessageBox.question(
            self, "Hapus Kunjungan",
            "Yakin ingin menghapus data kunjungan ini?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.parent and hasattr(self.parent, "delete_visit_by_row"):
                self.parent.delete_visit_by_row(row)

    def update_price_from_points(self):
        if self.parent and hasattr(self.parent, "settings"):
            point_count = self.points_input.value()
            price = self.parent.settings.calculate_price_from_points(point_count)
            self.price_input.setText(str(price))

    def get_point_count(self):
        return self.points_input.value()

    def get_visit_price(self):
        try:
            return int(self.price_input.text())
        except ValueError:
            return 0

    def get_current_price(self):
        return self.get_visit_price()

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

    def get_medical_notes(self):
        return self.medical_notes_input.text().strip()

    def load_visits(self, visits, therapists_dict=None):
        self.visit_table.setRowCount(len(visits))
        total_price = 0
        total_points = 0

        for row, visit in enumerate(visits):
            if isinstance(visit, dict):
                v_date = visit.get("date")
                v_price = visit.get("price", 0)
                v_discount = visit.get("discount_applied", False)
                v_points = visit.get("point_count", 0)
                v_therapist_id = visit.get("therapist_id")
                v_notes = visit.get("medical_notes", "-")
            else:
                v_date = visit.date
                v_price = visit.price
                v_discount = visit.discount_applied
                v_points = getattr(visit, "point_count", 0)
                v_therapist_id = getattr(visit, "therapist_id", None)
                v_notes = getattr(visit, "medical_notes", "-")

            if isinstance(v_date, str):
                v_date = datetime.fromisoformat(v_date)

            therapist_name = "-"
            if v_therapist_id and therapists_dict and v_therapist_id in therapists_dict:
                therapist_name = therapists_dict[v_therapist_id].name

            def create_centered_item(text, is_bold=False, color=None):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                if is_bold:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if color:
                    item.setForeground(QBrush(QColor(color)))
                return item

            self.visit_table.setItem(row, 0, create_centered_item(v_date.strftime("%d/%m/%y %H:%M") if v_date else "-"))
            self.visit_table.setItem(row, 1, create_centered_item(therapist_name))
            self.visit_table.setItem(row, 2, create_centered_item(f"{v_points} pt"))
            
            self.visit_table.setItem(row, 3, create_centered_item(f"Rp {v_price:,}", is_bold=True, color="#27ae60"))

            notes_item = create_centered_item(v_notes if v_notes else "-")
            notes_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.visit_table.setItem(row, 4, notes_item)
            
            discount_color = "#e67e22" if v_discount else "#95a5a6"
            self.visit_table.setItem(row, 5, create_centered_item("🎁" if v_discount else "-", color=discount_color))
            self.visit_table.setRowHeight(row, 50)

            total_price += v_price
            total_points += v_points

        self.total_info_label.setText(
            f"Total kunjungan: {len(visits)} | "
            f"Total titik: {total_points} | "
            f"Total pemasukan: Rp {total_price:,}"
        )
