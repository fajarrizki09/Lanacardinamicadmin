# Requirements Checklist - LancarDinamicAdmin

> Diturunkan dari PRD v0.1-draft. Dipakai oleh developer, QA, dan AI assistant.  
> Format: `[ ]` belum | `[/]` sedang | `[x]` selesai

---

## 1. Service / Layanan Generic

- [ ] Model `Service` punya field `pricing_type` (`per_unit`, `fixed`, `manual`, `free`, `package`)
- [ ] Model `Service` punya field `service_category`
- [ ] Model `Service` punya field `fixed_price`
- [ ] Model `Service` punya field `allow_manual_price`
- [x] Model `Service` punya field `unit_label`
- [x] Model `Service` punya field `default_quantity`
- [x] Model `Service` punya field `price_per_unit`
- [x] Model `Service` punya field `notes_template`
- [x] Model `Service` punya field `is_active`
- [x] `ServiceInventoryUsage` linked ke `service_id` (bukan hardcode)
- [ ] UI form service menampilkan pilihan `pricing_type`
- [ ] UI form service menampilkan pilihan `service_category`
- [x] UI label satuan mengikuti `unit_label` (bukan hardcode "titik bekam")
- [ ] Invoice menggunakan heading **"Detail Layanan"** (bukan "Detail Bekam")
- [ ] Laporan mendukung top layanan **per kategori** (`service_category`)
- [x] Laporan mendukung top layanan (sudah ada di owner_report_helper)

---

## 2. Pencatatan Kunjungan

- [x] Layanan nonaktif tidak bisa dipilih
- [x] Terapis nonaktif tidak bisa dipilih
- [ ] Visit model punya field `original_price` (terpisah dari `price`)
- [ ] Visit model punya field `discount_amount`
- [ ] Visit model punya field `final_price` (harga setelah diskon)
- [x] `discount_rule_id` tersimpan di visit
- [x] `discount_rule_name` tersimpan di visit
- [x] `is_free_visit` tersimpan
- [x] `free_visit_reason` wajib diisi jika `is_free_visit = true` (sudah dicek di import)
- [ ] Validasi `final_price >= 0` di **backend route** (bukan hanya di import)
- [ ] `manual_price` tidak boleh negatif (belum ada field/validasi eksplisit)
- [x] Stok alat dicek via `ServiceInventoryUsage` sebelum visit disimpan
- [ ] Stok alat **hanya berkurang setelah konfirmasi final** (perlu audit flow)
- [ ] Create visit + deduct stok bersifat atomic atau punya rollback aman
- [ ] Double submit dari UI dicegah (loading state / disable button)

---

## 3. Penjualan Herbal

- [x] Herbal bisa ikut kunjungan (`visit_id` di `HerbalTransaction`)
- [x] Herbal bisa dijual tanpa kunjungan (herbal-only)
- [x] Herbal-only boleh tanpa `patient_id`
- [x] Multi item herbal-only punya `sale_group_id` yang sama
- [ ] Stok **tidak berkurang** saat item ditambahkan di UI (perlu dicek di route herbals)
- [ ] Stok berkurang **hanya setelah konfirmasi final** (perlu audit flow herbals)
- [ ] Jika satu item stok kurang, seluruh transaksi multi-item dibatalkan (rollback)
- [x] Invoice herbal-only membaca semua item dalam `sale_group_id`
- [ ] Herbal nonaktif tidak bisa dijual (perlu cek validasi di route)

---

## 4. Stok Herbal

- [x] `transaction_type = sale` → stok berkurang
- [x] `transaction_type = stock_in` → stok bertambah
- [x] `transaction_type = return/retur` → stok bertambah
- [x] `transaction_type = adjustment` → koreksi manual
- [ ] Validasi stok tidak minus **di backend** (perlu dicek di route herbals)
- [ ] `adjustment` wajib alasan (perlu cek route)
- [ ] `adjustment` butuh Admin PIN (perlu dicek)
- [x] Semua perubahan stok masuk `herbal_transactions` (via transaction log)
- [x] `return` tidak menghapus transaksi `sale` lama (model sudah mendukung)
- [ ] Hard delete `Herbal` tidak boleh menghapus `herbal_transactions` terkait (perlu cek cascade)

---

## 5. Inventori Alat Klinik

- [ ] Model `Inventory` punya field `item_type` (`consumable` | `non_consumable`)
- [x] `ServiceInventoryUsage` bisa auto-deduct consumable
- [ ] Non-consumable **tidak** auto-deduct setiap kunjungan (belum ada pembeda)
- [ ] Stok tidak boleh minus setelah deduct (perlu cek validasi)
- [ ] `adjustment` wajib alasan (perlu cek route inventory)
- [ ] `adjustment` butuh Admin PIN (perlu cek)
- [x] Semua pergerakan stok masuk `inventory_transactions`
- [x] `service_inventory_usage` linked ke `service_id`
- [ ] Void visit punya kebijakan stok alat yang jelas (dikembalikan/tidak/user pilih)

---

## 6. Invoice

- [x] Invoice untuk layanan terapi saja
- [x] Invoice untuk herbal-only
- [x] Invoice untuk gabungan layanan + herbal
- [ ] Template invoice menggunakan heading **"Detail Layanan"** (bukan "bekam")
- [x] Invoice number unik
- [ ] Invoice path aman dari path traversal (perlu dicek `invoice_helper.py`)
- [ ] Nama file PDF aman untuk Windows (tidak ada karakter `\/:*?"<>|`)
- [x] PDF gagal dibuat menghasilkan status error (perlu validasi di route)
- [x] Void invoice tidak masuk pendapatan aktif (sudah dihandle di owner_report)
- [ ] Invoice tidak menyebabkan double count laporan (perlu audit query laporan)

---

## 7. Diskon, Voucher, Gratis

- [x] Diskon dihitung dari `original_price` / harga asli
- [ ] `discount_amount` tidak melebihi `original_price` (belum ada field terpisah di Visit)
- [ ] `final_price` tidak negatif (belum ada validasi backend eksplisit)
- [x] Voucher khusus pasien pakai `VoucherPatientTarget` (sudah ada model)
- [ ] Validasi voucher khusus pasien tidak bisa dipakai pasien lain (perlu cek route)
- [x] `VoucherUsage` punya unique index per visit (sudah ada `idx_voucher_usage_visit_unique`)
- [x] Free visit: `final_price = 0` (via `is_free_visit`)
- [x] Free visit wajib alasan (sudah divalidasi di import, perlu cek route utama juga)
- [ ] `original_price` tetap tersimpan walaupun gratis (belum ada field di Visit)
- [ ] Laporan memakai `final_price` (perlu audit formula laporan)

---

## 8. Void, Retur, Koreksi

- [x] Void tidak hard delete (pakai `invoice_status = 'void'`)
- [x] `void_reason` tersimpan di Visit dan HerbalTransaction
- [ ] Void wajib alasan (perlu cek route apakah reason diwajibkan)
- [ ] Void butuh Admin PIN (perlu cek route void)
- [x] Void tidak masuk pendapatan aktif (sudah difilter di owner_report_helper)
- [x] Retur herbal membuat transaksi `return/retur`
- [ ] Retur menambah stok (perlu cek implementasi di route herbals)
- [x] Retur mengurangi net revenue (sudah dihandle di owner_report_helper)
- [ ] Koreksi stok wajib alasan (perlu cek)
- [ ] Koreksi stok butuh Admin PIN (perlu cek)
- [x] Semua aksi sensitif masuk `audit_logs`

---

## 9. Laporan / Analytics / Owner Report

- [x] `visit_revenue = sum(price) dari visit aktif` (ada di owner_report_helper)
- [ ] `visit_revenue` harus pakai `final_price`, bukan `price` (saat ini pakai `Visit.price`)
- [x] `herbal_revenue = sale - return` (sudah diimplementasikan)
- [x] `total_revenue = visit_revenue + herbal_revenue`
- [x] Invoice tidak dihitung ulang jika visit/herbal sudah dihitung
- [ ] Herbal ikut kunjungan tidak double count (perlu audit query analytics)
- [x] Void dikecualikan (filter `invoice_status != 'void'`)
- [x] Return mengurangi `net_herbal_sales`
- [ ] Pending payment tidak dihitung jika laporan hanya dari `paid` (payment_rules perlu diselaraskan)
- [x] Dashboard aman terhadap null/empty (perlu cek semua endpoint dashboard)
- [x] Owner Report memisahkan `visit_revenue` dan `herbal_revenue`
- [ ] Laporan mendukung top kategori layanan (`service_category`)

---

## 10. Security & Runtime Data

- [x] Endpoint lokal memakai `X-App-Token` (ada `local_token.py`)
- [x] Aksi sensitif memakai Admin PIN (ada `admin_pin.py`)
- [ ] Error tidak membocorkan stack trace/path database ke frontend (perlu audit handler)
- [ ] Settings sensitif tidak bocor ke response frontend (perlu audit `/settings` route)
- [ ] Input user/payment reference di-escape sebelum ditampilkan di HTML
- [ ] `data.db` tidak ikut Git (ada di root, perlu cek `.gitignore`)
- [ ] `settings.json` tidak ikut Git
- [ ] `invoices/`, `backups/`, `logs/`, `exports/` tidak ikut Git/build
- [ ] `*.db-shm`, `*.db-wal` tidak ikut Git (saat ini ada `smart_discount_*.db-shm` di root)
- [ ] `__pycache__/`, `*.pyc` tidak ikut Git
- [x] Backup/restore ada fitur manual

---

## 11. TypeScript Migration

- [ ] `types.ts` menjadi single source of truth semua data model frontend
- [ ] `admin-globals.d.ts` hanya untuk Window/global declarations
- [ ] Tidak ada duplikasi type besar antara file
- [ ] Type frontend cocok dengan payload backend
- [x] Migrasi JS ke TS sudah dimulai (ada folder `ts/` dengan 14 file)
- [ ] Modul kritis (`visits`, `invoices`) belum dimigrasi — jangan migrasi dulu sebelum logic stabil
- [ ] Jalankan `tsc --noEmit` tanpa error di modul yang sudah dimigrasi

---

## 12. CRM WhatsApp Puppeteer Automation

- [ ] Fitur disabled by default.
- [ ] Ada setting `enable_whatsapp_puppeteer`.
- [ ] Admin harus klik tombol **Kirim WhatsApp**.
- [ ] Satu klik hanya mengirim ke satu pasien.
- [ ] Tidak ada bulk send.
- [ ] Tidak ada background send.
- [ ] Tidak bypass QR login WhatsApp Web.
- [ ] Nomor pasien dinormalisasi ke format `62`.
- [ ] Pasien **JANGAN DIHUBUNGI** ditolak.
- [ ] Template promo ditolak untuk pasien **JANGAN PROMO**.
- [ ] Pesan kosong ditolak.
- [ ] Send lock mencegah spam.
- [ ] Tombol disabled saat sending.
- [ ] Status `sending`/`sent`/`failed`/`blocked` tampil di UI.
- [ ] Log dibuat di `crm_whatsapp_logs`.
- [ ] Fallback **Copy Pesan** tetap tersedia.
- [ ] Error tidak membocorkan stack trace.
- [ ] Test mock tersedia.
- [ ] Test real kirim hanya manual/local, bukan CI.
