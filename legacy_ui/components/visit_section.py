from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QSpinBox, QMessageBox, QMenu, QCheckBox,
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
        self.services = []
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

        self.service_combo = QComboBox()
        self.service_combo.setFixedSize(220, field_h)
        self.service_combo.setStyleSheet(STYLES["search_input"])
        self.service_combo.currentIndexChanged.connect(self.on_service_changed)

        price_layout = QHBoxLayout()
        price_layout.setSpacing(5)
        
        self.price_input = QLineEdit("0")
        self.price_input.setReadOnly(True)
        self.price_input.setFixedSize(160, field_h)
        self.price_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.price_input.setStyleSheet(STYLES["search_input"])

        self.edit_price_btn = QPushButton("✏️")
        self.edit_price_btn.setFixedSize(34, field_h)
        self.edit_price_btn.setCheckable(True)
        self.edit_price_btn.setToolTip("Edit Harga Manual")
        self.edit_price_btn.setStyleSheet("""
            QPushButton { background: #f1f2f6; border: 1px solid #dcdde1; border-radius: 4px; }
            QPushButton:checked { background: #3498db; color: white; border-color: #2980b9; }
        """)
        self.edit_price_btn.toggled.connect(self.toggle_manual_price)

        price_layout.addWidget(self.price_input)
        price_layout.addWidget(self.edit_price_btn)

        self.therapist_combo = QComboBox()
        self.therapist_combo.setFixedSize(220, field_h)
        self.therapist_combo.setStyleSheet(STYLES["search_input"])

        self.free_visit_checkbox = QCheckBox("Kunjungan gratis")
        self.free_visit_checkbox.setToolTip("Tandai jika harga manual 0 memang kunjungan gratis.")
        self.free_visit_checkbox.setStyleSheet("font-size:12px;color:#2c3e50;")

        self.free_reason_combo = QComboBox()
        self.free_reason_combo.setFixedSize(160, field_h)
        self.free_reason_combo.setStyleSheet(STYLES["search_input"])
        self.free_reason_combo.addItems([
            "promo",
            "keluarga",
            "koreksi",
            "gratis lain-lain",
        ])
        self.free_reason_combo.setEnabled(False)
        self.free_visit_checkbox.toggled.connect(self.free_reason_combo.setEnabled)

        self.voucher_input = QLineEdit()
        self.voucher_input.setFixedSize(140, field_h)
        self.voucher_input.setPlaceholderText("Opsional")
        self.voucher_input.setStyleSheet(STYLES["search_input"])

        self.quantity_label = make_label("Jumlah Titik")
        grid.addWidget(make_label("Layanan"), 0, 0)
        grid.addWidget(self.quantity_label, 0, 1)
        grid.addWidget(make_label("Harga Total"), 0, 2)
        grid.addWidget(make_label("Terapis"), 0, 3)
        grid.addWidget(make_label("Gratis"), 0, 4)
        grid.addWidget(make_label("Voucher"), 0, 5)
        grid.addWidget(self.service_combo, 1, 0)
        grid.addWidget(self.points_input, 1, 1)
        grid.addLayout(price_layout, 1, 2)
        grid.addWidget(self.therapist_combo, 1, 3)
        free_layout = QHBoxLayout()
        free_layout.setSpacing(8)
        free_layout.addWidget(self.free_visit_checkbox)
        free_layout.addWidget(self.free_reason_combo)
        free_layout.addStretch()
        grid.addLayout(free_layout, 1, 4)
        grid.addWidget(self.voucher_input, 1, 5)
        grid.setColumnStretch(6, 1)

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

        self.visit_table = QTableWidget(0, 7)
        self.visit_table.setHorizontalHeaderLabels(
            ["Tanggal", "Layanan", "Terapis", "Satuan", "Harga", "Catatan Medis", "Diskon"]
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
        header.resizeSection(1, 130)
        header.resizeSection(3, 70)
        header.resizeSection(4, 120)
        header.resizeSection(6, 60)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

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

    def toggle_manual_price(self, checked):
        self.price_input.setReadOnly(not checked)
        if checked:
            self.price_input.setStyleSheet(STYLES["search_input"] + "border: 1px solid #3498db; background: #fff;")
            self.price_input.setFocus()
            self.price_input.selectAll()
        else:
            self.price_input.setStyleSheet(STYLES["search_input"])
            self.update_price_from_points()

    def update_price_from_points(self):
        if self.edit_price_btn.isChecked():
            return

        service = self.get_selected_service()
        if service and getattr(service, "name", "").lower() != "bekam":
            price = float(service.price_per_unit or 0) * self.points_input.value()
            self.price_input.setText(f"{price:,.0f}")
            return

        settings_source = None
        if self.parent and hasattr(self.parent, "settings_vm"):
            settings_source = self.parent.settings_vm
        elif self.parent and hasattr(self.parent, "settings"):
            # Fallback kompatibilitas untuk parent lama yang belum punya SettingsViewModel.
            settings_source = self.parent.settings

        if settings_source:
            price = settings_source.calculate_price_from_points(self.points_input.value())
            self.price_input.setText(f"{price:,}")

    def is_manual_price(self):
        return self.edit_price_btn.isChecked()

    def get_point_count(self):
        return self.points_input.value()

    def load_services(self, services):
        self.services = list(services or [])
        self.service_combo.blockSignals(True)
        self.service_combo.clear()
        for service in self.services:
            self.service_combo.addItem(service.name, service)
        self.service_combo.blockSignals(False)
        self.on_service_changed()

    def get_selected_service(self):
        return self.service_combo.currentData()

    def get_selected_service_id(self):
        service = self.get_selected_service()
        return getattr(service, "id", None) if service else None

    def get_selected_service_name(self):
        service = self.get_selected_service()
        return getattr(service, "name", "Bekam") if service else "Bekam"

    def on_service_changed(self):
        service = self.get_selected_service()
        if not service:
            self.quantity_label.setText("Jumlah")
            self.points_input.setSuffix("")
            self.points_input.setValue(1)
            self.medical_notes_input.setPlaceholderText("Catatan perkembangan medis")
            self.update_price_from_points()
            return

        unit_label = getattr(service, "unit_label", "sesi") or "sesi"
        default_quantity = max(1, int(getattr(service, "default_quantity", 1) or 1))
        self.quantity_label.setText(f"Jumlah {unit_label.title()}")
        self.points_input.setSuffix(f" {unit_label}")
        self.points_input.setValue(default_quantity)
        template = getattr(service, "notes_template", "") or "Catatan perkembangan medis"
        self.medical_notes_input.setPlaceholderText(template)
        self.update_price_from_points()

    def get_current_price(self):
        value = self.parse_current_price()
        return value if value is not None else 0

    def parse_current_price(self):
        text = self.price_input.text().strip().replace(",", "")
        if text == "":
            return None
        try:
            return int(text)
        except ValueError:
            return None

    def is_free_visit(self):
        return self.free_visit_checkbox.isChecked()

    def get_free_visit_reason(self):
        if not self.is_free_visit():
            return None
        return self.free_reason_combo.currentText().strip() or "gratis lain-lain"

    def get_voucher_code(self):
        return self.voucher_input.text().strip()

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
            price = float(price or 0)
            points = v.get("point_count", 0) if is_dict else getattr(v, "point_count", 0)
            discount = v.get("discount_applied", False) if is_dict else getattr(v, "discount_applied", False)
            tid = v.get("therapist_id") if is_dict else getattr(v, "therapist_id", None)
            service_name = v.get("service_name", "Bekam") if is_dict else getattr(v, "service_name", "Bekam")
            notes = v.get("medical_notes", "-") if is_dict else getattr(v, "medical_notes", "-")
            is_free = v.get("is_free_visit", False) if is_dict else getattr(v, "is_free_visit", False)
            free_reason = v.get("free_visit_reason") if is_dict else getattr(v, "free_visit_reason", None)
            discount_rule_name = v.get("discount_rule_name") if is_dict else getattr(v, "discount_rule_name", None)

            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            therapist_name = "-"
            if therapists_dict and tid in therapists_dict:
                therapist_name = therapists_dict[tid].name

            self.visit_table.setItem(row, 0, make_item(date.strftime("%d/%m/%y %H:%M"), Qt.AlignCenter))
            self.visit_table.setItem(row, 1, make_item(service_name or "Bekam", Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 2, make_item(therapist_name, Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 3, make_item(str(points), Qt.AlignCenter))
            self.visit_table.setItem(
                row, 4,
                make_item(f"Rp {price:,}", Qt.AlignRight | Qt.AlignVCenter, True, "#27ae60")
            )
            if is_free and free_reason:
                notes = f"{notes} | Gratis: {free_reason}" if notes and notes != "-" else f"Gratis: {free_reason}"
            if discount_rule_name:
                notes = f"{notes} | Diskon: {discount_rule_name}" if notes and notes != "-" else f"Diskon: {discount_rule_name}"
            self.visit_table.setItem(row, 5, make_item(notes, Qt.AlignLeft | Qt.AlignVCenter))
            self.visit_table.setItem(row, 6, make_item("DISKON" if discount else "-", Qt.AlignCenter))

            total_price += price
            total_points += points

        self.total_info_label.setText(
            f"Total kunjungan: {len(visits)} | "
            f"Total satuan: {total_points} | "
            f"Total pemasukan: Rp {total_price:,}"
        )
