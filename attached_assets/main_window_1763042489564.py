from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

from components.patient_form import PatientForm
from components.patient_list import PatientList
from components.visit_section import VisitSection
from components.action_buttons import ActionButtons

from dialogs.edit_patient_dialog import EditPatientDialog
from dialogs.analytics_dialog import AnalyticsDialog
from dialogs.settings_dialog import SettingsDialog
from dialogs.therapist_dialog import TherapistDialog

from helpers.import_export import ImportExportHelper
from threads.search_thread import SearchThread
from viewmodels.visit_view_model import VisitViewModel


class MainWindow(QMainWindow):
    def __init__(self, db, settings):
        super().__init__()
        self.setWindowTitle("🏥 Aplikasi Pasien Bekam - Versi Optimasi")
        self.resize(1200, 700)
        self.db = db
        self.settings = settings
        self.import_export = ImportExportHelper(self, db)

        self.visit_vm = VisitViewModel(db, settings)

        self.search_thread = None
        self.all_patients = []
        self.filtered_patients = []
        self.therapists_dict = {}

        self.init_ui()
        self.refresh_patients()
        self.refresh_therapists()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        self.patient_form = PatientForm(self)
        self.patient_list = PatientList(self)
        self.visit_section = VisitSection(self)
        self.action_buttons = ActionButtons(self)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
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

    def refresh_therapists(self):
        therapists = self.db.get_all_therapists(active_only=True)
        self.therapists_dict = {t.id: t for t in therapists}

    def add_patient(self):
        name, phone, address, gender = self.patient_form.get_inputs()

        if not name:
            QMessageBox.warning(self, "Error", "Nama tidak boleh kosong")
            return
        if not phone.isdigit():
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
            self.refresh_patients()
            self.visit_section.visit_table.setRowCount(0)
            self.visit_section.total_info_label.setText("Total kunjungan: 0 | Total pemasukan: Rp 0")
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
        text = text.strip().lower()

        if not text:
            if self.search_thread and self.search_thread.isRunning():
                self.search_thread.cancel()
                self.search_thread.wait()
            self.filtered_patients = self.all_patients
            self.patient_list.update_list(self.filtered_patients)
            return

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
            self.visit_section.total_info_label.setText("Total kunjungan: 0 | Total pemasukan: Rp 0")
            self.visit_section.therapist_combo.clear()
            self.visit_section.therapist_combo.addItem("-- Pilih Pasien Dulu --", None)
            return
        
        selected_patient = self.patient_list.get_selected_patient()
        if selected_patient and len(selected_patient) >= 4:
            patient_gender = selected_patient[3]
            self.visit_section.set_patient_gender(patient_gender)
            
            filtered_therapists = self.db.get_therapists_by_gender(patient_gender)
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

        try:
            price = int(self.visit_section.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Harga kunjungan harus berupa angka")
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
        self.visit_vm.add_visit(patient_id, price, therapist_id)

    def on_visit_done(self, normal_price, discounted_price, discount_applied):
        discount_pct = self.settings.get_discount_percentage()
        msg = f"Kunjungan dicatat! Biaya: Rp {discounted_price:,}"
        if discount_applied:
            msg += f" (Diskon {discount_pct}%!)"
        QMessageBox.information(self, "✅ Berhasil", msg)

        self.load_visits()
        self.refresh_patients()

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
            base_price = self.settings.get_base_price()
            self.visit_section.price_input.setText(str(base_price))

    def show_therapist_dialog(self):
        dlg = TherapistDialog(self.db, self)
        if dlg.exec_():
            self.refresh_therapists()
            current_row = self.patient_list.patient_list.currentRow()
            if current_row >= 0:
                self.load_selected_patient_data(current_row)
