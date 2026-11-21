# TASK: Perapihan UI Tab CRM – Lancar Dynamic Admin

## Tujuan
Rapikan tampilan toolbar pada tab CRM agar lebih modern, profesional, proporsional, dan responsif. Fokus pekerjaan adalah UI/UX. Jangan mengubah perilaku atau logika CRM yang sudah berjalan.

## 1. Masalah pada tampilan saat ini
Berdasarkan screenshot yang diberikan:
- Filter kategori pasien, status kontak, layanan, dan tag tersusun vertikal di sisi kiri.
- Input pencarian berada di tengah dan tidak sejajar dengan filter.
- Informasi jumlah pasien dan tombol refresh kurang terintegrasi dengan toolbar.
- Ruang kosong di sisi kanan terlalu besar.
- Susunan toolbar terlihat tidak seimbang.

## 2. Layout yang diinginkan

### Desktop
Susun seluruh kontrol dalam satu baris horizontal jika lebar layar memungkinkan:

`[Kategori] [Status Kontak] [Layanan] [Tag] [Cari nama / No. HP...] [Jumlah Pasien] [Refresh]`

Ketentuan:
- Semua kontrol sejajar secara vertikal.
- Tinggi filter, input pencarian, dan tombol refresh konsisten.
- Lebar filter proporsional dan label tidak terpotong secara tidak wajar.
- Input pencarian mengambil sisa ruang yang tersedia.
- Jumlah pasien ringkas dan mudah dibaca.
- Tombol refresh berada di sisi kanan.
- Jarak antar-elemen konsisten.
- Hindari toolbar terlalu padat atau menyisakan ruang kosong yang tidak perlu.

### Tablet
- Izinkan filter membungkus ke baris berikutnya jika ruang tidak cukup.
- Pertahankan ukuran kontrol yang nyaman digunakan.
- Search tetap mudah ditemukan dan digunakan.

### Mobile
- Gunakan susunan dua kolom atau layout bertumpuk yang paling sesuai dengan struktur aplikasi.
- Input pencarian menggunakan lebar penuh.
- Jumlah pasien dan tombol refresh tetap mudah diakses.
- Pastikan tidak ada horizontal overflow.

## 3. Gaya visual
Ikuti design system dan gaya dashboard Lancar Dynamic Admin yang sudah ada:
- Clean, modern, dan konsisten dengan halaman lain.
- Border tipis dan radius konsisten.
- Tinggi komponen seragam.
- Padding, margin, dan gap proporsional.
- Typography mudah dibaca.
- Focus state pada input/filter terlihat jelas.
- Hover state halus.
- Jangan menambahkan warna mencolok atau dekorasi berlebihan.
- Jangan mengubah tema global aplikasi.

## 4. Batasan fungsional — wajib dipertahankan
Jangan mengubah, menghapus, atau mengganti:
- Logika filter kategori pasien.
- Logika filter status kontak.
- Logika filter layanan.
- Logika filter tag.
- Fungsi pencarian pasien.
- Perhitungan dan sumber data jumlah pasien.
- Fungsi tombol refresh.
- Sistem follow-up CRM.
- Integrasi WhatsApp Web.
- API, database, dan struktur data.
- Event handler, selector, ID, atau class yang dipakai oleh JavaScript/TypeScript, kecuali benar-benar diperlukan untuk layout dan seluruh referensinya diperbarui secara aman.

Pekerjaan ini hanya perapihan struktur tampilan dan styling toolbar CRM.

## 5. Batasan perubahan source
1. Periksa struktur tab CRM dan identifikasi file HTML/template, CSS, serta TypeScript/JavaScript yang mengatur toolbar.
2. Gunakan komponen, class, token, dan pola styling yang sudah tersedia.
3. Jangan membuat arsitektur atau komponen global baru jika tidak diperlukan.
4. Jangan melakukan refactoring modul lain.
5. Jangan mengubah file yang tidak berkaitan dengan toolbar CRM.
6. Hindari duplikasi CSS dan selector yang terlalu umum sehingga memengaruhi halaman lain.
7. Scope CSS perubahan ke container toolbar CRM.
8. Pertahankan kompatibilitas dengan proses build dan packaging aplikasi EXE.
9. Jangan mengubah data, API, database, atau perilaku fitur.

## 6. Tahap pertama — AUDIT SAJA
Untuk tahap ini, jangan edit file apa pun.

Laporkan:
- File yang mengatur toolbar CRM.
- Struktur elemen toolbar saat ini.
- Penyebab layout tidak rapi berdasarkan source.
- Selector/class/ID yang harus dipertahankan agar fungsi tetap berjalan.
- Rekomendasi perubahan layout dan CSS.
- Daftar file yang nantinya perlu diubah.
- Risiko regresi yang perlu diperhatikan.

Setelah audit, berhenti dan tunggu instruksi saya.

**Jangan mulai implementasi sebelum saya mengirim persis: `Silakan mulai bekerja`.**

## 7. Setelah mendapat izin implementasi
Jika saya sudah mengirim `Silakan mulai bekerja`:
- Ubah hanya file yang sudah disepakati dalam audit.
- Terapkan layout responsif sesuai spesifikasi.
- Jangan memperluas scope tanpa persetujuan.
- Jalankan pemeriksaan/test yang relevan jika tersedia.
- Laporkan file yang diubah, ringkasan perubahan, hasil test, dan hal yang belum diverifikasi.

## Referensi
Gunakan screenshot CRM yang saya lampirkan sebagai referensi kondisi awal. Targetnya adalah toolbar yang lebih rapi dan seimbang, bukan menyalin tampilan secara kaku.
