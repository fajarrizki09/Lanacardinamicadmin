# Flowchart Logic LancarDinamicAdmin

Folder ini berisi flowchart per logic/domain utama aplikasi sebagai acuan coding, testing, QA, dan audit fitur.

## Daftar Flowchart

1. [Overview Project](./01-project-overview.md)
2. [Startup Desktop & Server](./02-startup-desktop-server.md)
3. [Pasien & Kunjungan](./03-patients-visits.md)
4. [Payment Status](./04-payment-status.md)
5. [Invoice & Refresh PDF](./05-invoice-refresh-pdf.md)
6. [Payment Gateway](./06-payment-gateway.md)
	- Termasuk flow Midtrans QRIS, payment link, validasi nominal, konfirmasi status, dan opsi kirim link/QR via WhatsApp Follow-up.
7. [Inventory Alat](./07-inventory.md)
8. [Produk / Herbal](./08-herbals.md)
9. [CRM Follow-up WhatsApp](./09-crm-followup-whatsapp.md)
10. [Voucher / Discount Rule](./10-voucher-discount.md)
11. [Reports / Analytics / Owner Report](./11-reports-analytics.md)
12. [Settings / Backup / License](./12-settings-backup-license.md)
13. [Audit Log Global](./13-audit-log-global.md)
14. [Error Handling Global](./14-error-handling-global.md)
15. [Database Migration & First Run](./15-database-migration-first-run.md)
16. [Admin PIN Session](./16-admin-pin-session.md)
17. [WhatsApp Baileys Gateway](./17-whatsapp-baileys-gateway.md)

## Catatan Penting

- Flowchart ini menggambarkan jalur aktif aplikasi, bukan `legacy_ui/`.
- Aplikasi aktif adalah hybrid desktop lokal: PySide6 WebEngine shell + FastAPI local server + UI web modular.
- Desktop shell hanya container UI; logic utama berada di FastAPI local server dan helper backend.
- Semua revenue harus mengikuti rule helper yang sama.
- Invoice PDF adalah snapshot dan bisa stale ketika data transaksi/payment berubah setelah PDF dibuat.
- Void invoice tidak masuk revenue.
- Operasi sensitif wajib license/admin PIN sesuai rule.
- Semua perubahan penting harus masuk audit log.
- Output runtime penting: `invoices/`, `backups/`, `exports/`, `settings.json`, dan `logs/`.
