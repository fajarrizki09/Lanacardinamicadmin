import unittest
import os
import sqlite3
import tempfile
import shutil
import time
from helpers.backup_helper import BackupHelper
from tests.api_test_utils import app_headers, client
from api import database_manager

class TestBackupRestoreHardening(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.tmp.name, "test_data.db")
        self.backup_dir = os.path.join(self.tmp.name, "backups")
        
        # Create a valid SQLite db
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY);")
        conn.close()
        
        self.helper = BackupHelper(db_path=self.db_path, backup_dir=self.backup_dir, log_dir=self.tmp.name)

    def tearDown(self):
        if os.path.exists(database_manager.restore_lock_path):
            try:
                os.remove(database_manager.restore_lock_path)
            except FileNotFoundError:
                pass
        self.tmp.cleanup()

    def test_backup_and_restore_success(self):
        backup_path = self.helper.create_backup(daily=False)
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        status = self.helper.restore_backup(backup_path)
        self.assertTrue(status.get("success", False))

    def test_restore_fails_on_corrupted_backup(self):
        backup_path = self.helper.create_backup(daily=False)
        self.assertIsNotNone(backup_path)
        
        # Corrupt the backup file
        with open(backup_path, "wb") as f:
            f.write(b"NOT A VALID SQLITE DATABASE BUT CORRUPTED BITS")
            
        status = self.helper.restore_backup(backup_path)
        self.assertFalse(status.get("success", True))
        
        # Could fail with 'file is not a database', 'korup', or 'dibatalkan'
        message = status.get("message", "").lower()
        self.assertTrue("korup" in message or "gagal" in message or "dibatalkan" in message, f"Unexpected message: {message}")
        
        # Check that original DB is intact and still valid
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        self.assertEqual(result[0].lower(), "ok")

    def test_restore_lock_blocks_write_requests(self):
        os.makedirs(os.path.dirname(database_manager.restore_lock_path), exist_ok=True)
        with open(database_manager.restore_lock_path, "w", encoding="utf-8") as lock_file:
            lock_file.write(str(time.time()))

        response = client().post(
            "/add_patient",
            data={"name": "Pasien Lock", "phone": "081234567890"},
            headers=app_headers("1234"),
        )

        self.assertEqual(response.status_code, 423)

    def test_second_restore_lock_is_rejected(self):
        with database_manager.restore_write_lock():
            with self.assertRaises(RuntimeError):
                with database_manager.restore_write_lock():
                    pass

    def test_stale_restore_lock_can_be_cleaned(self):
        os.makedirs(os.path.dirname(database_manager.restore_lock_path), exist_ok=True)
        with open(database_manager.restore_lock_path, "w", encoding="utf-8") as lock_file:
            lock_file.write("stale")
        old_time = time.time() - 3600
        os.utime(database_manager.restore_lock_path, (old_time, old_time))

        removed = database_manager.cleanup_stale_restore_lock(stale_seconds=1)

        self.assertTrue(removed)
        self.assertFalse(os.path.exists(database_manager.restore_lock_path))
