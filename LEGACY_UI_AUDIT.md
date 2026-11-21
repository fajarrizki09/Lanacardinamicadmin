# Legacy PySide UI Audit

Tanggal audit: 2026-05-09

Audit ini hanya membaca source secara statis. Tidak ada UI yang dijalankan, tidak ada file Python yang diubah, dan tidak ada database/API/license logic yang disentuh.

Update arsip: UI native lama sudah dipindahkan ke `legacy_ui/` sebagai arsip. Runtime aktif tidak boleh import `legacy_ui/`.

## Ringkasan

- Entry point desktop aktif adalah `main.py`.
- `main.py` membuat `QApplication`, menjalankan FastAPI lokal lewat thread, lalu membuka UI web di `QWebEngineView`.
- Backend aktif berada di `api/main.py` dan di-import oleh `main.py` saat menjalankan Uvicorn.
- Alur lisensi aktif sudah pindah ke halaman web `/license`; `legacy_ui/dialogs/license_dialog.py` hanya arsip.
- `legacy_ui/main_window.py`, `legacy_ui/components/`, `legacy_ui/dialogs/`, `legacy_ui/viewmodels/`, `legacy_ui/threads/`, dan `legacy_ui/helpers/import_export.py` adalah UI native lama. File-file ini tidak di-import oleh `main.py`.
- Tidak ditemukan penggunaan `PySide2`.
- Versi Qt yang dipakai source aktif dan legacy adalah `PySide6`.

## Entry Point Aktif

| File | Status | Bukti | Catatan |
|---|---|---|---|
| `main.py` | ACTIVE | Berisi `main()`, `if __name__ == "__main__"`, `QApplication`, `QWebEngineView`, dan `run_fastapi()` | Entry utama desktop app sekarang. |
| `api/main.py` | ACTIVE | Di-import dari `main.py` sebagai FastAPI app; juga bisa jalan mandiri dengan Uvicorn | Backend lokal untuk UI web. |
| `legacy_ui/main_window.py` | LEGACY ARCHIVE | Tidak ditemukan import dari `main.py` atau entry aktif | Hub UI native lama berbasis widget/dialog. |
| `attached_assets/main_*.py` | LEGACY | Snapshot asset lama yang meng-import `main_window` | Tidak dianggap entry aktif aplikasi utama. |

## Versi PySide

| Versi | Lokasi | Status | Risiko |
|---|---|---|---|
| `PySide6` | `main.py`, `legacy_ui/`, `helpers/license.py`, `helpers/import_export.py` | Dipakai | Runtime aktif memakai PySide6 untuk shell WebEngine; `legacy_ui/` hanya arsip. |
| `PySide2` | Tidak ditemukan | Tidak dipakai | Tidak ada risiko campuran PySide2/PySide6 dari source aktif. |

## File UI Native dan Status

| File | Status | Dipakai oleh | Rekomendasi |
|---|---|---|---|
| `main.py` | ACTIVE | Entry desktop utama | Pertahankan sebagai entry PySide WebEngine. |
| `api/main.py` | ACTIVE | `main.py` | Pertahankan sebagai backend lokal. |
| `helpers/license.py` | ACTIVE | `main.py`, `api/main.py`, `api/license_guard.py` | Pertahankan. Masih terkait license guard dan halaman lisensi web. |
| `legacy_ui/helpers/import_export.py` | LEGACY ARCHIVE | `legacy_ui/main_window.py`, `test_imports.py` | Helper dialog native lama; tidak dipakai runtime aktif. |
| `legacy_ui/main_window.py` | LEGACY ARCHIVE | Tidak ditemukan pemakai runtime aktif | Arsip UI native lama. Jangan jadikan entry point baru. |
| `legacy_ui/components/` | LEGACY ARCHIVE | `legacy_ui/main_window.py` dan dialog legacy | Arsip widget native lama. |
| `legacy_ui/dialogs/` | LEGACY ARCHIVE | `legacy_ui/main_window.py` dan dialog legacy | Arsip dialog native lama, termasuk `license_dialog.py`. |
| `legacy_ui/viewmodels/` | LEGACY ARCHIVE | `legacy_ui/main_window.py` dan dialog/component legacy | Arsip ViewModel UI native lama. |

## File PySide Tambahan

| File | Status | Dipakai oleh | Rekomendasi |
|---|---|---|---|
| `legacy_ui/threads/` | LEGACY ARCHIVE | `legacy_ui/main_window.py`, dialog legacy, viewmodel legacy | Arsip thread PySide native lama. |
| `attached_assets/*` | REMOVE CANDIDATE | Tidak dipakai entry aktif; berisi snapshot lama | Kandidat arsip/keluarkan dari distribusi setelah dicek ulang. |

## File yang Tidak Ditemukan Pemakaiannya

Dalam source aktif/non-asset, file berikut tidak ditemukan sebagai import target runtime:

- `legacy_ui/` tidak ditemukan sebagai import target runtime aktif.
- `main_window`, `components.*`, `dialogs.*`, `viewmodels.*`, dan `threads.*` tidak ditemukan di runtime aktif setelah arsip.

Catatan: `legacy_ui/main_window.py` tetap bukan kandidat hapus permanen cepat karena ia adalah root UI native lama. Banyak file legacy masih bergantung padanya sebagai hub.

## Risiko Jika Legacy Dibiarkan

- Ukuran source/build bisa tetap lebih besar karena modul native lama ikut terbawa jika spec/build mengumpulkan semua file.
- Developer baru bisa bingung antara UI web aktif dan UI native lama.
- Test import lama bisa memberi kesan fitur native masih menjadi jalur utama.
- Jika ada perubahan database helper, UI legacy bisa diam-diam rusak walau aplikasi utama tetap aman.

Risiko ini rendah untuk runtime utama selama `main.py` tetap menjadi entry point dan build tidak menjalankan `main_window.py`.

## Risiko Jika Legacy Langsung Dihapus

- Build/spec lama, installer, atau skrip internal mungkin masih mengasumsikan file native tersedia.
- Fitur license/import/export atau helper yang dibagi dengan dialog lama bisa ikut terganggu jika salah hapus dependency.
- Riwayat migrasi dari UI native ke UI web menjadi sulit dilacak.
- Ada kemungkinan import dinamis/manual yang tidak tertangkap audit statis.

Karena itu, penghapusan belum direkomendasikan pada tahap ini.

## Rekomendasi Tahap Berikutnya

1. Pertahankan `main.py`, `api/main.py`, `api/templates/license.html`, `api/static/modules/license.js`, dan `helpers/license.py` sebagai jalur aktif.
2. Perlakukan `legacy_ui/` sebagai arsip saja.
3. Pastikan ZIP/EXE distribusi tidak memakai `attached_assets/` dan tidak menjadikan `legacy_ui/main_window.py` sebagai entry point.
4. Jangan hapus permanen `legacy_ui/` sebelum ada fase cleanup khusus dan bukti build bersih.

## Verifikasi Audit

- Pencarian import dilakukan untuk `PySide2`, `PySide6`, `QApplication`, `main_window`, `dialogs.*`, `components.*`, dan `viewmodels.*`.
- `attached_assets/`, `.venv/`, `build/`, `dist/`, `.git/`, dan `__pycache__/` tidak dipakai sebagai dasar status runtime aktif.
- Tidak ada file Python yang diubah oleh audit ini.
