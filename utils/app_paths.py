import os
import sys

def get_app_data_dir() -> str:
    """
    Mengembalikan path direktori yang dapat ditulisi untuk menyimpan data aplikasi 
    (database, log, invoice, dll).
    Jika berjalan sebagai executable PyInstaller, kembalikan %APPDATA%/LancarDinamicAdmin.
    Jika berjalan dari source (.py), kembalikan root project.
    """
    app_name = "LancarDinamicAdmin"
    
    if getattr(sys, 'frozen', False):
        # Berjalan sebagai PyInstaller bundle (.exe)
        # Gunakan %APPDATA%\LancarDinamicAdmin sebagai tempat penyimpanan
        appdata = os.getenv('APPDATA')
        if not appdata:
            # Fallback jika APPDATA tidak ditemukan
            appdata = os.path.expanduser('~')
            
        base_dir = os.path.join(appdata, app_name)
    else:
        # Berjalan dari source (.py)
        # Direktori ini berada di utils/, project root ada 1 level di atasnya
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
    # Pastikan direktori utama ada
    os.makedirs(base_dir, exist_ok=True)
    
    # Pastikan subdirektori penting juga ada
    os.makedirs(os.path.join(base_dir, "invoices"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "backups"), exist_ok=True)
        
    return base_dir
