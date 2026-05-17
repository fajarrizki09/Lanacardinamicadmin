# Gap Analysis - LancarDinamicAdmin

> Dibuat berdasarkan pembacaan kode aktual vs. PRD v0.1-draft.  
> Tanggal: 2026-05-18

**Legenda Prioritas:**
- **P0** = Fatal / data bisa salah sekarang
- **P1** = Harus selesai sebelum trial
- **P2** = Harus selesai sebelum jual massal
- **P3** = Polish / kerapian

---

## Tabel Gap

| # | Area | Requirement PRD | Kondisi Kode Saat Ini | Gap | Prioritas | File Terkait | Rekomendasi |
|---|---|---|---|---|---|---|---|
| 1 | **Service Generic** | `pricing_type` di model dan UI | `Service` hanya punya `price_per_unit`. Tidak ada `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price` | Field model hilang. UI tidak bisa menampilkan mode harga yang berbeda | P1 | `db_models.py`, `api/routes/services.py`, `api/static/ts/services.ts` | Tambah kolom ke model Service + migrasi Alembic + UI selector |
| 2 | **Service Generic** | `service_category` di model dan laporan | Tidak ada field `service_category` di `Service` | Laporan tidak bisa breakdown per kategori layanan | P1 | `db_models.py`, `helpers/owner_report_helper.py` | Tambah field + filter category di laporan top services |
| 3 | **Visit Pricing** | `original_price`, `discount_amount`, `final_price` terpisah | Visit hanya punya `price` (Numeric). Tidak ada `original_price` atau `final_price` sebagai field terpisah | Invoice dan laporan tidak bisa menampilkan breakdown harga/diskon dengan benar. Formula laporan memakai `price` bukan `final_price` | P0 | `db_models.py`, `database.py`, `helpers/owner_report_helper.py` | Tambah kolom `original_price`, `discount_amount`, `final_price` ke Visit. Migrasi aman (kolom nullable dulu). Update formula laporan |
| 4 | **Visit Pricing** | `final_price >= 0` divalidasi backend | Tidak ditemukan validasi eksplisit `final_price >= 0` di route kunjungan (bukan hanya di data import) | Kasir bisa simpan kunjungan dengan harga negatif | P0 | `api/routes/patients.py` atau route visit utama | Tambah guard: `if final_price < 0: raise HTTPException(400)` |
| 5 | **Visit — Free Visit** | Free visit wajib alasan, divalidasi di route utama | Validasi sudah ada di `data.py` (import/xlsx), tapi perlu dicek di route **pencatatan kunjungan biasa** | Perlu dicek lebih lanjut di route visit utama (patients.py atau route kunjungan) | P1 | `api/routes/patients.py` | Verifikasi dan tambah validasi jika belum ada |
| 6 | **point_count** | Visit generic, bukan bekam-centric | `Visit.point_count` masih dipakai di seluruh kode (50+ referensi di tests, legacy_ui, export). Nama field masih bekam-centric | Field `point_count` membingungkan untuk layanan non-bekam. Semantiknya seharusnya `quantity` | P2 | `db_models.py`, `database.py`, `tests/`, `data.py` | Rename bertahap: tambah alias `quantity = point_count` dulu, lalu migrasi. Jangan hapus `point_count` sebelum migrasi aman |
| 7 | **Inventori — item_type** | Consumable vs non-consumable harus dibedakan | `Inventory` tidak punya field `item_type`. Auto-deduct via `ServiceInventoryUsage` tidak membedakan tipe item | Non-consumable akan ikut auto-deduct setiap kunjungan | P1 | `db_models.py`, `api/routes/inventory.py` (perlu dicek) | Tambah `item_type` = `consumable`/`non_consumable`. Auto-deduct hanya untuk `consumable` |
| 8 | **Herbal — Stok Minus** | Stok herbal tidak boleh minus | Perlu dicek lebih lanjut di `api/routes/herbals.py`. Ada kemungkinan validasi sudah ada, tapi perlu audit | Jika tidak ada: stok bisa minus | P0 | `api/routes/herbals.py` | Audit dan tambah: `if herbal.stock < quantity: raise HTTPException(400)` |
| 9 | **Herbal — Multi Item Rollback** | Jika satu item stok kurang, semua transaksi dibatalkan | Perlu dicek apakah ada rollback transaksional saat herbal-only multi-item di `herbals.py` | Kemungkinan tidak ada rollback atomik | P0 | `api/routes/herbals.py` | Implementasi: cek semua stok dulu, baru kurangi semua atau tidak sama sekali |
| 10 | **Herbal — Nonaktif** | Herbal nonaktif tidak bisa dijual | Perlu dicek di route herbals | Kemungkinan belum ada filter `is_active` saat penjualan | P1 | `api/routes/herbals.py` | Tambah: `if not herbal.is_active: raise HTTPException(400)` |
| 11 | **Void** | Void wajib alasan dan Admin PIN | Model sudah punya `void_reason`. Perlu cek apakah **required** di route void + apakah Admin PIN dipakai | Perlu dicek lebih lanjut di route void (`patients.py` atau `invoices.py`) | P1 | `api/routes/patients.py`, `api/routes/invoices.py` | Audit route void, pastikan: (1) reason required, (2) Admin PIN dipanggil |
| 12 | **Invoice Template** | Heading "Detail Layanan" (bukan "Bekam") | Perlu dicek di `helpers/invoice_helper.py` | Mungkin ada string hardcode "bekam" atau "titik bekam" di template PDF | P1 | `helpers/invoice_helper.py` | Grep "bekam" di invoice_helper, ganti ke istilah generik |
| 13 | **Invoice Path** | Aman dari path traversal | Perlu dicek di `invoice_helper.py`: apakah nama file di-sanitize | Kemungkinan belum ada sanitasi karakter Windows (`\/:*?"<>|`) dan `../` | P1 | `helpers/invoice_helper.py` | Tambah sanitasi nama file dan `os.path.abspath` + validasi path ada di dalam folder invoices |
| 14 | **Laporan — double count** | Herbal ikut kunjungan tidak dihitung dua kali | `owner_report_helper.py`: `visit_revenue` dari `Visit.price`, `herbal_revenue` dari `HerbalTransaction` terpisah. Jika herbal transaksi punya `visit_id`, kemungkinan tidak double count, tapi perlu verifikasi query analytics | Perlu dicek lebih lanjut di `api/routes/analytics.py` | P0 | `helpers/owner_report_helper.py`, `api/routes/analytics.py` | Audit query analytics. Pastikan tidak ada SUM yang gabunginvoice + visit |
| 15 | **Laporan — formula** | Laporan pakai `final_price`, bukan `price` | `owner_report_helper.py` masih memakai `Visit.price` sebagai base revenue | Saat ini hanya ada `Visit.price`, belum ada `final_price`. Ini harus diselesaikan bersamaan dengan gap #3 | P0 | `helpers/owner_report_helper.py` | Setelah field `final_price` ditambahkan, update formula owner_report |
| 16 | **Payment Status** | Status `refunded` di PRD | `payment_rules.py` punya `partial` tapi PRD pakai `refunded`. PRD tidak menyebut `partial` | Inkonsistensi standar payment_status antara PRD dan kode | P2 | `helpers/payment_rules.py`, `docs/PRD.md` | Selaraskan PRD dengan kode atau sebaliknya. Tambahkan `refunded` jika dibutuhkan |
| 17 | **Security — Error Leak** | Error tidak boleh bocor stack trace | FastAPI default mengirim detail exception. Perlu cek apakah ada global exception handler | Kemungkinan stack trace bisa bocor ke frontend lewat `HTTPException(500, detail=str(e))` | P1 | `api/main.py`, semua route | Tambah global exception handler yang meng-sanitasi `detail` di response 500 |
| 18 | **Security — Input Escape** | Input user di-escape sebelum tampil di HTML | `escapeHtml()` sudah ada di `services.ts`. Perlu cek modul lain (app.js, modules/*.js) | Perlu dicek lebih lanjut di `api/static/app.js` dan modul JS lain | P1 | `api/static/app.js`, `api/static/modules/` | Audit semua tempat innerHTML yang menggunakan data dari API tanpa escaping |
| 19 | **Runtime di Git** | `data.db`, `settings.json`, `*.db-shm`, invoices/, logs/ tidak ikut repo | Root directory punya `data.db`, `settings.json`, `smart_discount_*.db-shm` di repo | File runtime ikut repo. Jika di-push, data developer bisa tersebar | P1 | `.gitignore` | Update `.gitignore`, jalankan `git rm --cached` untuk file yang sudah ter-track |
| 20 | **TS Migration** | `types.ts` sebagai single source of truth | Ada folder `ts/` dengan 14 file TS. Tapi `Service` interface didefinisikan langsung di `services.ts` (bukan di types.ts terpisah) | Duplikasi type kemungkinan terjadi. Belum ada `types.ts` terpusat | P2 | `api/static/ts/*.ts`, `types/` folder | Buat `types.ts`, pindahkan semua interface ke sana, import dari sana |
| 21 | **LancarDinamicAdmin.zip** | File ZIP tidak boleh ikut repo | Ada `LancarDinamicAdmin.zip` (1.5MB) di root repo | Repo mengandung file ZIP besar | P1 | `.gitignore`, root | `git rm --cached LancarDinamicAdmin.zip` lalu tambah ke `.gitignore` |
| 22 | **dialogs.zip** | File ZIP tidak boleh ikut repo | Ada `dialogs.zip` (98KB) di root repo | File ZIP ikut repo | P2 | `.gitignore` | Hapus dari tracking atau pindahkan ke luar repo |
| 23 | **build/ dan dist/** | Folder build tidak boleh ikut repo | Ada folder `build/` dan `dist/` di root | Build artifacts ikut repo | P1 | `.gitignore` | Tambah `build/` dan `dist/` ke `.gitignore` |

---

## Ringkasan Gap per Prioritas

### P0 — Fatal (data bisa salah sekarang)
1. Visit tidak punya `original_price`, `discount_amount`, `final_price` terpisah
2. Tidak ada validasi `final_price >= 0` di route backend
3. Stok herbal mungkin bisa minus (perlu audit)
4. Herbal multi-item mungkin tidak punya rollback atomik
5. Laporan memakai `Visit.price` bukan `final_price` — sinkron dengan #1

### P1 — Harus selesai sebelum trial
1. Service tidak punya `pricing_type` dan `service_category`
2. Inventori tidak punya `item_type` (consumable / non-consumable)
3. Void tidak jelas apakah wajib alasan + Admin PIN di route
4. Invoice template mungkin masih ada label "bekam"
5. Invoice path mungkin belum aman dari traversal
6. Error response mungkin bocor stack trace
7. Runtime files (`data.db`, `settings.json`, ZIP, `*.db-shm`) masih di repo

### P2 — Selesai sebelum jual massal
1. `point_count` perlu rename bertahap ke `quantity`
2. Payment status: `refunded` vs `partial` perlu diselaraskan
3. `types.ts` sebagai single source of truth TypeScript
4. Input escaping perlu audit di semua modul JS

### P3 — Polish
1. Top kategori layanan di laporan (butuh `service_category` lebih dulu)
2. Laporan filter pending payment konsisten
