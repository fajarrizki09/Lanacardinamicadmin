AUDIT BUG DAN LOGIKA VOUCHER & DISKON KUNJUNGAN.

Masalah:
Saya ingin aturan diskon berdasarkan kelipatan kunjungan, misalnya setiap kunjungan ke-5, 10, 15, 20 mendapatkan diskon.

Kondisi saat ini:
- Tipe: Jumlah Kunjungan.
- Mulai kunjungan ke: 5.
- Diskon: 50%.
- Kunjungan sebelumnya: 10.
- Status aturan: Aktif.
- Hasil simulasi: Tidak ada diskon aktif yang cocok.

Lakukan audit:

1. Periksa fungsi perhitungan discount_rules.
2. Periksa bagaimana visit_count dihitung.
3. Periksa perbedaan jumlah kunjungan sebelumnya dengan nomor kunjungan berikutnya.
4. Periksa apakah tipe visit_count menggunakan perbandingan >=, ==, atau modulo.
5. Periksa fungsi simulasi diskon.
6. Periksa pengaruh toggle Harga Normal terhadap simulasi.
7. Periksa apakah aturan aktif dan prioritas memengaruhi hasil.
8. Periksa apakah simulasi dan transaksi sebenarnya menggunakan mesin perhitungan yang sama.

TARGET:
Sistem nantinya mendukung:
- Mode mulai kunjungan tertentu dan berlaku seterusnya.
- Mode kelipatan kunjungan, misalnya setiap 5 kunjungan.
- Diskon hanya diberikan pada nomor kunjungan yang memenuhi aturan.
- Perhitungan simulasi harus sama dengan transaksi sebenarnya.

PENTING:
AUDIT SAJA. Jangan mengubah source code, database, atau struktur aplikasi.

Tampilkan penyebab masalah berdasarkan bukti source code, file terkait, dan rekomendasi perubahan minimal.

Tunggu instruksi "Silakan mulai bekerja".