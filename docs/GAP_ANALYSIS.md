# Gap Analysis - LancarDinamicAdmin

> Dibuat berdasarkan pembacaan kode aktual vs. PRD v0.1-draft.  
> Tanggal: 2026-05-18  
> Update P0/P1/P2: gap fatal, gap trial, dan sebagian hardening jual massal sudah dipatch dan diberi regression test pada 2026-05-18.

**Legenda Prioritas:**
- **P0** = Fatal / data bisa salah sekarang
- **P1** = Harus selesai sebelum trial
- **P2** = Harus selesai sebelum jual massal
- **P3** = Polish / kerapian

---

## Tabel Gap

| # | Area | Requirement PRD | Kondisi Kode Saat Ini | Gap | Prioritas | File Terkait | Rekomendasi |
|---|---|---|---|---|---|---|---|
| 1 | **Service Generic** | `pricing_type` di model dan UI | **DONE BACKEND 2026-05-18:** `Service` sudah punya `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`; migrasi SQLite dan route add/update sudah menerima field baru | UI selector lanjutan masih perlu polishing agar operator bisa memilih mode harga secara eksplisit | P1 ✅ | `db_models.py`, `database.py`, `db_dataclasses.py`, `api/routes/services.py`, `types/admin-globals.d.ts` | Tambahkan polish UI selector dan test route service fixed/per-unit |
| 2 | **Service Generic** | `service_category` di model dan laporan | **DONE BACKEND 2026-05-18:** `service_category` sudah tersedia di model, DTO, route, dan payload service | Breakdown laporan per kategori masih perlu UI/filter tambahan | P1 ✅ | `db_models.py`, `database.py`, `helpers/owner_report_helper.py` | Tambah filter kategori/top kategori di laporan owner |
| 3 | **Visit Pricing** | `original_price`, `discount_amount`, `final_price` terpisah | **DONE + TESTED 2026-05-18:** `Visit` sudah punya field `original_price`, `discount_amount`, `final_price`; migration/backfill ditambahkan; `add_visit` menyimpan breakdown harga; regression test memastikan owner report memakai `final_price` | Gap utama sudah ditutup. UI/invoice visual tetap bisa diuji manual sebelum release | P0 ✅ | `db_models.py`, `database.py`, `db_dataclasses.py`, `tests/test_p0_regressions.py` | Jalankan test regresi sebelum build release |
| 4 | **Visit Pricing** | `final_price >= 0` divalidasi backend | **DONE + TESTED 2026-05-18:** flow `add_visit`, add/update patient visits sudah menolak harga negatif dan harga 0 tanpa flag gratis; test memastikan free visit wajib alasan | Risiko utama harga negatif/free visit tanpa alasan sudah ditutup di backend database layer | P0 ✅ | `database.py`, `tests/test_p0_regressions.py` | Jalankan test route/API tambahan bila endpoint berubah |
| 5 | **Visit — Free Visit** | Free visit wajib alasan, divalidasi di route utama | **DONE 2026-05-18:** validasi free visit wajib alasan sudah dikunci di database layer untuk add/import/update patient visits | Perlu test route/API agar error user-friendly tetap terjaga | P1 ✅ | `database.py`, `api/routes/patients.py` | Tambahkan test route/API free visit tanpa alasan |
| 6 | **point_count** | Visit generic, bukan bekam-centric | **DONE ALIAS 2026-05-18:** `Visit.quantity` sudah ditambahkan sebagai ORM synonym ke `point_count`; `Database.add_visit(..., quantity=...)` diterima; `VisitData.quantity` tersinkron dengan `point_count`; test P2 menjaga alias ini | Nama kolom fisik DB masih `point_count` agar backward-compatible. Rename fisik bisa dilakukan di major migration berikutnya | P2 ✅ | `db_models.py`, `database.py`, `db_dataclasses.py`, `tests/test_p2_hardening.py` | Jangan hapus `point_count` sebelum migration major; pakai `quantity` untuk kode baru |
| 7 | **Inventori — item_type** | Consumable vs non-consumable harus dibedakan | **DONE BACKEND 2026-05-18:** `Inventory.item_type` sudah ditambah dengan default `consumable`; add/edit inventory menerima field; auto-deduct layanan hanya memotong `consumable` | UI inventory perlu selector item type agar operator tidak perlu payload manual | P1 ✅ | `db_models.py`, `database.py`, `api/routes/inventory.py`, `types/admin-globals.d.ts` | Tambah selector UI consumable/non-consumable dan test auto-deduct |
| 8 | **Herbal — Stok Minus** | Stok herbal tidak boleh minus | **DONE + TESTED 2026-05-18:** validasi stok cukup dan herbal aktif ada di `_validate_visit_herbal_items`, `add_herbal_sale`, `add_visit`, dan `update_herbal_stock`; test memastikan stok kurang ditolak | Risiko stok minus dari sale/koreksi sudah ditutup di database layer | P0 ✅ | `database.py`, `api/routes/herbals.py`, `tests/test_p0_regressions.py` | Jalankan test route herbal sale stok kurang bila endpoint berubah |
| 9 | **Herbal — Multi Item Rollback** | Jika satu item stok kurang, semua transaksi dibatalkan | **DONE + TESTED 2026-05-18:** herbal-only sale memakai transaction context dan re-check semua item sebelum deduct; regression test memastikan stok semua item tetap dan transaksi tidak dibuat saat salah satu item kurang | Gap atomic rollback utama sudah ditutup | P0 ✅ | `database.py`, `api/routes/herbals.py`, `tests/test_p0_regressions.py` | Pertahankan test ini sebagai guard release |
| 10 | **Herbal — Nonaktif** | Herbal nonaktif tidak bisa dijual | **VERIFIED 2026-05-18:** database layer sudah menolak herbal nonaktif pada `_validate_visit_herbal_items` dan `add_herbal_sale`; route herbal sale memanggil layer ini | Tetap perlu integration test route untuk pesan error | P1 ✅ | `database.py`, `api/routes/herbals.py` | Tambahkan test route herbal nonaktif tidak bisa dijual |
| 11 | **Void** | Void wajib alasan dan Admin PIN | **DONE 2026-05-18:** route `/void_invoice` sudah memanggil `require_admin_pin`; reason kosong sekarang ditolak sebelum void | Perlu test route void tanpa reason/Admin PIN | P1 ✅ | `api/routes/invoices.py`, `database.py` | Tambahkan test void invoice reason/Admin PIN |
| 12 | **Invoice Template** | Heading "Detail Layanan" (bukan "Bekam") | **DONE 2026-05-18:** grep `invoice_helper.py` hanya menemukan fallback unit khusus Bekam; fallback diganti generik `layanan` | Tetap perlu visual regression PDF | P1 ✅ | `helpers/invoice_helper.py` | Tambahkan snapshot/visual check invoice generik |
| 13 | **Invoice Path** | Aman dari path traversal | **DONE 2026-05-18:** output dir dibuat absolut; filename disanitasi; output path divalidasi tetap di dalam folder invoice; service dan herbal invoice memakai helper aman | Perlu test permanen untuk nama invoice/pasien berbahaya | P1 ✅ | `helpers/invoice_helper.py` | Tambahkan test path traversal invoice |
| 14 | **Laporan — double count** | Herbal ikut kunjungan tidak dihitung dua kali | **DONE + TESTED 2026-05-18:** owner report/analytics memisahkan `visit_revenue` dan `herbal_revenue`; test skenario visit + herbal memastikan revenue layanan dan herbal dijumlah tepat satu kali | Gap double-count utama sudah ditutup | P0 ✅ | `helpers/owner_report_helper.py`, `database.py`, `api/routes/analytics.py`, `tests/test_p0_regressions.py` | Tambahkan test return herbal lanjutan bila flow return diubah |
| 15 | **Laporan — formula** | Laporan pakai `final_price`, bukan `price` | **DONE + TESTED 2026-05-18:** owner report, dashboard stats, dan analytics revenue expression memakai `Visit.final_price` dengan fallback ke `Visit.price`; `partial` memakai `amount_paid`; test mencakup paid/partial/free/void | Formula utama sudah diselaraskan dan dijaga test | P0 ✅ | `helpers/owner_report_helper.py`, `helpers/dashboard_stats_helper.py`, `database.py`, `tests/test_p0_regressions.py` | Jalankan regression test sebelum build release |
| 16 | **Payment Status** | Status `refunded` di PRD | **DONE 2026-05-18:** `VALID_PAYMENT_STATUSES` sekarang memuat `refunded`; normalize payment mengembalikan `amount_paid=0`; formatter UI punya label `Refund`; PRD sudah memuat `partial` dan `refunded` | Refund masih status data; flow refund uang otomatis belum dibuat | P2 ✅ | `helpers/payment_rules.py`, `api/static/ts/formatters.ts`, `docs/PRD.md`, `tests/test_p2_hardening.py` | Tambahkan workflow refund kas/gateway jika dibutuhkan di versi berikutnya |
| 17 | **Security — Error Leak** | Error tidak boleh bocor stack trace | **VERIFIED 2026-05-18:** `api/main.py` sudah punya global handler `HTTPException`, `RequestValidationError`, dan `Exception`; detail teknis 500 disanitasi dan dicatat ke log | Perlu audit route yang mengembalikan 400 `str(e)` agar pesan domain tetap aman | P1 ✅ | `api/main.py`, semua route | Tambahkan test exception handler dan audit pesan 400 |
| 18 | **Security — Input Escape** | Input user di-escape sebelum tampil di HTML | **HARDENED + TESTED 2026-05-18:** audit `innerHTML` dilakukan; helper `LancarDom.assertEscapedHtml()` ditambah untuk memblokir pattern raw HTML berbahaya saat memakai DOM helper; render badge inventory/herbal dari `dataset` sudah di-escape; test menjaga guard DOM dan escape badge | Template HTML besar masih boleh dipakai untuk HTML statis, tetapi data API/dataset wajib `escapeHtml()` | P1/P2 ✅ | `api/static/ts/dom.ts`, `api/static/ts/inventory.ts`, `api/static/ts/herbals.ts`, `tests/test_p2_hardening.py` | Untuk kode baru, escape semua data API sebelum masuk template; gunakan DOM helper bila render HTML dinamis |
| 19 | **Runtime di Git** | `data.db`, `settings.json`, `*.db-shm`, invoices/, logs/ tidak ikut repo | **VERIFIED 2026-05-18:** `.gitignore` sudah memuat `*.db`, `*.db-shm`, `*.db-wal`, `settings.json`, `data.db`, `invoices/`, `logs/`, `exports/`, `*.zip`, `build/`, `dist/` | Jika file sudah pernah ter-track, tetap perlu `git rm --cached` manual | P1 ✅ | `.gitignore` | Jalankan audit `git ls-files` dan `git rm --cached` bila masih tracked |
| 20 | **TS Migration** | `types.ts` sebagai single source of truth | **DONE 2026-05-18:** `api/static/ts/types.ts` ditambahkan sebagai pusat tipe frontend untuk kontrak umum (`AdminVisit`, `AdminServiceModel`, `AdminInventoryModel`, `PaymentStatus`, dll.); alias duplikat di `types/admin-globals.d.ts` dihapus agar tidak bentrok; test memastikan file tipe bersama ada | Beberapa tipe lokal modul tetap lokal karena khusus UI modul tersebut | P2 ✅ | `api/static/ts/types.ts`, `types/admin-globals.d.ts`, `tests/test_p2_hardening.py` | Untuk tipe lintas modul baru, tambahkan ke `api/static/ts/types.ts` dulu |
| 21 | **LancarDinamicAdmin.zip** | File ZIP tidak boleh ikut repo | **VERIFIED 2026-05-18:** `.gitignore` sudah memuat `*.zip` | Jika ZIP sudah tracked, tetap perlu `git rm --cached LancarDinamicAdmin.zip` manual | P1 ✅ | `.gitignore`, root | Audit `git ls-files *.zip` sebelum push |
| 22 | **dialogs.zip** | File ZIP tidak boleh ikut repo | Ada `dialogs.zip` (98KB) di root repo | File ZIP ikut repo | P2 | `.gitignore` | Hapus dari tracking atau pindahkan ke luar repo |
| 23 | **build/ dan dist/** | Folder build tidak boleh ikut repo | **VERIFIED 2026-05-18:** `.gitignore` sudah memuat `build/` dan `dist/` | Jika artifact sudah tracked, tetap perlu `git rm --cached -r build dist` manual | P1 ✅ | `.gitignore` | Audit `git ls-files build dist` sebelum push |

---

## Ringkasan Gap per Prioritas

### P0 — Fatal (data bisa salah sekarang)
1. ✅ Visit sudah punya `original_price`, `discount_amount`, `final_price` terpisah.
2. ✅ Validasi harga negatif/free visit sudah ada di backend database layer.
3. ✅ Stok herbal sale/koreksi dicek agar tidak minus.
4. ✅ Herbal multi-item sale memakai transaction context dan pre-check semua item.
5. ✅ Laporan utama memakai `Visit.final_price` dengan fallback `Visit.price`; `partial` memakai `amount_paid`.

Catatan: P0 inti sudah dipatch dan diberi regression test di `tests/test_p0_regressions.py`.

### P1 — Harus selesai sebelum trial
1. ✅ Backend service sudah punya `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`.
2. ✅ Backend inventory sudah punya `item_type`; auto-deduct hanya untuk `consumable`.
3. ✅ Void invoice sudah wajib alasan dan route sudah memakai Admin PIN.
4. ✅ Invoice helper tidak lagi memakai fallback unit khusus Bekam; fallback generik `layanan`.
5. ✅ Invoice output path sudah disanitasi dan dikunci di folder invoices.
6. ✅ Global API error handler sudah tersedia untuk sanitasi 500/validation error.
7. ✅ `.gitignore` sudah mencakup runtime files, ZIP, build/, dist/.

Catatan: P1 backend/security inti sudah dipatch/diverifikasi. Masih disarankan polish UI selector service/inventory dan test otomatis route/regression sebelum trial.

### P2 — Selesai sebelum jual massal
1. ✅ `point_count` sudah punya alias aman `quantity` di ORM, database API, dan dataclass.
2. ✅ Payment status `refunded` sudah diselaraskan dengan `partial` dan diuji.
3. ✅ `types.ts` sebagai single source of truth TypeScript sudah dibuat untuk kontrak frontend umum.
4. ✅ Input escaping sudah diaudit, DOM helper diberi guard unsafe HTML, dan render dataset raw sudah dipatch.

### P3 — Polish
1. ✅ Top kategori layanan sudah tampil di laporan owner melalui `top_service_categories`.
2. ✅ Laporan owner sudah punya KPI piutang/pending konsisten untuk `unpaid`, `pending`, dan sisa `partial`.

Catatan P3: test polish tersedia di `tests/test_p3_polish.py`.
