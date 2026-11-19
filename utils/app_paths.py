import os
import sys

def get_app_data_dir() -> str:
    """
    Mengembalikan path direktori yang dapat ditulisi untuk menyimpan data aplikasi
    (database, log, invoice, dll).

    Urutan prioritas:
    1. Environment variable LANCAR_APP_DATA_DIR dari desktop shell.
    2. %APPDATA%/LancarDinamicAdmin jika berjalan sebagai executable PyInstaller.
    3. Root project jika berjalan dari source (.py).
    """
    app_name = "LancarDinamicAdmin"

    override_dir = os.getenv("LANCAR_APP_DATA_DIR")
    if override_dir and override_dir.strip():
        base_dir = os.path.abspath(override_dir.strip())
    elif getattr(sys, "frozen", False):
        appdata = os.getenv("APPDATA")
        if not appdata:
            appdata = os.path.expanduser("~")

        base_dir = os.path.join(appdata, app_name)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Pastikan direktori utama ada
    os.makedirs(base_dir, exist_ok=True)

    # Pastikan subdirektori penting juga ada
    os.makedirs(os.path.join(base_dir, "invoices"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "backups"), exist_ok=True)

    return base_dir
