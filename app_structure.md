# Struktur Aplikasi Pasien Bekam

## 📂 Folder & File Utama
- `main.py`: Entry point aplikasi.
- `main_window.py`: Jendela utama dengan sistem Tab (Dashboard, Terapis, Alat, Herbal, Analitik).
- `database.py`: Logika database SQLAlchemy & SQLite (WAL Mode).
- `settings.py`: Manajemen konfigurasi aplikasi (harga, diskon, dll).

## 🧩 Komponen UI (`components/`)
- `patient_form.py`: Form pendaftaran pasien baru.
- `patient_list.py`: Daftar pasien dengan fitur pencarian & edit/hapus.
- `visit_section.py`: Area pencatatan kunjungan & riwayat medis.
- `inventory_transaction_form.py`: Form transaksi (Masuk/Keluar) untuk Alat & Herbal.
- `patient_item_widget.py`: Desain baris item pasien dalam list.

## 🖼️ Jendela Dialog (`dialogs/`)
- `inventory_dialog.py`: Manajemen stok alat (Split View).
- `herbal_dialog.py`: Manajemen stok herbal (Split View).
- `therapist_dialog.py`: Manajemen data terapis.
- `invoice_dialog.py`: Preview & cetak invoice PDF.
- `herbal_form_dialog.py` / `inventory_form_dialog.py`: Form tambah/edit master data.
- `analytics_dialog.py`: Laporan statistik & grafik.

## ⚙️ Logic & Helpers (`helpers/`, `threads/`, `viewmodels/`)
- `helpers/invoice_helper.py`: Generator PDF untuk invoice.
- `helpers/backup_helper.py`: Backup database otomatis.
- `threads/visit_thread.py`: Background processing untuk simpan kunjungan.
- `viewmodels/visit_view_model.py`: Pengatur data kunjungan & caching.

## 🛠️ Utils
- `utils/styles.py`: Kumpulan desain CSS (Modern Soft Pastel).

---
*Status: Arsitektur Modular, State-Managed, dan Optimized.*
