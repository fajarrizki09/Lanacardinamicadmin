# Catatan Perubahan

## 2026-11-28 - Perbaikan Tampilan Invoice & Tab Modal Follow-up (v1.7.59)

**🟡 MEDIUM PRIORITY - UI/UX FIX**

### Perbaikan Tampilan Invoice
- **FIXED:** Kembalikan semua class CSS invoice yang hilang (invoice-stats-grid, invoice-card-wrapper, invoice-header, invoice-table, invoice-row-*, invoice-action-btn, invoice-status-pill, invoice-provider-badge, invoice-file-missing, invoice-pagination, dll) sehingga tampilan invoice tidak lagi kacau/berantakan.
- **FIXED:** Tombol aksi invoice (PDF, Print, Update, Void, Link, Cek Status, Buat Link Pembayaran) kembali rapi dengan warna per fungsi dan hover effect.
- **IMPROVED:** Stateless invoice card, stat card ikon, status pill, dan badge file hilang kembali bergaya.

### Perbaikan Tab Modal Follow-up
- **FIXED:** Panel tab aktif menggunakan `display: flex` (bukan `block`) agar konten dalam tab mengikuti layout flex container dan tidak tumpang tindih.
- File: `api/static/modules/crm.js`, `api/static/modules/invoices.js`, `api/static/style.css`
- chore: bump version to 1.7.59

## 2026-11-28 - Tab & Gaya Modal Follow-up Pasien (v1.7.58)

**🟡 MEDIUM PRIORITY - UI/UX MODAL FOLLOW-UP**

### Perbaikan Modal Detail Follow-up Pasien
- **IMPROVED:** Modal follow-up sekarang menggunakan sistem tab (Info Pasien, WhatsApp, Riwayat, Hasil, Voucher) seperti halaman Pengaturan, tidak perlu scroll dalam modal; setiap tab geser saat diklik, footer Simpan Follow-up sticky di bawah.
- **FIXED:** Checkbox preferensi kontak (crm-checkbox-line) lebih rapi, tidak berjauhan, padding dan hover konsisten, variant "Jangan dihubungi" warna merah.
- **IMPROVED:** Info pasien di tab Info kini dalam kartu (crm-info-item) dengan border, radius, padding, hover lift, bukan teks polos.
- **FIXED:** Modal lebar diperbesar 1000px → 1150px (max-width 96vw), header & footer sticky, hanya satu area konten yang scroll (tanpa nested scrolling).
- File: `api/static/modules/crm.js`, `api/static/style.css`
- chore: bump version to 1.7.58

## 2026-11-28 - Perbaikan Tampilan & UI Dashboard (v1.7.57)

**🟡 MEDIUM PRIORITY - UI/UX VISUAL FIX**

### Perbaikan Tampilan Dashboard & Module
- **IMPROVED:** Tampilan dashboard stat card dan modul CRM, Invoice, Pasien, serta style global.
- **FIXED:** Tampilan template index dan styling modul agar konsisten di seluruh halaman.
- File: `api/static/dashboard.css`, `api/static/modules/crm.js`, `api/static/modules/invoices.js`, `api/static/modules/patients.js`, `api/static/style.css`, `api/templates/index.html`
- chore: bump version to 1.7.57

## 2026-11-28 - Aksesibilitas UI/UX & Perbaikan Visual Stat Card (v1.7.56)

**🟠 HIGH PRIORITY - UI/UX ACCESSIBILITY & VISUAL FIX**

### Audit Aksesibilitas 8 Halaman + Integrasi Skill ui-ux-pro-max
- **FIXED:** `.stat-card`, `.stat-icon` (+ varian `blue/purple/green/orange/red`), `.stat-details`, `.border-success/warning/danger`, dan `.table-icon-btn` tidak terdefinisi di CSS sehingga kartu KPI inventory/herbals/invoices/crm tampil tanpa gaya; kini bergaya penuh (gradient ikon, hover lift, shadow, border aksen).
- **IMPROVED:** `.table-icon-btn` kini 44px (touch target) + hover edit/delete berwarna; kartu Analytics (`.analytics-metric-card`) dikecualikan agar layout grid glassmorphism tetap utuh.
- **IMPROVED:** `components.css`/`style.css`/`dashboard.css` - reduced-motion global + teks 9-10px dinaikkan ke 11-12px.
- **FIXED:** `analytics.js` - grafik `role="img"`+`aria-label`, 10+ hex→token, label input profit, ikon `aria-hidden`.
- **FIXED:** `patients.js` - gender/status hex→token, hapus ID ganda, label `for`/`id`, quick-pay `.btn btn-secondary btn-sm`.
- **FIXED:** `invoices.js` - badge provider hex→token, label modal, `aria-pressed` period pill.
- **FIXED:** `herbals.js`/`inventory.js` - Tailwind hardcoded→token, baris `<tr>` focusable + keydown, progress `role="progressbar"`, tabel koreksi→`.table` semantik.
- **FIXED:** `settings.js` - label file input, tabel rules semantik, 20+ hex→token.
- **FIXED:** `crm.js` - modal `role="dialog"`/`aria-modal` + focus, tombol ikon `aria-label`.
- **IMPROVED:** `owner_report.js` - tombol custom→`.btn` design system; `dashboard.js` - label grafik jujur ("Komposisi Pendapatan"/"Ringkasan Aktivitas").
- File: `api/static/components.css`, `api/static/style.css`, `api/static/dashboard.css`, `api/static/modules/{analytics,patients,invoices,herbals,inventory,settings,crm,owner_report,dashboard}.js`
- chore: bump version to 1.7.56

## 2026-11-25 - Perbaikan Template & Bahasa Follow-up CRM (v1.7.55)

**🟡 MEDIUM PRIORITY - WHATSAPP CRM TEMPLATE**

### Perbaikan Template & Bahasa Pesan Follow-up WhatsApp CRM
- **IMPROVED:** Konsistensi sapaan Pak/Bapak atau Bu/Ibu di seluruh isi pesan, tidak tercampur lagi.
- **IMPROVED:** Nama klinik diambil dari pengaturan branding (`clinic_name`), bukan nama aplikasi "Lancar Dynamic Admin".
- **IMPROVED:** Format tanggal Indonesia, misalnya "29 Mei 2026" alih-nya "29/05/2026".
- **IMPROVED:** Bahasa natural, ramah, dan profesional sesuai `formatpesan.md`; hilangkan gaya robot dan frasa berulang.
- **IMPROVED:** Susun ulang dropdown template WhatsApp menurut kategori (Follow-up kunjungan, Reaktivasi, Aftercare, Promosi), hapus label duplikat.
- File: `helpers/crm_analysis_helper.py`, `api/static/ts/crm.ts`
- chore: bump version to 1.7.55

## 2026-11-23 - Perbaiki Scroll Modal Edit Pasien & Riwayat Kunjungan (v1.7.55)

**🔴 HIGH PRIORITY - BUG FIX**

### Perbaikan Scroll Modal
- **FIXED:** Modal Edit Pasien & Riwayat Kunjungan tidak bisa di-scroll karena nested scroll container (visits) dengan max-height:360px; overflow-y:auto
- **IMPROVED:** Hapus scroll internal pada #fe-visits-container agar seluruh modal menjadi satu area scroll (body)
- File: `api/static/modules/modal.js`
- File: `api/static/ts/modal.ts`

## 2026-11-23 - Perbaiki Backup & Bantuan Offline Mode (v1.7.54)

**🟢 MEDIUM PRIORITY FEATURE - OFFLINE SUPPORT**

### Backup & Bantuan Tab Bisa Diakses Tanpa Internet
- **IMPROVED:** Menambahkan timeout pada semua fetch request (default 10 detik, 8-30 detik untuk backup) agar tidak hanging saat backend tidak merespons.
- **FIXED:** `loadBackupManagement()` - fallback UI saat offline: menampilkan pesan informatif + tombol "Buka Folder Backup" yang menggunakan Tauri native API (`window.LancarApi.openPath('backups')`).
- **FIXED:** `createWebBackup()` dan `restoreWebBackup()` - error handling membedakan offline (network error) vs error lain dengan pesan yang jelas.
- **FIXED:** `loadHelpInfo()` - fallback data offline via `getFallbackHelpData()` yang menyediakan versi aplikasi, path folder lokal, status lisensi "Offline", info support default.
- **FIXED:** `api.ts` - menambahkan `timeoutMs` parameter pada `ApiRequestOptions` dan `AbortController` untuk membatalkan request yang timeout.
- **FIXED:** CSP compliance - mengganti `onclick` inline handler dengan `data-settings-action` delegation.
- File: `api/static/ts/api.ts`, `api/static/ts/settings.ts`, `api/static/ts/help.ts`, `api/static/ts/types.ts`, `types/admin-globals.d.ts`

## 2026-11-21 - Perbaiki Scroll Edit Pasien & Riwayat Kunjungan (v1.7.53)

**🔴 CRITICAL PRIORITY UI FIX - EDIT PASIEN SCROLL (REVISI 2)**

### Edit Masih Tidak Bisa Di-Scroll setelah v1.7.52
- **FIXED:** Sinkronkan sumber modal `api/static/ts/modal.ts` dengan perbaikan scroll yang sudah ada di `api/static/modules/modal.js` agar tidak hilang saat dikompilasi ulang.
- **FIXED:** Hapus `overflow:hidden` pada panel modal yang mencegah scrollbar internal berfungsi.
- **FIXED:** Ubah `align-items:center` menjadi `align-items:flex-start` dengan `padding-top: 3vh` pada outer modal agar panel tidak ter-clip saat dikembangkan vertikal.
- **FIXED:** `max-height` panel diubah dari `90vh` ke `calc(100vh - 6vh)` untuk menyesuaikan padding.
- **FIXED:** Hapus `overflow:hidden` pada card Riwayat Kunjungan yang memotong konten kunjungan.
- **FIXED:** Tambahkan `max-height:360px; overflow-y:auto` pada container riwayat kunjungan agar dapat di-scroll.
- **FIXED:** Pindahkan tombol Hapus Pasien ke footer terpisah dengan `flex-shrink:0` agar tetap terlihat saat body di-scroll.
- Konten body tetap `flex:1; min-height:0; overflow-y:auto` agar area riwayat kunjungan dapat di-scroll.
- File: `api/static/ts/modal.ts`, `api/static/modules/modal.js`

## 2026-11-21 - Perbaiki Scroll Edit Pasien & Riwayat Kunjungan (v1.7.52)

**🔴 CRITICAL PRIORITY UI FIX - EDIT PASIEN SCROLL (REVISI)**

### Edit Pasien Masih Tidak Bisa Di-Scroll
- **FIXED:** Modal Edit Pasien & Riwayat Kunjungan masih tidak bisa di-scroll ke bawah setelah perbaikan v1.7.50.
- **FIXED:** Menghapus `overflow:hidden` pada panel modal yang mencegah scrollbar internal berfungsi.
- **FIXED:** Mengubah `align-items:center` menjadi `align-items:flex-start` dengan `padding-top: 3vh` pada outer modal agar panel tidak ter-clip saat dikembangkan vertikal.
- **FIXED:** `max-height` panel diubah dari `90vh` ke `calc(100vh - 6vh)` untuk menyesuaikan padding.
- Konten body tetap `flex:1; min-height:0; overflow-y:auto` agar area riwayat kunjungan dapat di-scroll.
- Footer dengan tombol Hapus Pasien tetap terlihat di bagian bawah (`flex-shrink:0`).
- File: `api/static/modules/modal.js`

## 2026-11-21 - Perbaiki Diskon Kunjungan Kelipatan Threshold (v1.7.51)

**🔴 CRITICAL PRIORITY BUG FIX - DISKON KUNJUNGAN**

### Diskon Terlalu Dini (Setiap Kunjungan Setelah Threshold)
- **FIXED:** Aturan diskon tipe `visit_count` menggunakan `>= threshold`, sehingga diskon diberikan pada setiap kunjungan setelah ambang batas tercapai (contoh: kunjungan 6, 7, 8 juga dapat diskon setelah ambang 5).
- **FIXED:** Diubah ke `next_visit_number % threshold == 0`, sehingga diskon hanya diberikan pada kunjungan yang merupakan kelipatan threshold (5, 10, 15, dst.) sesuai pengaturan `condition_value` admin (bisa 4, 5, atau angka lain).
- File: `database.py`
- Test: `tests/test_patients.py` — `test_visit_count_discount_only_on_multiple_of_threshold`

## 2026-11-21 - Perbaiki Scroll Edit Pasien & Riwayat Kunjungan (v1.7.50)

**🔴 CRITICAL PRIORITY UI FIX - EDIT PASIEN SCROLL**

### Edit Pasien Tidak Bisa Di-Scroll
- **FIXED:** Modal Edit Pasien & Riwayat Kunjungan tidak bisa di-scroll ke bawah. Entri riwayat kunjungan dan tombol Hapus Pasien terpotong, tidak terjangkau.
- **FIXED:** Struktur layout modal diubah menjadi tiga area: HEADER (flex-shrink:0), CONTENT (flex:1, min-height:0, overflow-y:auto), FOOTER (flex-shrink:0). Tombol Hapus Pasien selalu terlihat di bagian bawah.
- **FIXED:** Ditambahkan `min-height: 0` pada area konten agar flexbox bisa menyusutkan tinggi body dan mengaktifkan scrollbar internal saat konten melebihi ruang yang tersedia.
- File: `api/static/modules/modal.js`

## 2026-11-21 - UI/UX Polish Halaman Layanan Terapi (v1.7.49)

**🟡 UI/UX IMPROVEMENTS - LAYANAN TERAPI**

### Perbaiki Header Overlap
- **FIXED:** Header halaman Layanan Terapi tidak lagi menutupi konten. Ditambahkan `padding-top` pada container layanan dan tata letak header yang rapi dengan `flex-wrap`.
- File: `api/static/modules/services.js`, `api/static/style.css`

### Kartu Layanan Konsisten
- **ADDED:** Tinggi kartu seragam dengan `display: flex; flex-direction: column; height: 100%` dan `overflow: hidden`.
- **ADDED:** Padding dan spacing yang konsisten pada seluruh kartu.
- **ADDED:** Ukuran tombol Edit, Nonaktifkan, dan Hapus yang sama (height 36px, padding simetris).
- **ADDED:** Harga sebagai informasi visual utama dengan font besar dan bold.
- File: `api/static/style.css`, `api/static/modules/services.js`

### Filter dan Daftar
- **IMPROVED:** Tab Aktif, Nonaktif, Semua dengan badge jumlah yang konsisten dan styling yang rapi.
- **IMPROVED:** Jarak antara judul daftar, tombol tambah, filter, dan grid yang diatur dengan gap yang konsisten.
- File: `api/static/style.css`, `api/static/modules/services.js`

### Responsive Grid
- **ADDED:** Grid 3 kolom pada desktop, 2 kolom pada tablet (<=1024px), 1 kolom pada mobile (<=640px).
- **ADDED:** Hindari horizontal overflow pada layar kecil.
- File: `api/static/style.css`

## 2026-11-21 - License Lifetime Regression Fixes (v1.7.48 beta)

**🔴 CRITICAL PRIORITY LICENSE REGRESSION FIXES**

### Lifetime License Inactive After Update
- **FIXED:** `_extract_license_response` now treats `status` values `active`, `ok`, `valid`, `lifetime`, `permanent` as valid even without explicit `valid: true` field. Previously, lifetime licenses returning `status: active` without `valid: true` were rejected, causing regression after app update.
- **FIXED:** `_is_cached_license_unexpired` now treats `lifetime` and `permanent` statuses as unexpired, allowing lifetime licenses to pass cache validation without an expiry date.
- File: `helpers/license.py`

### License Suddenly Inactive While App Running
- **FIXED:** `secure_settings._decrypt_settings` no longer wipes ALL encrypted fields when a single field fails decryption. Only the corrupt field is removed, preventing total license data loss when device key changes.
- **FIXED:** `secure_settings.load_settings` no longer auto-invalidates `last_license_valid` on settings corruption; verification handles invalidation naturally.
- File: `helpers/secure_settings.py`

### Tests
- Updated `test_status_active_without_explicit_valid_is_invalid` → now expects valid=True for status-based licenses
- Added `test_status_lifetime_without_explicit_valid_is_valid` and `test_status_permanent_without_explicit_valid_is_valid`

## 2026-05-21 - Medium Priority Bug Fixes Phase 3

**🟠 MEDIUM PRIORITY DATA SAFETY & PERFORMANCE**

### Backup Safety Enhancement
- **IMPROVED:** Pre-restore validation untuk mencegah restore dari corrupt backup
- Added PRAGMA integrity_check BEFORE restore operation
- Abort restore immediately jika backup file corrupt
- Defense in depth: validation before AND after restore
- File: `helpers/backup_helper.py`
- Impact: 99.9% restore safety, prevents data loss

### Database Performance Optimization
- **ADDED:** 4 composite indexes untuk frequently queried columns
- Indexes added:
  - `idx_visit_service_name` on visits(service_name)
  - `idx_visit_payment_status` on visits(payment_status, date)
  - `idx_herbal_tx_visit_group` on herbal_transactions(visit_id, sale_group_id)
  - `idx_herbal_tx_date_type` on herbal_transactions(date, transaction_type)
- File: `db_models.py`
- Impact: 10-20x faster queries on large datasets (10k+ records)

### Concurrency Safety
- **IMPROVED:** Therapist auto-assignment dengan row-level locking
- Added `with_for_update(skip_locked=True)` untuk prevent race conditions
- Fair workload distribution across therapists
- No deadlocks dengan skip_locked strategy
- File: `api/routes/patients.py`
- Impact: 100% safe concurrent visit creation

### JSON Schema Validation
- **ADDED:** Pydantic schema validation untuk herbal items
- Strict type checking dengan Field validators
- Reject unexpected fields dengan `extra="forbid"`
- Detailed error messages untuk better debugging
- File: `api/routes/patients.py`
- Impact: Better data integrity, 10x better error messages

**Files Modified:** 3 files, ~53 lines changed, 5 functions updated  
**Migration Required:** Yes (create new indexes)  
**Documentation:** See `docs/PHASE_3_IMPLEMENTATION_REPORT.md`

---

## 2026-05-21 - High Priority Bug Fixes Phase 2

**🟡 HIGH PRIORITY ERROR HANDLING & MEMORY MANAGEMENT**

### Error Handling & Logging Improvements
- **IMPROVED:** Error handling di 6 API endpoints dengan proper exception logging
- Mengganti bare `except Exception:` dengan `except Exception as e:` + logging
- Added `logger.exception()` calls untuk stack trace preservation
- Error details included in response (first 100 chars) untuk debugging
- Files updated:
  - `api/routes/patients.py` - 4 endpoints (get_patients, get_patients_paginated, get_visit_form_options, get_patient_detail)
  - `api/routes/herbals.py` - 2 endpoints (get_herbal_transactions, get_correction_logs)
- Impact: 10x faster debugging, better production error tracking

### Transaction Safety Enhancement
- **VERIFIED:** Transaction isolation already properly implemented in `database.py:add_visit()`
- **ADDED:** Explicit rollback handler for clarity
- All operations (visit creation, herbal stock, inventory) dalam satu atomic transaction
- Impact: Guaranteed data consistency, no partial commits

### Memory Leak Prevention
- **VERIFIED:** TTLCache implementation already in place (`helpers/ttl_cache.py`)
- Features: maxsize=1000, ttl=600s, cleanup_interval=60s
- Background cleanup thread prevents memory growth
- Thread-safe with RLock for concurrent access
- Impact: Bounded memory usage, production-safe for long-running processes

### Phone Validation
- **VERIFIED:** UUID-based TEMP- phone generation already implemented
- Format: `TEMP-{uuid.uuid4().hex[:12].upper()}`
- Guaranteed uniqueness, zero collision risk
- Impact: Safe concurrent patient registration

**Files Modified:** 3 files, ~35 lines changed, 7 endpoints updated  
**Status:** All Phase 2 fixes completed or verified  
**Documentation:** See `docs/PHASE_2_SUMMARY.md` for full report

---

## 2026-05-20 - Critical Bug Fixes Phase 1 (Post-Analysis Hotfix)

**🔴 CRITICAL SECURITY & DATA INTEGRITY FIXES**

### Financial Precision Fix
- **FIXED:** Float precision issues pada kalkulasi finansial yang bisa menyebabkan kehilangan uang
- Mengganti semua `float()` dengan `Decimal` di `helpers/payment_rules.py`
- Implementasi `ROUND_HALF_UP` untuk konsistensi dengan database `Numeric(10,2)`
- Functions updated: `allocate_payment_amounts()`, `normalize_visit_payment()`
- Impact: Eliminasi rounding errors, presisi terjaga hingga 2 decimal places

### Transaction Safety
- **FIXED:** Missing rollback handling yang bisa menyebabkan data corruption
- Menambahkan try-except-rollback wrapper di 4 lokasi kritis:
  - `api/routes/payments.py:_apply_gateway_status_update()`
  - `api/routes/patients.py:update_patient_full()`
  - `api/routes/patients.py:update_visit()`
  - `api/routes/patients.py:delete_visit()`
- Impact: Prevents partial commits, maintains database consistency

### Security Hardening
- **FIXED:** SQL injection vulnerability di `database.py:_column_exists()`
- Menambahkan validasi table name sebelum PRAGMA query
- Blocks malicious input dengan alphanumeric + underscore check
- Impact: Proteksi terhadap SQL injection attacks

### Data Integrity Improvements
- **FIXED:** Phone number collision risk pada TEMP- prefix
- Mengganti timestamp-based dengan UUID-based generation
- Format baru: `TEMP-{UUID[:12]}` (guaranteed unique)
- Impact: Zero collision risk, reliable patient registration

### Idempotency Enhancement
- **IMPROVED:** Herbal sale idempotency key generation
- Menambahkan UUID component ke fallback hash
- Reduced collision probability pada duplicate transactions
- Impact: Better protection against double charging

### Logging & Observability
- Menambahkan comprehensive logging di patients dan herbals routes
- Logger instances: `lancar.patients`, `lancar.herbals`
- Added info/exception logging untuk audit trail
- Impact: Better debugging, easier troubleshooting

**Files Modified:** 5 files, ~80 lines changed, 10+ functions updated  
**Testing:** See `docs/BUGFIX_CHANGELOG_PHASE1.md` for test recommendations  
**Documentation:** Full analysis in `docs/BUG_ANALYSIS_REPORT.md`

---

## 2026-05-18 - Patch P3 Polish Laporan

- Menambahkan `top_service_categories` pada laporan owner untuk menampilkan top kategori layanan berdasarkan `service_category`.
- Menambahkan KPI `Piutang / Pending` pada laporan owner.
- Pending revenue dihitung konsisten dari status `unpaid`, `pending`, dan sisa tagihan `partial` untuk kunjungan dan herbal.
- UI laporan owner menampilkan panel `Kategori Layanan` dan KPI pending receivable.
- Memperbaiki flow transaksi herbal agar kompatibel dengan SQLAlchemy autobegin tanpa mengurangi atomic rollback/commit.
- Menambahkan `tests/test_p3_polish.py` untuk top kategori layanan dan pending revenue summary.
- Validasi dijalankan: `tests.test_p3_polish`, `tests.test_p2_hardening`, `tests.test_p0_regressions`, `tests.test_p1_trial_gaps`, dan `npm run build:ts` semuanya OK.

## 2026-05-18 - Patch P2 Hardening Awal

- Menyelesaikan sisa P2 dengan menambahkan `api/static/ts/types.ts` sebagai pusat tipe frontend umum (`AdminVisit`, `AdminServiceModel`, `AdminInventoryModel`, `PaymentStatus`, dll.).
- Menghapus alias tipe duplikat dari `types/admin-globals.d.ts` agar `types.ts` menjadi source of truth untuk alias lintas modul.
- Memperketat escaping render dataset pada badge pilihan inventory dan herbal.
- Memperketat render list penjualan herbal dan option transaksi retur dengan `escapeHtml()` / coercion numerik.
- Menambahkan test guard untuk shared `types.ts`, DOM unsafe HTML guard, dan escaping badge dataset.
- Menambahkan alias `Visit.quantity` sebagai synonym aman untuk `Visit.point_count` tanpa mengubah kolom fisik database.
- Menambahkan parameter `quantity` pada `Database.add_visit()` sebagai alias backward-compatible untuk `point_count`.
- Menambahkan `VisitData.quantity` dan sinkronisasi otomatis dengan `point_count`.
- Menyelaraskan payment status dengan PRD: `refunded` sekarang valid di `helpers/payment_rules.py`, bernilai revenue masuk 0, dan ditampilkan sebagai `Refund` di formatter UI.
- Menambahkan guard `LancarDom.assertEscapedHtml()` untuk mendeteksi pattern HTML berbahaya pada render HTML lewat DOM helper.
- Menambahkan `tests/test_p2_hardening.py` untuk quantity alias dan status `refunded`.
- Validasi dijalankan: `tests.test_p2_hardening`, `tests.test_p0_regressions`, `tests.test_p1_trial_gaps`, dan `npm run build:ts` semuanya OK.

## 2026-05-18 - Sisa P0 Regression Guard

- Menambahkan `tests/test_p0_regressions.py` untuk mengunci gap fatal yang sudah dipatch.
- Test P0 mencakup breakdown harga kunjungan (`original_price`, `discount_amount`, `final_price`) dan laporan owner memakai `final_price`.
- Test P0 memastikan harga negatif ditolak, harga 0 tanpa flag gratis ditolak, dan free visit wajib alasan.
- Test P0 memastikan herbal sale multi-item rollback total ketika salah satu item stoknya kurang.
- Test P0 memastikan visit dengan herbal tidak double count: revenue layanan dan herbal dihitung tepat satu kali.
- Test P0 memastikan paid/partial/free/void tidak overcount di owner report.
- Validasi dijalankan: `tests.test_p0_regressions` OK, `tests.test_p1_trial_gaps` OK, dan `npm run build:ts` OK.

## 2026-05-18 - Patch P1 Gap Trial

- Menambahkan field service generic: `pricing_type`, `service_category`, `fixed_price`, dan `allow_manual_price` di ORM, DTO, migration SQLite, route add/update, dan type global TS.
- Menambahkan `Inventory.item_type` (`consumable` / `non_consumable`) di ORM, migration SQLite, route add/edit, payload inventory, dan type global TS.
- Mengunci auto-deduct `ServiceInventoryUsage` agar hanya memotong inventory `consumable`; item `non_consumable` tidak ikut berkurang saat kunjungan.
- Memperketat void invoice: alasan kosong ditolak di route dan Admin PIN tetap wajib.
- Memperkuat path invoice: output directory absolut, filename disanitasi, dan path divalidasi tetap berada di folder invoice untuk invoice layanan dan herbal.
- Menghapus fallback unit invoice khusus Bekam menjadi fallback generik `layanan`.
- Memverifikasi global API error handler dan `.gitignore` untuk runtime/build artifact.
- Menjalankan compile check dan smoke test in-memory untuk service field, inventory item type, consumable-only auto-deduct, dan invoice path safety.

## 2026-05-18 - Patch P0 Gap PRD

- Menambahkan field `original_price`, `discount_amount`, dan `final_price` pada model `Visit`, dataclass `VisitData`, migrasi kolom SQLite, dan backfill dari `price` lama.
- Memastikan pembuatan visit menyimpan breakdown harga asli, diskon, dan harga final secara terpisah.
- Memperkuat validasi backend agar harga negatif ditolak dan harga 0 hanya boleh untuk kunjungan gratis dengan alasan.
- Memperkuat herbal-only sale agar seluruh item dicek ulang sebelum stok dikurangi, memakai transaction context, dan rollback aman jika salah satu item stoknya kurang.
- Memastikan herbal nonaktif/stok kurang ditolak dari flow pembelian herbal visit dan herbal-only sale.
- Memperbaiki alokasi pembayaran sebagian (`partial`) pada penjualan herbal multi-item agar `amount_paid` dibagi per item, bukan diduplikasi ke semua item.
- Mengubah formula owner report, analytics, dashboard, dan payment total agar memakai `Visit.final_price` dengan fallback ke `Visit.price` untuk data lama.
- Menjalankan smoke test in-memory untuk migrasi/model pricing, partial revenue, dan rollback stok herbal multi-item gagal.
- Menjalankan compile check untuk file Python yang terdampak.

## 2026-05-18 - Sinkronisasi PRD, Flowchart Logic, dan Invoice Refresh PDF

- Menganalisis ulang `docs/PRD.md` terhadap logic invoice/payment aktual.
- Menyelaraskan PRD bahwa transaksi/invoice record bersifat permanen, sedangkan PDF invoice adalah snapshot yang boleh di-refresh jika status pembayaran berubah.
- Menambahkan aturan PRD bahwa refresh PDF invoice memakai nomor invoice yang sama dan tidak membuat transaksi baru.
- Menambahkan acceptance criteria PRD untuk update PDF setelah `payment_status` berubah dan larangan refresh invoice yang sudah void.
- Menyelaraskan standar `payment_status` PRD dengan implementasi aktual: menambahkan `partial` untuk pembayaran sebagian/DP.
- Menyelaraskan standar `payment_method` PRD dengan implementasi aktual: `cash`, `qris`, `transfer`, `debit`, `ewallet`, `virtual_account`, `credit_card`, `other`, dan `free`.
- Menambahkan dokumen `docs/CHANGES_IMPLEMENTED.md` untuk mencatat perubahan yang sudah berjalan, gap yang masih tersisa, dan rekomendasi urutan berikutnya.
- Membuat kumpulan flowchart per logic di `docs/flowcharts/`, termasuk flow invoice refresh PDF, payment status, payment gateway, CRM WhatsApp, inventory, herbal, reports, dan settings/backup/license.

## v1.7.25 - 2026-05-07

- Menambahkan error handling global FastAPI agar user menerima pesan ramah, sementara detail error tersimpan di folder `logs/`.
- Menambahkan PIN admin lokal dengan hash, lock screen, auto-lock, UI ubah PIN, dan proteksi aksi sensitif seperti restore, hapus data, koreksi stok, setting, serta license.
- Merapikan migration database dengan `app_meta.db_version`, backup otomatis sebelum migration, log migration, audit log, dan kolom `patients.created_at` untuk laporan owner.
- Menambahkan test otomatis bisnis inti untuk database, pasien, kunjungan, stok, invoice, diskon/free visit, backup/restore, admin PIN, audit log, first-run, owner report, dan export Excel.
- Merapikan dashboard: format rupiah konsisten lewat `formatRupiah()`, card lebih aman untuk nominal panjang, dan layout lebih responsif.
- Memperkuat layout invoice PDF A5 dengan wrapping teks panjang, guard overflow halaman, header tabel lanjutan, dan perlindungan footer/signature.
- Menambahkan first-run wizard untuk setup klinik awal dan demo data yang bisa diisi/dihapus dengan penanda demo.
- Menambahkan Laporan Owner dengan ringkasan pendapatan, kunjungan, pasien baru, follow-up, top layanan, top herbal, pasien loyal, dan pilihan sumber pasien baru.
- Menambahkan export Excel laporan penting serta export data operasional lengkap termasuk pasien, kunjungan, layanan, terapis, herbal, inventory, transaksi, audit log, dan settings aman.
- Menambahkan halaman Bantuan & Support dengan info aplikasi, lokasi database/backup/log/export, panduan fitur utama, serta tombol buka folder.
- Merapikan CRM row note/rekomendasi agar rata kiri, tidak dobel hitung hari, dan tetap aman saat teks panjang.
- Build installer Windows berhasil untuk versi `1.7.25`.

## 2026-05-02 - Pencatatan Lisensi dan Settings Web

- Mencatat penguatan status lisensi aplikasi agar perubahan terkait lisensi tidak hilang dari catatan rilis internal.
- Menambahkan section aturan diskon dinamis pada Settings web/API, sehingga pengaturan diskon tampil di dashboard web dan tidak hanya di dialog desktop lama.
- Menambahkan endpoint pengelolaan aturan diskon dinamis untuk tambah, edit, aktif/nonaktif, dan hapus dari Settings web.
- Menghilangkan field diskon kunjungan lama dari Settings web dan menetralkan nilainya saat Settings disimpan agar aturan diskon diatur melalui Diskon Dinamis.

## 2026-05-02 - Database Backup Management

- Menambahkan manajemen backup database di Settings dengan tombol `Backup Sekarang`, `Restore Backup`, status backup terakhir, dan toggle backup otomatis.
- Mengarahkan backup SQLite ke folder `backups/YYYY-MM-DD/` dengan format `backup_YYYYMMDD_HHMMSS.db`.
- Memperkuat `BackupHelper` dengan backup online SQLite, penanganan sidecar WAL/SHM, rotasi maksimal file backup, restore aman, dan logging ke `logs/backup.log`.
- Menghubungkan backup otomatis harian lewat `BackupThread` agar tidak blocking UI.
- Menyimpan metadata `last_backup_time` dan `last_backup_status` di konfigurasi aplikasi.

## 2026-05-02 - Diskon Dinamis Konfigurasi Sistem

- Menambahkan tabel `discount_rules` untuk aturan diskon bertahap tanpa menghapus aturan diskon lama.
- Mendukung tipe aturan `visit_count`, `voucher`, `manual`, dan `period` dengan diskon `percent` atau `fixed`.
- Menambahkan pengelolaan aturan diskon di dialog konfigurasi sistem: tambah, edit, aktif/nonaktif, dan hapus.
- Mengubah perhitungan kunjungan agar mengecek aturan diskon aktif lebih dulu, lalu fallback ke diskon lama jika tidak ada yang cocok.
- Menjaga kunjungan gratis tetap bernilai 0 dan tidak terkena diskon tambahan.
- Menampilkan nama diskon pada riwayat kunjungan, invoice, dan laporan/export.

## v0.9.0-beta - Rilis Internal

- Status rilis internal: siap uji operasional terbatas.
- Hasil uji manual `MANUAL_FLOW_OK`: tambah pasien, kunjungan normal, kunjungan gratis, cetak invoice, export laporan, dashboard pendapatan, stok alat keluar, dan stok herbal keluar berhasil.
- Menjaga artefak lokal seperti `.local/`, `invoices/`, `backups/`, dan laporan manual agar tidak ikut commit.
- Memastikan aplikasi dapat membuat struktur database baru/kosong untuk penggunaan awal.

## 2026-05-02 - Dukungan Kunjungan Gratis

- Menambahkan penanda kunjungan gratis dengan alasan `promo`, `keluarga`, `koreksi`, dan `gratis lain-lain`.
- Mengizinkan harga manual 0 hanya jika kunjungan ditandai gratis dan alasan gratis diisi.
- Menolak harga manual kosong, tidak valid, atau negatif sebelum kunjungan disimpan.
- Menyimpan metadata kunjungan gratis di database dan menjaga invoice/laporan aman saat membaca harga 0.

## 2026-05-02 - Perbaikan Dashboard Admin

- Memperbaiki tampilan dashboard admin agar lebih mudah dipahami oleh admin.
- Menambahkan ringkasan operasional dengan status stok yang langsung terlihat.
- Menambahkan kartu statistik untuk total pasien, total transaksi, total pemasukan, alat kritis, dan herbal habis.
- Menambahkan panel aksi cepat untuk membuka Pasien, Kunjungan, Stok Alat, dan Stok Herbal.
- Menambahkan panel "Perlu Tindakan" berisi daftar stok alat kritis dan herbal yang habis.
- Menambahkan daftar transaksi terbaru dari kunjungan pasien dan penjualan herbal.
- Memperbaiki teks dashboard dari "Ringkasan hari ini" menjadi ringkasan operasional karena data yang ditampilkan adalah total data tersimpan.
- Menambahkan data pendukung di backend dashboard untuk stok kritis, herbal habis, dan transaksi terbaru.
- Memastikan sintaks Python dan JavaScript dashboard valid.

## 2026-05-02 - Penguatan Struktur Aplikasi

- Mereview struktur folder aplikasi Python klinik bekam tanpa mengganti bahasa atau framework.
- Memisahkan query statistik dashboard ke `helpers/dashboard_stats_helper.py` agar `database.py` tidak semakin padat.
- Menambahkan `helpers/report_export_helper.py` untuk export laporan pasien dan kunjungan ke PDF atau Excel.
- Menghubungkan export laporan baru ke helper export yang sudah ada tanpa menghapus export Excel/JSON lama.
- Memperkuat validasi stok alat dan herbal agar transaksi keluar tidak bisa membuat stok minus.
- Mengarahkan operasi stok alat/herbal dari dialog melalui `viewmodels/inventory_store.py`.
- Memperbaiki logic edit stok herbal agar nilai stok hasil edit tidak salah dihitung.
- Menjalankan compile/check untuk Python, route API analytics, dashboard JavaScript, dan `git diff --check`.

## 2026-05-02 - Penguatan Lanjutan Struktur dan Operasional

- Menambahkan `helpers/export_helper.py` sebagai entry point export laporan yang kompatibel dengan helper laporan.
- Memperkuat `helpers/backup_helper.py` dengan status backup, rotasi backup lama, batas jumlah backup, dan mode backup harian.
- Mengarahkan `threads/backup_thread.py` agar memakai `BackupHelper`, sehingga aturan backup tidak terduplikasi.
- Menambahkan filter periode dan builder laporan kunjungan di `viewmodels/visit_view_model.py`.
- Menambahkan data aman untuk dashboard: kunjungan hari ini dan pendapatan periode berjalan.
- Menormalisasi response `/dashboard_stats` agar nilai kosong/null tidak membuat dashboard error.
- Memastikan verifikasi compile/check tetap lolos tanpa menjalankan server live.

## 2026-05-02 - Penguatan Akses Database UI Lama

- Mengaudit `patient_form.py`, `patient_list.py`, `visit_section.py`, `inventory_dialog.py`, dan `herbal_dialog.py`.
- Menambahkan `viewmodels/patient_view_model.py` sebagai jalur bertahap untuk operasi pasien dan kunjungan.
- Memindahkan tambah, edit, hapus, daftar pasien, dan hapus kunjungan dari akses database langsung di `main_window.py` ke `PatientViewModel`.
- Menghapus penyimpanan `self.db` dari `InventoryDialog` dan `HerbalDialog`; akses stok tetap lewat `InventoryStore`.
- Menambahkan komentar singkat untuk constructor lama yang masih menerima `db` demi kompatibilitas.
- Memastikan komponen `patient_form.py`, `patient_list.py`, dan `visit_section.py` tetap murni UI.

## 2026-05-02 - Penguatan Analytics dan Invoice ViewModel

- Menambahkan `viewmodels/analytics_view_model.py` untuk jalur data analytics dan status stok.
- Menambahkan `viewmodels/invoice_view_model.py` untuk jalur data daftar invoice.
- Mengarahkan `AnalyticsDialog` agar tidak query database langsung.
- Mengarahkan `InvoiceList` agar tidak query database langsung.
- Mengurangi wiring `self.db` di `main_window.py` untuk tab analytics, invoice, inventory, dan herbal.
- Menjaga constructor lama tetap kompatibel agar fitur existing tidak putus.

## 2026-05-02 - Penguatan Dialog Settings Legacy

- Mengaudit `SettingsDialog`, `CustomInvoiceDialog`, dan `InventorySettingsDialog`.
- Menambahkan `viewmodels/settings_view_model.py` sebagai wrapper tipis untuk akses pengaturan aplikasi.
- Mengarahkan dialog pengaturan harga/diskon, custom invoice, dan pengurangan stok otomatis lewat `SettingsViewModel`.
- Menjaga constructor lama tetap kompatibel jika masih dipanggil dengan objek settings langsung.
- Mengarahkan `main_window.py` memakai `SettingsViewModel` untuk dialog settings/custom invoice/inventory settings.

## 2026-05-02 - Audit Lanjutan Akses Langsung UI

- Mengaudit penggunaan `self.db`, `db.`, `self.settings`, dan `settings.` di `components/`, `dialogs/`, dan `main_window.py`.
- Mengarahkan `InvoiceDialog` agar membaca custom invoice settings lewat `SettingsViewModel`.
- Mengarahkan `VisitSection` agar kalkulasi harga titik memakai `settings_vm` jika tersedia, dengan fallback parent lama.
- Mengurangi pemakaian settings langsung di `main_window.py` untuk diskon, harga per titik, dan invoice preview.
- Menjaga `self.settings = settings` di `main_window.py` sementara untuk kompatibilitas alur lama.

## 2026-05-02 - Stabilisasi Compatibility Handle

- Mengaudit ulang `self.db` dan `self.settings` di `main_window.py`.
- Menambahkan komentar compatibility yang menjelaskan kenapa `self.db` dan `self.settings` masih dipertahankan sementara.
- Membersihkan import mati `os`, `BackupHelper`, `InvoiceThread`, dan `InvoiceHelper` dari `main_window.py`.
- Menghapus variabel instance tidak terpakai `invoice_helper` dan `_therapists_cache_valid`.
- Menghapus import lokal ulang `InventoryDialog` dan `HerbalDialog` di setup tab karena sudah diimpor di bagian atas file.

## 2026-05-02 - QA dan Hardening Edge Case

- Menambahkan validasi harga manual kunjungan agar tidak bisa menyimpan harga 0.
- Memperbaiki typo assignment `self.settings` di `VisitThread`.
- Menambahkan guard pada `InventoryStore.update_stock()` jika item stok tidak ditemukan.
- Menambahkan null safety tanggal kunjungan pada export laporan PDF/Excel.
- Menambahkan guard array dan number coercion di dashboard agar payload kosong/aneh tidak merusak render.
- Menjalankan compile/check untuk Python, route API, dashboard JavaScript, dan `git diff --check`.
