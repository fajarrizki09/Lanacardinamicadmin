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

## Arah Penguatan Struktur

Fokus penguatan aplikasi adalah merapikan struktur dan menambah fitur operasional, bukan memindahkan bahasa atau framework.

- Rapikan struktur folder agar setiap bagian aplikasi mudah ditemukan dan dirawat.
- Pisahkan tanggung jawab utama menjadi database, UI, helper, viewmodel, thread/background task, dan utilitas.
- Perkuat `database.py` atau pecah bertahap jika logic database sudah terlalu besar.
- Pastikan UI hanya mengurus tampilan dan event pengguna, bukan query database langsung.
- Pastikan viewmodel menjadi penghubung antara UI dan database untuk pasien, kunjungan, terapis, stok, herbal, invoice, dan laporan.
- Simpan helper untuk pekerjaan pendukung seperti backup, import/export, invoice, PDF, Excel, dan format data.
- Tambahkan backup otomatis yang jelas jadwalnya, lokasi simpannya, dan rotasi file lamanya.
- Tambahkan export laporan PDF dan Excel untuk data penting.
- Tambahkan validasi stok alat dan herbal sebelum transaksi keluar, agar stok tidak minus atau data tidak rancu.
- Tambahkan laporan pasien dan kunjungan yang mudah difilter berdasarkan periode, pasien, terapis, dan jenis transaksi.

## Target Modul/Fitur Berikutnya

- `helpers/backup_helper.py`: backup otomatis, rotasi backup, dan pesan status backup.
- `helpers/export_helper.py`: export laporan PDF dan Excel.
- `viewmodels/inventory_store.py`: validasi stok alat dan herbal sebelum perubahan stok.
- `viewmodels/visit_view_model.py`: laporan kunjungan, filter periode, dan ringkasan transaksi.
- `database.py`: query laporan pasien, kunjungan, stok kritis, transaksi herbal, dan invoice.
- `api/static/modules/dashboard.js`: ringkasan dashboard admin berbasis data backend.
- `api/routes/analytics.py`: endpoint laporan dan statistik.
