import os
import sys
import threading
import time
from contextlib import contextmanager

# Tambahkan direktori parent ke sys.path agar bisa import modul database utama
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import Database
from utils.app_paths import get_app_data_dir

base_dir = get_app_data_dir()

default_db_path = os.path.join(base_dir, "data.db")
db_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# Objek Koneksi Global yang bisa diimpor Router
db = Database(db_url)

_write_lock = threading.RLock()
_restore_in_progress = False
RESTORE_LOCK_STALE_SECONDS = int(os.getenv("RESTORE_LOCK_STALE_SECONDS", "900"))
restore_lock_path = os.path.join(base_dir, ".local", "restore.lock")


def _restore_lock_is_stale(path=None, stale_seconds=None):
	path = path or restore_lock_path
	stale_seconds = RESTORE_LOCK_STALE_SECONDS if stale_seconds is None else stale_seconds
	try:
		return (time.time() - os.path.getmtime(path)) > stale_seconds
	except FileNotFoundError:
		return False


def cleanup_stale_restore_lock(path=None, stale_seconds=None):
	path = path or restore_lock_path
	if os.path.exists(path) and _restore_lock_is_stale(path, stale_seconds):
		try:
			os.remove(path)
			try:
				import logging
				logging.getLogger("lancar.restore_lock").warning("Stale restore lock removed: %s", path)
			except Exception:
				pass
			return True
		except FileNotFoundError:
			return False
	return False


def is_restore_lock_active():
	cleanup_stale_restore_lock()
	return os.path.exists(restore_lock_path)


def is_restore_in_progress():
	return _restore_in_progress or is_restore_lock_active()


@contextmanager
def restore_write_lock():
	global _restore_in_progress
	with _write_lock:
		cleanup_stale_restore_lock()
		if os.path.exists(restore_lock_path):
			raise RuntimeError("Restore database sedang berjalan.")
		os.makedirs(os.path.dirname(restore_lock_path), exist_ok=True)
		with open(restore_lock_path, "x", encoding="utf-8") as lock_file:
			lock_file.write(str(time.time()))
		_restore_in_progress = True
		try:
			yield
		finally:
			_restore_in_progress = False
			try:
				os.remove(restore_lock_path)
			except FileNotFoundError:
				pass
