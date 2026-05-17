# QA Checklist - Lancar Dynamic Admin

Gunakan checklist ini untuk smoke test manual sebelum rilis. Catat tanggal, versi, OS, browser, dan database yang dipakai saat pengujian.

## 1. Aplikasi Dasar

- [ ] Aplikasi desktop bisa dibuka.
- [ ] Web admin/FastAPI bisa dibuka.
- [ ] Dashboard tampil tanpa error.
- [ ] Sidebar/menu utama bisa berpindah tab.
- [ ] Layout web admin tetap terbaca di desktop.
- [ ] Layout web admin tetap usable di viewport kecil/tablet.

## 2. Pasien

- [ ] Tambah pasien baru berhasil.
- [ ] Edit data pasien berhasil.
- [ ] Hapus pasien berhasil jika fitur tersedia.
- [ ] Nomor HP kosong diterima jika fitur mengizinkan nomor sementara.
- [ ] Nomor HP valid `08xxxxxxxxxx` diterima.
- [ ] Nomor HP invalid ditolak dengan pesan jelas.
- [ ] Nomor HP duplikat ditolak dengan pesan jelas.

## 3. Terapis

- [ ] Tambah terapis laki-laki berhasil.
- [ ] Tambah terapis perempuan berhasil.
- [ ] Nonaktifkan terapis berhasil.
- [ ] Terapis nonaktif tidak muncul/tidak bisa dipakai di form kunjungan.

## 4. Layanan

- [ ] Tambah layanan berhasil.
- [ ] Layanan harga normal bisa dipakai.
- [ ] Layanan harga `0`/gratis bisa disimpan sesuai aturan aplikasi.
- [ ] Nonaktifkan layanan berhasil.
- [ ] Layanan nonaktif tidak muncul di form kunjungan.

## 5. Kunjungan Normal

- [ ] Pilih pasien dari tabel berhasil.
- [ ] Pilih terapis sesuai gender berhasil.
- [ ] Pilih layanan berhasil.
- [ ] Isi titik/jumlah layanan berhasil.
- [ ] Isi catatan medis berhasil.
- [ ] Modal konfirmasi muncul sebelum simpan.
- [ ] Tombol batal di modal tidak menyimpan kunjungan.
- [ ] Simpan final berhasil.
- [ ] Riwayat kunjungan tampil setelah simpan.

## 6. Validasi Gender Terapis

- [ ] Pasien laki-laki dengan terapis laki-laki berhasil.
- [ ] Pasien laki-laki dengan terapis perempuan ditolak.
- [ ] Pasien perempuan dengan terapis perempuan berhasil.
- [ ] Pasien perempuan dengan terapis laki-laki ditolak.
- [ ] Pesan error validasi gender jelas.

## 7. Diskon/Voucher

- [ ] Kunjungan harga normal tersimpan sebagai harga normal.
- [ ] Kunjungan memakai voucher tersimpan dengan harga akhir benar.
- [ ] Kunjungan terkena rule diskon tersimpan dengan harga akhir benar.
- [ ] Kunjungan gratis tersimpan dengan harga akhir `0`.
- [ ] Panel riwayat menampilkan Harga Akhir dan badge sumber harga.
- [ ] Modal edit kunjungan menampilkan `final_price` dan badge sumber harga.
- [ ] Voucher/rule yang tidak valid tidak mengubah harga.

## 8. Kunjungan + Pembelian Herbal

- [ ] Tambah herbal di form kunjungan berhasil.
- [ ] Stok tidak berkurang saat tambah item herbal.
- [ ] Stok tidak berkurang saat modal konfirmasi dibuka.
- [ ] Batal modal tidak mengurangi stok.
- [ ] Simpan final mengurangi stok sesuai qty.
- [ ] `HerbalTransaction` bertipe sale tercatat dengan `visit_id`.
- [ ] Invoice visit menampilkan layanan + herbal.
- [ ] Total invoice visit benar.
- [ ] Stok kurang ditolak dan tidak membuat transaksi parsial.

## 9. Herbal-Only Sale

- [ ] Buka menu Obat Herbal berhasil.
- [ ] Klik Penjualan Herbal berhasil membuka form/modal.
- [ ] Pilih 1 herbal dan submit berhasil.
- [ ] Pilih beberapa herbal dalam satu submit berhasil.
- [ ] Stok tidak berkurang saat tambah item/modal.
- [ ] Batal tidak mengurangi stok.
- [ ] Simpan final mengurangi stok sesuai qty.
- [ ] `HerbalTransaction` sale tercatat dengan `visit_id` null.
- [ ] Semua item dalam satu submit punya `sale_group_id` sama.
- [ ] Stok kurang ditolak dan rollback.

## 10. Invoice Herbal-Only Group

- [ ] Transaksi herbal-only multi item tampil sebagai satu group.
- [ ] Buat Invoice menghasilkan satu PDF.
- [ ] PDF memuat semua item dalam group.
- [ ] Total PDF benar.
- [ ] `invoice_path` tersimpan untuk semua item group.
- [ ] Transaksi lama tanpa `sale_group_id` tetap bisa invoice satu item.

## 11. Inventori Alat

- [ ] Tambah item alat berhasil.
- [ ] Update stok masuk berhasil.
- [ ] Update stok keluar berhasil.
- [ ] Stok rendah terlihat jika fitur tersedia.
- [ ] Transaksi inventori tercatat jika fitur tersedia.

## 12. Analytics

- [ ] Total kunjungan benar.
- [ ] Pendapatan memakai `final_price`/harga akhir jika ada.
- [ ] Herbal sales dari visit masuk analytics.
- [ ] Herbal-only sales masuk analytics.
- [ ] Invoice herbal tidak dobel hitung.
- [ ] Diskon/voucher tidak salah hitung pendapatan.

## 13. Backup/Restore

- [ ] Backup berhasil dibuat.
- [ ] File backup tersimpan di lokasi yang benar.
- [ ] Restore berhasil.
- [ ] Muncul pesan reload/restart setelah restore.
- [ ] Setelah restart, data sesuai backup.
- [ ] Restore file invalid ditolak dengan pesan jelas.

## 14. License

- [ ] Aplikasi membaca status license.
- [ ] License valid membuka fitur sesuai aturan.
- [ ] License invalid menampilkan pesan jelas.
- [ ] License expired menampilkan pesan jelas.
- [ ] Settings sensitif tetap aman dan tidak tampil sembarangan.

## 15. Build EXE Smoke Test

- [ ] Build EXE percobaan.
- [ ] Jalankan EXE di PC sendiri.
- [ ] Jalankan EXE di PC lain.
- [ ] Cek database tersimpan di lokasi runtime yang benar.
- [ ] Cek invoice PDF bisa dibuat dari EXE.
- [ ] Cek printer/print PDF jika fitur tersedia.
- [ ] Cek backup/restore dari EXE.
