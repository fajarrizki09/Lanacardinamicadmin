# PRD - LancarDinamicAdmin

> **Versi:** 0.1-draft | **Tanggal:** 2026-05-18 | **Status:** Internal – belum untuk distribusi publik

---

## 1. Ringkasan Produk

**LancarDinamicAdmin** adalah aplikasi desktop hybrid untuk manajemen administrasi klinik terapi.  
Aplikasi berjalan lokal di Windows, tidak membutuhkan internet setelah aktivasi, dan menyimpan semua data secara lokal (SQLite).

Aplikasi menggabungkan backend Python/FastAPI dengan frontend berbasis browser (PySide6 WebEngine + JavaScript/TypeScript).  
Target pertama adalah klinik terapi skala kecil–menengah yang saat ini masih menggunakan catatan manual atau spreadsheet.

Aplikasi ini **bukan** aplikasi bekam saja. Bekam adalah salah satu jenis layanan dari banyak layanan terapi yang didukung.

---

## 2. Target Pengguna

| Peran | Deskripsi |
|---|---|
| **Owner Klinik** | Melihat laporan pendapatan, analitik, dan kondisi operasional klinik |
| **Admin / Kasir** | Mencatat kunjungan, penjualan herbal, membuat invoice, mengelola stok |
| **Terapis** | Dicatat nama dan statusnya; tidak perlu login aktif ke aplikasi |
| **Staff Stok / Operasional** | Mengelola inventori alat dan herbal, melakukan retur dan koreksi stok |
| **Support Aplikasi** | Mengakses log, melakukan backup/restore, mengelola lisensi |

---

## 3. Masalah yang Diselesaikan

- **Pencatatan pasien manual** → data kunjungan sulit dicari, mudah hilang
- **Invoice manual** → rawan salah hitung, tidak ada jejak perubahan
- **Stok herbal tidak teratur** → stok minus tidak terdeteksi, retur tidak tercatat
- **Stok alat habis pakai** → tidak ada track pemakaian per kunjungan
- **Laporan pendapatan tidak akurat** → tidak memisahkan layanan vs herbal, void tidak dikecualikan
- **Data kunjungan sulit dicari** → tidak ada filter tanggal, terapis, atau layanan
- **Retur/void tidak terlacak** → transaksi lama dihapus langsung, tidak ada jejak audit
- **Backup sering lupa** → tidak ada reminder atau backup otomatis

---

## 4. Tujuan Produk

1. Mencatat dan mencari data pasien dengan mudah
2. Mencatat kunjungan terapi untuk berbagai jenis layanan
3. Mencatat penjualan herbal (ikut kunjungan maupun standalone)
4. Mengelola stok alat klinik dan herbal/produk
5. Membuat invoice PDF yang akurat dan aman
6. Membuat laporan pendapatan untuk owner
7. Menyimpan audit log setiap aksi sensitif
8. Menyediakan backup dan restore data lokal
9. Berjalan lokal/offline setelah aktivasi sesuai aturan lisensi

---

## 5. Scope Fitur

- Manajemen pasien (CRUD, riwayat kunjungan)
- Manajemen terapis (CRUD, status aktif)
- Manajemen layanan terapi (generic, tidak terbatas bekam)
- Pencatatan kunjungan dengan pemilihan layanan, terapis, dan quantity
- Penjualan herbal ikut kunjungan (cart/draft)
- Penjualan herbal standalone (herbal-only sale)
- Inventori alat klinik (consumable dan non-consumable)
- Invoice PDF (layanan saja, herbal saja, atau gabungan)
- Diskon, voucher, dan kunjungan gratis
- Retur herbal
- Void invoice / kunjungan
- Dashboard ringkasan harian/mingguan
- Analitik (top layanan, top terapis, top produk)
- Owner Report (pendapatan bersih, komposisi revenue)
- CRM WhatsApp semi-manual (copy-paste atau buka WA Web)
- Backup / restore data lokal
- Admin PIN untuk aksi sensitif
- Lisensi / trial dengan limit waktu atau kunjungan

---

## 6. Non-Scope Saat Ini

- Bukan Rekam Medis Elektronik (RME) resmi
- Bukan integrasi SATUSEHAT / BPJS
- Bukan sistem multi-cabang cloud penuh
- Bukan WhatsApp auto-send resmi (kecuali ada provider API yang diintegrasikan)
- Bukan payment gateway production penuh sebelum alur E2E diuji
- Bukan aplikasi mobile native (Android/iOS)
- Bukan multi-user cloud database
- Bukan pengganti konsultasi medis

---

## 7. Definisi Entitas Utama

### Patient
Pasien klinik. Menyimpan nama, kontak, riwayat kunjungan, dan catatan umum.  
Relasi: satu pasien → banyak visit.

### Therapist
Terapis yang melakukan layanan. Punya status aktif/nonaktif.  
Relasi: satu terapis → banyak visit.

### Service / Layanan Terapi
Layanan yang tersedia di klinik. Generic, bukan bekam-only.  
Berisi pricing_type, unit_label, dan konfigurasi inventori yang dipakai.  
Relasi: satu service → banyak visit_items, satu service → banyak service_inventory_usage.

### Visit / Kunjungan
Satu sesi kunjungan pasien ke klinik. Berisi informasi layanan, terapis, harga, diskon, status pembayaran, dan status void.  
Relasi: satu visit → satu invoice, satu visit → banyak herbal_transactions (jika ada herbal).

### Herbal / Product
Produk herbal atau produk lain yang dijual. Punya stok.  
Relasi: satu herbal → banyak herbal_transactions.

### HerbalTransaction
Log setiap pergerakan herbal: `stock_in`, `sale`, `return`, `adjustment`.  
Relasi: ke herbal, ke visit (jika ikut kunjungan), ke sale_group (jika herbal-only multi item).

### InventoryItem
Item inventori klinik (alat habis pakai atau alat tahan lama).  
Field: `item_type` = `consumable` | `non_consumable`.  
Relasi: satu item → banyak inventory_transactions.

### InventoryTransaction
Log setiap pergerakan inventori alat. Berisi `transaction_type`, `quantity`, `reason`, `timestamp`.

### Invoice
Dokumen tagihan yang dihasilkan dari visit atau herbal-only sale.  
Nomor harus unik. Path file PDF harus aman dari path traversal.  
Relasi: satu invoice → satu visit atau satu sale_group.

### DiscountRule
Aturan diskon yang bisa diterapkan ke layanan atau herbal. Bisa berbasis persen atau nominal tetap.  
Nama rule harus disimpan untuk riwayat invoice.

### Voucher
Kode voucher dengan batas pemakaian. Bisa dibatasi per pasien.

### AuditLog
Log setiap aksi sensitif: entity, action, actor, reason, data_before, data_after, timestamp.

### Backup
Metadata backup yang tersimpan: nama file, ukuran, timestamp, hash validasi.

### License
Data lisensi aktif: mode (trial/full), tanggal ekspirasi, hardware_id terikat, status aktivasi.

---

## 8. Aturan Layanan Terapi Generic

Setiap layanan **harus** bersifat generic. Tidak ada logika yang hardcode untuk bekam.

### Field wajib Service:

| Field | Keterangan |
|---|---|
| `name` | Nama layanan |
| `service_category` | Kategori (Bekam, Pijat, Refleksi, Konsultasi, Ruqyah, Homecare, Paket, Lainnya) |
| `pricing_type` | `per_unit` / `fixed` / `manual` / `free` / `package` |
| `unit_label` | Label satuan yang tampil di UI dan invoice (titik, sesi, menit, paket, dll.) |
| `default_quantity` | Quantity default saat pilih layanan |
| `price_per_unit` | Harga per satuan (untuk `per_unit`) |
| `fixed_price` | Harga tetap (untuk `fixed` / `package`) |
| `allow_manual_price` | Boolean, boleh override harga di UI |
| `notes_template` | Template catatan default |
| `is_active` | Boolean, layanan aktif/nonaktif |
| `inventory_usage` | Daftar item consumable yang dipakai per sesi/unit layanan ini |

### Contoh konfigurasi:

| Layanan | pricing_type | unit_label |
|---|---|---|
| Bekam Basah | per_unit | titik |
| Bekam Kering | per_unit | titik |
| Pijat Terapi | fixed | sesi |
| Refleksi | fixed / manual | sesi / menit |
| Akupresur | per_unit / fixed | titik / sesi |
| Konsultasi Herbal | manual / free | sesi |
| Ruqyah | fixed / manual | sesi |
| Homecare | manual | kunjungan |
| Paket Terapi | package | paket |

### Aturan wajib:
- UI **tidak boleh** hardcode label "titik bekam". Harus baca `unit_label` dari service.
- Invoice harus menggunakan heading **"Detail Layanan"**, bukan "Detail Bekam".
- Laporan harus bisa menampilkan top layanan dan top kategori layanan.
- `service_inventory_usage` harus linked ke `service_id`, bukan hardcode per jenis terapi.

---

## 9. Aturan Pencatatan Kunjungan

### Flow:
```
Pilih pasien
  → Pilih layanan (aktif saja)
  → Pilih terapis (aktif saja)
  → Input quantity / harga
  → Tambah herbal (opsional, masuk cart)
  → Terapkan diskon / voucher / gratis
  → Validasi stok alat consumable
  → Konfirmasi final
  → Simpan visit
  → Kurangi stok alat
  → Buat invoice
  → Catat audit log
```

### Aturan wajib:
- Layanan nonaktif tidak boleh bisa dipilih.
- Terapis nonaktif tidak boleh bisa dipilih.
- `final_price` tidak boleh negatif.
- Kunjungan gratis wajib mengisi alasan.
- `original_price`, `discount_amount`, `final_price` harus tersimpan terpisah.
- `manual_price` tidak boleh negatif.
- Visit tidak boleh disimpan sebelum konfirmasi final dari user.
- Stok alat consumable hanya berkurang setelah visit tersimpan final.
- Jika stok alat tidak mencukupi, visit ditolak sebelum disimpan.
- Create visit + pengurangan stok harus bersifat atomic atau punya rollback yang aman.
- Double submit dari UI (klik ganda tombol simpan) harus dicegah.

---

## 10. Aturan Penjualan Herbal / Produk

### Mode 1 – Herbal ikut kunjungan:
- Item herbal masuk draft/cart dulu sebelum konfirmasi.
- Stok **tidak berkurang** saat item ditambahkan ke cart.
- Stok berkurang hanya setelah konfirmasi final.
- `herbal_transaction.visit_id` harus diisi jika ikut kunjungan.
- Invoice gabungan menampilkan layanan dan herbal dalam satu dokumen.

### Mode 2 – Herbal-only sale:
- Bisa dilakukan tanpa `patient_id`.
- Bisa satu item atau beberapa item sekaligus.
- Jika lebih dari satu item, semua item harus punya `sale_group_id` yang sama.
- Jika stok salah satu item tidak mencukupi, **seluruh transaksi dibatalkan**.
- Invoice herbal-only harus memuat semua item dalam `sale_group_id` yang sama.
- Data lama tanpa `sale_group_id` harus tetap aman dan tidak error.

---

## 11. Aturan Stok Herbal

### Jenis transaction_type:

| Tipe | Efek Stok |
|---|---|
| `stock_in` | Stok bertambah |
| `sale` | Stok berkurang |
| `return` | Stok bertambah |
| `adjustment` | Koreksi manual (bisa + atau -) |

### Aturan wajib:
- Stok tidak boleh minus setelah transaksi apapun.
- `sale` harus validasi stok cukup sebelum disimpan.
- `return` tidak menghapus transaksi `sale` lama; dibuat transaksi lawan baru.
- `return` mengurangi net herbal revenue.
- `adjustment` wajib punya alasan dan Admin PIN.
- Semua perubahan stok harus menyimpan log di `herbal_transactions`.
- Hapus data herbal tidak boleh menghapus histori transaksi terkait.

---

## 12. Aturan Inventori Alat Klinik

### Jenis item:

| Tipe | Contoh |
|---|---|
| `consumable` | Tisu, sarung tangan, lancet, kapas, alkohol swab, masker, minyak pijat |
| `non_consumable` | Cup bekam, pompa, bed terapi, sterilizer |

### Aturan wajib:
- `consumable` boleh auto-deduct berdasarkan `service_inventory_usage`.
- `non_consumable` **tidak boleh** auto-deduct setiap kunjungan, hanya melalui damage/lost/koreksi manual.
- Stok tidak boleh minus.
- `adjustment` wajib alasan dan Admin PIN.
- Semua pergerakan stok masuk `inventory_transactions`.
- `service_inventory_usage` harus linked ke `service_id`, bukan hardcode jenis terapi.
- Void kunjungan harus punya kebijakan stok alat yang jelas: dikembalikan, tidak dikembalikan, atau user memilih.

---

## 13. Aturan Invoice

### Invoice mendukung tiga jenis:
1. Layanan terapi saja
2. Herbal-only
3. Gabungan layanan + herbal

### Istilah yang wajib digunakan di template PDF:

| Istilah | Bukan |
|---|---|
| Detail Layanan | Detail Bekam |
| Produk / Herbal | (tidak ada larangan khusus) |
| Jumlah | — |
| Satuan | — |
| Terapis | — |
| Harga | — |
| Subtotal | — |
| Diskon | — |
| Total | — |
| Status Pembayaran | — |

### Aturan wajib:
- Nomor invoice harus unik.
- Path file PDF harus aman dari path traversal (tidak boleh ada `../` atau karakter tidak aman).
- Nama file PDF harus aman untuk Windows (tidak ada `\/:*?"<>|`).
- Invoice void tidak dihitung dalam pendapatan aktif.
- Kegagalan pembuatan PDF harus menghasilkan status error yang jelas, bukan silent fail.
- Invoice tidak boleh menyebabkan transaksi dobel.
- Invoice tidak boleh menjadi sumber double count jika visit/herbal sudah dihitung di laporan.

---

## 14. Aturan Diskon, Voucher, dan Gratis

- Diskon dihitung dari `original_price`.
- `discount_amount` tidak boleh lebih besar dari `original_price`.
- `final_price` tidak boleh negatif.
- Voucher bisa punya batas penggunaan (max usage count).
- Voucher yang dikaitkan ke pasien tertentu tidak boleh dipakai pasien lain.
- Kunjungan gratis: `final_price = 0`, `original_price` tetap disimpan.
- Kunjungan gratis wajib memiliki alasan.
- Diskon dan voucher tidak boleh diaplikasikan dobel ke transaksi yang sama.
- Nama rule diskon harus tersimpan di histori dan muncul di invoice.
- Laporan pendapatan harus menggunakan `final_price`, bukan `original_price`.

---

## 15. Aturan Void, Retur, dan Koreksi

- Tidak boleh hard delete transaksi penting (visit, herbal_transaction, invoice).
- Void menggunakan status-based approach: field `status = 'void'`.
- Void wajib mengisi alasan.
- Void memerlukan Admin PIN.
- Data void tidak masuk pendapatan aktif.
- Retur herbal membuat `herbal_transaction` baru dengan `transaction_type = 'return'`.
- Retur menambah stok herbal.
- Retur mengurangi net herbal revenue.
- Koreksi stok inventori wajib alasan dan Admin PIN.
- Semua aksi void/retur/koreksi harus masuk audit log.
- Audit log wajib mencatat: `entity`, `action`, `actor`, `reason`, `timestamp`, `data_before`, `data_after`.

---

## 16. Aturan Laporan, Analytics, dan Owner Report

### Formula dasar:

```
visit_revenue   = SUM(final_price) dari visit dengan status aktif/non-void dan payment_status = paid
herbal_revenue  = SUM(sale) - SUM(return) dari herbal_transactions aktif
total_revenue   = visit_revenue + herbal_revenue
```

### Aturan wajib:
- Tidak boleh double count: jangan jumlahkan invoice total + visit/herbal jika sudah dihitung.
- Herbal yang ikut kunjungan tidak boleh dihitung dua kali (sebagai bagian visit DAN sebagai herbal standalone).
- Data void harus dikecualikan dari pendapatan aktif.
- Retur mengurangi `net_herbal_revenue`.
- `pending payment` jangan dianggap sebagai `paid income` di laporan jika laporan hanya menghitung `paid`.
- Kunjungan gratis: `final_price = 0`, tapi `original_price` tetap bisa dipakai untuk analitik promosi.
- Owner Report harus memisahkan `visit_revenue` dan `herbal_revenue`.
- Dashboard harus aman terhadap payload null/kosong (tidak boleh crash jika data kosong).

---

## 17. Aturan Payment Status

### Standar payment_status:

| Status | Keterangan |
|---|---|
| `unpaid` | Belum dibayar |
| `pending` | Menunggu konfirmasi payment gateway |
| `paid` | Lunas |
| `failed` | Pembayaran gagal |
| `refunded` | Dana dikembalikan |
| `void` | Dibatalkan |

### Standar payment_method:
`cash`, `transfer`, `qris`, `gateway`, `manual`

### Standar payment_provider:
`manual`, `gateway_mock`, `xendit`, `midtrans`, `duitku`

### Aturan wajib:
- `payment_reference` harus unik jika menggunakan gateway.
- `gateway_mock` tidak dianggap production dan tidak boleh digunakan di rilis resmi.
- Webhook/callback harus divalidasi; tidak boleh update transaksi yang salah.
- `payment_url` yang expired harus ditangani dengan fallback yang jelas.
- Laporan harus mendokumentasikan status mana yang dihitung (biasanya hanya `paid`).

---

## 18. Role, Admin PIN, dan Security

### Aksi yang wajib memerlukan Admin PIN:
- Delete data (pasien, terapis, layanan)
- Void visit / invoice
- Restore backup
- Koreksi stok (herbal dan inventori)
- Mengubah pengaturan penting
- Mengubah data lisensi

### Aturan keamanan wajib:
- Endpoint lokal harus menggunakan `X-App-Token` jika sesuai desain keamanan.
- Error tidak boleh membocorkan stack trace, path database, atau path file ke frontend.
- Pengaturan sensitif (license key, database path, secret) tidak boleh bocor ke response frontend.
- Input dari user atau payment reference yang ditampilkan di HTML harus di-escape.
- License key tidak boleh hardcoded di source code.

---

## 19. Backup, Restore, dan Runtime Data

### Aturan backup/restore:
- Backup manual harus bisa dibuat kapan saja dari UI.
- File restore harus divalidasi sebelum diterapkan (cek format dan integritas).
- Setelah restore, user diberi informasi apakah perlu restart/reload.

### File runtime yang tidak boleh masuk ke build, Git, ZIP, atau installer:

```
settings.json
data.db
*.db-shm
*.db-wal
invoices/
backups/
logs/
exports/
__pycache__/
*.pyc
*.pdf (test/temp)
*.zip (lama)
```

File-file ini harus ada di `.gitignore` dan diabaikan oleh sistem build EXE.

---

## 20. TypeScript Migration Requirement

### Prinsip:
- `types.ts` adalah **single source of truth** untuk semua data model di frontend.
- `admin-globals.d.ts` hanya untuk deklarasi `Window` / global browser.
- Hindari duplikasi type antara file.
- Jangan migrasi semua module JS ke TS sekaligus.

### Urutan migrasi yang aman:

| Prioritas | Module |
|---|---|
| 1 | Shared types (`types.ts`) |
| 2 | Helper / utils frontend |
| 3 | Dashboard |
| 4 | Settings |
| 5 | Services (layanan) |
| 6 | Therapists |
| 7 | Inventory / Herbals |
| 8 | Invoices |
| 9 | Visits |
| 10 | Analytics / Owner Report |

---

## 21. Acceptance Criteria

### Layanan Terapi Generic
- **Given** admin menambah layanan "Pijat Terapi" dengan `unit_label = "sesi"` dan `pricing_type = "fixed"`  
  **When** kasir memilih layanan tersebut di form kunjungan  
  **Then** UI menampilkan label "sesi" (bukan "titik"), dan invoice memakai "Detail Layanan"

### Kunjungan
- **Given** terapis berstatus nonaktif  
  **When** kasir mencoba memilih terapis tersebut  
  **Then** terapis tidak muncul di daftar pilihan

- **Given** stok alat consumable habis  
  **When** kasir mencoba konfirmasi kunjungan yang membutuhkan alat tersebut  
  **Then** sistem menolak dan menampilkan pesan stok tidak cukup

- **Given** kasir mengaplikasikan diskon sehingga `final_price < 0`  
  **When** konfirmasi kunjungan  
  **Then** sistem menolak dengan pesan bahwa harga akhir tidak boleh negatif

### Herbal Sale
- **Given** stok Madu = 1  
  **When** kasir menjual Madu sebanyak 2  
  **Then** transaksi ditolak dan stok tetap 1

- **Given** herbal-only sale multi item dengan salah satu stok tidak cukup  
  **When** konfirmasi  
  **Then** seluruh transaksi dibatalkan, stok semua item tetap tidak berubah

### Stok Herbal
- **Given** admin melakukan `adjustment` stok tanpa mengisi alasan  
  **When** submit  
  **Then** sistem menolak dan meminta alasan

- **Given** `return` dilakukan atas penjualan herbal  
  **When** retur berhasil disimpan  
  **Then** stok herbal bertambah dan net herbal revenue berkurang

### Stok Alat
- **Given** item inventori adalah `non_consumable`  
  **When** ada kunjungan baru dengan service terkait  
  **Then** stok non_consumable tidak berkurang otomatis

### Invoice
- **Given** visit berhasil disimpan  
  **When** invoice PDF dibuat  
  **Then** nomor invoice unik dan nama file tidak mengandung karakter tidak aman Windows

- **Given** visit di-void  
  **When** owner report dijalankan  
  **Then** invoice void tersebut tidak masuk hitungan pendapatan aktif

### Diskon / Gratis
- **Given** kasir menandai kunjungan sebagai gratis  
  **When** konfirmasi tanpa mengisi alasan  
  **Then** sistem menolak dengan pesan wajib mengisi alasan

- **Given** voucher dikaitkan ke pasien A  
  **When** kasir mencoba menggunakannya untuk pasien B  
  **Then** sistem menolak voucher tersebut

### Void / Retur
- **Given** kasir mencoba void visit tanpa Admin PIN  
  **When** submit void  
  **Then** sistem meminta Admin PIN

- **Given** void berhasil dilakukan  
  **When** laporan pendapatan dijalankan  
  **Then** data dari visit yang di-void tidak muncul dalam pendapatan aktif

### Laporan
- **Given** ada herbal yang ikut kunjungan  
  **When** owner report dijalankan  
  **Then** herbal tersebut tidak dihitung dua kali (bukan sebagai bagian visit DAN herbal standalone)

### Security
- **Given** terjadi error internal server  
  **When** frontend menerima response  
  **Then** response tidak mengandung stack trace atau path file sistem

### Backup
- **Given** admin memilih file backup yang korup  
  **When** restore dijalankan  
  **Then** sistem menolak dan menampilkan pesan error yang jelas

### TypeScript Migration
- **Given** tipe baru ditambahkan di `types.ts`  
  **When** module TS lain menggunakan data tersebut  
  **Then** tidak ada duplikasi type di file lain

---

## 22. Risk Matrix

| Area | Risiko | Dampak | Prioritas | Mitigasi | Test |
|---|---|---|---|---|---|
| Stok Herbal | Stok minus setelah sale | Tinggi | P1 | Validasi stok sebelum simpan, rollback jika gagal | Unit test stok <0 |
| Laporan | Double count pendapatan | Tinggi | P1 | Pisahkan sumber laporan, jangan jumlah invoice + visit | Integration test revenue formula |
| Invoice | Total invoice salah | Tinggi | P1 | Hitung dari final_price visit + herbal, bukan dari field invoice | E2E test invoice amount |
| Laporan | Void masih masuk laporan | Tinggi | P1 | Filter `status != void` dan `payment_status in (paid)` | Test laporan dengan data void |
| Stok Herbal | Retur tidak menambah stok | Tinggi | P1 | Unit test: retur → stok+1 | Test return flow |
| Kunjungan | Free visit tanpa alasan | Sedang | P2 | Validasi required field reason jika final_price=0 | Test form validation |
| Kunjungan | final_price negatif | Tinggi | P1 | Clamp final_price ≥ 0 di backend | Unit test diskon > original_price |
| Inventori | Non-consumable auto deduct | Sedang | P2 | Cek item_type sebelum auto-deduct | Test kunjungan dengan non-consumable item |
| Invoice | Herbal multi-item invoice tidak lengkap | Sedang | P2 | Query invoice berdasarkan sale_group_id bukan satu item | Test invoice herbal multi-item |
| Build | File runtime ikut build/installer | Sedang | P2 | Cek .gitignore dan PyInstaller spec | Review file build output |
| Frontend | Type TS tidak cocok backend | Sedang | P2 | types.ts sebagai single source, validasi saat integrasi | Type check (tsc --noEmit) |
| Security | Stack trace bocor ke frontend | Tinggi | P1 | Global error handler, return pesan generik | Test error endpoint |

---

## 23. Roadmap Bertahap

### Fase 1 — Clean up & Safety Patch
**Tujuan:** Stabilkan codebase yang ada tanpa risiko fitur baru  
**Pekerjaan:** Hapus file runtime dari Git, rapikan .gitignore, patch validasi kritis (stok minus, final_price negatif, void filter laporan)  
**Output:** Codebase bersih, validasi dasar berjalan  
**Syarat Selesai:** Tidak ada file runtime di Git, semua validasi P1 lulus unit test

### Fase 2 — Transaction Integrity
**Tujuan:** Pastikan semua alur transaksi atomic dan aman  
**Pekerjaan:** Atomic create visit + stok deduct, atomic herbal-only multi item, rollback aman, cegah double submit  
**Output:** Tidak ada stok bisa minus karena race condition atau error tengah jalan  
**Syarat Selesai:** Integration test transaction gagal → rollback, stok tetap benar

### Fase 3 — Service Generic
**Tujuan:** Hapus semua logika hardcode bekam, buat service benar-benar generic  
**Pekerjaan:** Refactor UI label, invoice template, service_inventory_usage, form kunjungan  
**Output:** Layanan non-bekam dapat didaftarkan, dicatat, dan di-invoice tanpa error  
**Syarat Selesai:** Demo kunjungan Pijat Terapi dan Konsultasi Herbal berhasil end-to-end

### Fase 4 — Reporting Correctness
**Tujuan:** Pastikan semua laporan menghasilkan angka yang benar  
**Pekerjaan:** Perbaiki formula revenue, pisah visit_revenue dan herbal_revenue, filter void, filter pending  
**Output:** Owner report akurat, tidak ada double count  
**Syarat Selesai:** Test laporan dengan skenario lengkap (normal + void + retur + gratis) menghasilkan angka yang benar

### Fase 5 — TypeScript Stabilization
**Tujuan:** Migrasi JS ke TS bertahap sesuai urutan prioritas  
**Pekerjaan:** Mulai dari types.ts → utils → dashboard → settings → services → therapists → inventory/herbals → invoices → visits → analytics  
**Output:** Semua module yang sudah dimigrasi lulus `tsc --noEmit`  
**Syarat Selesai:** Tidak ada type error di module yang sudah dimigrasi

### Fase 6 — QA Internal
**Tujuan:** Uji semua alur utama secara end-to-end  
**Pekerjaan:** Smoke test semua acceptance criteria, uji skenario edge case, uji backup/restore  
**Output:** Test report internal, daftar bug yang ditemukan dan sudah diperbaiki  
**Syarat Selesai:** Semua acceptance criteria P1 dan P2 lulus

### Fase 7 — Build EXE Bersih
**Tujuan:** Hasilkan installer EXE yang bersih tanpa file runtime  
**Pekerjaan:** Verifikasi PyInstaller spec, cek tidak ada data.db/settings.json/invoices/backups di dalam EXE  
**Output:** EXE installer yang siap dicoba  
**Syarat Selesai:** Instalasi di mesin baru berhasil, tidak ada file runtime di dalam EXE

### Fase 8 — Trial Terbatas
**Tujuan:** Uji di lingkungan nyata dengan pengguna terbatas  
**Pekerjaan:** Deploy ke 1–3 klinik pilot, kumpulkan feedback, perbaiki bug produksi  
**Output:** Daftar bug produksi yang ditemukan dan diperbaiki  
**Syarat Selesai:** Tidak ada bug kritis setelah 2 minggu pilot

### Fase 9 — Siap Dijual
**Tujuan:** Rilis ke pasar  
**Pekerjaan:** Finalisasi lisensi, dokumentasi user, packaging installer, harga dan model bisnis  
**Output:** Produk siap dijual  
**Syarat Selesai:** Semua fase sebelumnya selesai, lisensi berjalan per aturan, tidak ada klaim fitur yang belum ada

---

## 24. Hal yang Tidak Boleh Dilakukan Dulu

- **Jangan rewrite total** — refactor inkremental, bukan ganti semua sekaligus
- **Jangan ganti framework** — Python/FastAPI/PySide6 sudah dipilih, stick dengan itu
- **Jangan pindah ke PostgreSQL dulu** — SQLite sudah mencukupi untuk skala lokal single-user
- **Jangan migrasi semua JS ke TS sekaligus** — ikuti urutan prioritas di Fase 5
- **Jangan tambah payment provider baru** sebelum alur payment_status rapi dan E2E tested
- **Jangan klaim RME / SATUSEHAT / BPJS** di marketing maupun di UI
- **Jangan jual massal** sebelum smoke test Fase 6 lulus
- **Jangan hapus field lama** seperti `point_count` tanpa migrasi skema yang kompatibel dan aman
- **Jangan hardcode data klinik** (nama klinik, nomor HP, dsb.) di source code; harus dari settings
- **Jangan release production** dengan `gateway_mock` aktif

---

*Dokumen ini adalah referensi internal untuk developer, QA, dan AI coding assistant. Bukan dokumen marketing.*
