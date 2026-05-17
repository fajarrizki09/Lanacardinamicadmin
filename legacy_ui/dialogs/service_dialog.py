from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QSpinBox
)
from PySide6.QtCore import Qt
from utils.styles import STYLES


class ServiceDialog(QDialog):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setWindowTitle("Kelola Layanan")
        self.resize(980, 560)
        self.setStyleSheet(STYLES.get("main_window", ""))

        self.init_ui()
        self.bind_signals()
        self.load_services()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(12)

        left_panel = QFrame()
        left_panel.setStyleSheet(STYLES["card"])
        left_panel.setFixedWidth(320)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        title = QLabel("Tambah Layanan")
        title.setStyleSheet(STYLES["inventory_header"])
        left_layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Pijat Refleksi")
        self.name_input.setStyleSheet(STYLES["search_input"])

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("sesi / titik / area")
        self.unit_input.setText("sesi")
        self.unit_input.setStyleSheet(STYLES["search_input"])

        self.default_qty_input = QSpinBox()
        self.default_qty_input.setRange(1, 999)
        self.default_qty_input.setValue(1)
        self.default_qty_input.setStyleSheet(STYLES["search_input"])

        self.price_input = QSpinBox()
        self.price_input.setRange(0, 100000000)
        self.price_input.setSingleStep(5000)
        self.price_input.setPrefix("Rp ")
        self.price_input.setStyleSheet(STYLES["search_input"])

        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText("Template catatan pencatatan")
        self.template_input.setStyleSheet(STYLES["search_input"])

        self.add_btn = QPushButton("Tambah Layanan")
        self.add_btn.setStyleSheet(STYLES["add_button"])
        self.add_btn.clicked.connect(self.on_add_clicked)

        left_layout.addWidget(QLabel("Nama Layanan"))
        left_layout.addWidget(self.name_input)
        left_layout.addWidget(QLabel("Satuan"))
        left_layout.addWidget(self.unit_input)
        left_layout.addWidget(QLabel("Jumlah Default"))
        left_layout.addWidget(self.default_qty_input)
        left_layout.addWidget(QLabel("Harga per Satuan"))
        left_layout.addWidget(self.price_input)
        left_layout.addWidget(QLabel("Template Catatan"))
        left_layout.addWidget(self.template_input)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.add_btn)
        left_layout.addStretch()

        right_panel = QFrame()
        right_panel.setStyleSheet(STYLES["card"])
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)

        header = QLabel("Daftar Layanan")
        header.setStyleSheet(STYLES["inventory_header"])
        right_layout.addWidget(header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Nama", "Satuan", "Default", "Harga/Satuan", "Template", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        right_layout.addWidget(self.table)

        action_bar = QHBoxLayout()
        self.deactivate_btn = QPushButton("Nonaktifkan")
        self.deactivate_btn.setStyleSheet(STYLES["delete_button"])
        self.deactivate_btn.clicked.connect(self.on_deactivate_clicked)

        self.close_btn = QPushButton("Tutup")
        self.close_btn.setStyleSheet(STYLES["action_button"])
        self.close_btn.clicked.connect(self.accept)

        action_bar.addStretch()
        action_bar.addWidget(self.deactivate_btn)
        action_bar.addWidget(self.close_btn)
        right_layout.addLayout(action_bar)

        root_layout.addWidget(left_panel)
        root_layout.addWidget(right_panel, 1)

    def bind_signals(self):
        self.vm.data_changed.connect(self.load_services)

    def load_services(self):
        services = self.vm.get_all_services(active_only=False)
        self.table.setRowCount(0)

        for service in services:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(service.name)
            name_item.setData(Qt.UserRole, service.id)
            if not service.is_active:
                name_item.setForeground(Qt.gray)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(service.unit_label))
            self.table.setItem(row, 2, QTableWidgetItem(str(service.default_quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(f"Rp {service.price_per_unit:,.0f}"))
            self.table.setItem(row, 4, QTableWidgetItem(service.notes_template or "-"))
            self.table.setItem(row, 5, QTableWidgetItem("Aktif" if service.is_active else "Nonaktif"))

        self.table.clearSelection()

    def on_add_clicked(self):
        try:
            self.vm.add_service(
                self.name_input.text(),
                self.unit_input.text(),
                self.default_qty_input.value(),
                self.price_input.value(),
                self.template_input.text(),
            )
            self.name_input.clear()
            self.unit_input.setText("sesi")
            self.default_qty_input.setValue(1)
            self.price_input.setValue(0)
            self.template_input.clear()
            self.name_input.setFocus()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def on_deactivate_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Layanan", "Silakan pilih layanan terlebih dahulu")
            return

        service_id = self.table.item(row, 0).data(Qt.UserRole)
        service_name = self.table.item(row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Konfirmasi",
            f"Nonaktifkan layanan '{service_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                self.vm.deactivate_service(service_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
