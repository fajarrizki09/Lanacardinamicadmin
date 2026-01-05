from PySide6.QtCore import QThread, Signal
import shutil
import os
from datetime import datetime

class BackupThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, db_path, backup_dir):
        super().__init__()
        self.db_path = db_path
        self.backup_dir = backup_dir

    def run(self):
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_file)
            
            # Keep only last 7 backups
            backups = sorted([os.path.join(self.backup_dir, f) for f in os.listdir(self.backup_dir) if f.endswith('.db')])
            while len(backups) > 7:
                os.remove(backups.pop(0))
                
            self.finished.emit(True, backup_file)
        except Exception as e:
            self.finished.emit(False, str(e))
