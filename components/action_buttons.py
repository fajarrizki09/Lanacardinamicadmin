from PySide6.QtWidgets import QHBoxLayout, QPushButton
from utils.styles import STYLES

class ActionButtons(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        self.therapist_btn = QPushButton("Kelola Terapis")
        self.settings_btn = QPushButton("Pengaturan")
        self.analytics_btn = QPushButton("Analitik")
        self.export_btn = QPushButton("Export")
        self.import_btn = QPushButton("Import")
        
        self.therapist_btn.setStyleSheet(STYLES["update_button"])
        self.settings_btn.setStyleSheet(STYLES["settings_button"])
        self.analytics_btn.setStyleSheet(STYLES["analytics_button"])
        self.export_btn.setStyleSheet(STYLES["action_button"])
        self.import_btn.setStyleSheet(STYLES["action_button"])
        
        self.addWidget(self.therapist_btn)
        self.addWidget(self.settings_btn)
        self.addWidget(self.analytics_btn)
        self.addWidget(self.export_btn)
        self.addWidget(self.import_btn)
