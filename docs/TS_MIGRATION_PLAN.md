# TypeScript Migration Plan

Dokumen ini mencatat status migrasi frontend admin dari JavaScript ke TypeScript. Tujuannya migrasi bertahap tanpa mengubah backend Python, endpoint API, schema database, atau logic bisnis utama.

## Status Saat Ini

File TypeScript yang sudah menjadi source utama dan dibuild ke `api/static/modules/`:

| Source TS | Output JS | Status |
| --- | --- | --- |
| `api/static/ts/utils.ts` | `api/static/modules/utils.js` | Selesai |
| `api/static/ts/api.ts` | `api/static/modules/api.js` | Selesai |
| `api/static/ts/formatters.ts` | `api/static/modules/formatters.js` | Selesai |
| `api/static/ts/dom.ts` | `api/static/modules/dom.js` | Selesai |
| `api/static/ts/validators.ts` | `api/static/modules/validators.js` | Selesai |
| `api/static/ts/help.ts` | `api/static/modules/help.js` | Selesai |
| `api/static/ts/therapists.ts` | `api/static/modules/therapists.js` | Selesai |
| `api/static/ts/services.ts` | `api/static/modules/services.js` | Selesai |
| `api/static/ts/audit.ts` | `api/static/modules/audit.js` | Selesai |

Tahap persiapan tipe domain:

| Tahap | Status |
| --- | --- |
| Tipe pendukung dashboard, analytics, owner report, inventory, herbal, discount rule, settings, dan response generik | Selesai tahap 11 |

Global helper yang tersedia:

| Namespace | Isi |
| --- | --- |
| `window.LancarApi` | `request`, `getJson`, `postForm`, `isSuccess`, `getErrorMessage` |
| `window.LancarFormatters` | `currency`, `date`, `dateTime`, `status` |
| `window.LancarDom` | `byId`, `query`, `queryAll`, `setText`, `setHtml`, `show`, `hide`, `getInputValue` |
| `window.LancarValidators` | `isNonEmpty`, `isValidIndonesianPhone`, `normalizePhone`, `isPositiveNumber`, `parseNumberInput`, `requiredText` |

## File Belum Dimigrasikan

Ukuran file berdasarkan kondisi saat dokumen ini dibuat:

| File | Ukuran relatif | Risiko | Alasan risiko |
| --- | ---: | --- | --- |
| `settings.js` | Sangat besar | Sangat tinggi | Mencakup pengaturan klinik, backup/restore, lisensi, PIN admin, demo data, import/export, voucher/diskon. Banyak endpoint sensitif dan form POST. |
| `patients.js` | Sangat besar | Sangat tinggi | Server-side DataTable, form kunjungan, pencarian pasien, harga layanan, produk/herbal di kunjungan, pembayaran, konfirmasi stok, dan detail riwayat. |
| `herbals.js` | Besar | Sangat tinggi | CRUD produk, koreksi stok, penjualan, retur, validasi stok, dan pembayaran produk. Menyentuh stok dan transaksi. |
| `crm.js` | Besar | Tinggi | Follow-up pasien, WhatsApp, voucher khusus, meta pasien, status outcome, dan beberapa modal dinamis. |
| `modal.js` | Besar | Sangat tinggi | Modal edit pasien/kunjungan/terapis, update patient full, delete pasien, delete kunjungan. Banyak handler global lama. |
| `inventory.js` | Sedang-besar | Tinggi | CRUD inventori, koreksi stok, satuan kemasan, dan perubahan stok manual. |
| `invoices.js` | Sedang-besar | Sangat tinggi | Generate/print invoice, void invoice, gateway mock, status pembayaran, dan tampilan transaksi. |
| `analytics.js` | Sedang | Tinggi | Laporan pendapatan, profit, void invoice, expense preview. Risiko salah agregasi/label bisnis. |
| `dashboard.js` | Sedang | Sedang-tinggi | Ringkasan statistik, discount summary, stok rendah, transaksi terakhir. Harus jaga tampilan awal app. |
| `owner_report.js` | Sedang | Tinggi | Laporan owner, export Excel, top layanan/herbal/pasien, follow-up CRM. |
| `license.js` | Kecil | Tinggi | Kecil secara teknis, tetapi domain lisensi sensitif. Jangan migrasi sebelum ada test manual lisensi. |

## Urutan Migrasi Yang Disarankan

1. **Helper dan tipe pendukung tambahan**
   - Tipe domain pendukung tahap 11 sudah ditambahkan di `types/types.ts`.
   - Tambah helper kecil jika benar-benar diperlukan, misalnya `table.ts` untuk helper DataTable non-bisnis atau `forms.ts` untuk baca field form.
   - Jangan gunakan helper baru di file besar sampai smoke test helper selesai.

2. **File read-only atau hampir read-only**
   - `dashboard.js` dapat dipertimbangkan lebih dulu dibanding transaksi, tetapi pecah dulu tipe payload dashboard.
   - `owner_report.js` setelah tipe owner report dan export flow siap. Jangan ubah endpoint export.
   - `analytics.js` hanya setelah tipe response analytics jelas. Jangan ubah rumus tampilan.

3. **File CRUD sedang dengan efek terbatas**
   - `inventory.js` hanya setelah semua field stok dan satuan punya tipe jelas. Harus fokus pada typing, bukan perubahan logic koreksi stok.
   - `herbals.js` sebaiknya dipecah: render daftar, helper stok, modal penjualan, modal retur. Jangan migrasi seluruh file sekaligus.

4. **File sensitif yang harus ditunda**
   - `invoices.js`: tunda sampai tipe invoice/payment/gateway matang dan test manual invoice siap.
   - `crm.js`: tunda sampai tipe CRM contact, follow-up history, voucher khusus, dan meta pasien lengkap.
   - `patients.js`: tunda paling akhir atau pecah per area. Ini file paling rawan karena menyentuh pasien, kunjungan, harga, stok herbal, pembayaran, dan DataTable.
   - `settings.js`: tunda sampai ada strategi split per panel.
   - `modal.js`: tunda sampai `patients.js` sudah mulai terurai, karena modal ini bergantung pada struktur pasien/kunjungan lama.
   - `license.js`: meski kecil, domain lisensi harus ditunda sampai test aktivasi/status lisensi jelas.

## Bagian Yang Harus Dipecah Dulu

### `patients.js`
- Tipe payload pasien dan detail pasien.
- Helper DataTable mapping.
- Helper pencarian pasien kunjungan.
- Helper item herbal pada kunjungan.
- Helper kalkulasi tampilan harga layanan.
- Handler submit kunjungan tetap terakhir.

### `settings.js`
- Panel profile klinik dan logo.
- Panel backup/restore.
- Panel lisensi dan PIN admin.
- Panel voucher/diskon.
- Panel import/export.
- Setiap panel sebaiknya menjadi TS terpisah sebelum file utama dipindah.

### `herbals.js`
- Helper satuan dan label kemasan.
- Render tabel herbal.
- Koreksi stok.
- Modal penjualan.
- Modal retur.
- CRUD edit/delete.

### `inventory.js`
- Helper satuan dan label kemasan.
- Render tabel inventory.
- Pilih row inventory.
- Preview koreksi stok.
- Submit edit/delete.

### `invoices.js`
- Helper path invoice dan action PDF.
- Helper gateway mock.
- Helper void invoice.
- Render tabel invoice.
- Search/pagination state.

### `crm.js`
- Constants dan label helpers.
- Render filter/list.
- Modal follow-up.
- WhatsApp message helpers.
- Save meta/outcome/voucher khusus.

## Aturan Aman Untuk Tahap Berikutnya

- Jangan rename endpoint API.
- Jangan rename field payload dari backend.
- Jangan ubah format `FormData` yang sudah dipakai backend.
- Jangan ubah format `inventory_usage`, `herbal_items`, invoice id prefix, atau payment status.
- Jangan ubah kalkulasi harga, diskon, stok, pembayaran, atau laporan saat hanya melakukan migrasi TS.
- Hindari `any`; gunakan `unknown`, type guard ringan, atau tipe domain kecil.
- Kalau harus memakai `any` sementara, beri komentar `TODO(ts-migration)`.
- Setelah satu file dimigrasikan, expose handler lama ke `window` secara eksplisit jika masih dipakai inline `onclick`.
- Keluarkan output JS hasil build dari direct JS typecheck di `tsconfig.json` agar tidak dobel dengan source TS.
- Jalankan minimal:
  - `npm run build:ts`
  - `npx tsc --noEmit`
  - `node --check` untuk semua output TS yang sudah aktif
  - smoke test mock `window` untuk helper atau modul yang expose global

## Catatan Build

HTML tetap memuat file JS dari `api/static/modules/`. Source TS berada di `api/static/ts/` dan dibuild oleh:

```bash
npm run build:ts
```

Typecheck project:

```bash
npx tsc --noEmit
```
