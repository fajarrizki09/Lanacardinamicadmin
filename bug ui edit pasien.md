# TASK: FIX SCROLLING EDIT PASIEN & RIWAYAT KUNJUNGAN

Project: Lancar Dynamic Admin

## MASALAH

Halaman/modal Edit Pasien & Riwayat Kunjungan tidak bisa di-scroll ke bawah.

Berdasarkan screenshot:
- Header Edit Pasien berada di bagian atas.
- Form Biodata Pasien terlihat.
- Riwayat Kunjungan memiliki beberapa entri.
- Entri riwayat berikutnya terpotong.
- Footer dan tombol Hapus Pasien berada di bawah.
- Pengguna tidak bisa menjangkau seluruh konten.

## TARGET PERBAIKAN

Buat struktur layout dengan tiga area:

1. HEADER
   - Tetap berada di bagian atas.
   - Judul Edit Pasien & Riwayat Kunjungan.
   - Tombol Simpan Semua Perubahan.
   - Tombol tutup.

2. CONTENT
   - Menjadi area scroll utama.
   - Biodata pasien.
   - Seluruh riwayat kunjungan.
   - Seluruh input dan catatan medis.
   - Dapat di-scroll sampai entri terakhir.

3. FOOTER
   - Jika menggunakan footer tetap, jangan sampai menutupi konten.
   - Tombol Hapus Pasien tetap dapat dijangkau.
   - Perhatikan padding bawah area scroll.

## INVESTIGASI CSS

Periksa:
- height dan max-height.
- min-height: 0.
- overflow-y.
- overflow: hidden.
- display: flex.
- flex-direction: column.
- position: fixed/sticky.
- z-index.
- body scroll lock.
- nested scrolling container.

Pastikan hanya satu area utama yang bertanggung jawab terhadap scrolling.

Gunakan pendekatan layout flex yang sesuai jika memungkinkan:

- Modal: display flex, flex-direction column.
- Header: flex-shrink 0.
- Content: flex: 1, min-height: 0, overflow-y: auto.
- Footer: flex-shrink 0.

Sesuaikan dengan struktur source code yang sebenarnya, jangan menerapkan CSS secara membabi buta.

## BATASAN WAJIB

Jangan mengubah:
- Fungsi penyimpanan pasien.
- Fungsi edit biodata.
- Fungsi edit riwayat kunjungan.
- Perhitungan harga.
- Data terapis dan layanan.
- Catatan medis.
- Fungsi hapus pasien.
- API dan database.
- Sistem invoice.
- Sistem CRM.

Jangan melakukan refactoring modul lain.

## RESPONSIVE

Pastikan:
- Resolusi laptop 1366x768 dapat menampilkan seluruh konten melalui scrolling.
- Resolusi 1920x1080 tetap rapi.
- Jendela aplikasi yang diperkecil tetap bisa digunakan.
- Tidak ada horizontal overflow yang tidak diperlukan.
- Seluruh riwayat kunjungan dapat dijangkau.

## TAHAP PERTAMA: AUDIT SAJA

Jangan edit source code.

Laporkan:
1. File template/modal Edit Pasien.
2. File CSS terkait.
3. Penyebab utama scrolling tidak berfungsi.
4. Elemen yang menyebabkan overflow terkunci.
5. Solusi minimal.
6. File yang perlu diubah.

Tunggu instruksi:

"Silakan mulai bekerja".