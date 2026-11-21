# TASK: UI/UX POLISH – HALAMAN LAYANAN TERAPI

Project: Lancar Dynamic Admin

Tujuan:
Menyempurnakan tampilan halaman Layanan Terapi agar lebih profesional, konsisten, dan nyaman digunakan.

Pertahankan identitas desain aplikasi saat ini:
- Dark sidebar.
- Light dashboard.
- Warna hijau/teal sebagai warna utama.
- Rounded cards.
- Clean modern dashboard.

## PRIORITAS 1 – PERBAIKI HEADER OVERLAP

Berdasarkan screenshot:
- Header halaman menutupi sebagian konten Daftar Layanan.
- Tombol Tambah Layanan terlihat tertutup.
- Periksa posisi sticky/fixed header.
- Periksa z-index, padding-top, margin-top, dan container halaman.
- Pastikan konten tidak tertutup header ketika halaman dibuka atau di-scroll.

## PRIORITAS 2 – KARTU LAYANAN

- Samakan tinggi kartu jika memungkinkan.
- Konsistenkan padding dan spacing.
- Rapikan posisi nama layanan, kategori, harga, dan status.
- Pastikan harga menjadi informasi visual utama.
- Samakan ukuran tombol Edit, Nonaktifkan, dan Hapus.
- Pastikan tombol tidak terpotong pada resolusi laptop.

## PRIORITAS 3 – FILTER DAN DAFTAR

- Rapikan tab Aktif, Nonaktif, Semua.
- Konsistenkan ukuran badge jumlah.
- Perbaiki jarak antara judul daftar, tombol tambah, filter, dan grid.
- Pertahankan fungsi pencarian dan filter.

## PRIORITAS 4 – RESPONSIVE

Desktop:
- Pertahankan grid tiga kolom jika lebar layar mencukupi.

Tablet:
- Gunakan dua kolom.

Mobile:
- Gunakan satu kolom.
- Hindari horizontal overflow.

## BATASAN WAJIB

- Jangan mengubah API.
- Jangan mengubah database.
- Jangan mengubah perhitungan harga.
- Jangan mengubah fungsi CRUD layanan.
- Jangan mengubah status aktif/nonaktif.
- Jangan mengubah struktur data.
- Jangan melakukan refactoring modul lain.
- Jangan mengubah desain sidebar secara keseluruhan.
- Gunakan CSS dan komponen yang sudah tersedia.
- Hindari perubahan global yang memengaruhi halaman lain.

## TAHAP PERTAMA: AUDIT SAJA

Identifikasi:
1. File template halaman Layanan Terapi.
2. File CSS yang mengatur header dan kartu.
3. Penyebab header menutupi konten.
4. Komponen yang mengatur grid dan tombol.
5. Daftar file yang perlu diubah.

Jangan edit source code sebelum mendapat instruksi:

"Silakan mulai bekerja".