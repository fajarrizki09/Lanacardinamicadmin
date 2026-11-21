import logging

from PySide6.QtCore import QThread, QTimer, Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from helpers.license import (
    LICENSE_ERROR_MESSAGE,
    LICENSE_STATUS_NETWORK_ERROR,
    LICENSE_STATUS_OK,
    get_last_license_message,
    get_saved_clinic_id,
    get_saved_license_key,
    save_license_key,
    verify_license,
)


class LicenseVerifyWorker(QThread):
    finished = Signal(str, str)

    def __init__(self, license_key: str, clinic_id: str, parent=None):
        super().__init__(parent)
        self.license_key = license_key
        self.clinic_id = clinic_id

    def run(self):
        try:
            save_license_key(self.license_key, clinic_id=self.clinic_id)
            status = verify_license(exit_on_fail=False, show_message=False)
            self.finished.emit(status, get_last_license_message())
        except Exception as exc:
            logging.exception("License verification failed")
            self.finished.emit(LICENSE_STATUS_NETWORK_ERROR, str(exc))


class LicenseDialog(QDialog):
    def __init__(self, status: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aktivasi Lisensi")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._verified = False
        self._worker = None
        self._busy = False

        self.init_ui(status)
        self.bind_shortcuts()

    @property
    def verified(self):
        return self._verified

    def init_ui(self, status):
        self.setStyleSheet("""
            QDialog { background: #f6f8fb; color: #17231f; }
            QLabel#title { font-size: 24px; font-weight: 700; color: #10231d; }
            QLabel#subtitle { font-size: 13px; color: #60706a; }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cfd8d3;
                border-radius: 8px;
                padding: 13px 14px;
                font-size: 15px;
                selection-background-color: #0f766e;
            }
            QLineEdit:focus { border: 1px solid #0f766e; }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 11px 16px;
                font-weight: 650;
            }
            QPushButton#primary { background: #0f766e; color: white; }
            QPushButton#primary:disabled { background: #9fb8b2; }
            QPushButton#secondary { background: #e9efec; color: #1f332d; }
            QPushButton#secondary:disabled { color: #7c8a86; }
            QLabel#status { font-size: 12px; padding: 8px 0; }
        """)

        title = QLabel("Aktivasi Lisensi")
        title.setObjectName("title")

        subtitle = QLabel("Masukkan lisensi untuk mengaktifkan aplikasi")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Tempel kode lisensi di sini")
        self.license_input.setText(get_saved_license_key())
        self.license_input.setClearButtonEnabled(True)
        self.license_input.returnPressed.connect(self.activate)

        self.clinic_id_input = QLineEdit()
        self.clinic_id_input.setPlaceholderText("Masukkan Clinic ID")
        self.clinic_id_input.setText(get_saved_clinic_id())
        self.clinic_id_input.setClearButtonEnabled(True)
        self.clinic_id_input.returnPressed.connect(self.activate)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        if status == LICENSE_STATUS_NETWORK_ERROR:
            self.set_status("Tidak ada koneksi internet. Sambungkan internet lalu coba aktivasi lagi.", "error")
        elif status:
            self.set_status("Lisensi belum aktif atau perlu diverifikasi ulang.", "muted")

        self.loading = QProgressBar()
        self.loading.setRange(0, 0)
        self.loading.setTextVisible(False)
        self.loading.setFixedHeight(6)
        self.loading.hide()

        self.activate_btn = QPushButton("Aktivasi")
        self.activate_btn.setObjectName("primary")
        self.activate_btn.clicked.connect(self.activate)

        self.paste_btn = QPushButton("Tempel dari Clipboard")
        self.paste_btn.setObjectName("secondary")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addWidget(self.paste_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.activate_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.license_input)
        layout.addWidget(self.clinic_id_input)
        layout.addWidget(self.status_label)
        layout.addWidget(self.loading)
        layout.addLayout(button_layout)

    def bind_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+V"), self, activated=self.paste_from_clipboard)

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.license_input.setText(text)
            self.license_input.setFocus(Qt.ShortcutFocusReason)
            self.license_input.selectAll()

    def set_status(self, message, kind="muted"):
        colors = {
            "success": "#0f766e",
            "error": "#b42318",
            "muted": "#60706a",
        }
        self.status_label.setStyleSheet(f"color: {colors.get(kind, colors['muted'])};")
        self.status_label.setText(message)

    def set_busy(self, busy):
        self._busy = busy
        self.license_input.setEnabled(not busy)
        self.clinic_id_input.setEnabled(not busy)
        self.activate_btn.setEnabled(not busy)
        self.paste_btn.setEnabled(not busy)
        self.loading.setVisible(busy)
        self.activate_btn.setText("Memverifikasi..." if busy else "Aktivasi")

    def validate_license_key(self, license_key, clinic_id):
        if not license_key:
            self.set_status("Kode lisensi tidak boleh kosong.", "error")
            return False
        if len(license_key) <= 10:
            self.set_status("Format lisensi terlalu pendek. Periksa kembali kode lisensi.", "error")
            return False
        if not clinic_id:
            self.set_status("Clinic ID wajib diisi.", "error")
            return False
        return True

    def activate(self):
        license_key = self.license_input.text().strip()
        clinic_id = self.clinic_id_input.text().strip()
        if not self.validate_license_key(license_key, clinic_id):
            return

        self.set_busy(True)
        self.set_status("Menghubungi server lisensi...", "muted")

        self._worker = LicenseVerifyWorker(license_key, clinic_id, self)
        self._worker.finished.connect(self.on_verify_finished)
        self._worker.start()

    def on_verify_finished(self, status: str, message: str):
        self._worker = None

        if status == LICENSE_STATUS_OK:
            self._verified = True
            self.set_status("Lisensi aktif", "success")
            QTimer.singleShot(1000, self.accept)
            return

        self.set_busy(False)
        if status == LICENSE_STATUS_NETWORK_ERROR:
            self.set_status(message or "Tidak ada koneksi internet. Periksa koneksi lalu coba lagi.", "error")
            return

        self.set_status(message or LICENSE_ERROR_MESSAGE, "error")

    def closeEvent(self, event):
        if self._busy:
            event.ignore()
            return
        event.accept()
