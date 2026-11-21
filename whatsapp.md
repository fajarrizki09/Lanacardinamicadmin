Lakukan audit khusus masalah tombol WhatsApp pada tab CRM Lancar Dynamic Admin.

MASALAH:
Ketika tombol WhatsApp di tab CRM diklik, browser eksternal tidak terbuka.

PERIKSA ALUR BERIKUT:

1. Frontend CRM:
   - Tombol WhatsApp dan event click.
   - Handler JavaScript/TypeScript.
   - Pembentukan URL WhatsApp.
   - Normalisasi nomor HP.
   - Apakah menggunakan window.open(), window.location, atau anchor target="_blank".
   - Apakah ada error JavaScript.

2. PySide6 WebEngine:
   - Konfigurasi QWebEngineView.
   - Implementasi createWindow().
   - Penanganan newWindowRequested.
   - acceptNavigationRequest jika digunakan.
   - Integrasi QDesktopServices.openUrl().
   - Apakah external URL diarahkan ke browser default Windows.

3. Backend:
   - Periksa apakah ada endpoint atau helper khusus WhatsApp.
   - Pastikan tidak ada konflik dengan implementasi WhatsApp lama.

4. Periksa juga apakah tombol WhatsApp CRM menggunakan handler berbeda dengan tombol WhatsApp di halaman lain.

TUJUAN:
Menemukan penyebab mengapa klik WhatsApp CRM tidak memicu browser eksternal.

TARGET PERILAKU:
Ketika tombol WhatsApp diklik:
- Nomor HP pasien dinormalisasi dengan benar.
- URL https://wa.me/nomor terbentuk dengan benar.
- Browser default Windows terbuka.
- WhatsApp Web diarahkan ke percakapan pasien.
- Tidak mengandalkan server OpenWA atau engine WhatsApp lama.
- Tidak mengganggu fungsi CRM lainnya.

BATASAN:
- AUDIT SAJA.
- Jangan edit source code.
- Jangan menghapus fitur.
- Jangan mengubah API/database.
- Jangan melakukan refactoring.
- Identifikasi file dan fungsi yang bermasalah.
- Berikan bukti dari source code dan rekomendasi perbaikan.

Tunggu instruksi "Silakan mulai bekerja" sebelum melakukan perubahan.