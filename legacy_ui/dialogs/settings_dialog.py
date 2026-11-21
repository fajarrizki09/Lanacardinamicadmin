from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QGroupBox, QFormLayout, QMessageBox,
    QComboBox, QDoubleSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt
from datetime import datetime
from viewmodels.settings_view_model import SettingsViewModel
from helpers.backup_helper import BackupHelper
from threads.backup_thread import BackupThread

class SettingsDialog(QDialog):
    def __init__(self, settings_source, parent=None):
        super().__init__(parent)
        if isinstance(settings_source, SettingsViewModel):
            self.settings_vm = settings_source
        else:
            # Kompatibilitas constructor lama: SettingsDialog(settings, parent)
            self.settings_vm = SettingsViewModel(settings_source)
        self.setWindowTitle("⚙️ Pengaturan Aplikasi")
        self.resize(760, 760)
        self.selected_rule_id = None
        self.backup_thread = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        price_settings = self.settings_vm.get_price_settings()
        clinic_profile = self.settings_vm.get_clinic_profile()

        branding_group = QGroupBox("Branding Klinik")
        branding_layout = QFormLayout()

        self.clinic_name_input = QLineEdit(clinic_profile.get("clinic_name", "Klinik Bekam Sunnah Pro"))
        self.clinic_tagline_input = QLineEdit(clinic_profile.get("clinic_tagline", "Professional Cupping Therapy"))
        self.clinic_address_input = QLineEdit(clinic_profile.get("clinic_address", ""))
        self.clinic_phone_input = QLineEdit(clinic_profile.get("clinic_phone", ""))
        self.clinic_email_input = QLineEdit(clinic_profile.get("clinic_email", ""))
        self.clinic_website_input = QLineEdit(clinic_profile.get("clinic_website", ""))
        self.clinic_logo_input = QLineEdit(clinic_profile.get("clinic_logo_path", ""))
        self.clinic_logo_input.setPlaceholderText("Path file logo, opsional")

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.clinic_logo_input, 1)
        self.logo_browse_btn = QPushButton("Pilih Logo")
        self.logo_browse_btn.clicked.connect(self.choose_logo)
        logo_row.addWidget(self.logo_browse_btn)

        branding_layout.addRow("Nama Klinik:", self.clinic_name_input)
        branding_layout.addRow("Tagline:", self.clinic_tagline_input)
        branding_layout.addRow("Alamat:", self.clinic_address_input)
        branding_layout.addRow("Nomor Kontak:", self.clinic_phone_input)
        branding_layout.addRow("Email:", self.clinic_email_input)
        branding_layout.addRow("Website:", self.clinic_website_input)
        branding_layout.addRow("Logo:", logo_row)
        branding_group.setLayout(branding_layout)
        
        price_group = QGroupBox("Harga")
        price_layout = QFormLayout()
        
        self.price_per_point_input = QSpinBox()
        self.price_per_point_input.setRange(1000, 1000000)
        self.price_per_point_input.setValue(price_settings["price_per_point"])
        self.price_per_point_input.setSingleStep(1000)
        self.price_per_point_input.setPrefix("Rp ")
        price_layout.addRow("Harga per Titik:", self.price_per_point_input)
        
        example_label = QLabel(f"Contoh: 13 titik = Rp {13 * price_settings['price_per_point']:,}")
        example_label.setStyleSheet("color: #666; font-style: italic;")
        price_layout.addRow("", example_label)
        self.price_per_point_input.valueChanged.connect(
            lambda v: example_label.setText(f"Contoh: 13 titik = Rp {13 * v:,}")
        )
        
        self.base_price_input = QSpinBox()
        self.base_price_input.setRange(0, 10000000)
        self.base_price_input.setValue(price_settings["base_price"])
        self.base_price_input.setSingleStep(10000)
        self.base_price_input.setPrefix("Rp ")
        price_layout.addRow("Harga Dasar (opsional):", self.base_price_input)
        price_group.setLayout(price_layout)
        
        discount_group = QGroupBox("Pengaturan Diskon")
        discount_layout = QFormLayout()
        
        self.discount_percentage_input = QSpinBox()
        self.discount_percentage_input.setRange(0, 100)
        self.discount_percentage_input.setValue(price_settings["discount_percentage"])
        self.discount_percentage_input.setSuffix(" %")
        discount_layout.addRow("Persentase Diskon:", self.discount_percentage_input)
        
        self.min_visits_input = QSpinBox()
        self.min_visits_input.setRange(1, 100)
        self.min_visits_input.setValue(price_settings["min_visits_for_discount"])
        self.min_visits_input.setSuffix(" kunjungan")
        discount_layout.addRow("Minimum Kunjungan:", self.min_visits_input)
        
        discount_group.setLayout(discount_layout)

        backup_config = self.settings_vm.get_backup_config()
        backup_group = QGroupBox("Database Management")
        backup_layout = QFormLayout()

        self.backup_auto_checkbox = QCheckBox("Backup otomatis aktif")
        self.backup_auto_checkbox.setChecked(backup_config["auto_enabled"])
        backup_layout.addRow("Backup Otomatis:", self.backup_auto_checkbox)

        self.backup_interval_combo = QComboBox()
        self.backup_interval_combo.addItems(["daily"])
        self.backup_interval_combo.setCurrentText(backup_config["interval"])
        backup_layout.addRow("Interval:", self.backup_interval_combo)

        self.backup_max_input = QSpinBox()
        self.backup_max_input.setRange(1, 100)
        self.backup_max_input.setValue(backup_config["max_files"])
        backup_layout.addRow("Maksimal File:", self.backup_max_input)

        status_text = backup_config["last_backup_status"]
        if backup_config["last_backup_time"]:
            status_text += f" ({backup_config['last_backup_time']})"
        self.backup_status_label = QLabel(status_text)
        self.backup_status_label.setWordWrap(True)
        backup_layout.addRow("Status Terakhir:", self.backup_status_label)

        backup_buttons = QHBoxLayout()
        self.backup_now_btn = QPushButton("Backup Sekarang")
        self.restore_backup_btn = QPushButton("Restore Backup")
        self.backup_now_btn.clicked.connect(self.backup_now)
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        backup_buttons.addWidget(self.backup_now_btn)
        backup_buttons.addWidget(self.restore_backup_btn)
        backup_layout.addRow("", backup_buttons)
        backup_group.setLayout(backup_layout)

        rules_group = QGroupBox("Aturan Diskon Dinamis")
        rules_layout = QVBoxLayout()

        self.rules_table = QTableWidget(0, 6)
        self.rules_table.setHorizontalHeaderLabels(["Nama", "Tipe", "Diskon", "Syarat", "Aktif", "Prioritas"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rules_table.itemSelectionChanged.connect(self.on_rule_selected)
        rules_layout.addWidget(self.rules_table)

        rule_form = QFormLayout()
        self.rule_name_input = QLineEdit()
        self.rule_name_input.setPlaceholderText("Contoh: Diskon member 5x")
        rule_form.addRow("Nama:", self.rule_name_input)

        self.rule_type_combo = QComboBox()
        self.rule_type_combo.addItems(["visit_count", "voucher", "manual", "period"])
        rule_form.addRow("Tipe:", self.rule_type_combo)

        self.rule_discount_type_combo = QComboBox()
        self.rule_discount_type_combo.addItems(["percent", "fixed"])
        rule_form.addRow("Jenis Diskon:", self.rule_discount_type_combo)

        self.rule_discount_value_input = QDoubleSpinBox()
        self.rule_discount_value_input.setRange(0, 10000000)
        self.rule_discount_value_input.setDecimals(2)
        self.rule_discount_value_input.setSingleStep(1)
        rule_form.addRow("Nilai Diskon:", self.rule_discount_value_input)

        self.rule_condition_input = QDoubleSpinBox()
        self.rule_condition_input.setRange(0, 1000000)
        self.rule_condition_input.setDecimals(2)
        self.rule_condition_input.setSingleStep(1)
        rule_form.addRow("Syarat:", self.rule_condition_input)

        self.rule_voucher_input = QLineEdit()
        self.rule_voucher_input.setPlaceholderText("Kode voucher jika tipe voucher")
        rule_form.addRow("Kode Voucher:", self.rule_voucher_input)

        self.rule_start_input = QLineEdit()
        self.rule_start_input.setPlaceholderText("YYYY-MM-DD, opsional")
        rule_form.addRow("Mulai:", self.rule_start_input)

        self.rule_end_input = QLineEdit()
        self.rule_end_input.setPlaceholderText("YYYY-MM-DD, opsional")
        rule_form.addRow("Selesai:", self.rule_end_input)

        self.rule_priority_input = QSpinBox()
        self.rule_priority_input.setRange(1, 9999)
        self.rule_priority_input.setValue(100)
        rule_form.addRow("Prioritas:", self.rule_priority_input)

        self.rule_active_input = QCheckBox("Aktif")
        self.rule_active_input.setChecked(True)
        rule_form.addRow("", self.rule_active_input)
        rules_layout.addLayout(rule_form)

        rule_buttons = QHBoxLayout()
        self.add_rule_btn = QPushButton("Tambah Aturan")
        self.update_rule_btn = QPushButton("Edit Aturan")
        self.toggle_rule_btn = QPushButton("Aktif/Nonaktif")
        self.delete_rule_btn = QPushButton("Hapus")
        self.clear_rule_btn = QPushButton("Bersihkan")
        self.add_rule_btn.clicked.connect(self.add_discount_rule)
        self.update_rule_btn.clicked.connect(self.update_discount_rule)
        self.toggle_rule_btn.clicked.connect(self.toggle_discount_rule)
        self.delete_rule_btn.clicked.connect(self.delete_discount_rule)
        self.clear_rule_btn.clicked.connect(self.clear_rule_form)
        rule_buttons.addWidget(self.add_rule_btn)
        rule_buttons.addWidget(self.update_rule_btn)
        rule_buttons.addWidget(self.toggle_rule_btn)
        rule_buttons.addWidget(self.delete_rule_btn)
        rule_buttons.addWidget(self.clear_rule_btn)
        rules_layout.addLayout(rule_buttons)
        rules_group.setLayout(rules_layout)
        
        info_label = QLabel(
            "💡 <i>Sistem harga berbasis titik: Admin dapat mengatur harga per titik, "
            "misal 10.000 per titik sehingga 13 titik = 130.000. "
            "Pasien akan mendapat diskon otomatis setelah mencapai jumlah kunjungan minimum.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px;")
        
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Simpan")
        self.cancel_btn = QPushButton("Batal")
        
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(branding_group)
        layout.addWidget(price_group)
        layout.addWidget(discount_group)
        layout.addWidget(backup_group)
        layout.addWidget(rules_group)
        layout.addWidget(info_label)
        layout.addLayout(button_layout)
        self.load_discount_rules()

    def choose_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Logo Klinik",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.clinic_logo_input.setText(file_path)

    def parse_rule_date(self, text):
        text = text.strip()
        if not text:
            return None
        return datetime.strptime(text, "%Y-%m-%d")

    def collect_rule_data(self):
        name = self.rule_name_input.text().strip()
        if not name:
            raise ValueError("Nama aturan diskon wajib diisi.")
        rule_type = self.rule_type_combo.currentText()
        voucher_code = self.rule_voucher_input.text().strip()
        if rule_type == "voucher" and not voucher_code:
            raise ValueError("Kode voucher wajib diisi untuk tipe voucher.")
        if rule_type == "visit_count" and self.rule_condition_input.value() <= 0:
            raise ValueError("Syarat kunjungan wajib lebih dari 0 untuk tipe visit_count.")
        return {
            "name": name,
            "type": rule_type,
            "discount_type": self.rule_discount_type_combo.currentText(),
            "discount_value": self.rule_discount_value_input.value(),
            "condition_value": self.rule_condition_input.value() or None,
            "voucher_code": voucher_code or None,
            "start_date": self.parse_rule_date(self.rule_start_input.text()),
            "end_date": self.parse_rule_date(self.rule_end_input.text()),
            "is_active": self.rule_active_input.isChecked(),
            "priority": self.rule_priority_input.value(),
        }

    def load_discount_rules(self):
        rules = self.settings_vm.get_discount_rules()
        self.rules_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.type))
            self.rules_table.setItem(row, 2, QTableWidgetItem(f"{rule.discount_value:g} {rule.discount_type}"))
            self.rules_table.setItem(row, 3, QTableWidgetItem(str(rule.condition_value or rule.voucher_code or "-")))
            self.rules_table.setItem(row, 4, QTableWidgetItem("Ya" if rule.is_active else "Tidak"))
            self.rules_table.setItem(row, 5, QTableWidgetItem(str(rule.priority)))
            self.rules_table.item(row, 0).setData(Qt.UserRole, rule)

    def on_rule_selected(self):
        row = self.rules_table.currentRow()
        if row < 0 or not self.rules_table.item(row, 0):
            return
        rule = self.rules_table.item(row, 0).data(Qt.UserRole)
        self.selected_rule_id = rule.id
        self.rule_name_input.setText(rule.name)
        self.rule_type_combo.setCurrentText(rule.type)
        self.rule_discount_type_combo.setCurrentText(rule.discount_type)
        self.rule_discount_value_input.setValue(rule.discount_value)
        self.rule_condition_input.setValue(rule.condition_value or 0)
        self.rule_voucher_input.setText(rule.voucher_code or "")
        self.rule_start_input.setText(rule.start_date.strftime("%Y-%m-%d") if rule.start_date else "")
        self.rule_end_input.setText(rule.end_date.strftime("%Y-%m-%d") if rule.end_date else "")
        self.rule_active_input.setChecked(rule.is_active)
        self.rule_priority_input.setValue(rule.priority)

    def clear_rule_form(self):
        self.selected_rule_id = None
        self.rules_table.clearSelection()
        self.rule_name_input.clear()
        self.rule_type_combo.setCurrentIndex(0)
        self.rule_discount_type_combo.setCurrentIndex(0)
        self.rule_discount_value_input.setValue(0)
        self.rule_condition_input.setValue(0)
        self.rule_voucher_input.clear()
        self.rule_start_input.clear()
        self.rule_end_input.clear()
        self.rule_active_input.setChecked(True)
        self.rule_priority_input.setValue(100)

    def add_discount_rule(self):
        try:
            self.settings_vm.add_discount_rule(self.collect_rule_data())
            self.clear_rule_form()
            self.load_discount_rules()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menambah aturan diskon:\n{e}")

    def update_discount_rule(self):
        if not self.selected_rule_id:
            QMessageBox.warning(self, "Pilih Aturan", "Pilih aturan diskon yang ingin diedit.")
            return
        try:
            self.settings_vm.update_discount_rule(self.selected_rule_id, self.collect_rule_data())
            self.load_discount_rules()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal mengedit aturan diskon:\n{e}")

    def toggle_discount_rule(self):
        if not self.selected_rule_id:
            QMessageBox.warning(self, "Pilih Aturan", "Pilih aturan diskon dahulu.")
            return
        rule = self.rules_table.item(self.rules_table.currentRow(), 0).data(Qt.UserRole)
        self.settings_vm.set_discount_rule_active(self.selected_rule_id, not rule.is_active)
        self.load_discount_rules()

    def delete_discount_rule(self):
        if not self.selected_rule_id:
            QMessageBox.warning(self, "Pilih Aturan", "Pilih aturan diskon yang ingin dihapus.")
            return
        if QMessageBox.question(self, "Hapus Aturan", "Hapus aturan diskon ini?") != QMessageBox.Yes:
            return
        self.settings_vm.delete_discount_rule(self.selected_rule_id)
        self.clear_rule_form()
        self.load_discount_rules()

    def _backup_dir(self):
        return "backups"

    def _backup_helper(self):
        return BackupHelper(
            self.settings_vm.get_database_path(),
            self._backup_dir(),
            max_backups=self.backup_max_input.value(),
        )

    def _set_backup_status(self, status):
        backup_time = datetime.now().isoformat(timespec="seconds")
        self.settings_vm.save_backup_status(status, backup_time)
        self.backup_status_label.setText(f"{status} ({backup_time})")

    def backup_now(self):
        if self.backup_thread and self.backup_thread.isRunning():
            QMessageBox.information(self, "Backup Berjalan", "Backup masih berjalan.")
            return
        self.backup_now_btn.setEnabled(False)
        self.backup_status_label.setText("Backup sedang berjalan...")
        self.backup_thread = BackupThread(
            self.settings_vm.get_database_path(),
            self._backup_dir(),
            daily=False,
            max_backups=self.backup_max_input.value(),
        )
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()

    def on_backup_finished(self, success, message):
        self.backup_now_btn.setEnabled(True)
        status = "success" if success else "failed"
        full_status = f"{status}: {message}"
        self._set_backup_status(full_status)
        if success:
            QMessageBox.information(self, "Backup Berhasil", f"Backup berhasil dibuat:\n{message}")
        else:
            QMessageBox.critical(self, "Backup Gagal", message)

    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih file backup", self._backup_dir(), "Database Files (*.db)")
        if not file_path:
            return
        confirm = QMessageBox.question(
            self,
            "Restore Backup",
            "Restore akan menimpa database aktif. Database aktif akan dibackup terlebih dahulu. Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            parent = self.parent()
            if parent and hasattr(parent, "db") and hasattr(parent.db, "engine"):
                parent.db.engine.dispose()
            status = self._backup_helper().restore_backup(file_path)
            status_text = ("success" if status["success"] else "failed") + f": {status['message']}"
            self._set_backup_status(status_text)
            if not status["success"]:
                QMessageBox.critical(self, "Restore Gagal", status["message"])
                return
            if parent and hasattr(parent, "refresh_after_restore"):
                parent.refresh_after_restore()
            QMessageBox.information(
                self,
                "Restore Berhasil",
                "Backup berhasil direstore. Silakan reload atau restart aplikasi agar data terbaru terbaca sempurna.",
            )
        except Exception as e:
            self._set_backup_status(f"failed: {e}")
            QMessageBox.critical(self, "Restore Gagal", str(e))
        
    def save_settings(self):
        self.settings_vm.save_clinic_profile({
            "clinic_name": self.clinic_name_input.text().strip() or "Klinik Bekam Sunnah Pro",
            "clinic_tagline": self.clinic_tagline_input.text().strip(),
            "clinic_address": self.clinic_address_input.text().strip(),
            "clinic_phone": self.clinic_phone_input.text().strip(),
            "clinic_email": self.clinic_email_input.text().strip(),
            "clinic_website": self.clinic_website_input.text().strip(),
            "clinic_logo_path": self.clinic_logo_input.text().strip(),
        })
        self.settings_vm.save_price_settings(
            self.price_per_point_input.value(),
            self.base_price_input.value(),
            self.discount_percentage_input.value(),
            self.min_visits_input.value(),
        )
        self.settings_vm.save_backup_config(
            self.backup_auto_checkbox.isChecked(),
            self.backup_interval_combo.currentText(),
            self.backup_max_input.value(),
        )
        
        QMessageBox.information(
            self, "Berhasil", 
            "Pengaturan berhasil disimpan!\n"
            f"Harga per titik: Rp {self.price_per_point_input.value():,}\n"
            "Perubahan akan diterapkan pada kunjungan berikutnya."
        )
        self.accept()
