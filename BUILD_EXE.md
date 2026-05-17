# Build EXE Windows

Panduan ini untuk membuat paket EXE/installer dari source code. Fokus build adalah source aplikasi, bukan data runtime klinik.

## Prasyarat

- Windows 10/11.
- Python 3.11.
- Virtualenv `.venv` sudah dibuat dan dependency `requirements.txt` sudah terinstall.
- PyInstaller tersedia di environment build. Jika belum ada, tambahkan sesuai workflow project sebelum build.
- Inno Setup 6 opsional, hanya diperlukan untuk membuat installer `.exe`.

Path Inno Setup yang dipakai `build.bat`:

```text
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

## Build Dengan Script

Dari root project:

```powershell
.\build.bat
```

Script akan:

1. memakai `.venv\Scripts\python.exe`;
2. menaikkan patch version via `scripts\bump_version.py`;
3. membersihkan `dist\LancarDinamicAdmin` dan `build\LancarDinamicAdmin`;
4. menjalankan PyInstaller onedir untuk `main.py`;
5. menyertakan `api/templates` dan `api/static`;
6. mengecualikan arsip UI native lama di `legacy_ui/`;
7. membuat installer dengan Inno Setup jika tersedia.

Output utama:

```text
dist\LancarDinamicAdmin\LancarDinamicAdmin.exe
dist\LancarDinamicAdmin_Setup_v<version>.exe
```

## Source Yang Perlu Ikut Build

Build perlu membawa source dan asset aplikasi, antara lain:

- `main.py`
- `api/`
- `helpers/`
- `utils/`
- `database.py`
- `settings.py`
- `version.py`
- `icon.ico`
- modul Python lain yang diimport aplikasi
- asset static offline di `api/static/`
- template HTML di `api/templates/`

`legacy_ui/` adalah arsip UI native lama dan tidak perlu ikut build EXE.

## Runtime Yang Harus Dikecualikan

Jangan ikutkan file/folder berikut ke ZIP, installer, atau EXE distribusi:

- `settings.json`
- `data.db`
- `*.db`
- `*.db-shm`
- `*.db-wal`
- `invoices/`
- `backups/`
- `logs/`
- `exports/` bila berisi data/laporan nyata
- `__pycache__/`
- `*.pyc`
- file PDF invoice hasil smoke test
- temporary test files
- ZIP lama hasil build sebelumnya
- `legacy_ui/`

Catatan: `settings.json` tidak boleh dimasukkan ke PyInstaller data. File ini dibuat runtime di device user.

## Cek Hasil Build

Gunakan folder bersih untuk uji hasil build:

1. Salin hasil `dist\LancarDinamicAdmin` ke folder test kosong.
2. Pastikan tidak ada `settings.json`, `data.db`, `invoices`, `backups`, atau `logs` bawaan developer.
3. Jalankan `LancarDinamicAdmin.exe`.
4. Pastikan dashboard terbuka.
5. Aktivasi lisensi di device test/user sesuai alur aplikasi.
6. Coba tambah pasien test.
7. Coba tambah kunjungan dasar.
8. Coba buat dan buka invoice test.
9. Tutup aplikasi dan buka lagi untuk memastikan runtime tersimpan lokal.

## Troubleshooting

### EXE tidak terbuka

- Jalankan dari PowerShell agar error terlihat:

```powershell
cd dist\LancarDinamicAdmin
.\LancarDinamicAdmin.exe
```

- Pastikan dependency PySide6/WebEngine ikut terbawa PyInstaller.
- Pastikan `api/templates` dan `api/static` ada di output.
- Cek log runtime di folder data aplikasi user jika build frozen menulis log.

### Port localhost bentrok

Aplikasi default memakai `127.0.0.1:8000` dan akan mencoba port berikutnya jika bentrok. Jika dashboard terus menunggu API siap:

- tutup proses aplikasi lama;
- cek Task Manager untuk proses Python/EXE lama;
- jalankan ulang aplikasi.

### PySide/WebEngine blank

- Pastikan build dilakukan dari virtualenv yang benar.
- Pastikan `PySide6==6.6.1` sesuai `requirements.txt`.
- Jangan menghapus folder PySide/WebEngine dari output `dist`.
- Coba build ulang setelah membersihkan folder `build` dan `dist`.

### Installer membawa data lama

Jika installer berisi database atau invoice lama, build dari workspace bersih dan pastikan runtime berikut tidak ada di sumber paket:

- `settings.json`
- `data.db`
- `invoices/`
- `backups/`
- `logs/`

Jangan memakai ZIP lama untuk distribusi ulang.
