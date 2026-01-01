import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, QTimer

from utils.styles import STYLES
from components.patient_form import PatientForm
from components.patient_list import PatientList
from components.visit_section import VisitSection
from components.action_buttons import ActionButtons

from dialogs.edit_patient_dialog import EditPatientDialog
from dialogs.analytics_dialog import AnalyticsDialog
from dialogs.settings_dialog import SettingsDialog
from dialogs.therapist_dialog import TherapistDialog

from helpers.invoice_helper import InvoiceHelper
from helpers.import_export import ImportExportHelper
from helpers.backup_helper import BackupHelper
from threads.search_thread import SearchThread
from viewmodels.visit_view_model import VisitViewModel


class MainWindow(QMainWindow):
    def __init__(self, db, settings):
        super().__init__()
        self.setWindowTitle("🏥 Aplikasi Pasien Bekam - Versi Optimasi Pro")
        self.resize(1200, 700)
        self.db = db
        self.settings = settings
        self.import_export = ImportExportHelper(self, db)

        self.visit_vm = VisitViewModel(db, settings)
        self.invoice_helper = InvoiceHelper()
        self.backup_helper = BackupHelper()
        
        # Auto-backup on startup
        self.backup_helper.create_backup()

        self.search_thread = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.all_patients = []
        self.filtered_patients = []
        self.therapists_dict = {}
        self._therapists_cache_valid = False

        self.init_ui()
        self.refresh_patients()
        self.refresh_therapists()

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet(STYLES.get("main_window", ""))
        self.setCentralWidget(main_widget)

        self.sunnah_calendar_label = QLabel()
        self.update_sunnah_info()

        self.patient_form = PatientForm(self)
        self.patient_list = PatientList(self)
        self.visit_section = VisitSection(self)
        self.action_buttons = ActionButtons(self)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.addWidget(self.sunnah_calendar_label)
        left_layout.addWidget(self.patient_form)
        left_layout.addWidget(self.patient_list)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.addWidget(self.visit_section)
        right_layout.addLayout(self.action_buttons)

        content_layout = QHBoxLayout()
        content_layout.addLayout(left_layout, 1)
        content_layout.addLayout(right_layout, 2)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addLayout(content_layout)
        main_widget.setLayout(main_layout)

        self.connect_signals()

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

    def connect_signals(self):
        self.patient_form.add_btn.clicked.connect(self.add_patient)
        self.patient_list.update_btn.clicked.connect(self.on_update_patient_clicked)
        self.patient_list.delete_btn.clicked.connect(self.delete_patient)
        self.patient_list.search_input.textChanged.connect(self.search_patients)
        self.patient_list.patient_list.currentRowChanged.connect(self.load_selected_patient_data)

        self.visit_section.visit_btn.clicked.connect(self.catat_kunjungan)

        self.action_buttons.therapist_btn.clicked.connect(self.show_therapist_dialog)
        self.action_buttons.settings_btn.clicked.connect(self.show_settings_dialog)
        self.action_buttons.analytics_btn.clicked.connect(self.show_analytics)
        self.action_buttons.export_btn.clicked.connect(self.import_export.export_data)
        self.action_buttons.import_btn.clicked.connect(self.handle_import)

        self.visit_vm.visit_added.connect(self.on_visit_done)
        self.visit_vm.visit_failed.connect(self.on_visit_failed)

    def refresh_therapists(self, force=False):
        if not force and self._therapists_cache_valid and self.therapists_dict:
            return
        
        therapists = self.db.get_all_therapists(active_only=True)
        self.therapists_dict = {t.id: t for t in therapists}
        self._therapists_cache_valid = True

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

        self.db.add_patient(name, phone, address, gender)
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
        patient = self.db.get_patient_with_visits(patient_id)
        visits = [{
            "id": v.id,
            "date": v.date.isoformat() if hasattr(v.date, 'isoformat') else v.date,
            "price": v.price,
            "discount_applied": v.discount_applied
        } for v in patient.visits]

        dialog = EditPatientDialog(patient, visits, self)
        if dialog.exec_():
            new_name, new_phone, new_address, new_gender, updated_visits = dialog.get_data()

            try:
                self.db.update_patient(patient_id, new_name, new_phone, new_address, new_gender)
                
                from database import VisitData
                visit_data_list = [
                    VisitData(
                        id=v.get('id'),
                        date=v['date'],
                        price=v['price'],
                        discount_applied=v['discount_applied']
                    ) for v in updated_visits
                ]
                self.db.update_patient_visits(patient_id, visit_data_list)
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
            self.db.delete_patient(patient_id)
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

        self.all_patients = self.db.get_patients()
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
            self.visit_section.total_info_label.setText("Total kunjungan: 0 | Total titik: 0 | Total pemasukan: Rp 0")
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
            if confirm != QMessageBox.Yes:
                return

        patient_id = selected_patient[0]
        self.visit_vm.add_visit(patient_id, point_count, therapist_id)

    def on_visit_done(self, normal_price, discounted_price, discount_applied):
        discount_pct = self.settings.get_discount_percentage()
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

        # Generate Invoice
        invoice_path = None
        try:
            invoice_path = self.invoice_helper.generate_invoice(
                patient_name,
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                point_count,
                discounted_price,
                therapist_name
            )
            msg_invoice = f"\n\nInvoice telah dibuat: {os.path.basename(invoice_path)}"
        except Exception as e:
            msg_invoice = f"\n\nGagal membuat invoice: {str(e)}"

        msg = f"Kunjungan dicatat! {point_count} titik | Biaya: Rp {discounted_price:,}"
        if discount_applied:
            msg += f" (Diskon {discount_pct}%!)"
        msg += msg_invoice
        
        QMessageBox.information(self, "✅ Berhasil", msg)

        self.load_visits()
        self.refresh_patients()
        
        # Reset selection to maintain the current patient view
        selected_patient = self.patient_list.get_selected_patient()
        if selected_patient:
            patient_id = selected_patient[0]
            for i, p in enumerate(self.filtered_patients):
                if p[0] == patient_id:
                    self.patient_list.patient_list.setCurrentRow(i)
                    break

    def on_visit_failed(self, message):
        QMessageBox.critical(self, "Gagal", f"Terjadi kesalahan saat mencatat kunjungan:\n{message}")

    def handle_import(self):
        if self.import_export.import_data():
            self.refresh_patients()

    def show_analytics(self):
        dlg = AnalyticsDialog(self.db, self)
        dlg.exec_()

    def show_settings_dialog(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec_():
            price_per_point = self.settings.get_price_per_point()
            self.visit_section.update_price_from_points()
            QMessageBox.information(
                self, "Pengaturan Diperbarui",
                f"Harga per titik sekarang: Rp {price_per_point:,}"
            )

    def show_therapist_dialog(self):
        dlg = TherapistDialog(self.db, self)
        if dlg.exec_():
            self._therapists_cache_valid = False
            self.refresh_therapists(force=True)
            current_row = self.patient_list.patient_list.currentRow()
            if current_row >= 0:
                self.load_selected_patient_data(current_row)
