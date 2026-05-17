import os
import shutil
import sqlite3
from datetime import datetime

class BackupHelper:
    def __init__(self, db_path="data.db", backup_dir="backups", max_backups=10, log_dir="logs"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = max(1, int(max_backups or 10))
        self.log_dir = log_dir
        self.log_path = os.path.join(self.log_dir, "backup.log")
        self.last_status = {
            "success": False,
            "message": "Backup belum dijalankan.",
            "path": None,
            "created_at": None,
        }
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"{timestamp} - {message}\n")
        except Exception:
            pass

    def _set_status(self, success, message, path=None):
        self.last_status = {
            "success": bool(success),
            "message": message,
            "path": path,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._log(f"{'SUCCESS' if success else 'FAILED'} - {message}" + (f" - {path}" if path else ""))
        return self.last_status

    def get_status(self):
        return dict(self.last_status)

    def rotate_backups(self):
        backups = self._list_backup_files()
        removed = []
        if len(backups) > self.max_backups:
            for old_backup in backups[: len(backups) - self.max_backups]:
                os.remove(old_backup)
                removed.append(old_backup)
        return removed

    def _list_backup_files(self):
        backups = sorted(
            [
                os.path.join(root, f)
                for root, _, files in os.walk(self.backup_dir)
                for f in files
                if f.endswith(".db")
            ],
            key=os.path.getmtime,
        )
        return backups

    def _dated_backup_dir(self):
        target_dir = os.path.join(self.backup_dir, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def _copy_sqlite_online(self, destination):
        source = sqlite3.connect(self.db_path, timeout=10)
        try:
            target = sqlite3.connect(destination)
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            source.close()

    def _copy_sidecars(self, destination):
        copied = []
        for suffix in ("-wal", "-shm"):
            source_sidecar = f"{self.db_path}{suffix}"
            if os.path.exists(source_sidecar):
                target_sidecar = f"{destination}{suffix}"
                shutil.copy2(source_sidecar, target_sidecar)
                copied.append(target_sidecar)
        return copied

    def create_backup(self, daily=False):
        if not os.path.exists(self.db_path):
            self._set_status(False, f"Database tidak ditemukan: {self.db_path}")
            return None

        dated_dir = self._dated_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(dated_dir, backup_filename)

        if daily:
            today_prefix = datetime.now().strftime("backup_%Y%m%d_")
            today_backups = [
                path for path in self._list_backup_files()
                if os.path.basename(path).startswith(today_prefix)
            ]
            if today_backups:
                latest = sorted(today_backups, key=os.path.getmtime)[-1]
                self._set_status(True, "Backup harian sudah tersedia.", latest)
                return latest

        try:
            self._copy_sqlite_online(backup_path)
            self._copy_sidecars(backup_path)
            removed = self.rotate_backups()
            message = "Backup berhasil dibuat."
            if removed:
                message += f" {len(removed)} backup lama dihapus."
            self._set_status(True, message, backup_path)
            return backup_path
        except Exception as exc:
            self._set_status(False, f"Gagal membuat backup: {exc}")
            return None

    def restore_backup(self, backup_path):
        backup_root = os.path.abspath(self.backup_dir)
        backup_path = os.path.abspath(backup_path)
        if os.path.commonpath([backup_root, backup_path]) != backup_root:
            return self._set_status(False, "Path backup tidak valid.")
        if not os.path.exists(backup_path):
            return self._set_status(False, f"File backup tidak ditemukan: {backup_path}")
        if not backup_path.lower().endswith(".db"):
            return self._set_status(False, "File restore harus berformat .db")

        pre_restore = self.create_backup(daily=False)
        if not pre_restore:
            return self._set_status(False, "Restore dibatalkan karena backup database aktif gagal dibuat.")

        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)) or ".", exist_ok=True)
            shutil.copy2(backup_path, self.db_path)
            for suffix in ("-wal", "-shm"):
                target_sidecar = f"{self.db_path}{suffix}"
                if os.path.exists(target_sidecar):
                    try:
                        os.remove(target_sidecar)
                    except OSError as exc:
                        shutil.copy2(pre_restore, self.db_path)
                        return self._set_status(
                            False,
                            f"Database masih terkunci, gagal membersihkan {os.path.basename(target_sidecar)}: {exc}",
                            backup_path,
                        )

            # Hardening: Run PRAGMA integrity_check after restore
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                conn.close()
                if not result or result[0].lower() != "ok":
                    raise Exception(f"Integritas file backup korup: {result[0] if result else 'Unknown'}")
            except Exception as e:
                # Rollback!
                shutil.copy2(pre_restore, self.db_path)
                return self._set_status(False, f"Restore dibatalkan: {e}", backup_path)

            self.rotate_backups()
            return self._set_status(True, "Restore backup berhasil.", backup_path)
        except Exception as exc:
            return self._set_status(False, f"Gagal restore backup: {exc}", backup_path)
