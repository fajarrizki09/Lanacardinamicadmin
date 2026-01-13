from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QSpinBox, QMessageBox, QMenu,
    QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from datetime import datetime
from utils.styles import STYLES


class VisitSection(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_patient_gender = None
        self.init_ui()

    # =====================================================
    # UI
    # =====================================================
    def init_ui(self):
        self.setTitle("")
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ================= CARD FORM =================
        form_card = QFrame()
        form_card.setStyleSheet(STYLES["card"])
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(10)

        title = QLabel("📝 Catat Kunjungan")
        title.setStyleSheet("font-size:15px;font-weight:700;color:#2c3e50;")
        form_layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)

        label_style = STYLES["transaction_label"] + "font-size:13px;"

        def make_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(label_style)
            return lbl

        field_h = 34

        # ================= INPUT =================
        self.points_input = QSpinBox()
        self.points_input.setRange(1, 50)
        self.points_input.setValue(13)
        self.points_input.setSuffix(" titik")
        self.points_input.setFixedSize(140, field_h)
        self.points_input.valueChanged.connect(self.update_price_from_points)

        self.price_input = QLineEdit("0")
        self.price_input.setReadOnly(True)
        self.price_input.setFixedSize(200, field_h)
        self.price_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.price_input.setStyleSheet(STYLES["search_input"])

        self.therapist_combo = QComboBox()
        self.therapist_combo.setFixedSize(220, field_h)
        self.therapist_combo.setStyleSheet(STYLES["search_input"])

        grid.addWidget(make_label("Jumlah Titik"), 0, 0)
        grid.addWidget(make_label("Harga Total"), 0, 1)
        grid.addWidget(make_label("Terapis"), 0, 2)
        grid.addWidget(self.points_input, 1, 0)
        grid.addWidget(self.price_input, 1, 1)
        grid.addWidget(self.therapist_combo, 1, 2)
        grid.setColumnStretch(3, 1)

        form_layout.addLayout(grid)

        # ================= NOTES + BUTTON =================
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        notes_col = QVBoxLayout()
        notes_label = QLabel("Catatan Perkembangan Medis")
        notes_label.setStyleSheet(label_style)

        self.medical_notes_input = QLineEdit()
        self.medical_notes_input.setPlaceholderText(
            "Contoh: Keluhan pusing berkurang, titik darah lancar..."
        )
        self.medical_notes_input.setFixedHeight(field_h)
        self.medical_notes_input.setStyleSheet(STYLES["search_input"])

        notes_col.addWidget(notes_label)
        notes_col.addWidget(self.medical_notes_input)

        self.visit_btn = QPushButton("➕ Catat Kunjungan")
        self.visit_btn.setFixedSize(140, field_h)
        self.visit_btn.setStyleSheet(STYLES["visit_button_compact"])

        bottom.addLayout(notes_col, 1)
        bottom.addWidget(self.visit_btn, 0, Qt.AlignBottom)

        form_layout.addLayout(bottom)

        # ================= CARD TABLE =================
        table_card = QFrame()
        table_card.setStyleSheet(STYLES["card"])
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(6)

        header_lbl = QLabel("📊 Riwayat Kunjungan")
        header_lbl.setStyleSheet("font-size:15px;font-weight:700;color:#2c3e50;")
        table_layout.addWidget(header_lbl)

        self.visit_table = QTableWidget(0, 6)
        self.visit_table.setHorizontalHeaderLabels(
            ["Tanggal", "Terapis", "Titik", "Harga", "Catatan Medis", "Diskon"]
        )

        self.visit_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            QHeaderView::section {
                background: #f4f6f8;
                color: #2c3e50;
                font-weight: 600;
                padding: 6px;
                border: none;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)

        header = self.visit_table.horizontalHeader()
        header.setMinimumHeight(36)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(QHeaderView.Fixed)

        header.resizeSection(0, 140)
        header.resizeSection(2, 70)
        header.resizeSection(3, 120)
        header.resizeSection(5, 60)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.visit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.visit_table.setShowGrid(False)
        self.visit_table.setMinimumHeight(320)

        self.visit_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.visit_table.customContextMenuRequested.connect(self.show_context_menu)

        table_layout.addWidget(self.visit_table)

        self.total_info_label = QLabel(
            "Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0"
        )
        self.total_info_label.setAlignment(Qt.AlignRight)
        self.total_info_label.setStyleSheet("font-weight:600;font-size:12px;")
        table_layout.addWidget(self.total_info_label)

        root.addWidget(form_card)
        root.addWidget(table_card)

        self.update_price_from_points()

    # =====================================================
    # LOGIC
    # =====================================================
    def show_context_menu(self, pos):
        row = self.visit_table.rowAt(pos.y())
        if row < 0:
            return

        self.visit_table.selectRow(row)
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ Hapus Kunjungan")

        if menu.exec(self.visit_table.mapToGlobal(pos)) == delete_action:
            self.delete_visit(row)

    def delete_visit(self, row):
        if QMessageBox.question(
            self,
            "Hapus Kunjungan",
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
            self.price_input.setText(f"{price:,}")

    def get_point_count(self):
        return self.points_input.value()

    def get_current_price(self):
        try:
            return int(self.price_input.text().replace(",", ""))
        except ValueError:
            return 0

    def set_patient_gender(self, gender):
        self.current_patient_gender = gender

    def load_therapists(self, therapists):
        self.therapist_combo.clear()
        self.therapist_combo.addItem("-- Pilih Terapis --", None)

        for t in therapists:
            icon = "👨" if getattr(t, "gender", "") == "Laki-laki" else "👩"
            name = f"{icon} {t.name}"
            if getattr(t, "specialization", None):
                name += f" ({t.specialization})"
            self.therapist_combo.addItem(name, t.id)

    def get_selected_therapist_id(self):
        return self.therapist_combo.currentData()

    def get_medical_notes(self):
        return self.medical_notes_input.text().strip()

    def load_visits(self, visits, therapists_dict=None):
        self.visit_table.setRowCount(len(visits))
        total_price = 0
        total_points = 0

        def make_item(text, align, bold=False, color=None):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(align)
            if bold:
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            if color:
                item.setForeground(QBrush(QColor(color)))
            return item

        for row, v in enumerate(visits):
            is_dict = isinstance(v, dict)

            date = v.get("date") if is_dict else v.date
            price = v.get("price", 0) if is_dict else v.price
            points = v.get("point_count", 0) if is_dict else getattr(v, "point_count", 0)
            discount = v.get("discount_applied", False) if is_dict else getattr(v, "discount_applied", False)
            tid = v.get("therapist_id") if is_dict else getattr(v, "therapist_id", None)
            notes = v.get("medical_notes", "-") if is_dict else getattr(v, "medical_notes", "-")

            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            therapist_name = "-"
            if therapists_dict and tid in therapists_dict:
                therapist_name = therapists_dict[tid].name

            self.visit_table.setItem(row, 0, make_item(date.strftime("%d/%m/%y %H:%M"), Qt.AlignCenter))
            self.visit_table.setItem(row, 1, make_item(therapist_name, Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 2, make_item(f"{points} pt", Qt.AlignCenter))
            self.visit_table.setItem(
                row, 3,
                make_item(f"Rp {price:,}", Qt.AlignRight | Qt.AlignVCenter, True, "#27ae60")
            )
            self.visit_table.setItem(row, 4, make_item(notes, Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 5, make_item("🎁" if discount else "-", Qt.AlignCenter))

            total_price += price
            total_points += points

        self.total_info_label.setText(
            f"Total kunjungan: {len(visits)} | "
            f"Total titik: {total_points} | "
            f"Total pemasukan: Rp {total_price:,}"
        )
