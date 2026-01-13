from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from utils.styles import STYLES


class TherapistDialog(QDialog):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model

        self.setWindowTitle("👨‍⚕️ Kelola Terapis")
        self.resize(840, 540)
        self.setStyleSheet(STYLES.get("main_window", ""))

        self.init_ui()
        self.bind_signals()
        self.load_therapists()

    # ================= UI =================

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(12)

        # =====================================================
        # LEFT PANEL – FORM
        # =====================================================
        left_panel = QFrame()
        left_panel.setStyleSheet(STYLES["card"])
        left_panel.setFixedWidth(280)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        title = QLabel("➕ Tambah Terapis")
        title.setStyleSheet(STYLES["inventory_header"])
        left_layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama terapis")
        self.name_input.setStyleSheet(STYLES["search_input"])

        self.gender_combo = QComboBox()
        self.gender_combo.setStyleSheet(STYLES["search_input"])
        self.gender_combo.addItems(["Laki-laki", "Perempuan"])

        self.specialization_input = QLineEdit()
        self.specialization_input.setPlaceholderText("Spesialisasi (opsional)")
        self.specialization_input.setStyleSheet(STYLES["search_input"])

        self.add_btn = QPushButton("➕ Tambah Terapis")
        self.add_btn.setStyleSheet(STYLES["add_button"])
        self.add_btn.clicked.connect(self.on_add_clicked)

        left_layout.addWidget(QLabel("Nama"))
        left_layout.addWidget(self.name_input)
        left_layout.addWidget(QLabel("Gender"))
        left_layout.addWidget(self.gender_combo)
        left_layout.addWidget(QLabel("Spesialisasi"))
        left_layout.addWidget(self.specialization_input)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.add_btn)
        left_layout.addStretch()

        # =====================================================
        # RIGHT PANEL – TABLE
        # =====================================================
        right_panel = QFrame()
        right_panel.setStyleSheet(STYLES["card"])
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)

        header = QLabel("📋 Daftar Terapis")
        header.setStyleSheet(STYLES["inventory_header"])
        right_layout.addWidget(header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Nama", "Gender", "Spesialisasi", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        right_layout.addWidget(self.table)

        # ---------- ACTION BAR ----------
        action_bar = QHBoxLayout()

        self.deactivate_btn = QPushButton("🛑 Nonaktifkan")
        self.deactivate_btn.setStyleSheet(STYLES["delete_button"])
        self.deactivate_btn.clicked.connect(self.on_deactivate_clicked)

        self.close_btn = QPushButton("Tutup")
        self.close_btn.setStyleSheet(STYLES["action_button"])
        self.close_btn.clicked.connect(self.accept)

        action_bar.addStretch()
        action_bar.addWidget(self.deactivate_btn)
        action_bar.addWidget(self.close_btn)

        right_layout.addLayout(action_bar)

        # =====================================================
        # ASSEMBLE SPLIT VIEW
        # =====================================================
        root_layout.addWidget(left_panel)
        root_layout.addWidget(right_panel, 1)

    # ================= SIGNAL =================

    def bind_signals(self):
        self.vm.data_changed.connect(self.load_therapists)

    # ================= LOGIC =================

    def load_therapists(self):
        therapists = self.vm.get_all_therapists(active_only=False)
        self.table.setRowCount(0)

        for t in therapists:
            row = self.table.rowCount()
            self.table.insertRow(row)

            icon = "👨" if t.gender == "Laki-laki" else "👩"
            name_item = QTableWidgetItem(f"{icon} {t.name}")
            name_item.setData(Qt.UserRole, t.id)

            if not t.is_active:
                name_item.setForeground(Qt.gray)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(t.gender))
            self.table.setItem(row, 2, QTableWidgetItem(t.specialization or "-"))

            status = "✅ Aktif" if t.is_active else "❌ Nonaktif"
            self.table.setItem(row, 3, QTableWidgetItem(status))

        self.table.clearSelection()

    def on_add_clicked(self):
        try:
            self.vm.add_therapist(
                self.name_input.text(),
                self.gender_combo.currentText(),
                self.specialization_input.text()
            )
            self.name_input.clear()
            self.specialization_input.clear()
            self.name_input.setFocus()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def on_deactivate_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Pilih Terapis", "Silakan pilih terapis terlebih dahulu"
            )
            return

        therapist_id = self.table.item(row, 0).data(Qt.UserRole)
        therapist_name = self.table.item(row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Konfirmasi",
            f"Nonaktifkan terapis '{therapist_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                self.vm.deactivate_therapist(therapist_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
