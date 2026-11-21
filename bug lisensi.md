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
5. Apakah masalah di aplikasi, GAS, atau Vercel.
6. Solusi minimal yang aman.
7. Test regresi khusus lisensi lifetime.
8. Risiko terhadap pelanggan lain.

Berhenti setelah audit. Tunggu instruksi:

"Silakan mulai bekerja".