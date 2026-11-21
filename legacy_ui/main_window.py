from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from datetime import datetime
import os
from utils.styles import STYLES
from components.patient_form import PatientForm
from components.patient_list import PatientList
from components.visit_section import VisitSection
from components.action_buttons import ActionButtons

from dialogs.edit_patient_dialog import EditPatientDialog
from dialogs.analytics_dialog import AnalyticsDialog
from dialogs.settings_dialog import SettingsDialog
from dialogs.therapist_dialog import TherapistDialog
from dialogs.service_dialog import ServiceDialog
from dialogs.invoice_dialog import InvoiceDialog
from dialogs.custom_invoice_dialog import CustomInvoiceDialog
from dialogs.inventory_dialog import InventoryDialog
from dialogs.inventory_settings_dialog import InventorySettingsDialog
from dialogs.herbal_dialog import HerbalDialog

from helpers.import_export import ImportExportHelper
from helpers.license import is_license_invalid
from threads.backup_thread import BackupThread
from threads.search_thread import SearchThread
from viewmodels.analytics_view_model import AnalyticsViewModel
from viewmodels.invoice_view_model import InvoiceViewModel
from viewmodels.patient_view_model import PatientViewModel
from viewmodels.settings_view_model import SettingsViewModel
from viewmodels.visit_view_model import VisitViewModel
from viewmodels.therapist_view_model import TherapistViewModel
from viewmodels.service_view_model import ServiceViewModel



from viewmodels.inventory_store import InventoryStore

from components.invoice_list import InvoiceList

class MainWindow(QMainWindow):
    def __init__(self, db, settings):
        super().__init__()
        # ...
        # Compatibility handles for older helpers/dialog flows while migration to viewmodels continues.
        # Operational patient, analytics, invoice, inventory, and settings flows now use viewmodels.
        self.db = db
        self.inventory_store = InventoryStore(db)
        self.settings = settings
        self.import_export = ImportExportHelper(self, db)

        self.patient_vm = PatientViewModel(db)
        self.visit_vm = VisitViewModel(db, settings)
        self.therapist_vm = TherapistViewModel(db)
        self.service_vm = ServiceViewModel(db)
        self.analytics_vm = AnalyticsViewModel(db)
        self.invoice_vm = InvoiceViewModel(db)
        self.settings_vm = SettingsViewModel(settings, db)
        self.therapist_vm.data_changed.connect(self.on_therapists_changed)
        self.service_vm.data_changed.connect(self.on_services_changed)
        self.invoice_list_view = None
        self.backup_thread = None
        self.run_backup()

        self.search_thread = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        self.all_patients = []
        self.filtered_patients = []
        self.therapists_dict = {}
        self.services = []

        self.init_ui()
        self.update_branding()
        self.refresh_patients()
        self.refresh_therapists()
        self.refresh_services()

    def run_backup(self):
        backup_config = self.settings_vm.get_backup_config()
        if not backup_config["auto_enabled"]:
            return
        db_path = self.settings_vm.get_database_path()
        self.backup_thread = BackupThread(
            db_path,
            "backups",
            daily=backup_config["interval"] == "daily",
            max_backups=backup_config["max_files"],
        )
        self.backup_thread.finished.connect(self._on_backup_finished)
        self.backup_thread.start()

    def _on_backup_finished(self, success, message):
        status = ("success" if success else "failed") + f": {message}"
        self.settings_vm.save_backup_status(status, datetime.now().isoformat(timespec="seconds"))
        if not success:
            print(f"Backup failed: {message}")
        else:
            print(f"Backup successful: {message}")

    def _ensure_license(self):
        return not is_license_invalid()

    def refresh_after_restore(self):
        self.patient_vm.invalidate_cache() if hasattr(self.patient_vm, "invalidate_cache") else None
        self.visit_vm.invalidate_cache()
        self.analytics_vm = AnalyticsViewModel(self.db)
        self.invoice_vm = InvoiceViewModel(self.db)
        self.refresh_patients()
        self.refresh_therapists()
        self.load_visits()
        if self.invoice_list_view:
            self.invoice_list_view.refresh_list()

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet(STYLES.get("main_window", ""))
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dcdde1; background: white; border-radius: 5px; }
            QTabBar::tab { 
                background: #f1f2f6; 
                padding: 12px 20px; 
                margin-right: 2px; 
                border-top-left-radius: 5px; 
                border-top-right-radius: 5px; 
            }
            QTabBar::tab:selected { background: white; border-bottom-color: white; font-weight: bold; color: #3498db; }
        """)

        # --- TAB 1: DASHBOARD & PASIEN ---
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()

        # --- TAB 2: TERAPIS ---
        self.tab_therapist = QWidget()
        self.setup_therapist_tab()

        # --- TAB 3: STOK ALAT ---
        self.tab_services = QWidget()
        self.setup_services_tab()

        # --- TAB 4: STOK ALAT ---
        self.tab_inventory = QWidget()
        self.setup_inventory_tab()

        # --- TAB 5: STOK HERBAL ---
        self.tab_herbal = QWidget()
        self.setup_herbal_tab()

        # --- TAB 6: ANALITIK ---
        self.tab_analytics = QWidget()
        self.setup_analytics_tab()

        # --- TAB 7: INVOICE ---
        self.tab_invoice = QWidget()
        self.setup_invoice_tab()

        self.tabs.addTab(self.tab_dashboard, "🏠 Dashboard")
        self.tabs.addTab(self.tab_therapist, "👨‍⚕️ Terapis")
        self.tabs.addTab(self.tab_services, "🧾 Layanan")
        self.tabs.addTab(self.tab_inventory, "⚙️ Stok Alat")
        self.tabs.addTab(self.tab_herbal, "🌿 Stok Herbal")
        self.tabs.addTab(self.tab_analytics, "📊 Analitik")
        self.tabs.addTab(self.tab_invoice, "📑 Invoice")

        main_layout.addWidget(self.tabs)
        self.connect_signals()

    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(10, 10, 10, 10)

        self.sunnah_calendar_label = QLabel()
        self.update_sunnah_info()
        self.branding_label = QLabel()
        self.branding_logo_label = QLabel()
        self.branding_logo_label.setAlignment(Qt.AlignCenter)
        self.branding_logo_label.setVisible(False)
        self.branding_label.setWordWrap(True)
        self.branding_label.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 10px;
                color: #2c3e50;
            }
        """)

        self.patient_form = PatientForm(self)
        self.patient_list = PatientList(self)
        self.visit_section = VisitSection(self)
        self.action_buttons = ActionButtons(self)

        # Dashboard layout with two columns
        content_layout = QHBoxLayout()

        # LEFT COLUMN: Sunnah info, Patient registration, Patient list
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        left_column.addWidget(self.branding_logo_label)
        left_column.addWidget(self.branding_label)
        left_column.addWidget(self.sunnah_calendar_label)
        left_column.addWidget(self.patient_form)
        left_column.addWidget(self.patient_list, 1) # Give priority to patient list height

        # RIGHT COLUMN: Visit section & Action buttons at the bottom
        right_column = QVBoxLayout()
        right_column.setSpacing(10)

        right_column.addWidget(self.visit_section, 1)

        # Action Bar at the bottom of right column
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        action_bar.addWidget(self.action_buttons.settings_btn)
        action_bar.addWidget(self.action_buttons.export_btn)
        action_bar.addWidget(self.action_buttons.import_btn)

        right_column.addLayout(action_bar)

        content_layout.addLayout(left_column, 2)
        content_layout.addLayout(right_column, 3)

        layout.addLayout(content_layout)

    def setup_therapist_tab(self):
        layout = QVBoxLayout(self.tab_therapist)
        self.therapist_mgr = TherapistDialog(self.therapist_vm, self)
        self.therapist_mgr.setWindowFlags(Qt.Widget)
        layout.addWidget(self.therapist_mgr)

    def setup_services_tab(self):
        layout = QVBoxLayout(self.tab_services)
        self.service_mgr = ServiceDialog(self.service_vm, self)
        self.service_mgr.setWindowFlags(Qt.Widget)
        layout.addWidget(self.service_mgr)

    def setup_inventory_tab(self):
        layout = QVBoxLayout(self.tab_inventory)
        self.inventory_mgr = InventoryDialog(None, self.inventory_store, self)
        self.inventory_mgr.setWindowFlags(Qt.Widget)
        layout.addWidget(self.inventory_mgr)

    def setup_herbal_tab(self):
        layout = QVBoxLayout(self.tab_herbal)
        self.herbal_mgr = HerbalDialog(None, self.inventory_store, self)
        self.herbal_mgr.setWindowFlags(Qt.Widget)
        layout.addWidget(self.herbal_mgr)

    def setup_analytics_tab(self):
        layout = QVBoxLayout(self.tab_analytics)
        self.analytics_mgr = AnalyticsDialog(self.analytics_vm, self)
        self.analytics_mgr.setWindowFlags(Qt.Widget)
        layout.addWidget(self.analytics_mgr)

    def setup_invoice_tab(self):
        layout = QVBoxLayout(self.tab_invoice)
        self.invoice_list_view = InvoiceList(self.invoice_vm, self)
        layout.addWidget(self.invoice_list_view)

    def update_sunnah_info(self):
        from datetime import datetime, date
        today = date.today()
        # Sunnah dates for Jan 2026 based on search: 17 Rajab (Jan 8), 19 Rajab (Jan 10), 21 Rajab (Jan 12)
        # For simplicity, let's provide a few sample sunnah dates for Jan/Feb 2026
        sunnah_dates = [
            date(2026, 1, 8), date(2026, 1, 10), date(2026, 1, 12),
            date(2026, 2, 7), date(2026, 2, 9), date(2026, 2, 11)
        ]

        if today in sunnah_dates:
            self.sunnah_calendar_label.setText("🌟 HARI INI: Waktu Sunnah Bekam (17, 19, atau 21 Hijriah)")
            self.sunnah_calendar_label.setStyleSheet(STYLES["sunnah_label_active"])
        else:
            # Find next sunnah date
            next_date = next((d for d in sunnah_dates if d > today), None)
            if next_date:
                days_left = (next_date - today).days
                self.sunnah_calendar_label.setText(f"📅 Jadwal Sunnah Terdekat: {next_date.strftime('%d %b %Y')} ({days_left} hari lagi)")
            else:
                self.sunnah_calendar_label.setText("📅 Jadwal Sunnah Bekam: Tanggal 17, 19, 21 Hijriah")
            self.sunnah_calendar_label.setStyleSheet(STYLES["sunnah_label"])

    def update_branding(self):
        profile = self.settings_vm.get_clinic_profile()
        clinic_name = profile.get("clinic_name") or "Lancar Dynamic Admin"
        self.setWindowTitle(f"{clinic_name} - Admin")

        if not hasattr(self, "branding_label"):
            return

        logo_path = profile.get("clinic_logo_path") or ""
        if hasattr(self, "branding_logo_label") and logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                self.branding_logo_label.setPixmap(
                    pixmap.scaled(180, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.branding_logo_label.setVisible(True)
        elif hasattr(self, "branding_logo_label"):
            self.branding_logo_label.clear()
            self.branding_logo_label.setVisible(False)

        lines = [f"<b style='font-size:16px'>{clinic_name}</b>"]
        if profile.get("clinic_tagline"):
            lines.append(profile["clinic_tagline"])
        contact_parts = [p for p in [
            profile.get("clinic_phone"),
            profile.get("clinic_email"),
            profile.get("clinic_website"),
        ] if p]
        if profile.get("clinic_address"):
            lines.append(profile["clinic_address"])
        if contact_parts:
            lines.append(" | ".join(contact_parts))
        self.branding_label.setText("<br>".join(lines))

    def connect_signals(self):
        self.patient_form.add_btn.clicked.connect(self.add_patient)
        self.patient_list.update_btn.clicked.connect(self.on_update_patient_clicked)
        self.patient_list.delete_btn.clicked.connect(self.delete_patient)
        self.patient_list.search_input.textChanged.connect(self.search_patients)
        self.patient_list.patient_list.currentRowChanged.connect(self.load_selected_patient_data)

        self.visit_section.visit_btn.clicked.connect(self.catat_kunjungan)

        self.action_buttons.therapist_btn.clicked.connect(self.show_therapist_dialog)
        self.action_buttons.settings_btn.clicked.connect(self.show_settings_dialog)
        self.action_buttons.settings_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.action_buttons.settings_btn.customContextMenuRequested.connect(self.show_settings_context_menu)
        self.action_buttons.analytics_btn.clicked.connect(self.show_analytics)
        self.action_buttons.inventory_btn.clicked.connect(self.show_inventory_dialog)
        self.action_buttons.herbal_btn.clicked.connect(self.show_herbal_dialog)
        self.action_buttons.export_btn.clicked.connect(self.import_export.export_data)
        self.action_buttons.import_btn.clicked.connect(self.handle_import)

        self.visit_vm.visit_added.connect(self.on_visit_done)
        self.visit_vm.visit_failed.connect(self.on_visit_failed)

    def delete_visit_by_row(self, row):
        selected_patient = self.patient_list.get_selected_patient()
        if not selected_patient:
            return

        patient_id = selected_patient[0]
        visits = self.visit_vm.get_visits_for_patient(patient_id)
        visits.sort(key=lambda v: v.date, reverse=True)

        if row < len(visits):
            visit = visits[row]
            visit_id = visit.id if hasattr(visit, 'id') else visit.get('id')

            try:
                self.patient_vm.delete_visit(patient_id, visit_id)
                self.visit_vm.invalidate_cache(patient_id)
                self.load_visits()
                self.refresh_patients()
                QMessageBox.information(self, "Berhasil", "Data kunjungan berhasil dihapus.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menghapus kunjungan: {str(e)}")

    def refresh_therapists(self):
        therapists = self.therapist_vm.get_all_therapists(active_only=True)
        self.therapists_dict = {t.id: t for t in therapists}

    def refresh_services(self):
        self.services = self.service_vm.get_all_services(active_only=True)
        if hasattr(self, "visit_section"):
            self.visit_section.load_services(self.services)

    def on_services_changed(self):
        self.refresh_services()
        self.load_visits()

    def on_therapists_changed(self):
        self.refresh_therapists()
        self.load_selected_patient_data(
            self.patient_list.patient_list.currentRow()
        )



    def add_patient(self):
        name, phone, address, gender = self.patient_form.get_inputs()

        if not name:
            QMessageBox.warning(self, "Error", "Nama tidak boleh kosong")
            return

        # Jika nomor HP kosong, generate nomor sementara
        if not phone:
            from datetime import datetime
            phone = "TEMP-" + datetime.now().strftime("%H%M%S%f")[:10]
        elif not phone.isdigit() and not phone.startswith("TEMP-"):
            QMessageBox.warning(self, "Error", "Nomor HP harus berupa angka")
            return

        if any(p[2] == phone for p in self.all_patients):
            QMessageBox.warning(self, "Duplikat", f"Nomor HP {phone} sudah terdaftar.")
            return

        self.patient_vm.add_patient(name, phone, address, gender)
        self.patient_form.clear_inputs()
        self.refresh_patients()
        self.patient_form.name_input.setFocus()

        for i, patient in enumerate(self.all_patients):
            if patient[1] == name and patient[2] == phone:
                self.patient_list.patient_list.setCurrentRow(i)
                self.patient_list.patient_list.scrollToItem(self.patient_list.patient_list.item(i))
                break

    def on_update_patient_clicked(self):
        selected_patient = self.patient_list.get_selected_patient()
        if not selected_patient:
            QMessageBox.warning(self, "Pilih Pasien", "Silakan pilih pasien yang ingin diedit")
            return

        patient_id = selected_patient[0]
        self.update_patient(patient_id)

    def update_patient(self, patient_id):
        patient = self.patient_vm.get_patient_with_visits(patient_id)
        visits = [{
            "id": v.id,
            "date": v.date.isoformat() if hasattr(v.date, 'isoformat') else v.date,
            "price": v.price,
            "discount_applied": v.discount_applied
        } for v in patient.visits]

        dialog = EditPatientDialog(patient, visits, self)
        if dialog.exec_():
            if not self._ensure_license():
                return
            new_name, new_phone, new_address, new_gender, updated_visits = dialog.get_data()

            try:
                self.patient_vm.update_patient(patient_id, new_name, new_phone, new_address, new_gender)
                self.patient_vm.update_patient_visits(patient_id, updated_visits)
                self.visit_vm.invalidate_cache(patient_id)
                self.refresh_patients()

                for i, p in enumerate(self.filtered_patients):
                    if p[0] == patient_id:
                        self.patient_list.patient_list.setCurrentRow(i)
                        break

                self.load_visits()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Gagal menyimpan perubahan: {str(e)}")

    def delete_patient(self):
        selected_patient = self.patient_list.get_selected_patient()
        if not selected_patient:
            QMessageBox.warning(self, "Pilih Pasien", "Pilih pasien yang ingin dihapus")
            return

        patient_id, patient_name, _ = selected_patient[:3]
        confirm = QMessageBox.question(
            self, "Hapus Pasien",
            f"Yakin ingin menghapus pasien '{patient_name}' beserta riwayatnya?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.patient_vm.delete_patient(patient_id)
            self.visit_vm.invalidate_cache(patient_id)
            self.refresh_patients()
            self.visit_section.visit_table.setRowCount(0)
            self.visit_section.total_info_label.setText("Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0")
            QMessageBox.information(self, "Berhasil", f"Pasien '{patient_name}' berhasil dihapus.")

    def refresh_patients(self):
        selected_patient = self.patient_list.get_selected_patient()
        selected_patient_id = selected_patient[0] if selected_patient else None

        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait()

        self.all_patients = self.patient_vm.get_patients()
        self.filtered_patients = self.all_patients
        self.patient_list.update_list(self.filtered_patients)

        if selected_patient_id is not None:
            for i, p in enumerate(self.filtered_patients):
                if p[0] == selected_patient_id:
                    self.patient_list.patient_list.setCurrentRow(i)
                    break
        else:
            self.patient_list.patient_list.setCurrentRow(-1)

    def search_patients(self, text):
        self.search_timer.stop()
        self._current_search_text = text.strip().lower()

        if not self._current_search_text:
            if self.search_thread and self.search_thread.isRunning():
                self.search_thread.cancel()
                self.search_thread.wait()
            self.filtered_patients = self.all_patients
            self.patient_list.update_list(self.filtered_patients)
            return

        self.search_timer.start(300)

    def _perform_search(self):
        text = self._current_search_text

        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait()

        self.search_thread = SearchThread(self.all_patients, text)
        self.search_thread.results_ready.connect(self.on_search_results)
        self.search_thread.start()

    def on_search_results(self, filtered_patients):
        self.filtered_patients = filtered_patients or []
        self.patient_list.update_list(self.filtered_patients)

    def load_selected_patient_data(self, index):
        if index < 0:
            self.visit_section.visit_table.setRowCount(0)
            self.visit_section.total_info_label.setText("Total kunjungan: 0 | Total satuan: 0 | Total pemasukan: Rp 0")
            self.visit_section.therapist_combo.clear()
            self.visit_section.therapist_combo.addItem("-- Pilih Pasien Dulu --", None)
            return

        selected_patient = self.patient_list.get_selected_patient()
        if selected_patient and len(selected_patient) >= 4:
            patient_gender = selected_patient[3]
            self.visit_section.set_patient_gender(patient_gender)

            self.refresh_therapists()
            filtered_therapists = [
                t for t in self.therapists_dict.values() 
                if t.gender == patient_gender
            ]
            self.visit_section.load_therapists(filtered_therapists)

        self.load_visits()

    def load_visits(self):
        selected_patient = self.patient_list.get_selected_patient()
        if not selected_patient:
            return

        patient_id = selected_patient[0]
        visits = self.visit_vm.get_visits_for_patient(patient_id)

        visits.sort(key=lambda v: v.date, reverse=True)
        self.visit_section.load_visits(visits, self.therapists_dict)
        self.visit_section.total_info_label.setText(
            self.visit_vm.get_summary_text(visits)
        )

    def catat_kunjungan(self):
        if not self._ensure_license():
            return

        selected_patient = self.patient_list.get_selected_patient()
        if not selected_patient:
            QMessageBox.warning(self, "Pilih Pasien", "Silakan pilih pasien dahulu")
            return

        point_count = self.visit_section.get_point_count()
        if point_count <= 0:
            QMessageBox.warning(self, "Error", "Jumlah titik harus lebih dari 0")
            return

        therapist_id = self.visit_section.get_selected_therapist_id()
        if therapist_id is None:
            confirm = QMessageBox.question(
                self, "Konfirmasi",
                "Terapis belum dipilih. Lanjutkan tanpa terapis?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.No:
                return

        medical_notes = self.visit_section.get_medical_notes()
        manual_price = None
        is_free_visit = self.visit_section.is_free_visit()
        free_visit_reason = self.visit_section.get_free_visit_reason()
        if self.visit_section.is_manual_price():
            manual_price = self.visit_section.parse_current_price()
            if manual_price is None:
                QMessageBox.warning(self, "Error", "Harga manual tidak boleh kosong atau tidak valid")
                return
            if manual_price < 0:
                QMessageBox.warning(self, "Error", "Harga manual tidak boleh kurang dari 0")
                return
            if manual_price == 0 and not is_free_visit:
                QMessageBox.warning(self, "Error", "Harga manual 0 hanya boleh untuk kunjungan gratis")
                return
        elif is_free_visit:
            QMessageBox.warning(self, "Error", "Aktifkan edit harga manual dan isi 0 untuk kunjungan gratis")
            return

        service_name = self.visit_section.get_selected_service_name()
        if manual_price is None and service_name.lower() != "bekam":
            manual_price = self.visit_section.get_current_price()
            if manual_price == 0 and not is_free_visit:
                QMessageBox.warning(self, "Error", "Harga layanan 0 hanya boleh untuk kunjungan gratis")
                return

        self.visit_vm.add_visit(
            patient_id=selected_patient[0],
            point_count=point_count,
            therapist_id=therapist_id,
            service_id=self.visit_section.get_selected_service_id(),
            service_name=service_name,
            medical_notes=medical_notes,
            manual_price=manual_price,
            is_free_visit=is_free_visit,
            free_visit_reason=free_visit_reason,
            voucher_code=self.visit_section.get_voucher_code()
        )

        # Clear input setelah simpan
        self.visit_section.medical_notes_input.clear()
        
        if self.invoice_list_view:
            self.invoice_list_view.refresh_list()

    def on_visit_done(self, normal_price, discounted_price, discount_applied, discount_rule_name=""):
        discount_pct = self.settings_vm.get_price_settings()["discount_percentage"]
        point_count = self.visit_section.get_point_count()
        selected_patient = self.patient_list.get_selected_patient()

        if not selected_patient:
            return

        patient_id = selected_patient[0]
        patient_name = selected_patient[1]

        therapist_id = self.visit_section.get_selected_therapist_id()
        therapist_name = "--"
        if therapist_id and therapist_id in self.therapists_dict:
            therapist_name = self.therapists_dict[therapist_id].name

        # Show Modern Invoice Dialog
        visit_date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        invoice_dlg = InvoiceDialog(
            patient_name,
            visit_date_str,
            point_count,
            discounted_price,
            therapist_name,
            self.settings_vm,
            self,
            discount_rule_name=discount_rule_name,
            service_name=self.visit_section.get_selected_service_name()
        )
        invoice_dlg.exec_()

        self.load_visits()
        self.refresh_patients()

        # Reset selection to maintain the current patient view
        for i in range(self.patient_list.patient_list.count()):
            item = self.patient_list.patient_list.item(i)
            p_data = item.data(Qt.UserRole)
            if p_data and p_data[0] == patient_id:
                self.patient_list.patient_list.setCurrentRow(i)
                break

    def on_visit_failed(self, message):
        QMessageBox.critical(self, "Gagal", f"Terjadi kesalahan saat mencatat kunjungan:\n{message}")

    def handle_import(self):
        if self.import_export.import_data():
            self.refresh_patients()

    def show_therapist_dialog(self):
        self.tabs.setCurrentIndex(1)

    def show_inventory_dialog(self):
        self.tabs.setCurrentIndex(3)

    def show_herbal_dialog(self):
        self.tabs.setCurrentIndex(4)

    def show_analytics(self):
        self.tabs.setCurrentIndex(5)

    def show_inventory_settings(self):
        dlg = InventorySettingsDialog(self.settings_vm, self)
        dlg.exec_()

    def show_settings_dialog(self):
        dlg = SettingsDialog(self.settings_vm, self)
        if dlg.exec_():
            price_per_point = self.settings_vm.get_price_per_point()
            self.visit_section.update_price_from_points()
            self.update_branding()
            QMessageBox.information(
                self, "Pengaturan Diperbarui",
                f"Harga per titik sekarang: Rp {price_per_point:,}"
            )

    def show_settings_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        custom_action = menu.addAction("Kustomisasi Cetak Invoice")
        inv_settings_action = menu.addAction("⚙️ Atur Stok Otomatis")

        action = menu.exec_(self.action_buttons.settings_btn.mapToGlobal(pos))
        if action == custom_action:
            self.show_custom_invoice_dialog()
        elif action == inv_settings_action:
            self.show_inventory_settings()

    def show_custom_invoice_dialog(self):
        dlg = CustomInvoiceDialog(self.settings_vm, self)
        if dlg.exec_():
            data = dlg.get_data()
            self.settings_vm.save_custom_invoice_settings(data)
            self.update_branding()
            QMessageBox.information(self, "Sukses", "Kustomisasi invoice berhasil disimpan.")
