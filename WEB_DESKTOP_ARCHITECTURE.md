# Web Desktop Architecture

Dokumen ini menetapkan arah project sebagai Web Desktop App: aplikasi desktop Python yang memakai FastAPI lokal sebagai backend dan PySide6 WebEngine sebagai shell desktop.

## Arsitektur Aktif

| Bagian | File/Folder | Peran |
|---|---|---|
| Desktop shell | `main.py` | Entry point utama aplikasi. Membuat `QApplication`, menjalankan FastAPI lokal, memilih port localhost, dan membuka UI web di `QWebEngineView`. |
| Backend lokal | `api/main.py` | FastAPI app untuk endpoint lokal, middleware token, license guard, route HTML, static files, dan API bisnis. |
| Template UI | `api/templates/` | HTML utama yang dirender oleh FastAPI. |
| Asset UI | `api/static/` | JavaScript, CSS, dan asset web untuk UI utama aplikasi. |
| Halaman lisensi web | `api/templates/license.html`, `api/static/modules/license.js` | UI aktif untuk aktivasi/verifikasi lisensi dari WebEngine. |
| License helper | `helpers/license.py` | Helper license yang masih dipakai oleh shell desktop dan backend. |

Jalur runtime normal:

1. User menjalankan `python main.py` atau EXE yang entry point-nya `main.py`.
2. `main.py` membuat session desktop dan menjalankan FastAPI lokal di `127.0.0.1`.
3. Jika lisensi belum valid, `main.py` tetap membuka WebEngine dan mengarahkannya ke `/license`.
4. Jika lisensi valid, `main.py` membuka dashboard utama di `/`.
5. `api/main.py` menyajikan halaman utama, halaman lisensi, static asset, dan endpoint API.
6. PySide6 `QWebEngineView` menampilkan UI web dari backend lokal.
7. Request API dari frontend memakai proteksi lokal yang sudah ada, termasuk `X-App-Token` dan `X-Admin-Pin` untuk endpoint sensitif.

## Legacy Native UI

File/folder UI native lama sudah dipindahkan ke `legacy_ui/` sebagai arsip. Folder ini tidak termasuk runtime aktif dan tidak boleh dijadikan tempat pengembangan fitur bisnis baru.

| File/Folder | Status | Catatan |
|---|---|---|
| `legacy_ui/main_window.py` | LEGACY ARCHIVE | Window native lama berbasis PySide6 widgets. Tidak menjadi entry point aktif. |
| `legacy_ui/components/` | LEGACY ARCHIVE | Widget native lama yang dipakai oleh `legacy_ui/main_window.py` dan dialog legacy. |
| `legacy_ui/dialogs/` | LEGACY ARCHIVE | Dialog native lama, termasuk `license_dialog.py`. Startup aktif sudah memakai halaman web `/license`. |
| `legacy_ui/viewmodels/` | LEGACY ARCHIVE | ViewModel untuk UI native lama. |
| `legacy_ui/threads/` | LEGACY ARCHIVE | Thread PySide yang hanya dipakai jalur UI native lama. |
| `legacy_ui/helpers/import_export.py` | LEGACY ARCHIVE | Helper import/export lama berbasis dialog PySide native. Tidak dipakai runtime aktif. |

Legacy UI tetap dipertahankan untuk saat ini agar riwayat migrasi tidak hilang. Jangan import folder `legacy_ui/` dari runtime aktif.

## Aturan Pengembangan Fitur Baru

- Jangan menambah fitur bisnis baru di `legacy_ui/main_window.py`, `legacy_ui/components/`, `legacy_ui/dialogs/`, `legacy_ui/viewmodels/`, atau helper lama di `legacy_ui/helpers/`.
- Fitur bisnis baru harus dibuat lewat UI web di `api/templates/` dan `api/static/`.
- Logic backend untuk fitur baru harus masuk lewat API lokal di `api/main.py` atau modul backend terkait.
- PySide6 dipakai sebagai shell desktop, bukan sebagai framework UI utama.
- Jangan menghidupkan kembali `legacy_ui/dialogs/license_dialog.py` untuk alur lisensi startup. Alur lisensi aktif ada di halaman web `/license`.
- Jika fitur membutuhkan aksi admin, tetap gunakan proteksi `X-Admin-Pin` yang sudah ada.
- Jika fitur memakai API lokal, tetap ikuti proteksi `X-App-Token` per sesi.
- Jangan mengubah database schema, license validation, atau alur invoice dari file legacy.

## Build dan Distribusi

- Build EXE/distribusi harus memakai `main.py` sebagai entry point.
- Jangan memakai `legacy_ui/main_window.py` sebagai entry point build baru.
- Pastikan `api/templates/` dan `api/static/` ikut dalam paket distribusi karena itulah UI utama.
- Pastikan `api/templates/license.html` dan `api/static/modules/license.js` ikut dalam paket distribusi karena dipakai saat startup license.
- `legacy_ui/dialogs/license_dialog.py` boleh tetap ada di source sebagai arsip, tetapi tidak menjadi dependency startup aktif.
- `legacy_ui/` boleh tetap ada di source, tetapi tidak boleh menjadi arah pengembangan baru atau dependency build runtime.
- File runtime tetap tidak boleh ikut distribusi: `settings.json`, `data.db`, `*.db`, `invoices/`, `backups/`, `logs/`, `__pycache__/`, `*.pyc`, dan file PDF hasil test/smoke.

## Rekomendasi Maintenance

1. Pakai `LEGACY_UI_AUDIT.md` sebagai rujukan detail status file.
2. Saat review PR, tolak fitur bisnis baru yang ditambahkan ke UI native legacy.
3. Jika perlu cleanup permanen, buat fase khusus setelah build EXE dan test backend lulus.
4. Jika ada file legacy yang masih dibutuhkan build, dokumentasikan alasannya sebelum mengembalikannya ke runtime aktif.
