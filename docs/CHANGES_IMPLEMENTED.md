# Catatan Perubahan yang Sudah Berjalan

> Tanggal catatan: 2026-05-18  
> Sumber analisis: `docs/PRD.md`, kode aktual, flowchart logic, dan perubahan terakhir di modul invoice.

---

## 1. Invoice PDF Refresh Setelah Payment Status Berubah

### Status

**Sudah berjalan / sudah diimplementasikan.**

### Masalah PRD / logic sebelumnya

Sebelumnya invoice PDF diperlakukan seperti hasil final permanen. Padahal status pembayaran transaksi bisa berubah setelah invoice dibuat, misalnya:

- `unpaid` → `paid`
- `partial` → `paid`
- `pending` → `paid`
- `pending` → `failed` / `expired`

Akibatnya database sudah benar, tetapi file PDF invoice lama masih berisi status pembayaran lama.

### Perubahan yang dilakukan

File terkait:

- `api/routes/invoices.py`
- `api/static/modules/invoices.js`
- `docs/PRD.md`
- `docs/flowcharts/05-invoice-refresh-pdf.md`
- `docs/flowcharts/04-payment-status.md`
- `docs/flowcharts/06-payment-gateway.md`

Perubahan:

1. Generate invoice sekarang membedakan:
   - generate pertama: `invoice_generated`
   - refresh PDF invoice visit: `invoice_pdf_refreshed`
   - generate herbal pertama: `herbal_invoice_generated`
   - refresh PDF invoice herbal: `herbal_invoice_pdf_refreshed`
2. Tombol **Update PDF** muncul di invoice yang sudah punya PDF dan belum void.
3. Setelah status pembayaran manual diubah, UI menanyakan apakah user ingin **Update PDF Sekarang**.
4. Refresh PDF memakai nomor invoice yang sama, bukan membuat transaksi baru.
5. Audit log menyimpan status/metode pembayaran, path lama, dan path baru.
6. Invoice void tetap tidak boleh di-refresh atau ditandai lunas.

### Prinsip final

```text
Transaksi / invoice record = permanen
Payment status = bisa berubah
PDF invoice = snapshot, boleh di-refresh
Nomor invoice = tetap stabil
```

---

## 2. Flowchart Per Logic

### Status

**Sudah dibuat.**

### Lokasi

`docs/flowcharts/`

File yang tersedia:

1. `README.md`
2. `01-project-overview.md`
3. `02-startup-desktop-server.md`
4. `03-patients-visits.md`
5. `04-payment-status.md`
6. `05-invoice-refresh-pdf.md`
7. `06-payment-gateway.md`
8. `07-inventory.md`
9. `08-herbals.md`
10. `09-crm-followup-whatsapp.md`
11. `10-voucher-discount.md`
12. `11-reports-analytics.md`
13. `12-settings-backup-license.md`

### Catatan

Flowchart invoice sudah mencerminkan logic terbaru: PDF invoice adalah snapshot dan bisa di-refresh saat status pembayaran berubah.

---

## 3. PRD Diselaraskan dengan Payment Status Aktual

### Status

**Sudah diperbarui di `docs/PRD.md`.**

### Perubahan

PRD sebelumnya mencantumkan `refunded`, tetapi belum menyebut `partial`, sedangkan kode aktual memakai `partial` untuk DP / pembayaran sebagian.

PRD sekarang mencantumkan:

- `unpaid`
- `pending`
- `paid`
- `partial`
- `failed`
- `refunded`
- `void`

PRD juga diselaraskan dengan metode pembayaran aktual:

- `cash`
- `qris`
- `transfer`
- `debit`
- `ewallet`
- `virtual_account`
- `credit_card`
- `other`
- `free`

### Catatan

`refunded` masih tertulis sebagai requirement, tetapi implementasi refund penuh perlu dicek/ditentukan di fase retur/refund berikutnya.

---

## 4. CRM WhatsApp Puppeteer Automation — Dokumentasi Rencana

### Status

**Dokumentasi sudah dibuat, implementasi real send belum dilakukan.**

### File terkait

- `docs/WHATSAPP_PUPPETEER_AUTOMATION.md`
- `docs/PRD.md`
- `docs/REQUIREMENTS_CHECKLIST.md`
- `docs/ROADMAP_REFACTOR.md`
- `docs/TEST_PLAN.md`
- `docs/SAFETY_PATCH_PLAN.md`
- `docs/COMMIT_PLAN.md`

### Prinsip yang sudah dicatat

- Mode semi-manual tetap default.
- Puppeteer optional dan disabled by default.
- Tidak boleh bulk blasting.
- Tidak boleh background sender.
- Tidak boleh bypass QR WhatsApp Web.
- Satu klik admin = satu pasien = satu pesan.
- Guardrail wajib sebelum real send.

---

## 5. Gap PRD yang Masih Perlu Dikerjakan

Berikut gap yang masih tercatat berdasarkan `docs/GAP_ANALYSIS.md` dan pembacaan PRD:

### P0 / P1 penting

1. `Visit` belum punya field terpisah `original_price`, `discount_amount`, `final_price` di model.
2. `Service` belum punya field lengkap PRD seperti `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`.
3. `Inventory` belum punya `item_type` (`consumable` / `non_consumable`) di model aktif.
4. Revenue report masih perlu diselaraskan penuh dengan rule `paid` dan `partial amount_paid`.
5. Refund/retur payment status perlu aturan lebih jelas jika `refunded` tetap dipertahankan di PRD.
6. TypeScript `types.ts` sebagai single source of truth belum selesai penuh.

### Catatan progres sebagian

- Validasi harga negatif sudah terlihat ada di `database.py` pada flow add visit.
- Logic payment `partial` sudah tersedia di `helpers/payment_rules.py`.
- Invoice path/opening sudah memakai resolver aman di route invoice.
- Flowchart per logic sudah dibuat untuk membantu audit lanjutan.

---

## 6. Rekomendasi Urutan Berikutnya

1. Selesaikan model pricing visit: `original_price`, `discount_amount`, `final_price`.
2. Update report agar revenue memakai field final yang benar dan amount paid untuk partial.
3. Tambahkan `item_type` inventory agar non-consumable tidak auto-deduct.
4. Lengkapi service generic: `pricing_type`, `service_category`, `fixed_price`, `allow_manual_price`.
5. Tambahkan test untuk invoice refresh PDF setelah payment status berubah.
6. Audit refund/retur: tentukan apakah `refunded` dipakai sebagai status payment atau cukup retur herbal/void.
