# Lancar Dynamic Admin

Aplikasi desktop klinik untuk operasional pasien, kunjungan, layanan, kasir herbal, stok, invoice, laporan, backup, audit log, dan lisensi. Aplikasi berjalan lokal di Windows dengan Python, FastAPI localhost, PySide WebEngine, SQLAlchemy, dan SQLite.

## Tech Stack

Dependency runtime mengikuti `requirements.txt`:

- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0.post1`
- `python-multipart==0.0.6`
- `PySide6==6.6.1`
- `SQLAlchemy==2.0.23`
- `matplotlib==3.8.2`
- `pandas==2.1.4`
- `openpyxl==3.1.2`
- `reportlab==4.0.7`

## Fitur Utama

- Manajemen pasien, terapis, layanan, kunjungan, dan invoice.
- Produk/herbal, transaksi kasir herbal, retur, koreksi stok, dan margin.
- Inventori alat/bahan dengan satuan dasar dan satuan kemasan.
- Laporan operasional, laporan owner, export Excel, audit log, dan backup.
- PDF invoice untuk layanan dan produk/herbal.
- Lisensi aplikasi lokal dengan aktivasi per device.
- Proteksi API lokal dengan `X-App-Token` per sesi.
- Proteksi endpoint sensitif dengan `X-Admin-Pin`.
- Filtering field sensitif dari response settings.
- Proteksi hard delete untuk data transaksi penting.

## Menjalankan Development

Panduan lengkap ada di [INSTALL.md](INSTALL.md).

Ringkas:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Menjalankan Test

Test backend/helper/API ringan tidak menjalankan UI PySide/WebEngine dan memakai database temporary.

```powershell
python -m unittest tests.test_security_token tests.test_admin_pin tests.test_settings_security tests.test_patients tests.test_herbals tests.test_delete_safety
```

## Build EXE

Panduan build lengkap ada di [BUILD_EXE.md](BUILD_EXE.md).

Build utama di Windows:

```powershell
.\build.bat
```

Script build membersihkan `dist\LancarDinamicAdmin` dan `build\LancarDinamicAdmin`, lalu membuat aplikasi PyInstaller onedir. Jika Inno Setup tersedia, installer juga dibuat di folder `dist`.

## File Runtime Yang Tidak Boleh Dibagikan

Jangan ikutkan file/folder ini ke Git, ZIP, installer, atau paket distribusi:

- `settings.json`
- `data.db`
- `*.db`
- `invoices/`
- `backups/`
- `logs/`
- `__pycache__/`
- `*.pyc`
- file PDF invoice hasil smoke test
- temporary test files
- `exports/` jika berisi laporan/data klinik nyata

`settings.json`, database, invoice, backup, dan log dibuat di runtime pada device user. Aktivasi lisensi dilakukan di device user, bukan di mesin developer.

## Checklist Rilis

Checklist lengkap ada di [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Minimal sebelum dibagikan:

```powershell
python -m py_compile main.py api\main.py database.py settings.py
python -m unittest tests.test_security_token tests.test_admin_pin tests.test_settings_security tests.test_patients tests.test_herbals tests.test_delete_safety
git diff --check
```

Pastikan build dicoba dari folder bersih dan tidak membawa data klinik lama.
