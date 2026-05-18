# Roadmap Refactor - LancarDinamicAdmin

> Dokumen kerja. Bukan janji fitur. Urutkan dari keamanan data dulu, baru fitur baru.  
> Setiap fase harus lulus syarat selesai sebelum lanjut ke fase berikutnya.

---

## Fase 1 — Clean Commit & Runtime Cleanup

### Tujuan
Membersihkan repo dari file runtime, build artifact, dan ZIP sementara.  
Memastikan semua commit bersih dan tidak tercampur data developer.

### File Utama
- `.gitignore`
- `LancarDinamicAdmin.zip`, `dialogs.zip`
- `data.db`, `settings.json`
- `smart_discount_*.db-shm`
- `dist/`, `build/`
- `__pycache__/`, `*.pyc`

### Task Detail
1. Update `.gitignore` dengan semua pola runtime (lihat PRD §19)
2. `git rm --cached` untuk semua file runtime yang sudah ter-track
3. Hapus atau pindahkan ZIP yang tidak perlu dari repo
4. Verifikasi `git status` bersih setelah commit ini
5. Buat template commit yang terpisah untuk docs, fix, refactor, test, chore

### Risiko
- `git rm --cached` tidak menghapus file dari disk, hanya dari tracking — aman
- Jika ada rekan yang pull sebelum ini, mereka perlu reset lokal

### Test Manual
- `git status` = clean
- Buka `dist/` dan `build/` → tidak ada di git log

### Test Otomatis
- Tidak perlu untuk fase ini

### Syarat Selesai
- `git status` bersih (tidak ada file runtime ter-track)
- `LancarDinamicAdmin.zip` tidak ter-track
- `data.db`, `settings.json` tidak ter-track
- `*.db-shm` tidak ter-track
- Commit bertipe `chore` dan terpisah dari commit lain

---

## Fase 2 — Safety Patch

### Tujuan
Menutup risiko data fatal kecil tanpa rewrite besar.  
Setiap patch kecil, bisa di-commit terpisah, dan tidak merusak fitur yang sudah jalan.

### File Utama
- `api/routes/patients.py` (atau route kunjungan utama)
- `api/routes/herbals.py`
- `api/routes/inventory.py`
- `api/routes/invoices.py`
- `helpers/invoice_helper.py`
- `database.py`

### Task Detail
1. Validasi `final_price >= 0` di backend route kunjungan
2. Validasi `free_visit` wajib alasan di route kunjungan biasa
3. Validasi stok herbal tidak minus sebelum sale
4. Validasi rollback atomik untuk herbal-only multi item
5. Validasi stok inventori tidak minus sebelum deduct
6. Sanitasi nama file PDF (karakter Windows tidak aman)
7. Validasi path invoice tidak ada path traversal
8. Input escape untuk payment_reference di halaman mock payment
9. Void wajib alasan di route void
10. Void membutuhkan Admin PIN di route void

### Risiko
- Patch validasi bisa memblokir flow yang sebelumnya terlewat (false positive) → test dulu
- Rollback atomik herbal multi-item butuh SQLAlchemy transaction scope yang benar

### Test Manual
- Coba input kunjungan dengan diskon > harga → harus ditolak
- Coba void tanpa alasan → harus ditolak
- Coba jual herbal stok 0 → harus ditolak

### Test Otomatis
- `test_discount_never_negative`
- `test_herbal_sale_rollback_if_one_item_out_of_stock`
- `test_inventory_not_negative`
- `test_free_visit_requires_reason`
- `test_admin_pin_required_for_void`

### Syarat Selesai
- Semua patch lulus unit test
- Tidak ada regression di smoke test pasien, kunjungan, herbal, stok
- Setiap patch punya commit tersendiri

---

## Fase 3 — Transaction Integrity

### Tujuan
Memastikan create visit, deduct stok, buat invoice, dan audit log berjalan atomik.  
Tidak ada state setengah-tersimpan jika terjadi error di tengah proses.

### File Utama
- `database.py` (fungsi `add_visit`)
- `api/routes/patients.py`
- `api/routes/herbals.py`
- `helpers/invoice_helper.py`

### Task Detail
1. Audit `add_visit`: apakah stok deduct dan visit create dalam satu transaction block?
2. Jika tidak atomik: wrap dalam `session.begin()` atau gunakan `try/except/rollback`
3. Audit herbal sale multi-item: rollback semua jika salah satu stok kurang
4. Audit invoice create: jika PDF gagal, pastikan visit tetap tersimpan dan status invoice jelas (`pdf_failed`)
5. Pastikan return/retur membuat transaksi lawan (bukan update record lama)
6. Pastikan void menggunakan `invoice_status = 'void'` (sudah ada), bukan delete

### Risiko
- Mengubah transaction scope bisa mempengaruhi performa jika session terlalu panjang
- Rollback harus diuji dengan skenario error yang dipaksakan (mock error di tengah proses)

### Test Manual
- Simulasikan stok alat yang pas (sisa 1, dibutuhkan 1): kunjungan berhasil, stok jadi 0
- Simulasikan stok alat = 0: kunjungan ditolak
- Simulasikan herbal stok 1, jual 2 item sekaligus: semua item ditolak

### Test Otomatis
- `test_create_visit_atomic_with_inventory_deduct`
- `test_herbal_sale_group_id_multi_item`
- `test_invoice_pdf_fail_status_clear`

### Syarat Selesai
- Semua alur transaksional tidak menghasilkan state setengah tersimpan
- Rollback berfungsi pada semua skenario error yang diuji

---

## Fase 4 — Reporting Correctness

### Tujuan
Pastikan semua laporan (dashboard, owner report, analytics) menghasilkan angka yang benar dan tidak double count.

### File Utama
- `helpers/owner_report_helper.py`
- `api/routes/analytics.py`
- `helpers/dashboard_stats_helper.py`
- `db_models.py` (tergantung Fase 5: field `final_price`)

### Task Detail
1. Audit formula `visit_revenue`: pastikan gunakan `final_price` (setelah field ditambahkan di Fase 5)
2. Audit `herbal_revenue`: pastikan herbal yang ikut kunjungan tidak dihitung dua kali
3. Audit `analytics.py`: pastikan tidak ada double count antara invoice total dan visit total
4. Filter void konsisten di semua query laporan
5. Filter pending/unpaid: pastikan tidak masuk paid income di owner report
6. Dashboard: pastikan semua endpoint aman dari null payload

### Risiko
- Perubahan formula bisa mengubah angka laporan eksisting → dokumentasikan perubahan
- Jika field `final_price` belum ada, Fase 4 harus menunggu Fase 5 selesai dulu

### Test Manual
- Buat kunjungan normal, void, gratis → owner report harus tunjukkan angka benar
- Buat herbal sale ikut kunjungan → tidak boleh muncul dua kali di laporan

### Test Otomatis
- `test_void_excluded_from_revenue`
- `test_return_reduces_net_herbal_sales`
- `test_dashboard_no_double_count`

### Syarat Selesai
- Semua formula laporan verified dengan unit test + data dummy end-to-end
- Tidak ada double count dalam skenario apapun

---

## Fase 5 — Service Generic & Visit Pricing

### Tujuan
Menghapus semua logika hardcode bekam. Service harus benar-benar generic.  
Menambahkan field `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price` ke Service.  
Menambahkan field `original_price`, `discount_amount`, `final_price` ke Visit.

### File Utama
- `db_models.py`
- `database.py`
- `api/routes/services.py`
- `api/static/ts/services.ts`
- `helpers/invoice_helper.py`
- `helpers/owner_report_helper.py`

### Task Detail
1. Tambah field ke `Service`: `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`
2. Buat migrasi schema aman (kolom nullable + default)
3. Tambah field ke `Visit`: `original_price`, `discount_amount`, `final_price`
4. Update `add_visit` di `database.py` untuk menerima dan menyimpan field baru
5. Update route services: tampilkan dan simpan field baru
6. Update UI form service: tambah selector `pricing_type` dan `service_category`
7. Update `invoice_helper.py`: ganti heading "bekam" ke "Detail Layanan"
8. Update `owner_report_helper.py`: gunakan `final_price` sebagai dasar revenue
9. Rename alias `point_count` → `quantity` secara bertahap (jangan hapus `point_count` belum)

### Risiko
- Migrasi schema bisa gagal jika tidak ada `PRAGMA user_version` atau tanpa Alembic
- `point_count` rename harus bertahap — semua referensi di test dan legacy_ui harus diperbarui dulu

### Test Manual
- Tambah layanan "Pijat Terapi" dengan `pricing_type = fixed`, `unit_label = sesi`
- Catat kunjungan Pijat Terapi → invoice harus tampilkan "Detail Layanan" bukan "Detail Bekam"
- Tambah layanan "Konsultasi Herbal" dengan `pricing_type = manual`

### Test Otomatis
- `test_create_visit_per_unit_service`
- `test_create_visit_fixed_service`
- `test_create_visit_manual_price`
- `test_invoice_generic_labels`

### Syarat Selesai
- Demo kunjungan Pijat Terapi, Refleksi, Konsultasi Herbal berhasil end-to-end
- Tidak ada string "bekam" hardcode di invoice template
- Semua field baru tersimpan dan terbaca benar di laporan

---

## Fase 6 — TypeScript Stabilization

### Tujuan
Migrasi JS ke TS bertahap. Tidak merusak logic yang sudah berjalan.  
`types.ts` sebagai single source of truth.

### File Utama
- `api/static/ts/types.ts` (dibuat baru atau dipindahkan)
- `api/static/ts/*.ts` (semua file yang sudah ada)
- `api/static/modules/*.js` (yang belum dimigrasi)
- `tsconfig.static.json`

### Task Detail
1. Buat `types.ts` atau pindahkan semua interface ke file terpusat
2. Hapus duplikasi interface (misal: `Service` didefinisikan ulang di `services.ts`)
3. Migrasi modul helper/utils
4. Migrasi dashboard
5. Migrasi settings
6. Tunda migrasi visits, invoices sampai fase selesai

### Risiko
- Jangan migrasi visits dan invoices sebelum pricing logic stabil (Fase 5 harus selesai dulu)
- Type mismatch antara backend response dan frontend type akan terdeteksi saat runtime, bukan compile time

### Test Manual
- Jalankan `tsc --noEmit` di semua file yang sudah dimigrasi → tidak boleh ada error

### Test Otomatis
- CI: `npx tsc --noEmit`

### Syarat Selesai
- `tsc --noEmit` bersih di semua file TS yang sudah dimigrasi
- Tidak ada duplikasi type yang berarti

---

## Fase CRM-A — WhatsApp Automation Readiness

### Tujuan
Menyiapkan modul CRM Follow-up agar aman untuk opsi WhatsApp automation tanpa mengubah mode default semi-manual.

### File Utama
- `api/static/modules/crm.js`
- `api/static/ts/` (jika CRM mulai dimigrasi)
- `api/routes/crm.py`
- `helpers/crm_analysis_helper.py`
- `tests/`

### Task Detail
1. Tambah `data-testid` stabil di composer CRM WhatsApp.
2. Rapikan modal WhatsApp composer agar status, error, dan tombol mudah diuji.
3. Pastikan tombol **Buka WhatsApp** tidak dobel membuka tab.
4. Pastikan `crm_whatsapp_logs` selalu terisi untuk aktivitas WhatsApp.
5. Pastikan contact preference (`JANGAN DIHUBUNGI`, `JANGAN PROMO`, reminder opt-out) tervalidasi di UI dan backend.
6. Pastikan semi-manual tetap default dan fallback.

### Syarat Selesai
- UI CRM punya selector/test id stabil.
- Tidak ada double open tab untuk flow WhatsApp semi-manual.
- Contact preference enforceable sebelum masuk fase Puppeteer.

---

## Fase CRM-B — Puppeteer Mock Sender

### Tujuan
Menguji flow baru tanpa mengirim WhatsApp real.

### File Utama
- `api/routes/crm.py`
- `helpers/whatsapp_puppeteer_helper.py` (rencana)
- `helpers/crm_analysis_helper.py`
- `api/static/modules/crm.js`
- `tests/test_crm_whatsapp_puppeteer.py`

### Task Detail
1. Tambah setting `enable_whatsapp_puppeteer=false`.
2. Tambah backend endpoint mock untuk send.
3. Simpan log `sent_mock`/`failed_mock` atau mapping status mock yang jelas.
4. UI tombol **Kirim WhatsApp** bisa diuji tanpa kirim real.
5. Pastikan fallback **Copy Pesan** tetap tersedia.

### Syarat Selesai
- Semua guardrail bisa dites otomatis tanpa WhatsApp Web.
- Tidak ada real send di CI.

---

## Fase CRM-C — Puppeteer Local Prototype

### Tujuan
Membuat prototype lokal yang hanya berjalan manual di mesin developer/admin dan hanya untuk nomor test sendiri.

### File Utama
- `tools/whatsapp_puppeteer/send_whatsapp.js`
- `package.json`
- `.local/whatsapp-profile` (runtime, tidak masuk Git/build)
- `docs/WHATSAPP_PUPPETEER_AUTOMATION.md`

### Task Detail
1. Tambah script `tools/whatsapp_puppeteer/send_whatsapp.js`.
2. Gunakan `userDataDir` lokal agar session WhatsApp Web tersimpan lokal.
3. Login QR manual, tidak bypass QR.
4. Kirim hanya ke nomor test milik sendiri saat prototype.
5. Jangan bulk dan jangan background send.

### Syarat Selesai
- Script menerima JSON input dan mengembalikan JSON result.
- Manual real-send hanya berjalan lokal, bukan CI.

---

## Fase CRM-D — Backend Integration

### Tujuan
Menghubungkan FastAPI ke sender lokal secara terkontrol.

### File Utama
- `api/routes/crm.py`
- `helpers/whatsapp_puppeteer_helper.py`
- `tools/whatsapp_puppeteer/send_whatsapp.js`
- `api/static/modules/crm.js`

### Task Detail
1. FastAPI memanggil Node script via subprocess.
2. Tangani JSON result dari Node.
3. Simpan log `sending`, lalu update ke `sent`/`failed`/`blocked`.
4. Tampilkan status ke UI.
5. Sanitasi semua error yang dikirim ke frontend.

### Syarat Selesai
- Endpoint hanya aktif jika setting enabled.
- Semua status hasil tercatat di `crm_whatsapp_logs`.

---

## Fase CRM-E — QA & Guardrails

### Tujuan
Memastikan automation tetap admin-triggered, tidak spam, dan patuh preferensi kontak.

### Task Detail
1. Send lock.
2. Admin confirmation sebelum kirim.
3. Enforcement **JANGAN DIHUBUNGI**.
4. Enforcement **JANGAN PROMO** untuk template promo.
5. Empty message block.
6. One-click-one-message guard.
7. Duplicate click prevention.
8. Manual QA checklist.
9. Puppeteer mock test.

### Syarat Selesai
- Semua guardrail test lulus.
- Manual real-send hanya ke nomor test sendiri.
- Semi-manual fallback tetap tersedia.

---

## Fase 7 — QA Internal

### Tujuan
Uji semua alur utama dengan data dummy di mesin developer.  
Dokumen test report internal.

### File Utama
- `tests/test_core_business_flows.py`
- `tests/test_herbals.py`
- `tests/test_invoices_security.py`
- Semua test baru yang dibuat di Fase 2–5

### Task Detail
1. Jalankan seluruh test suite: `pytest tests/ -v`
2. Jalankan smoke test manual (lihat TEST_PLAN.md)
3. Uji edge case: stok = 0, discount = 100%, void setelah paid, return setelah void
4. Catat semua bug yang ditemukan
5. Perbaiki bug sebelum lanjut ke Fase 8

### Risiko
- Bug dari Fase 2–5 mungkin belum terdeteksi sebelum QA
- Data dummy harus dikosongkan lagi sebelum build EXE

### Syarat Selesai
- Semua acceptance criteria P0 dan P1 lulus
- `pytest` lulus tanpa kegagalan di test yang relevan
- Tidak ada bug kritis yang belum tertangani

---

## Fase 8 — Build EXE Bersih

### Tujuan
EXE installer tidak membawa data developer.  
Aplikasi bisa diinstall di mesin kosong dan langsung berjalan.

### File Utama
- `build.bat` / `build_protected.bat`
- `LancarDinamicAdmin.spec`
- PyInstaller `datas` dan `excludes`

### Task Detail
1. Audit `LancarDinamicAdmin.spec`: pastikan `data.db`, `settings.json`, `invoices/`, `backups/` tidak masuk
2. Test instalasi di folder baru yang kosong
3. Test di PC yang tidak punya Python terinstall
4. Pastikan aplikasi membuat `settings.json` dan `data.db` sendiri saat pertama jalan

### Risiko
- Jika runtime files ikut di spec, data developer bisa tersebar ke pengguna
- Path hardcode di `spec` bisa berbeda di mesin lain

### Syarat Selesai
- EXE tidak mengandung `data.db`, `settings.json`, atau isi folder `invoices/`
- Instalasi di folder kosong berhasil dan aplikasi bisa jalan
- Smoke test di mesin baru lulus

---

## Fase 9 — Trial Terbatas

### Tujuan
Uji di lingkungan nyata dengan 1–3 klinik pilot sebelum dijual massal.

### Task Detail
1. Deploy EXE ke 1 klinik pilot (bisa komputer dummy)
2. Panduan backup manual untuk pengguna pilot
3. Kumpulkan feedback dan bug report
4. Perbaiki semua bug produksi yang ditemukan
5. Finalisasi model lisensi dan harga

### Syarat Selesai
- Tidak ada bug kritis setelah 2 minggu penggunaan pilot
- Owner report akurat sesuai transaksi nyata
- Backup/restore berhasil diverifikasi
