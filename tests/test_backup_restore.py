import unittest
import os
import sqlite3
import tempfile
import shutil
from helpers.backup_helper import BackupHelper

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
