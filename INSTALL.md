# Install Development Windows

Panduan ini untuk menjalankan aplikasi dari source code di mesin development Windows. Jangan gunakan database produksi/user untuk test development.

## Syarat

- Windows 10/11.
- Python 3.11 direkomendasikan.
- Git opsional, jika source diambil dari repository.
- Akses terminal PowerShell.

Dependency aplikasi mengikuti `requirements.txt`:

- FastAPI dan Uvicorn untuk backend lokal.
- PySide6 untuk desktop WebEngine.
- SQLAlchemy dan SQLite untuk database lokal.
- Pandas/OpenPyXL untuk laporan Excel.
- ReportLab untuk PDF invoice.
- Matplotlib untuk chart/laporan.

## Setup Virtualenv

Dari folder project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika PowerShell menolak aktivasi virtualenv, jalankan PowerShell sebagai user biasa lalu izinkan script untuk sesi ini:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Menjalankan Aplikasi

```powershell
python main.py
```

Aplikasi akan:

- menjalankan FastAPI lokal di `127.0.0.1`;
- memilih port berikutnya jika `8000` sedang dipakai;
- membuka UI desktop PySide WebEngine;
- membuat database/settings runtime bila belum ada.

## Menjalankan Test

Test yang disarankan sebelum mengubah atau build:

```powershell
python -m unittest tests.test_security_token tests.test_admin_pin tests.test_settings_security tests.test_patients tests.test_herbals tests.test_delete_safety
```

Test tersebut tidak menjalankan UI PySide/WebEngine dan memakai database temporary. Jangan arahkan test ke `data.db` produksi/user.

## Catatan Database Development

Runtime lokal dapat membuat file berikut:

- `settings.json`
- `data.db`
- `data.db-shm`
- `data.db-wal`
- `invoices/`
- `backups/`
- `logs/`
- `exports/`

File/folder tersebut adalah data runtime dan tidak boleh ikut Git, ZIP, EXE, atau installer distribusi.

## Troubleshooting

### Port localhost bentrok

Jika muncul pesan port `8000` dipakai, aplikasi akan memakai port berikutnya, misalnya `8001`. Tutup proses lama jika aplikasi tidak bisa siap.

### PySide/WebEngine tidak terbuka

- Pastikan menjalankan di desktop Windows, bukan environment headless.
- Pastikan dependency `PySide6==6.6.1` terinstall dari virtualenv aktif.
- Coba jalankan ulang dari PowerShell biasa, bukan terminal service/background.

### Database error saat development

Untuk data development kosong, tutup aplikasi lalu hapus file runtime development seperti `data.db`, `data.db-shm`, dan `data.db-wal`. Jangan hapus database klinik/user produksi.

### License

Jangan menulis license key asli di dokumentasi, source code, test, atau commit. Aktivasi lisensi dilakukan di device user/klinik.
