from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt
from datetime import datetime
from utils.styles import STYLES


class VisitSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Kunjungan Pasien")
        self.parent = parent
        self.current_patient_gender = None
        self.init_ui()

    # =========================
    # UI SETUP
    # =========================
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

        # ---- Button ----
        self.visit_btn = QPushButton("Catat Kunjungan")
        self.visit_btn.setStyleSheet(STYLES.get("visit_button", ""))

        # ---- Tabel Kunjungan ----
        self.visit_table = QTableWidget(0, 5)
        self.visit_table.setHorizontalHeaderLabels(
            ["Tanggal", "Terapis", "Titik", "Harga", "Diskon"]
        )
        self.visit_table.setMinimumHeight(300)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.visit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.visit_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.visit_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.visit_table.setShowGrid(False)
        self.visit_table.setFocusPolicy(Qt.NoFocus)
        
        # Style the table header and rows
        self.visit_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f2f6;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #3498db;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        header = self.visit_table.horizontalHeader()
        from PySide6.QtWidgets import QHeaderView
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

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
        layout.addWidget(self.visit_btn)
        layout.addWidget(self.visit_table)
        layout.addWidget(self.total_info_label)
        self.setLayout(layout)

        # Hitung harga awal
        self.update_price_from_points()

    # =========================
    # PRICE & DATA
    # =========================
    def update_price_from_points(self):
        """
        Update harga otomatis berdasarkan jumlah titik & settings
        """
        if self.parent and hasattr(self.parent, "settings"):
            point_count = self.points_input.value()
            price = self.parent.settings.calculate_price_from_points(point_count)
            self.price_input.setText(str(price))

    def get_point_count(self):
        return self.points_input.value()

    def get_visit_price(self):
        """
        Ambil harga final (sudah diskon)
        """
        try:
            return int(self.price_input.text())
        except ValueError:
            return 0

    # Alias untuk kompatibilitas MainWindow
    def get_current_price(self):
        return self.get_visit_price()

    # =========================
    # THERAPIST
    # =========================
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

    # =========================
    # VISIT TABLE
    # =========================
    def load_visits(self, visits, therapists_dict=None):
        self.visit_table.setRowCount(len(visits))

        total_price = 0
        total_points = 0

        for row, visit in enumerate(visits):
            # ... (data extraction logic)
            if isinstance(visit, dict):
                date = visit.get("date")
                price = visit.get("price", 0)
                discount_applied = visit.get("discount_applied", False)
                point_count = visit.get("point_count", 0)
                therapist_id = visit.get("therapist_id")
            else:
                date = visit.date
                price = visit.price
                discount_applied = visit.discount_applied
                point_count = getattr(visit, "point_count", 0)
                therapist_id = getattr(visit, "therapist_id", None)

            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            therapist_name = "-"
            if therapist_id and therapists_dict and therapist_id in therapists_dict:
                therapist_name = therapists_dict[therapist_id].name

            # Helper to create center-aligned items
            def create_centered_item(text):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                return item

            self.visit_table.setItem(row, 0, create_centered_item(date.strftime("%d/%m/%y %H:%M")))
            self.visit_table.setItem(row, 1, create_centered_item(therapist_name))
            self.visit_table.setItem(row, 2, create_centered_item(f"{point_count} pt"))
            
            price_item = create_centered_item(f"Rp {price:,}")
            price_item.setForeground(Qt.darkGreen)
            self.visit_table.setItem(row, 3, price_item)
            
            self.visit_table.setItem(row, 4, create_centered_item("🎁 Diskon" if discount_applied else "-"))
            
            self.visit_table.setRowHeight(row, 45)

            total_price += price
            total_points += point_count

        self.total_info_label.setText(
            f"Total kunjungan: {len(visits)} | "
            f"Total titik: {total_points} | "
            f"Total pemasukan: Rp {total_price:,}"
        )
