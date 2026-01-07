from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QSpinBox,
    QMessageBox, QMenu, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from datetime import datetime
from utils.styles import STYLES


class VisitSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.current_patient_gender = None
        self.init_ui()

    def init_ui(self):
        # ---- CARD STYLE ----
        self.setTitle("")
        self.setStyleSheet("""
        QGroupBox {
            background: #ffffff;
            border: 1px solid #e5eaf0;
            border-radius: 14px;
            margin-top: 10px;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # ================= TOP FORM ROW =================
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        # ---- Jumlah Titik ----
        points_layout = QHBoxLayout()
        self.points_input = QSpinBox()
        self.points_input.setRange(1, 50)
        self.points_input.setValue(13)
        self.points_input.setSuffix(" titik")
        self.points_input.setFixedWidth(120)
        self.points_input.valueChanged.connect(self.update_price_from_points)

        points_layout.addWidget(QLabel("Jumlah Titik"))
        points_layout.addWidget(self.points_input)

        # ---- Harga ----
        price_layout = QHBoxLayout()
        self.price_input = QLineEdit("0")
        self.price_input.setReadOnly(True)
        self.price_input.setFixedWidth(150)
        self.price_input.setStyleSheet("""
            QLineEdit {
                background: #f4f6f8;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        price_layout.addWidget(QLabel("Harga Total"))
        price_layout.addWidget(self.price_input)

        # ---- Terapis ----
        therapist_layout = QHBoxLayout()
        self.therapist_combo = QComboBox()
        self.therapist_combo.setMinimumWidth(220)

        therapist_layout.addWidget(QLabel("Terapis"))
        therapist_layout.addWidget(self.therapist_combo)

        top_row.addLayout(points_layout)
        top_row.addLayout(price_layout)
        top_row.addLayout(therapist_layout)
        top_row.addStretch()

        # ================= NOTES =================
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Catatan Perkembangan Medis")
        notes_label.setStyleSheet("font-weight: 600; color: #34495e;")

        self.medical_notes_input = QLineEdit()
        self.medical_notes_input.setPlaceholderText(
            "Contoh: Keluhan pusing berkurang, titik darah lancar..."
        )
        self.medical_notes_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ccd6dd;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background: #f7fbff;
            }
        """)

        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.medical_notes_input)

        # ================= BUTTON =================
        self.visit_btn = QPushButton("➕ Catat Kunjungan")
        self.visit_btn.setFixedHeight(42)
        self.visit_btn.setStyleSheet(STYLES.get("visit_button", ""))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.visit_btn)
        btn_layout.addStretch()

        # ================= TABLE =================
        self.visit_table = QTableWidget(0, 6)
        self.visit_table.setHorizontalHeaderLabels(
            ["Tanggal", "Terapis", "Titik", "Harga", "Catatan Medis", "Diskon"]
        )
        self.visit_table.setMinimumHeight(360)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.visit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.visit_table.setShowGrid(False)
        self.visit_table.setFocusPolicy(Qt.NoFocus)
        self.visit_table.setFrameShape(QTableWidget.NoFrame)
        self.visit_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.visit_table.customContextMenuRequested.connect(self.show_context_menu)
        self.visit_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.visit_table.verticalScrollBar().setSingleStep(20)

        self.visit_table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: 1px solid #e1e8ed;
                border-radius: 10px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f3f6;
            }
            QTableWidget::item:selected {
                background: #eef5ff;
                border-left: 3px solid #3498db;
            }
            QHeaderView::section {
                background: #f8fafc;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #d0d7de;
                font-weight: 600;
                font-size: 12px;
                color: #34495e;
            }
        """)

        header = self.visit_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignCenter)

        # ================= FOOTER =================
        self.total_info_label = QLabel(
            "Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0"
        )
        self.total_info_label.setAlignment(Qt.AlignRight)
        self.total_info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding-top: 6px;
                font-weight: 600;
            }
        """)

        # ================= ASSEMBLE =================
        layout.addLayout(top_row)
        layout.addLayout(notes_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.visit_table)
        layout.addWidget(self.total_info_label)

        self.update_price_from_points()

    # ================= LOGIC (UNCHANGED) =================

    def show_context_menu(self, pos):
        row = self.visit_table.rowAt(pos.y())
        if row < 0:
            return
        self.visit_table.selectRow(row)
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ Hapus Kunjungan")
        if menu.exec_(self.visit_table.mapToGlobal(pos)) == delete_action:
            self.delete_visit(row)

    def delete_visit(self, row):
        if QMessageBox.question(
            self, "Hapus Kunjungan",
            "Yakin ingin menghapus data kunjungan ini?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.parent and hasattr(self.parent, "delete_visit_by_row"):
                self.parent.delete_visit_by_row(row)

    def update_price_from_points(self):
        if self.parent and hasattr(self.parent, "settings"):
            price = self.parent.settings.calculate_price_from_points(
                self.points_input.value()
            )
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
        for t in therapists:
            icon = "👨" if t.gender == "Laki-laki" else "👩"
            name = f"{icon} {t.name}"
            if t.specialization:
                name += f" ({t.specialization})"
            self.therapist_combo.addItem(name, t.id)

    def get_selected_therapist_id(self):
        return self.therapist_combo.currentData()

    def get_medical_notes(self):
        return self.medical_notes_input.text().strip()

    def load_visits(self, visits, therapists_dict=None):
        self.visit_table.setRowCount(len(visits))
        total_price = total_points = 0

        for row, v in enumerate(visits):
            if isinstance(v, dict):
                date = v.get("date")
                price = v.get("price", 0)
                discount = v.get("discount_applied", False)
                points = v.get("point_count", 0)
                tid = v.get("therapist_id")
                notes = v.get("medical_notes", "-")
            else:
                date = v.date
                price = v.price
                discount = v.discount_applied
                points = getattr(v, "point_count", 0)
                tid = getattr(v, "therapist_id", None)
                notes = getattr(v, "medical_notes", "-")

            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            therapist = "-"
            if tid and therapists_dict and tid in therapists_dict:
                therapist = therapists_dict[tid].name

            def cell(text, align=Qt.AlignCenter, bold=False, color=None):
                i = QTableWidgetItem(str(text))
                i.setTextAlignment(align)
                if bold:
                    f = i.font()
                    f.setBold(True)
                    i.setFont(f)
                if color:
                    i.setForeground(QBrush(QColor(color)))
                return i

            self.visit_table.setItem(row, 0, cell(date.strftime("%d/%m/%y %H:%M")))
            self.visit_table.setItem(row, 1, cell(therapist))
            self.visit_table.setItem(row, 2, cell(f"{points} pt"))
            self.visit_table.setItem(row, 3, cell(f"Rp {price:,}", bold=True, color="#27ae60"))
            self.visit_table.setItem(row, 4, cell(notes, Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 5, cell("🎁" if discount else "-", color="#e67e22" if discount else "#95a5a6"))
            self.visit_table.setRowHeight(row, 42)

            total_price += price
            total_points += points

        self.total_info_label.setText(
            f"Total kunjungan: {len(visits)} | "
            f"Total titik: {total_points} | "
            f"Total pemasukan: Rp {total_price:,}"
        )
