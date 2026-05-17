# Catatan Perubahan

## v1.7.25 - 2026-05-07

- Menambahkan error handling global FastAPI agar user menerima pesan ramah, sementara detail error tersimpan di folder `logs/`.
- Menambahkan PIN admin lokal dengan hash, lock screen, auto-lock, UI ubah PIN, dan proteksi aksi sensitif seperti restore, hapus data, koreksi stok, setting, serta license.
- Merapikan migration database dengan `app_meta.db_version`, backup otomatis sebelum migration, log migration, audit log, dan kolom `patients.created_at` untuk laporan owner.
- Menambahkan test otomatis bisnis inti untuk database, pasien, kunjungan, stok, invoice, diskon/free visit, backup/restore, admin PIN, audit log, first-run, owner report, dan export Excel.
- Merapikan dashboard: format rupiah konsisten lewat `formatRupiah()`, card lebih aman untuk nominal panjang, dan layout lebih responsif.
- Memperkuat layout invoice PDF A5 dengan wrapping teks panjang, guard overflow halaman, header tabel lanjutan, dan perlindungan footer/signature.
- Menambahkan first-run wizard untuk setup klinik awal dan demo data yang bisa diisi/dihapus dengan penanda demo.
- Menambahkan Laporan Owner dengan ringkasan pendapatan, kunjungan, pasien baru, follow-up, top layanan, top herbal, pasien loyal, dan pilihan sumber pasien baru.
- Menambahkan export Excel laporan penting serta export data operasional lengkap termasuk pasien, kunjungan, layanan, terapis, herbal, inventory, transaksi, audit log, dan settings aman.
- Menambahkan halaman Bantuan & Support dengan info aplikasi, lokasi database/backup/log/export, panduan fitur utama, serta tombol buka folder.
- Merapikan CRM row note/rekomendasi agar rata kiri, tidak dobel hitung hari, dan tetap aman saat teks panjang.
- Build installer Windows berhasil untuk versi `1.7.25`.

## 2026-05-02 - Pencatatan Lisensi dan Settings Web

- Mencatat penguatan status lisensi aplikasi agar perubahan terkait lisensi tidak hilang dari catatan rilis internal.
- Menambahkan section aturan diskon dinamis pada Settings web/API, sehingga pengaturan diskon tampil di dashboard web dan tidak hanya di dialog desktop lama.
- Menambahkan endpoint pengelolaan aturan diskon dinamis untuk tambah, edit, aktif/nonaktif, dan hapus dari Settings web.
- Menghilangkan field diskon kunjungan lama dari Settings web dan menetralkan nilainya saat Settings disimpan agar aturan diskon diatur melalui Diskon Dinamis.

## 2026-05-02 - Database Backup Management

- Menambahkan manajemen backup database di Settings dengan tombol `Backup Sekarang`, `Restore Backup`, status backup terakhir, dan toggle backup otomatis.
- Mengarahkan backup SQLite ke folder `backups/YYYY-MM-DD/` dengan format `backup_YYYYMMDD_HHMMSS.db`.
- Memperkuat `BackupHelper` dengan backup online SQLite, penanganan sidecar WAL/SHM, rotasi maksimal file backup, restore aman, dan logging ke `logs/backup.log`.
- Menghubungkan backup otomatis harian lewat `BackupThread` agar tidak blocking UI.
- Menyimpan metadata `last_backup_time` dan `last_backup_status` di konfigurasi aplikasi.

## 2026-05-02 - Diskon Dinamis Konfigurasi Sistem

- Menambahkan tabel `discount_rules` untuk aturan diskon bertahap tanpa menghapus aturan diskon lama.
- Mendukung tipe aturan `visit_count`, `voucher`, `manual`, dan `period` dengan diskon `percent` atau `fixed`.
- Menambahkan pengelolaan aturan diskon di dialog konfigurasi sistem: tambah, edit, aktif/nonaktif, dan hapus.
- Mengubah perhitungan kunjungan agar mengecek aturan diskon aktif lebih dulu, lalu fallback ke diskon lama jika tidak ada yang cocok.
- Menjaga kunjungan gratis tetap bernilai 0 dan tidak terkena diskon tambahan.
- Menampilkan nama diskon pada riwayat kunjungan, invoice, dan laporan/export.

## v0.9.0-beta - Rilis Internal

- Status rilis internal: siap uji operasional terbatas.
- Hasil uji manual `MANUAL_FLOW_OK`: tambah pasien, kunjungan normal, kunjungan gratis, cetak invoice, export laporan, dashboard pendapatan, stok alat keluar, dan stok herbal keluar berhasil.
- Menjaga artefak lokal seperti `.local/`, `invoices/`, `backups/`, dan laporan manual agar tidak ikut commit.
- Memastikan aplikasi dapat membuat struktur database baru/kosong untuk penggunaan awal.

## 2026-05-02 - Dukungan Kunjungan Gratis

- Menambahkan penanda kunjungan gratis dengan alasan `promo`, `keluarga`, `koreksi`, dan `gratis lain-lain`.
- Mengizinkan harga manual 0 hanya jika kunjungan ditandai gratis dan alasan gratis diisi.
- Menolak harga manual kosong, tidak valid, atau negatif sebelum kunjungan disimpan.
- Menyimpan metadata kunjungan gratis di database dan menjaga invoice/laporan aman saat membaca harga 0.

## 2026-05-02 - Perbaikan Dashboard Admin

- Memperbaiki tampilan dashboard admin agar lebih mudah dipahami oleh admin.
- Menambahkan ringkasan operasional dengan status stok yang langsung terlihat.
- Menambahkan kartu statistik untuk total pasien, total transaksi, total pemasukan, alat kritis, dan herbal habis.
- Menambahkan panel aksi cepat untuk membuka Pasien, Kunjungan, Stok Alat, dan Stok Herbal.
- Menambahkan panel "Perlu Tindakan" berisi daftar stok alat kritis dan herbal yang habis.
- Menambahkan daftar transaksi terbaru dari kunjungan pasien dan penjualan herbal.
- Memperbaiki teks dashboard dari "Ringkasan hari ini" menjadi ringkasan operasional karena data yang ditampilkan adalah total data tersimpan.
- Menambahkan data pendukung di backend dashboard untuk stok kritis, herbal habis, dan transaksi terbaru.
- Memastikan sintaks Python dan JavaScript dashboard valid.

## 2026-05-02 - Penguatan Struktur Aplikasi

- Mereview struktur folder aplikasi Python klinik bekam tanpa mengganti bahasa atau framework.
- Memisahkan query statistik dashboard ke `helpers/dashboard_stats_helper.py` agar `database.py` tidak semakin padat.
- Menambahkan `helpers/report_export_helper.py` untuk export laporan pasien dan kunjungan ke PDF atau Excel.
- Menghubungkan export laporan baru ke helper export yang sudah ada tanpa menghapus export Excel/JSON lama.
- Memperkuat validasi stok alat dan herbal agar transaksi keluar tidak bisa membuat stok minus.
- Mengarahkan operasi stok alat/herbal dari dialog melalui `viewmodels/inventory_store.py`.
- Memperbaiki logic edit stok herbal agar nilai stok hasil edit tidak salah dihitung.
- Menjalankan compile/check untuk Python, route API analytics, dashboard JavaScript, dan `git diff --check`.

## 2026-05-02 - Penguatan Lanjutan Struktur dan Operasional

- Menambahkan `helpers/export_helper.py` sebagai entry point export laporan yang kompatibel dengan helper laporan.
- Memperkuat `helpers/backup_helper.py` dengan status backup, rotasi backup lama, batas jumlah backup, dan mode backup harian.
- Mengarahkan `threads/backup_thread.py` agar memakai `BackupHelper`, sehingga aturan backup tidak terduplikasi.
- Menambahkan filter periode dan builder laporan kunjungan di `viewmodels/visit_view_model.py`.
- Menambahkan data aman untuk dashboard: kunjungan hari ini dan pendapatan periode berjalan.
- Menormalisasi response `/dashboard_stats` agar nilai kosong/null tidak membuat dashboard error.
- Memastikan verifikasi compile/check tetap lolos tanpa menjalankan server live.

## 2026-05-02 - Penguatan Akses Database UI Lama

- Mengaudit `patient_form.py`, `patient_list.py`, `visit_section.py`, `inventory_dialog.py`, dan `herbal_dialog.py`.
- Menambahkan `viewmodels/patient_view_model.py` sebagai jalur bertahap untuk operasi pasien dan kunjungan.
- Memindahkan tambah, edit, hapus, daftar pasien, dan hapus kunjungan dari akses database langsung di `main_window.py` ke `PatientViewModel`.
- Menghapus penyimpanan `self.db` dari `InventoryDialog` dan `HerbalDialog`; akses stok tetap lewat `InventoryStore`.
- Menambahkan komentar singkat untuk constructor lama yang masih menerima `db` demi kompatibilitas.
- Memastikan komponen `patient_form.py`, `patient_list.py`, dan `visit_section.py` tetap murni UI.

## 2026-05-02 - Penguatan Analytics dan Invoice ViewModel

- Menambahkan `viewmodels/analytics_view_model.py` untuk jalur data analytics dan status stok.
- Menambahkan `viewmodels/invoice_view_model.py` untuk jalur data daftar invoice.
- Mengarahkan `AnalyticsDialog` agar tidak query database langsung.
- Mengarahkan `InvoiceList` agar tidak query database langsung.
- Mengurangi wiring `self.db` di `main_window.py` untuk tab analytics, invoice, inventory, dan herbal.
- Menjaga constructor lama tetap kompatibel agar fitur existing tidak putus.

## 2026-05-02 - Penguatan Dialog Settings Legacy

- Mengaudit `SettingsDialog`, `CustomInvoiceDialog`, dan `InventorySettingsDialog`.
- Menambahkan `viewmodels/settings_view_model.py` sebagai wrapper tipis untuk akses pengaturan aplikasi.
- Mengarahkan dialog pengaturan harga/diskon, custom invoice, dan pengurangan stok otomatis lewat `SettingsViewModel`.
- Menjaga constructor lama tetap kompatibel jika masih dipanggil dengan objek settings langsung.
- Mengarahkan `main_window.py` memakai `SettingsViewModel` untuk dialog settings/custom invoice/inventory settings.

## 2026-05-02 - Audit Lanjutan Akses Langsung UI

- Mengaudit penggunaan `self.db`, `db.`, `self.settings`, dan `settings.` di `components/`, `dialogs/`, dan `main_window.py`.
- Mengarahkan `InvoiceDialog` agar membaca custom invoice settings lewat `SettingsViewModel`.
- Mengarahkan `VisitSection` agar kalkulasi harga titik memakai `settings_vm` jika tersedia, dengan fallback parent lama.
- Mengurangi pemakaian settings langsung di `main_window.py` untuk diskon, harga per titik, dan invoice preview.
- Menjaga `self.settings = settings` di `main_window.py` sementara untuk kompatibilitas alur lama.

## 2026-05-02 - Stabilisasi Compatibility Handle

- Mengaudit ulang `self.db` dan `self.settings` di `main_window.py`.
- Menambahkan komentar compatibility yang menjelaskan kenapa `self.db` dan `self.settings` masih dipertahankan sementara.
- Membersihkan import mati `os`, `BackupHelper`, `InvoiceThread`, dan `InvoiceHelper` dari `main_window.py`.
- Menghapus variabel instance tidak terpakai `invoice_helper` dan `_therapists_cache_valid`.
- Menghapus import lokal ulang `InventoryDialog` dan `HerbalDialog` di setup tab karena sudah diimpor di bagian atas file.

## 2026-05-02 - QA dan Hardening Edge Case

- Menambahkan validasi harga manual kunjungan agar tidak bisa menyimpan harga 0.
- Memperbaiki typo assignment `self.settings` di `VisitThread`.
- Menambahkan guard pada `InventoryStore.update_stock()` jika item stok tidak ditemukan.
- Menambahkan null safety tanggal kunjungan pada export laporan PDF/Excel.
- Menambahkan guard array dan number coercion di dashboard agar payload kosong/aneh tidak merusak render.
- Menjalankan compile/check untuk Python, route API, dashboard JavaScript, dan `git diff --check`.
