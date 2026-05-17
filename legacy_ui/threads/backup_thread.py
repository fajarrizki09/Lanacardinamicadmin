from PySide6.QtCore import QThread, Signal
from helpers.backup_helper import BackupHelper

class BackupThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, db_path, backup_dir, daily=False, max_backups=10):
        super().__init__()
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.daily = daily
        self.max_backups = max_backups

    def run(self):
        helper = BackupHelper(self.db_path, self.backup_dir, max_backups=self.max_backups)
        backup_file = helper.create_backup(daily=self.daily)
        status = helper.get_status()
        self.finished.emit(bool(backup_file), status["message"] if not backup_file else backup_file)
