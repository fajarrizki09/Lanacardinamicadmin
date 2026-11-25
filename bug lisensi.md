# CRITICAL AUDIT: REGRESI LISENSI LIFETIME SETELAH UPDATE

Project: Lancar Dynamic Admin

## MASALAH

Lisensi dengan masa berlaku LIFETIME sebelumnya berjalan normal.

Setelah aplikasi diperbarui, lisensi tiba-tiba menjadi tidak aktif.

Jangan menganggap lisensi benar-benar expired. Investigasi kemungkinan kesalahan verifikasi, perubahan hardware fingerprint, dan kegagalan membaca secure settings.

## TEMUAN AWAL YANG WAJIB DIVERIFIKASI

### 1. helpers/license.py

Periksa fungsi:
- _extract_license_response()
- generate_hardware_fingerprint_hash()
- _is_cached_license_unexpired()
- _is_recent_valid_check()
- _save_license_cache()
- verify_license()

Periksa apakah status active tanpa field valid=true ditolak.

Periksa apakah nilai lifetime, permanent, null, atau tanggal kosong ditangani sesuai kontrak API GAS.

Jangan mengubah format respons server secara asumtif.

### 2. HARDWARE FINGERPRINT

Bandingkan implementasi fingerprint versi sebelum dan sesudah update.

Periksa:
- MAC address.
- Disk serial.
- CPU ID.
- Windows version/build.
- Hostname.
- Device ID.

Pastikan update aplikasi tidak menyebabkan identitas perangkat berubah tanpa alasan.

Periksa juga payload yang dikirim ke GAS dan aturan device binding di sisi server jika source tersedia.

### 3. SECURE SETTINGS

Audit helpers/secure_settings.py.

Periksa:
- Apakah data aktivasi gagal didekripsi?
- Apakah device key berubah?
- Apakah settings lama masih terbaca?
- Apakah lokasi APPDATA berubah?
- Apakah kegagalan satu field menyebabkan seluruh data lisensi dibuang?
- Apakah ada perbedaan perilaku antara EXE lama dan EXE baru?

### 4. SERVER RESPONSE

Periksa kontrak respons verify_license.

Bandingkan:
- Status aktif.
- Status lifetime.
- Field valid.
- Expired_at / expires_at.
- Clinic ID.
- Device ID.
- Hardware fingerprint.

Jika source GAS tidak tersedia, jangan mengarang hasil pemeriksaan. Catat data respons yang dibutuhkan.

### 5. PERBANDINGAN VERSI

Periksa Git history dan perubahan file lisensi sebelum dan sesudah update.

Identifikasi commit yang mengubah:
- Algoritma fingerprint.
- Parsing respons API.
- Penyimpanan settings.
- Verifikasi cache.
- Device binding.

Cari perubahan paling mungkin yang menyebabkan regresi.

## TARGET

Lisensi lifetime yang valid harus tetap aktif setelah update aplikasi selama:
- License key masih valid.
- Device binding masih sesuai.
- Server mengonfirmasi lisensi aktif.
- Data aktivasi dapat dibaca dengan benar.

Jangan mengubah aturan keamanan untuk sekadar memaksa lisensi aktif.

## BATASAN

AUDIT SAJA.

- Jangan edit source code.
- Jangan menghapus device binding.
- Jangan melewati verifikasi server.
- Jangan mengubah database lisensi.
- Jangan mengaktifkan lisensi secara paksa.
- Jangan menghapus secure settings.
- Jangan membuat ulang device ID.
- Jangan mengubah GAS atau Vercel.

## LAPORAN WAJIB

1. Penyebab utama berdasarkan bukti.
2. File dan fungsi bermasalah.
3. Perubahan kode yang memicu regresi.
4. Perbandingan versi lama dan baru.
5. Apakah masalah di aplikasi, GAS, atau Vercel.# AUDIT BUG LISENSI MENDADAK NONAKTIF SAAT APLIKASI MASIH BERJALAN

## KONDISI BUG
Lisensi awalnya ACTIVE dan aplikasi berjalan normal. Setelah beberapa menit, status lisensi tiba-tiba berubah menjadi tidak aktif, padahal aplikasi masih terbuka dan pengguna tidak melakukan logout, update, atau instalasi ulang.

## TUJUAN
Temukan penyebab pasti perubahan status lisensi saat runtime.

## ATURAN WAJIB
- AUDIT SAJA. Jangan mengubah source code.
- Jangan menghapus atau mereset data lisensi.
- Jangan mengganti device binding atau hardware fingerprint.
- Jangan mengubah konfigurasi server GAS/Vercel.
- Jangan membuat bypass atau melemahkan validasi lisensi.
- Jangan refactor modul lain.
- Tampilkan bukti berupa nama file, fungsi, dan nomor baris.

## AREA YANG WAJIB DITELUSURI

1. Semua pemanggilan `verify_license()` dan fungsi verifikasi terkait.
2. Timer, scheduler, background worker, thread, atau mekanisme pemeriksaan lisensi berkala.
3. Perubahan nilai:
   - `last_license_valid`
   - `license_status`
   - `license_cache`
   - `last_verified`
   - status aktivasi lainnya.
4. Penanganan timeout, koneksi gagal, HTTP 4xx/5xx, respons kosong, dan JSON tidak valid.
5. Mekanisme cache dan offline grace period.
6. Pemrosesan respons GAS/Vercel, khususnya perbedaan respons saat startup dan verifikasi ulang.
7. Kemungkinan dua proses verifikasi berjalan bersamaan dan saling menimpa hasil.
8. Event atau callback yang mengubah tampilan status lisensi ketika aplikasi masih terbuka.

## PENTING: BEDAKAN TIGA KONDISI

- VALID: server mengonfirmasi lisensi aktif.
- TEMPORARY_ERROR: jaringan bermasalah, timeout, server error, atau respons tidak dapat dibaca.
- INVALID/REVOKED: server secara eksplisit mengonfirmasi lisensi tidak valid atau dicabut.

Periksa apakah TEMPORARY_ERROR saat ini keliru diperlakukan sebagai INVALID.

Jangan mengubah kebijakan validasi sebelum akar masalah ditemukan.

## OUTPUT AUDIT

Buat laporan:

1. Alur pemeriksaan lisensi sejak aplikasi dibuka sampai beberapa menit kemudian.
2. Semua pemicu verifikasi ulang beserta intervalnya.
3. Titik kode yang dapat mengubah ACTIVE menjadi INACTIVE.
4. Bukti kode yang menyebabkan perubahan tersebut.
5. Apakah ada race condition atau cache overwrite.
6. Apakah masalah berasal dari aplikasi, jaringan, atau respons server.
7. Rekomendasi perbaikan paling kecil dan aman.
8. File yang nantinya perlu diubah.

**Jangan melakukan perbaikan dahulu. Tunggu instruksi: SILAKAN MULAI BEKERJA.**
6. Solusi minimal yang aman.
7. Test regresi khusus lisensi lifetime.
8. Risiko terhadap pelanggan lain.

Berhenti setelah audit. Tunggu instruksi:

"Silakan mulai bekerja".