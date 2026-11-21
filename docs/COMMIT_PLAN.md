# Commit Plan - LancarDinamicAdmin

> Commit kecil, urut, dan aman. Satu commit = satu perubahan dengan tujuan jelas.  
> Setiap commit harus lulus test yang relevan sebelum di-push.

---

## Filosofi Commit

1. **Satu commit = satu tujuan** — jangan campur fix dengan refactor
2. **Prefix wajib:** `chore:`, `docs:`, `fix:`, `refactor:`, `test:`, `feat:`
3. **Setiap commit harus lulus test terkait** sebelum dipush
4. **Urutan ini adalah urutan aman** — jangan loncat ke commit berikutnya sebelum yang sekarang aman

---

## Blok 1 — Cleanup & Dokumentasi (Fase 1)

### Commit 1
```
chore: update gitignore to exclude runtime artifacts
```
**File berubah:** `.gitignore`  
**Tujuan:** Tambah pola `data.db`, `settings.json`, `*.db-shm`, `*.db-wal`, `invoices/`, `backups/`, `logs/`, `exports/`, `__pycache__/`, `*.pyc`, `dist/`, `build/`, `*.zip`  
**Risiko:** Tidak ada — hanya edit `.gitignore`  
**Test sebelum commit:** `git status` — pastikan tidak ada file baru yang ter-ignore secara tidak sengaja

### Commit 2
```
chore: remove tracked runtime artifacts from repository
```
**File berubah:** `data.db`, `settings.json`, `*.db-shm`, `LancarDinamicAdmin.zip`, `dialogs.zip`, `build/`, `dist/`  
**Tujuan:** Hapus dari tracking Git dengan `git rm --cached`  
**Risiko:** File tidak terhapus dari disk, hanya dari Git tracking — aman  
**Test sebelum commit:** Clone repo di lokasi baru → pastikan tidak ada file runtime

### Commit 3
```
docs: add PRD.md product requirement document
```
**File berubah:** `docs/PRD.md`  
**Tujuan:** Simpan PRD sebagai referensi  
**Risiko:** Tidak ada  

### Commit 4
```
docs: add requirements checklist from PRD
```
**File berubah:** `docs/REQUIREMENTS_CHECKLIST.md`  
**Risiko:** Tidak ada  

### Commit 5
```
docs: add gap analysis vs current codebase
```
**File berubah:** `docs/GAP_ANALYSIS.md`  
**Risiko:** Tidak ada  

### Commit 6
```
docs: add refactor roadmap and safety patch plan
```
**File berubah:** `docs/ROADMAP_REFACTOR.md`, `docs/SAFETY_PATCH_PLAN.md`  
**Risiko:** Tidak ada  

### Commit 7
```
docs: add test plan and commit plan
```
**File berubah:** `docs/TEST_PLAN.md`, `docs/COMMIT_PLAN.md`  
**Risiko:** Tidak ada  

---

## Blok 2 — Safety Patches P0 (Fase 2)

### Commit 8
```
fix: prevent negative visit final price
```
**File kemungkinan berubah:** `api/routes/patients.py`, `database.py`  
**Tujuan:** Validasi `final_price >= 0` di backend sebelum simpan visit  
**Risiko:** Rendah — validasi tambahan, tidak ubah schema  
**Test sebelum commit:** `test_discount_never_negative` harus lulus

### Commit 9
```
fix: require reason for free visits in main route
```
**File kemungkinan berubah:** `api/routes/patients.py`  
**Tujuan:** Pastikan `free_visit_reason` wajib di route utama (bukan hanya di import)  
**Risiko:** Rendah  
**Test sebelum commit:** `test_free_visit_requires_reason` harus lulus

### Commit 10
```
fix: prevent herbal stock from going negative
```
**File kemungkinan berubah:** `api/routes/herbals.py`  
**Tujuan:** Cek stok sebelum kurangi, tolak jika kurang  
**Risiko:** Rendah  
**Test sebelum commit:** `test_herbal_sale_insufficient` harus lulus

### Commit 11
```
fix: prevent inventory stock from going negative
```
**File kemungkinan berubah:** `database.py`, `api/routes/inventory.py`  
**Tujuan:** Cek stok alat sebelum deduct, tolak kunjungan jika tidak cukup  
**Risiko:** Rendah  
**Test sebelum commit:** `test_inventory_not_negative` harus lulus

### Commit 12
```
fix: ensure herbal multi-item sale is atomic with rollback
```
**File kemungkinan berubah:** `api/routes/herbals.py`  
**Tujuan:** Cek SEMUA stok dulu sebelum kurangi. Rollback jika satu gagal  
**Risiko:** Medium — ubah urutan operasi transaksi  
**Test sebelum commit:** `test_herbal_sale_rollback_if_one_item_out_of_stock` harus lulus

---

## Blok 3 — Safety Patches P1 (Fase 2 lanjutan)

### Commit 13
```
fix: exclude voided visits from all revenue reports
```
**File kemungkinan berubah:** `helpers/dashboard_stats_helper.py`, `api/routes/analytics.py`  
**Tujuan:** Audit dan tambah filter `invoice_status != 'void'` di semua query revenue  
**Risiko:** Nilai dashboard mungkin berubah — ini koreksi yang benar  
**Test sebelum commit:** `test_void_excluded_from_revenue` harus lulus

### Commit 14
```
fix: standardize herbal return transaction type
```
**File kemungkinan berubah:** `api/routes/herbals.py`  
**Tujuan:** Standarkan `transaction_type = 'return'` (bukan `retur`) untuk transaksi baru  
**Risiko:** Data lama dengan `retur` tetap terbaca karena owner_report sudah handle  
**Test sebelum commit:** `test_herbal_return_adds_stock` harus lulus

### Commit 15
```
fix: prevent invoice path traversal in file generation
```
**File kemungkinan berubah:** `helpers/invoice_helper.py`  
**Tujuan:** Sanitasi nama file PDF, validasi path ada dalam folder invoices  
**Risiko:** Rendah — sanitasi output, tidak ubah logika bisnis  
**Test sebelum commit:** `test_invoice_path_traversal_blocked` harus lulus

### Commit 16
```
fix: escape user input in payment and invoice displays
```
**File kemungkinan berubah:** `api/static/app.js`, template HTML  
**Tujuan:** Ganti `innerHTML` dengan data user ke `escapeHtml()` atau `textContent`  
**Risiko:** Rendah — tidak ada perubahan logika  
**Test sebelum commit:** Manual test: input script tag di payment_reference → tidak execute

### Commit 17
```
fix: enforce admin pin for adjustment and void actions
```
**File kemungkinan berubah:** `api/routes/inventory.py`, `api/routes/herbals.py`, route void  
**Tujuan:** Pastikan semua aksi sensitif memanggil `require_admin_pin(request)`  
**Risiko:** Rendah — fungsi sudah ada, tinggal dipanggil  
**Test sebelum commit:** `test_admin_pin_required_for_adjustment` dan `test_admin_pin_required_for_void` harus lulus

### Commit 18
```
fix: prevent double submit on visit and herbal sale forms
```
**File kemungkinan berubah:** `api/static/app.js` atau modul form kunjungan  
**Tujuan:** Disable tombol saat loading, re-enable setelah selesai  
**Risiko:** Rendah — UI guard saja  
**Test sebelum commit:** Manual test double-click tombol simpan

---

## Blok 4 — Automated Tests (Fase 2 paralel)

### Commit 19
```
test: add stock and pricing integrity tests
```
**File kemungkinan berubah:** `tests/test_visit_pricing.py` (baru), `tests/test_inventory_safety.py` (baru)  
**Tujuan:** Tambah test untuk semua validasi yang dipatch di Blok 2–3  
**Risiko:** Tidak ada — menambah test  

### Commit 20
```
test: add herbal sale and return safety tests
```
**File kemungkinan berubah:** `tests/test_herbal_safety.py` (baru)  
**Tujuan:** Test stok herbal, multi-item rollback, retur  
**Risiko:** Tidak ada  

### Commit 21
```
test: add invoice safety and revenue report tests
```
**File kemungkinan berubah:** `tests/test_invoice_safety.py` (baru), `tests/test_revenue_reports.py` (baru)  
**Tujuan:** Test path traversal, total invoice, double count, void  
**Risiko:** Tidak ada  

---

## Blok 5 — Refactor Service Generic (Fase 5)

### Commit 22
```
refactor: add pricing_type and service_category fields to Service model
```
**File kemungkinan berubah:** `db_models.py`, migrasi schema  
**Tujuan:** Tambah `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`  
**Risiko:** Medium — migrasi schema. Kolom nullable dulu agar aman  
**Test sebelum commit:** Pastikan semua test lama masih lulus

### Commit 23
```
refactor: add original_price, discount_amount, final_price to Visit model
```
**File kemungkinan berubah:** `db_models.py`, `database.py`  
**Tujuan:** Tambah field pricing split ke Visit  
**Risiko:** Medium — migrasi schema. Kolom nullable, isi `price` lama ke `final_price` jika bisa  
**Test sebelum commit:** Tidak ada regression di test visit existing

### Commit 24
```
refactor: update service form UI to support pricing_type and category
```
**File kemungkinan berubah:** `api/static/ts/services.ts`, `api/routes/services.py`  
**Tujuan:** UI form service menampilkan dropdown pricing_type dan service_category  
**Risiko:** Medium — ubah UI, pastikan tidak merusak submit form yang sudah ada  

### Commit 25
```
refactor: use generic service labels in invoice template
```
**File kemungkinan berubah:** `helpers/invoice_helper.py`  
**Tujuan:** Ganti semua label "bekam"/"titik bekam" ke istilah generik  
**Risiko:** Rendah — hanya perubahan string di template  
**Test sebelum commit:** Buat invoice Pijat Terapi → tidak ada kata "bekam"

### Commit 26
```
refactor: update revenue formula to use final_price
```
**File kemungkinan berubah:** `helpers/owner_report_helper.py`  
**Tujuan:** Ganti `Visit.price` ke `Visit.final_price` setelah field tersedia  
**Risiko:** Nilai laporan mungkin berubah — ini koreksi yang benar  
**Test sebelum commit:** `test_void_excluded_from_revenue`, `test_free_visit_zero_revenue` harus lulus

---

## Blok 6 — TypeScript Stabilization (Fase 6)

### Commit 27
```
refactor: centralize frontend data types in types.ts
```
**File kemungkinan berubah:** `api/static/ts/types.ts` (baru atau update), semua file TS yang duplikasi interface  
**Tujuan:** `types.ts` = single source of truth. Hapus duplikasi interface  
**Risiko:** Medium — perubahan import di banyak file TS  
**Test sebelum commit:** `npx tsc --noEmit` tanpa error

### Commit 28
```
refactor: migrate helper utils to TypeScript
```
**File kemungkinan berubah:** `api/static/modules/` utils yang belum TS  
**Risiko:** Medium  
**Test sebelum commit:** `npx tsc --noEmit` bersih

---

## Blok 7 — CRM WhatsApp Puppeteer Automation

### Commit 29
```
docs: update CRM WhatsApp automation requirements
```
**File kemungkinan berubah:** `docs/PRD.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `docs/ROADMAP_REFACTOR.md`, `docs/TEST_PLAN.md`, `docs/SAFETY_PATCH_PLAN.md`, `docs/WHATSAPP_PUPPETEER_AUTOMATION.md`  
**Tujuan:** Sinkronkan arah produk: semi-manual tetap default, Puppeteer optional dan disabled by default.  
**Risiko:** Tidak ada — dokumentasi saja.

### Commit 30
```
test(e2e): add stable selectors for CRM WhatsApp composer
```
**File kemungkinan berubah:** `api/static/modules/crm.js`, test UI/e2e  
**Tujuan:** Tambah `data-testid` untuk modal CRM, textarea pesan, tombol copy, tombol buka WA, dan tombol kirim Puppeteer.  
**Risiko:** Rendah — tidak mengubah logic bisnis.

### Commit 31
```
feat(crm): add WhatsApp Puppeteer send settings
```
**File kemungkinan berubah:** `settings.py`, `api/routes/settings.py`, UI settings jika diperlukan  
**Tujuan:** Tambah setting `enable_whatsapp_puppeteer=false`.  
**Risiko:** Rendah jika default tetap false.

### Commit 32
```
feat(crm): add mock WhatsApp Puppeteer sender
```
**File kemungkinan berubah:** `helpers/whatsapp_puppeteer_helper.py`, tests  
**Tujuan:** Sender mock untuk test guardrail tanpa kirim real.  
**Risiko:** Rendah — tidak menyentuh WhatsApp Web real.

### Commit 33
```
feat(crm): add backend endpoint for WhatsApp Puppeteer send
```
**File kemungkinan berubah:** `api/routes/crm.py`, `helpers/crm_analysis_helper.py`, `helpers/whatsapp_puppeteer_helper.py`  
**Tujuan:** Endpoint admin-triggered one-click-one-message dengan guardrail.  
**Risiko:** Medium — wajib test contact preference, send lock, sanitized error.

### Commit 34
```
feat(tools): add local WhatsApp Puppeteer sender prototype
```
**File kemungkinan berubah:** `tools/whatsapp_puppeteer/send_whatsapp.js`, `package.json`, docs setup  
**Tujuan:** Prototype lokal dengan QR manual dan userDataDir lokal.  
**Risiko:** Medium — hanya boleh manual/local, bukan CI.

### Commit 35
```
feat(crm): connect follow-up modal to WhatsApp sender
```
**File kemungkinan berubah:** `api/static/modules/crm.js`, style jika perlu  
**Tujuan:** Tombol **Kirim WhatsApp**, status sending/sent/failed/blocked, fallback copy.  
**Risiko:** Medium — wajib duplicate click prevention.

### Commit 36
```
test(crm): add WhatsApp Puppeteer guardrail tests
```
**File kemungkinan berubah:** `tests/test_crm_whatsapp_puppeteer.py`, e2e/mock tests  
**Tujuan:** Test no phone, invalid phone, do-not-contact, no-promo, empty message, send lock, mock success/failure, sanitized error.  
**Risiko:** Tidak ada — test.

### Commit 37
```
docs: add WhatsApp Puppeteer setup and safety guide
```
**File kemungkinan berubah:** `docs/WHATSAPP_PUPPETEER_AUTOMATION.md`, user/admin guide jika diperlukan  
**Tujuan:** Panduan setup QR login, troubleshooting, batasan non-bulk, dan real-send manual/local.

---

## Ringkasan Jumlah Commit

| Blok | Jenis | Jumlah |
|---|---|---|
| Blok 1 — Cleanup & Docs | chore + docs | 7 |
| Blok 2 — Safety P0 | fix | 5 |
| Blok 3 — Safety P1 | fix | 6 |
| Blok 4 — Tests | test | 3 |
| Blok 5 — Service Generic | refactor | 5 |
| Blok 6 — TypeScript | refactor | 2 |
| Blok 7 — CRM WhatsApp Puppeteer | docs + test + feat | 9 |
| **Total** | | **37** |

---

## Aturan Commit

- Format: `type: short description` (Bahasa Indonesia atau Inggris, konsisten)
- Body commit boleh berisi: kenapa perubahan ini diperlukan, file apa yang berubah, risiko
- Jangan commit `data.db`, `settings.json`, `*.pyc`, file ZIP ke repo
- Jangan squash commit yang punya tujuan berbeda
- Setiap commit yang ada `fix:` harus disertai test yang memverifikasi fixnya
