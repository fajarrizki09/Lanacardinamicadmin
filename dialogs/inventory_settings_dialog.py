from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QPushButton, QFormLayout, QMessageBox
)
from utils.styles import STYLES

class InventorySettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Pengaturan Pengurangan Stok Otomatis")
        self.setMinimumWidth(400)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel("Tentukan berapa banyak stok berkurang secara otomatis\nsetiap kali kunjungan dicatat:")
        info_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(info_label)

        self.form_layout = QFormLayout()
        
        config = self.settings.get_inventory_config()
        
        self.pisau_spin = QSpinBox()
        self.pisau_spin.setRange(0, 10)
        self.pisau_spin.setValue(config.get("Pisau Bedah", 1))
        self.pisau_spin.setSuffix(" pcs")
        
        self.tisu_spin = QSpinBox()
        self.tisu_spin.setRange(0, 50)
        self.tisu_spin.setValue(config.get("Tisu", 2))
        self.tisu_spin.setSuffix(" unit")

        self.form_layout.addRow("Pisau Bedah per Pasien:", self.pisau_spin)
        self.form_layout.addRow("Tisu per Kunjungan:", self.tisu_spin)
        
        layout.addLayout(self.form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Simpan")
        save_btn.setStyleSheet(STYLES["add_button"])
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Batal")
        cancel_btn.setStyleSheet(STYLES["delete_button"])
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def save_settings(self):
        new_config = {
            "Pisau Bedah": self.pisau_spin.value(),
            "Tisu": self.tisu_spin.value()
        }
        self.settings.set_inventory_config(new_config)
        QMessageBox.information(self, "Berhasil", "Pengaturan stok otomatis berhasil diperbarui!")
        self.accept()
