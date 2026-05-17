# Release Checklist

Gunakan checklist ini sebelum aplikasi dibagikan ke user/klinik. Tujuannya memastikan build bersih, data runtime tidak ikut, dan fitur inti tetap berjalan.

## 1. Verifikasi Source

- [ ] Pastikan perubahan yang akan dirilis sudah direview.
- [ ] Pastikan tidak ada secret, license key asli, API key, atau data private di source/dokumentasi.
- [ ] Pastikan `.gitignore` masih mengecualikan runtime files.
- [ ] Jalankan:

```powershell
git diff --check
```

## 2. Compile Check

Jalankan minimal:

```powershell
python -m py_compile main.py api\main.py database.py settings.py
```

Jika ada file Python lain yang baru diubah, compile juga file tersebut.

## 3. Test Wajib

Jalankan test backend/helper/API ringan:

```powershell
python -m unittest tests.test_security_token tests.test_admin_pin tests.test_settings_security tests.test_patients tests.test_herbals tests.test_delete_safety
```

Pastikan hasilnya `OK`.

## 4. Pastikan Runtime Tidak Ikut Distribusi

Sebelum ZIP/installer dibagikan, pastikan file/folder berikut tidak ikut:

- [ ] `settings.json`
- [ ] `data.db`
- [ ] `*.db`
- [ ] `*.db-shm`
- [ ] `*.db-wal`
- [ ] `invoices/`
- [ ] `backups/`
- [ ] `logs/`
- [ ] `exports/` yang berisi data nyata
- [ ] `__pycache__/`
- [ ] `*.pyc`
- [ ] file PDF invoice hasil smoke test
- [ ] temporary test files
- [ ] ZIP lama hasil build sebelumnya

## 5. Build Bersih

- [ ] Aktifkan virtualenv `.venv`.
- [ ] Pastikan dependency sesuai `requirements.txt`.
- [ ] Jalankan:

```powershell
.\build.bat
```

- [ ] Pastikan output EXE ada di `dist\LancarDinamicAdmin`.
- [ ] Jika Inno Setup tersedia, pastikan installer ada di `dist`.

## 6. Uji Build Di Folder Bersih

Jangan uji dari folder development yang berisi data lama. Gunakan folder test kosong.

- [ ] Jalankan EXE dari folder bersih.
- [ ] Pastikan dashboard terbuka.
- [ ] Pastikan API lokal siap tanpa stuck di loading.
- [ ] Pastikan port bentrok ditangani atau aplikasi memakai port lokal berikutnya.
- [ ] Pastikan lisensi belum memakai license key developer.
- [ ] Aktivasi lisensi dilakukan di device user/test sesuai prosedur resmi.

## 7. Smoke Test Fitur Inti

- [ ] Tambah pasien test.
- [ ] Tambah kunjungan dasar.
- [ ] Buat invoice layanan.
- [ ] Buka/print invoice.
- [ ] Tambah produk/herbal test bila perlu.
- [ ] Jual herbal test dan pastikan stok berkurang.
- [ ] Jalankan backup manual.
- [ ] Buka tab pengaturan dan pastikan status lisensi tampil benar.
- [ ] Cek endpoint sensitif tetap meminta PIN admin dari UI.

## 8. Proteksi Data Dan Keamanan

- [ ] `X-App-Token` masih wajib untuk API lokal.
- [ ] Endpoint admin/owner masih wajib `X-Admin-Pin`.
- [ ] `/settings` tidak mengirim field sensitif.
- [ ] Delete transaksi penting tidak hard delete data laporan/stok/invoice.
- [ ] Invoice void memakai status void dan alasan, bukan delete file/data diam-diam.

## 9. Sebelum Dibagikan Ke Klinik

- [ ] Jangan kirim `settings.json` dari mesin developer.
- [ ] Jangan kirim `data.db` dari mesin developer.
- [ ] Jangan kirim folder `invoices`, `backups`, atau `logs` developer.
- [ ] Jangan kirim file invoice PDF smoke test.
- [ ] Jangan sertakan license key asli di dokumen chat/email.
- [ ] Sertakan instruksi aktivasi lisensi di device user.
- [ ] Sertakan versi build dan tanggal rilis.

## 10. Catatan Rollback

Sebelum upgrade di klinik yang sudah berjalan:

- [ ] Minta user melakukan backup dari aplikasi.
- [ ] Simpan installer versi sebelumnya jika perlu rollback.
- [ ] Catat lokasi backup dan database user.
- [ ] Jangan overwrite database user secara manual kecuali ada instruksi recovery yang jelas.
