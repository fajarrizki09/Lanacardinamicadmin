# Rencana Migrasi CSS Biasa ke Tailwind CSS

Tanggal: 2026-05-19

## Tujuan

Migrasi bertahap dari `api/static/style.css` ke Tailwind CSS tanpa merusak UI aplikasi klinik yang sudah berjalan. Pendekatan utama adalah **incremental migration**, bukan rewrite total.

## Kondisi Saat Ini

- CSS utama ada di `api/static/style.css`.
- Template utama: `api/templates/index.html`.
- UI dirender dinamis lewat file JS di `api/static/modules/*.js`.
- Banyak markup HTML dibuat sebagai string template di JavaScript.
- Tailwind sudah terpasang dan berjalan berdampingan dengan `style.css`.
- `package.json` sudah memiliki script build CSS dan build asset gabungan.

## Prinsip Migrasi

1. Jangan hapus `style.css` langsung.
2. Tailwind dipakai berdampingan dulu dengan CSS lama.
3. Migrasi mulai dari komponen kecil dan stabil.
4. Hindari mengubah semua class sekaligus karena HTML tersebar di banyak JS module.
5. Tetap jaga build desktop/PyInstaller agar asset CSS final tetap tersedia offline.

## Target Struktur Baru

```text
api/static/
  style.css                 # CSS legacy sementara
  tailwind.css              # output hasil build Tailwind
  src/
    input.css               # source Tailwind

tailwind.config.js
postcss.config.js
package.json
```

## Dependency yang Dibutuhkan

Tambahkan dev dependency:

- `tailwindcss`
- `postcss`
- `autoprefixer`

Script yang disarankan di `package.json`:

```json
{
  "scripts": {
    "build:css": "tailwindcss -i ./api/static/src/input.css -o ./api/static/tailwind.css --minify",
    "watch:css": "tailwindcss -i ./api/static/src/input.css -o ./api/static/tailwind.css --watch",
    "build:assets": "npm run build:css && npm run build:ts"
  }
}
```

Catatan: sesuaikan dengan script existing agar tidak memutus `build:ts`.

## Konfigurasi Tailwind Content

`tailwind.config.js` harus scan file berikut karena class Tailwind akan berada di template dan string JS:

```js
module.exports = {
  content: [
    './api/templates/**/*.html',
    './api/static/**/*.js',
    './api/static/modules/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0f766e',
          light: '#14b8a6',
          dark: '#115e59'
        }
      }
    }
  },
  safelist: []
};
```

## Source Tailwind Awal

Buat `api/static/src/input.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
}
```

## Integrasi Template

Di `api/templates/index.html`, tambahkan CSS Tailwind sebelum atau sesudah `style.css` sesuai strategi:

### Fase awal

Load Tailwind **sebelum** `style.css` agar CSS legacy tetap menang jika ada konflik:

```html
<link rel="stylesheet" href="/static/tailwind.css?v={{ cache_buster }}">
<link rel="stylesheet" href="/static/style.css?v={{ cache_buster }}&activity_layout=20260515_modal_v4">
```

### Fase lanjutan

Jika komponen sudah stabil dengan Tailwind, Tailwind bisa dipindah setelah `style.css` untuk override class utility.

## Tahapan Migrasi

### Fase 0 — Persiapan Build

- Tambahkan dependency Tailwind.
- Tambahkan `tailwind.config.js`.
- Tambahkan `postcss.config.js`.
- Tambahkan `api/static/src/input.css`.
- Generate `api/static/tailwind.css`.
- Pastikan PyInstaller tetap memasukkan `api/static` via `--add-data "api/static;api/static"`.

Status: Selesai awal pada 2026-05-19.

Catatan progres:

- Dependency Tailwind sudah ditambahkan ke `package.json` dan `package-lock.json`:
  - `tailwindcss`
  - `postcss`
  - `autoprefixer`
- File konfigurasi sudah dibuat:
  - `tailwind.config.js`
  - `postcss.config.js`
- Source CSS Tailwind sudah dibuat:
  - `api/static/src/input.css`
- Output CSS sudah berhasil digenerate:
  - `api/static/tailwind.css`
- Script build CSS sudah ditambahkan:
  - `npm run build:css`
  - `npm run watch:css`
  - `npm run build:assets`

### Fase 1 — Token dan Utility Mapping

Mapping CSS variable lama ke Tailwind theme:

| CSS Lama | Tailwind Theme |
| --- | --- |
| `--primary` | `primary.DEFAULT` |
| `--primary-light` | `primary.light` |
| `--primary-dark` | `primary.dark` |
| `--success` | `emerald/green` custom |
| `--danger` | `red` custom |
| `--warning` | `amber` custom |
| `--bg-color` | `slate/neutral` custom |
| `--card-bg` | `white` |
| `--text-main` | `slate-900` custom |
| `--text-muted` | `slate-500/600` custom |

Status: Selesai awal pada 2026-05-19.

Catatan progres:

- Token warna utama sudah dipetakan di `tailwind.config.js`.
- Token CSS runtime juga disiapkan di `api/static/src/input.css` dengan prefix `--tw-app-*`.
- Mapping belum sepenuhnya menggantikan seluruh `:root` di `style.css`; CSS legacy tetap dipertahankan untuk kompatibilitas.

### Fase 2 — Migrasi Komponen Kecil

Prioritas komponen yang aman:

1. Toast (`#toast-container`, `.toast`, `.toast-success`, `.toast-error`).
2. Loader (`.loader-container`, `.spinner`).
3. Button umum (`.btn`, `.btn-primary`, `.btn-secondary`).
4. Card umum (`.card`, `.card-header`).
5. Badge/status kecil.

Alasan: komponen ini kecil, sering dipakai, dan mudah diuji visual.

Status: Sebagian besar komponen kecil selesai dimigrasikan pada 2026-05-20.

Catatan progres:

- Komponen Tailwind awal sudah dibuat di `api/static/src/input.css`:
  - `.tw-card`
  - `.tw-btn`
  - `.tw-btn-primary`
  - `.tw-btn-secondary`
  - `.tw-loader`
  - `.tw-spinner`
- Komponen kecil tambahan sudah dipindahkan ke Tailwind component layer:
  - `#toast-container`
  - `.toast`, `.toast-success`, `.toast-error`, `.toast-warning`, `.toast-info`
  - `.toast-message`, `.toast-close`, `.toast-hide`
  - `.tw-toast`, `.tw-toast-success`, `.tw-toast-error`, `.tw-toast-warning`, `.tw-toast-info`
  - `.status-indicator`, `.dot`
  - `.badge`, `.badge-ok`, `.badge-low`
  - `.badge-success-soft`, `.badge-danger-soft`, `.badge-warning-soft`, `.badge-info-soft`, `.badge-muted-soft`
  - `.status-badge` dan varian `.herbal`, `.retur`, `.visit`, `.void`
- Loader global di `api/templates/index.html` sudah memakai class Tailwind tambahan:
  - `tw-loader`
  - `tw-spinner`
- Toast di `api/static/modules/utils.js` dan source TypeScript `api/static/ts/utils.ts` sudah diberi class Tailwind tambahan:
  - `tw-toast`
  - `tw-toast-{type}`
- First-run wizard di `api/static/app.js` mulai memakai class Tailwind tambahan:
  - `tw-card`
  - `tw-btn`
  - `tw-btn-primary`
  - `tw-btn-secondary`
- Selector legacy untuk toast, badge umum, status badge transaksi, status indicator, dan badge soft CRM sudah dihapus dari `api/static/style.css` karena sudah digantikan oleh Tailwind component layer.
- Class legacy yang masih dipakai sebagai hook tetap dipertahankan di markup agar kompatibilitas JavaScript tetap aman.

### Fase 3 — Layout Utama

Migrasi bertahap:

1. `body` layout.
2. `.sidebar`.
3. `.nav-links`.
4. `.main-content`.
5. `header`.
6. `#app-container` dan `#display-area`.

Catatan: sidebar dan navigasi adalah area sensitif karena mempengaruhi semua tab. Lakukan setelah komponen kecil stabil.

Status: Sebagian besar shell utama selesai dimigrasikan pada 2026-05-19.

Catatan progres:

- `tailwind.css` sudah di-load di `api/templates/index.html` sebelum `style.css`.
- `body`, `.sidebar`, logo sidebar, `.nav-links`, `.main-content`, `header`, `#app-container`, loader, dan `#display-area` sudah diberi class Tailwind utility di `api/templates/index.html`.
- Selector legacy duplikat untuk shell utama sudah dibersihkan dari `api/static/style.css` pada migrasi sebelumnya.
- Area yang masih perlu dicek visual: responsive sidebar/header dan tab dengan konten tabel besar.

### Fase 4 — Modul per Tab

Urutan rekomendasi:

1. `help.js` — paling aman, konten informatif.
2. `settings.js` — banyak form, tapi bisa per bagian.
3. `therapists.js` dan `services.js` — CRUD sederhana.
4. `inventory.js` dan `herbals.js` — tabel dan form.
5. `patients.js` dan visits — kompleks, DataTables, form kunjungan.
6. `invoices.js`, `analytics.js`, `crm.js`, `owner_report.js` — data besar dan layout kompleks.
7. `whatsapp_gateway.js` — hati-hati karena ada status realtime/QR.

Status: Modul `help.js` selesai dimigrasikan pada 2026-05-20; migrasi aman awal `settings.js` mulai dikerjakan pada 2026-05-20.

Catatan progres:

- Modul Bantuan (`api/static/modules/help.js`) sudah menjadi modul tab pertama yang style-nya dipindahkan penuh ke Tailwind component layer tanpa rewrite logic.
- Source TypeScript modul Bantuan berada di `api/static/ts/help.ts`; tidak perlu perubahan logic karena migrasi dilakukan pada class CSS yang sudah ada.
- Modul Pengaturan (`api/static/modules/settings.js`) mulai dimigrasikan secara bertahap. Bagian yang sudah dipindahkan ke Tailwind component layer:
  - layout `.settings-compact-grid`, `.settings-left-stack`, `.settings-right-stack`, `.settings-card-stack`,
  - card shell `.settings-system-card`, `.settings-license-card`, `.settings-security-card`, `.settings-demo-card`, `.settings-export-card`, `.settings-import-card`, `.settings-backup-card`,
  - copy/help text `.settings-security-copy`, `.settings-security-help`, `.settings-logo-help`,
  - form kecil `.admin-pin-change-form`, `.admin-pin-reset-box`, `.admin-pin-reset-heading`,
  - backup list `.backup-list`, `.backup-item`,
  - status row `.settings-muted-row`, `.settings-info-row`, `.settings-error-row`.
- Subbagian Diskon/Voucher juga sudah dipindahkan ke Tailwind component layer:
  - admin card `.discount-admin-card`, `.discount-admin-grid`, `.discount-rule-form`, `.discount-simulator`,
  - helper/flow/type picker `.discount-helper-text`, `.discount-flow-strip`, `.discount-type-picker`, `.discount-input-help`, `.discount-form-actions`,
  - simulasi `.discount-simulation-result`, `.discount-sim-selected`, `.discount-sim-empty`, `.discount-sim-conflict`, `.discount-sim-note`,
  - dashboard discount `.discount-dashboard-panel`, `.discount-dashboard-summary`, `.discount-dashboard-note`, `.discount-dashboard-list`, `.discount-dashboard-history`, `.discount-dashboard-row`.
- Komponen shared activation control sudah dipindahkan ke Tailwind component layer:
  - `.activation-field`, `.activation-switch`, `.activation-track`, `.activation-copy`,
  - `.activation-action`,
  - variasi kunjungan gratis `.visit-free-toggle`.
- Subbagian Services yang stabil sudah dipindahkan ke Tailwind component layer:
  - unit picker `.service-unit-picker`, `.service-unit-custom`,
  - toggle harga manual `.service-manual-price-toggle`,
  - editor pemakaian inventaris `.service-usage-editor`, `.service-usage-head`, `.service-usage-add`, `.service-usage-list`, `.service-usage-empty`, `.service-usage-row`, `.service-usage-summary`.
- Modul Services juga sudah dipindahkan dari inline style utama ke Tailwind component layer:
  - grid/form `.service-form-grid`, `.service-form-card`, `.service-modal-actions`,
  - direktori/filter `.service-directory-card`, `.service-directory-header`, `.service-counts`, `.service-filter-row`, `.service-filter-btn`,
  - list item `.service-list`, `.service-empty-state`, `.service-row`, `.service-avatar`, `.service-info`, `.service-name`, `.service-price`, `.service-meta`, `.service-note`, `.service-actions`, `.service-icon-btn`.
- Subbagian Inventory/Herbal helper unit dan form tambah Inventory sudah dipindahkan ke Tailwind component layer:
  - helper shared `.unit-help-note`, `.unit-field-hint`,
  - layout form `.inventory-add-form`, `.inventory-item-name-field`, `.inventory-item-type-field`, `.inventory-base-unit-field`, `.inventory-package-unit-field`, `.inventory-package-size-field`, `.inventory-initial-stock-field`, `.inventory-min-stock-field`, `.inventory-save-btn`.
- Shared stock quick-add/workflow untuk Inventory dan Herbal sudah dipindahkan ke Tailwind component layer:
  - `.stock-quick-add-card`, `.stock-quick-add-head`, `.stock-quick-add-form`,
  - `.stock-mode-picker`, `.stock-workflow-note`, `.stock-preview`.
- Tabel/workspace Herbal dan badge payment kecil sudah dipindahkan ke Tailwind component layer:
  - `.herbal-stock-table`, `.herbal-product-cell`, `.herbal-product-name-wrap`, `.herbal-product-name`, `.herbal-cell-muted`, `.herbal-table-wrap`, `.herbal-workspace`,
  - `.p-status-badge`, `.p-method-badge`.
- Subbagian Analytics monitor grid/item sudah dipindahkan ke Tailwind component layer:
  - `.analytics-monitor-grid`, `.analytics-monitor-grid-spaced`, `.analytics-monitor-item`, `.analytics-monitor-item.danger`, `.analytics-monitor-item.is-accented`.
- Subbagian Analytics header/filter periode sudah dipindahkan ke Tailwind component layer:
  - `.analytics-compact-header`, `.analytics-period-filter`, `.analytics-period-filter-compact`.
- Subbagian Analytics KPI strip sudah dipindahkan ke Tailwind component layer:
  - `.analytics-kpi-strip`, `.analytics-kpi-card-compact`, `.analytics-kpi-value-row`, `.analytics-kpi-money`, `.analytics-trend`, `.analytics-stock-card`.
- Subbagian Analytics Neraca Laba Rugi sudah dipindahkan ke Tailwind component layer:
  - `.analytics-profit-card`, `.analytics-card-header-spaced`, `.profit-loss-grid`, `.analytics-profit-input-field`.
- Audit navigasi isi halaman per tab mulai dilakukan. Pain point awal:
  - Tab Kunjungan: pembelian herbal tambahan dan aksi pembayaran harus lebih cepat terlihat dalam alur form.
  - Tab Herbal: tambah produk dan koreksi stok harus tetap menjadi area prioritas, tidak terkubur jauh di bawah tabel/riwayat.
- Class prioritas layout lintas tab sudah ditambahkan:
  - `.tab-priority-card`, `.tab-inventory-workspace`, `.visit-priority-flow`, `.visit-priority-section`, `.visit-secondary-section`.
- Tab Inventory mulai diselaraskan dengan pola Herbal:
  - area tambah peralatan dan koreksi stok diberi marker prioritas,
  - wrapper tabel + form koreksi memakai `.inventory-workspace`.
- Modul Terapis mulai dipindahkan dari inline style ke Tailwind component layer:
  - form/card `.therapist-form-card`, `.therapist-gender-permission`,
  - direktori/filter `.therapist-directory-card`, `.therapist-directory-header`, `.therapist-counts`, `.therapist-filter-row`, `.therapist-filter-btn`,
  - list item `.therapist-list`, `.therapist-row`, `.therapist-avatar`, `.therapist-info`, `.therapist-name`, `.therapist-specialization`, `.therapist-badges`, `.therapist-cross-gender-badge`, `.therapist-actions`, `.therapist-icon-btn`,
  - empty state `.therapist-empty-state`.
- Modul Patients mulai dipindahkan dari inline style ke Tailwind component layer:
  - table `.patient-table`,
  - form card `.patient-form-card`, `.patient-form-label-optional`,
  - visit form `.visit-form-card`, `.visit-voucher-label-optional`, `.visit-submit-button`,
  - badge `.selected-patient-badge`,
  - panel `.visit-panel`, `.visit-panel-content`, `.visit-panel-empty`,
  - stats `.patient-stats-row`, `.patient-stats-card`, `.patient-stats-badge`,
  - price display `.visit-price-main`, `.visit-price-badge`.
- Komponen shared yang dipakai lintas tab sudah mulai berpindah ke Tailwind, terutama tombol umum, card umum, tabel dasar, stat card, toast, badge umum, badge CRM soft, dan status badge transaksi.
- First-run wizard di `api/static/app.js` sudah memakai class Tailwind tambahan.

### Fase 5 — Bersihkan CSS Legacy

Setelah komponen sudah Tailwind:

- Hapus selector legacy yang tidak terpakai dari `style.css`.
- Pertahankan CSS yang sulit diganti Tailwind:
  - animasi khusus,
  - DataTables override,
  - print style,
  - WebEngine-specific workaround.
- Gunakan audit manual dengan pencarian class.

Status: Berjalan bertahap.

Catatan progres:

- `style.css` masih dipertahankan untuk CSS fitur khusus, DataTables override, modal, invoice, CRM, owner report, WhatsApp, dan layout kompleks lain.
- Selector legacy yang sudah dipindahkan ke Tailwind telah dihapus untuk mengurangi duplikasi: toast, badge umum, badge CRM soft, status badge transaksi, dan status indicator.
- Selector legacy Help & Support sudah dihapus setelah dipindahkan ke Tailwind component layer.
- Selector legacy Settings/Backup awal sudah dihapus setelah dipindahkan ke Tailwind component layer.
- Selector legacy Diskon/Voucher dan dashboard discount sudah dihapus setelah dipindahkan ke Tailwind component layer.
- Selector legacy activation control shared sudah dihapus setelah dipindahkan ke Tailwind component layer; rule disabled khusus `.visit-free-toggle + select:disabled` masih tetap di `style.css` karena terkait form kunjungan.
- Selector legacy Services untuk unit picker/manual price/inventory usage editor sudah dihapus setelah dipindahkan ke Tailwind component layer.
- Inline style utama di `services.js` dan source `ts/services.ts` sudah diganti class Tailwind/component hooks; hasil grep tidak menemukan `style=`, `onmouseover`, atau `onmouseout` tersisa di `api/static/modules/services.js`.
- Selector legacy helper unit dan form tambah Inventory sudah dihapus setelah dipindahkan ke Tailwind component layer. Helper `.unit-help-note` / `.unit-field-hint` tetap aman karena dipakai juga oleh `herbals.js`.
- Selector legacy shared stock quick-add/workflow sudah dihapus dari `style.css`, termasuk responsive rule `.stock-quick-add-form` di media global.
- Selector legacy tabel/workspace Herbal dan badge payment kecil sudah dihapus dari `style.css`, termasuk responsive rule `.herbal-workspace`.
- Selector legacy Analytics monitor grid/item sudah dihapus dari `style.css`, termasuk responsive rule `.analytics-monitor-grid`.
- Selector legacy `.analytics-period-filter` sudah dihapus dari `style.css` setelah dipindahkan ke Tailwind component layer.
- Inline style KPI strip Analytics di `analytics.js`/`ts/analytics.ts` sudah diganti dengan class component Tailwind. Selector global `.stats-grid`, `.stat-card`, `.stat-icon`, dan `.stat-details` tetap dipertahankan karena dipakai lintas Dashboard/Analytics.
- Inline style blok Analytics Neraca Laba Rugi di `analytics.js`/`ts/analytics.ts` sudah diganti dengan class component Tailwind. Responsive rule legacy `.profit-loss-grid` sudah dipindahkan ke Tailwind media block.
- Alur form Kunjungan disesuaikan agar section herbal tambahan muncul sebelum section voucher/catatan/pembayaran minor, dengan order CSS eksplisit di `.visit-priority-flow`.
- Tab Herbal diberi marker prioritas pada quick-add dan koreksi stok agar area input/stok mudah dijaga posisinya saat migrasi lanjutan.
- Tab Inventory diberi marker prioritas pada quick-add dan koreksi stok agar admin tidak perlu scroll jauh untuk input atau cek stok manual.
- Inline style utama di `therapists.js` dan source `ts/therapists.ts` sudah diganti class Tailwind/component hooks; hasil grep tidak menemukan `style=`, `onmouseover`, atau `onmouseout` tersisa di `api/static/modules/therapists.js`.
- Cleanup berikutnya sebaiknya per modul agar mudah diuji visual.

## Risiko

1. Tailwind purge tidak mendeteksi class dinamis di string JS.
   - Solusi: pakai `safelist` di `tailwind.config.js`.

2. Konflik antara `style.css` dan Tailwind.
   - Solusi: fase awal load Tailwind sebelum CSS legacy.

3. Build PyInstaller tidak menyertakan CSS output.
   - Solusi: output tetap di `api/static/tailwind.css`, folder sudah ikut `--add-data`.

4. Banyak HTML inline di JS.
   - Solusi: migrasi module per module, bukan global rewrite.

5. Ukuran CSS membesar selama transisi.
   - Solusi: minify Tailwind dan cleanup `style.css` bertahap.

## Checklist Implementasi

- [x] Install Tailwind dependencies.
- [x] Buat `tailwind.config.js`.
- [x] Buat `postcss.config.js`.
- [x] Buat `api/static/src/input.css`.
- [x] Tambah script `build:css`.
- [x] Tambah link `tailwind.css` di `index.html`.
- [x] Build CSS pertama.
- [x] Test build/typecheck lokal.
- [ ] Test visual aplikasi lokal.
- [x] Migrasi toast.
- [x] Migrasi loader awal.
- [x] Migrasi button awal.
- [x] Migrasi card awal.
- [x] Migrasi sidebar/header.
- [ ] Migrasi module per tab.
  - [x] `help.js` — **100% complete**
  - [x] `settings.js` — **100% complete** (all major sections migrated)
  - [x] `therapists.js` — **100% complete**
  - [x] `services.js` — **100% complete**
  - [x] `invoices.js` — **100% complete**
  - [x] `crm.js` — **100% complete**
  - [x] `whatsapp_gateway.js` — **100% complete**
  - [x] `inventory.js` — **100% complete** (all inline styles migrated, dynamic colors preserved)
  - [x] `herbals.js` — **100% complete** (all inline styles migrated, dynamic colors preserved)
  - [ ] `patients.js` — sebagian sudah dimigrasikan (table, form card, badge, panel, stats)
  - [ ] visits — belum dimigrasikan penuh
  - [ ] `analytics.js` — sebagian sudah dimigrasikan (monitor grid, KPI, profit/loss)
  - [ ] `owner_report.js` — tidak perlu migrasi (sudah menggunakan class CSS bersih)
- [ ] Cleanup CSS legacy penuh.
- [ ] Build installer ulang.

## Log Progres 2026-05-20

### Selesai (Update Terbaru)

**Migrasi Inventory Module (100% Complete):**
- Menambahkan 25+ komponen Inventory ke Tailwind component layer:
  - Stat cards: `.inventory-stats-grid`, `.inventory-stat-card-success`, `.inventory-stat-card-warning`
  - Table: `.inventory-table-card`, `.inventory-table-header`, `.inventory-table-wrapper`, `.inventory-table`
  - Headers: `.inventory-th-name`, `.inventory-th-type`, `.inventory-th-stock`, `.inventory-th-limit`, `.inventory-th-progress`, `.inventory-th-action`
  - Rows: `.inventory-row`, `.inventory-td-name`, `.inventory-td-type`, `.inventory-td-stock`, `.inventory-td-limit`, `.inventory-td-progress`, `.inventory-td-action`
  - Badges: `.inventory-badge`, `.inventory-type-badge`, `.inventory-status-badge-*`
  - Progress: `.inventory-progress-bar`, `.inventory-progress-fill-*`
  - Empty state: `.inventory-empty-state`
  - Helper text: `.inventory-helper-text`
- Mengganti semua 20+ inline style di `api/static/ts/inventory.ts` dengan class component Tailwind.
- Dynamic color styles preserved (9 instances): stat count colors, progress bar colors, stock display colors.
- Build validation: `npm run build:css`, `npm run typecheck`, `npm run build:ts` — semua berhasil.

**Migrasi Herbals Module (100% Complete):**
- Menambahkan 25+ komponen Herbals ke Tailwind component layer:
  - Stat cards: `.herbal-stats-grid`, `.herbal-stat-card-success`, `.herbal-stat-card-warning`, `.herbal-stat-card-danger`
  - Action buttons: `.herbal-actions-row`, `.herbal-btn-sale`, `.herbal-btn-return`
  - Table: `.herbal-table-card`, `.herbal-table-header`, `.herbal-table-wrapper`, `.herbal-table`
  - Headers: `.herbal-th-product`, `.herbal-th-stock`, `.herbal-th-price`, `.herbal-th-margin`, `.herbal-th-status`, `.herbal-th-action`
  - Rows: `.herbal-row`, `.herbal-td-product`, `.herbal-td-stock`, `.herbal-td-price`, `.herbal-td-margin`, `.herbal-td-status`, `.herbal-td-action`
  - Badges: `.herbal-status-badge-*`, `.herbal-margin-badge-*`
  - Empty state: `.herbal-empty-state`
  - Helper text: `.herbal-helper-text`
  - Modals: `.herbal-sale-modal-*`, `.herbal-correction-history-*`
- Mengganti semua 20+ inline style di `api/static/ts/herbals.ts` dengan class component Tailwind.
- Dynamic color styles preserved (9 instances): stat count colors, margin colors, stock display colors.
- Build validation: `npm run build:css`, `npm run typecheck`, `npm run build:ts` — semua berhasil.

**Migrasi CRM Module (100% Complete):**
- Menambahkan 8 komponen CRM ke Tailwind component layer:
  - `.crm-recommendation-icon`, `.crm-status-flex`, `.crm-custom-tags-input`,
  - `.crm-modal-actions-end`, `.crm-voucher-confirm-wrap`,
  - `.crm-outcome-grid`, `.crm-outcome-note-textarea`, `.crm-outcome-actions`.
- Mengganti semua 9 inline style di `api/static/ts/crm.ts` dengan class component Tailwind.
- Hasil grep tidak menemukan `style="` tersisa di `crm.ts`.
- Build validation: `npm run build:css`, `npm run typecheck`, `npm run build:ts` — semua berhasil.

**Migrasi WhatsApp Gateway Module (100% Complete):**
- Menambahkan 13 komponen WhatsApp Gateway ke Tailwind component layer:
  - `.wa-gateway-container`, `.wa-card-green`, `.wa-card-teal`,
  - `.wa-icon-green`, `.wa-icon-teal`, `.wa-result-panel`, `.wa-login-panel`,
  - `.wa-actions-row`, `.wa-btn-refresh`, `.wa-btn-send`, `.wa-btn-logout`, `.wa-test-textarea`.
- Mengganti semua 13 inline style di `api/static/ts/whatsapp_gateway.ts` dengan class component Tailwind.
- Hasil grep tidak menemukan `style="` tersisa di `whatsapp_gateway.ts`.
- Build validation: `npm run build:css`, `npm run typecheck`, `npm run build:ts` — semua berhasil.

**Migrasi Settings Module (100% Complete via Subagent):**
- Menambahkan 50+ komponen Settings ke Tailwind component layer untuk 11 major sections:
  - Clinic Identity, Payment Links, License, Security (PIN), Demo Data,
  - Export Data, Import Data, Backup Management, Discount & Voucher,
  - Free Visit Reasons, Common Components.
- Mengganti semua inline style utama di `api/static/ts/settings.ts` dengan class component Tailwind.
- Build validation: `npm run build:css`, `npm run typecheck`, `npm run build:ts` — semua berhasil.

**Owner Report Module:**
- Hasil grep tidak menemukan `style="` di `api/static/ts/owner_report.ts`.
- Owner Report sudah menggunakan class CSS yang bersih, tidak perlu migrasi inline styles.

**Layout Consistency (Inventory & Herbal):**
- Tab Inventory: Table di atas, forms side-by-side di bawah, pagination 10 items.
- Tab Herbal: Struktur sama dengan Inventory untuk konsistensi UX.

### Selesai (Sebelumnya)

- Melanjutkan migrasi modul Patients pada komponen aman:
  - table header `.patient-table`,
  - form card `.patient-form-card`, `.patient-form-label-optional`,
  - visit form `.visit-form-card`, `.visit-voucher-label-optional`, `.visit-submit-button`,
  - selected patient badge `.selected-patient-badge`,
  - visit panel `.visit-panel`, `.visit-panel-content`, `.visit-panel-empty`,
  - stats row `.patient-stats-row`, `.patient-stats-card`, `.patient-stats-badge`,
  - price display `.visit-price-main`, `.visit-price-badge`.
- Sinkronisasi dilakukan di file generated JS `api/static/modules/patients.js` dan source TypeScript `api/static/ts/patients.ts`.
- Menambahkan selector Patients di `api/static/src/input.css`.
- Melanjutkan migrasi `settings.js` pada subbagian Diskon/Voucher dan dashboard discount.
- Melanjutkan migrasi komponen shared activation control yang dipakai lintas modul Settings, Voucher, Terapis, Layanan, dan Kunjungan.
- Melanjutkan migrasi modul `services.js` pada subbagian aman: unit picker, toggle harga manual, dan editor pemakaian inventaris otomatis.
- Melanjutkan migrasi modul `services.js` tahap lanjutan dengan mengganti inline style utama menjadi class component Tailwind.
- Melanjutkan migrasi modul `inventory.js` pada form tambah Inventory dan helper unit yang juga dipakai Herbal.
- Melanjutkan migrasi shared stock quick-add/workflow yang dipakai `inventory.js` dan `herbals.js`.
- Melanjutkan migrasi tabel/workspace Herbal dan badge payment kecil.
- Melanjutkan migrasi subbagian Analytics monitor grid/item yang paling sering muncul dan relatif stabil.
- Melanjutkan migrasi subbagian Analytics header/filter periode.
- Melanjutkan migrasi subbagian Analytics KPI strip.
- Melanjutkan migrasi subbagian Analytics Neraca Laba Rugi.
- Memulai audit navigasi isi halaman per tab sesuai masukan UX.
- Menyesuaikan tab Kunjungan:
  - form diberi `.visit-priority-flow`,
  - section produk/herbal tambahan diberi `.visit-priority-section`,
  - voucher/catatan/pembayaran diberi `.visit-secondary-section`,
  - CSS order dipakai supaya herbal tambahan tetap di atas section sekunder.
- Menyesuaikan tab Herbal:
  - quick-add produk diberi `.tab-priority-card`,
  - workspace diberi `.tab-inventory-workspace`,
  - koreksi stok diberi `.tab-priority-card`.
- Perubahan disinkronkan di file JS runtime dan TypeScript source:
  - `api/static/modules/patients.js`, `api/static/ts/patients.ts`,
  - `api/static/modules/herbals.js`, `api/static/ts/herbals.ts`.
- Melanjutkan audit navigasi ke tab Inventory:
  - quick-add inventory diberi `.tab-priority-card`,
  - wrapper tabel/form koreksi diganti dari inline flex menjadi `.inventory-workspace.tab-inventory-workspace`,
  - card koreksi stok diberi `.tab-priority-card`,
  - `.inventory-workspace` dibuat responsif di Tailwind component layer.
- Perubahan Inventory disinkronkan di:
  - `api/static/modules/inventory.js`,
  - `api/static/ts/inventory.ts`.
- Mengganti inline style blok Neraca Laba Rugi di `api/static/modules/analytics.js` dan `api/static/ts/analytics.ts`:
  - card wrapper menjadi `.analytics-profit-card`,
  - header spacing menjadi `.analytics-card-header-spaced`,
  - grid laporan menjadi `.profit-loss-grid`,
  - field biaya operasional menjadi `.analytics-profit-input-field`,
  - icon memakai utility `text-primary`.
- Menambahkan component terkait di `api/static/src/input.css`.
- Membersihkan responsive rule `.profit-loss-grid` dari `api/static/style.css`.
- Mengganti inline style KPI strip Analytics di `api/static/modules/analytics.js` dan `api/static/ts/analytics.ts`:
  - wrapper KPI menjadi `.analytics-kpi-strip`,
  - padding card menjadi `.analytics-kpi-card-compact`,
  - value/trend row menjadi `.analytics-kpi-value-row`,
  - nominal panjang menjadi `.analytics-kpi-money`,
  - trend naik/turun menjadi `.analytics-trend.up/.down`,
  - stok kritis menjadi `.analytics-stock-card.ok/.danger`.
- Menambahkan selector KPI strip Analytics di `api/static/src/input.css` tanpa menghapus component global `.stat-*` yang masih dipakai lintas modul.
- Mengganti inline style header/filter Analytics di `api/static/modules/analytics.js` dan `api/static/ts/analytics.ts`:
  - wrapper header menjadi `.analytics-compact-header`,
  - tombol filter periode memakai `.analytics-period-filter.analytics-period-filter-compact`,
  - status aktif tombol memakai class `.active`.
- Memindahkan selector `.analytics-period-filter` dari `api/static/style.css` ke `api/static/src/input.css`.
- Mengganti inline style kecil pada analytics monitor:
  - `style="margin-bottom:16px;"` menjadi `.analytics-monitor-grid-spaced`,
  - `style="border-left:4px solid #0f766e;"` menjadi `.analytics-monitor-item.is-accented`.
- Sinkronisasi dilakukan di `api/static/modules/analytics.js` dan `api/static/ts/analytics.ts`.
- Memindahkan selector Analytics monitor dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.analytics-monitor-grid`
  - `.analytics-monitor-grid-spaced`
  - `.analytics-monitor-item`
- Memindahkan responsive rule `.analytics-monitor-grid` ke Tailwind media block.
- Membersihkan selector legacy terkait dari `api/static/style.css`.
- Memindahkan selector Herbal/payment kecil dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.herbal-stock-table`
  - `.herbal-product-cell`
  - `.herbal-product-name-wrap`
  - `.herbal-product-name`
  - `.herbal-cell-muted`
  - `.herbal-table-wrap`
  - `.herbal-workspace`
  - `.p-status-badge`
  - `.p-method-badge`
- Memindahkan responsive rule `.herbal-workspace` ke Tailwind media block.
- Membersihkan selector legacy terkait dari `api/static/style.css`.
- Memindahkan selector shared stock dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.stock-quick-add-card`
  - `.stock-quick-add-head`
  - `.stock-quick-add-form`
  - `.stock-mode-picker`
  - `.stock-workflow-note`
  - `.stock-preview`
- Memindahkan responsive rule `.stock-quick-add-form` ke Tailwind media block.
- Membersihkan selector legacy terkait dari `api/static/style.css`.
- Memindahkan selector Inventory/helper dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.unit-help-note`
  - `.unit-field-hint`
  - `.inventory-add-form`
  - `.inventory-item-name-field`
  - `.inventory-item-type-field`
  - `.inventory-base-unit-field`
  - `.inventory-package-unit-field`
  - `.inventory-package-size-field`
  - `.inventory-initial-stock-field`
  - `.inventory-min-stock-field`
  - `.inventory-save-btn`
- Memindahkan responsive rule form Inventory ke Tailwind media block.
- Membersihkan selector legacy terkait dari `api/static/style.css`.
- Menambahkan selector Services tambahan di `api/static/src/input.css`:
  - `.service-form-grid`
  - `.service-form-card`
  - `.service-directory-card`
  - `.service-directory-header`
  - `.service-counts`
  - `.service-filter-row`
  - `.service-filter-btn`
  - `.service-list`
  - `.service-empty-state`
  - `.service-row`
  - `.service-avatar`
  - `.service-info`
  - `.service-name`
  - `.service-price`
  - `.service-meta`
  - `.service-note`
  - `.service-actions`
  - `.service-icon-btn`
  - `.service-modal-actions`
- Sinkronisasi dilakukan di file generated JS `api/static/modules/services.js` dan source TypeScript `api/static/ts/services.ts`.
- Melanjutkan migrasi modul `therapists.js` dengan mengganti inline style utama menjadi class component Tailwind.
- Menambahkan selector Terapis di `api/static/src/input.css`:
  - `.therapist-form-card`
  - `.therapist-gender-permission`
  - `.therapist-directory-card`
  - `.therapist-directory-header`
  - `.therapist-counts`
  - `.therapist-filter-row`
  - `.therapist-filter-btn`
  - `.therapist-empty-state`
  - `.therapist-list`
  - `.therapist-row`
  - `.therapist-avatar`
  - `.therapist-info`
  - `.therapist-name`
  - `.therapist-specialization`
  - `.therapist-badges`
  - `.therapist-cross-gender-badge`
  - `.therapist-actions`
  - `.therapist-icon-btn`
- Sinkronisasi dilakukan di file generated JS `api/static/modules/therapists.js` dan source TypeScript `api/static/ts/therapists.ts`.
- Memindahkan selector Services dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.service-unit-picker`
  - `.service-unit-custom.is-hidden`
  - `.service-manual-price-toggle`
  - `.service-usage-editor`
  - `.service-usage-head`
  - `.service-usage-add`
  - `.service-usage-list`
  - `.service-usage-empty`
  - `.service-usage-row`
  - `.service-usage-summary`
- Membersihkan selector legacy Services terkait dari `api/static/style.css`.
- Memindahkan selector activation dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.activation-field`
  - `.activation-switch`
  - `.activation-track`
  - `.activation-copy`
  - `.activation-action`
  - `.visit-free-toggle`
- Membersihkan selector legacy activation terkait dari `api/static/style.css`.
- Rule `.visit-free-toggle + select:disabled` sengaja dipertahankan di `style.css` karena masih spesifik ke form kunjungan dan belum masuk tahap migrasi Visits penuh.
- Memindahkan selector Diskon/Voucher dari `api/static/style.css` ke `api/static/src/input.css`:
  - `.discount-admin-card`
  - `.discount-helper-text`
  - `.discount-flow-strip`
  - `.discount-admin-grid`
  - `.discount-rule-form`
  - `.discount-simulator`
  - `.discount-type-picker`
  - `.discount-input-help`
  - `.discount-form-actions`
  - `.discount-checkbox-line`
  - `.discount-simulation-result`
  - `.discount-sim-selected`
  - `.discount-sim-empty`
  - `.discount-sim-conflict`
  - `.discount-sim-note`
  - `.discount-dashboard-panel`
  - `.discount-dashboard-summary`
  - `.discount-dashboard-note`
  - `.discount-dashboard-list`
  - `.discount-dashboard-history`
  - `.discount-dashboard-row`
- Memindahkan responsive rule discount ke Tailwind media block.
- Membersihkan selector legacy terkait dari `api/static/style.css`.
- Melanjutkan Fase 4 pada modul Pengaturan (`settings.js`) secara bertahap.
- Memindahkan style aman Settings/Backup dari `api/static/style.css` ke Tailwind component layer di `api/static/src/input.css`:
  - `.settings-compact-grid`
  - `.settings-left-stack`
  - `.settings-right-stack`
  - `.settings-card-stack`
  - `.settings-system-card`
  - `.settings-license-card`
  - `.settings-security-card`
  - `.settings-demo-card`
  - `.settings-export-card`
  - `.settings-import-card`
  - `.settings-backup-card`
  - `.settings-security-copy`
  - `.settings-security-help`
  - `.settings-logo-help`
  - `.admin-pin-change-form`
  - `.admin-pin-reset-box`
  - `.admin-pin-reset-heading`
  - `.backup-list`
  - `.backup-item`
  - `.settings-muted-row`
  - `.settings-info-row`
  - `.settings-error-row`
- Memindahkan responsive rule Settings awal ke Tailwind media block.
- Membersihkan selector legacy Settings/Backup yang sudah digantikan dari `api/static/style.css`.
- Melanjutkan Fase 4 dengan modul Bantuan (`help.js`) sebagai tab pertama yang dimigrasikan.
- Memindahkan style Help & Support dari `api/static/style.css` ke Tailwind component layer di `api/static/src/input.css`:
  - `.help-page`
  - `.help-hero`
  - `.help-info-panel`
  - `.help-guide-card`
  - `.help-muted`
  - `.help-support-card`
  - `.help-wa-btn`
  - `.help-grid`
  - `.help-info-grid`
  - `.help-detail-row`
  - `.help-path-row`
  - `.help-full-btn`
  - `.help-folder-actions`
- Memindahkan responsive rule Help & Support ke Tailwind `@media (max-width: 680px)` di `api/static/src/input.css`.
- Membersihkan selector legacy Help & Support dari `api/static/style.css`.
- Mencatat perubahan migrasi layout utama yang sudah dilakukan sebelumnya:
  - `body`, `.sidebar`, `.nav-links`, `.main-content`, `header`, `#app-container`, loader, dan `#display-area` memakai Tailwind utility di `api/templates/index.html`.
- Menambahkan konfigurasi VS Code agar Tailwind at-rule tidak lagi muncul sebagai warning CSS biasa:
  - `.vscode/tailwindcss-custom-data.json`
  - referensi `css.customData`, `scss.customData`, dan `less.customData` di `.vscode/settings.json`.
- Memigrasikan toast ke Tailwind component layer di `api/static/src/input.css`:
  - `#toast-container`
  - `.toast*`
  - `.tw-toast*`
  - `.toast-message`
  - `.toast-close`
  - `.toast-hide`
- Memigrasikan badge/status kecil ke Tailwind component layer:
  - `.badge`, `.badge-ok`, `.badge-low`
  - `.badge-success-soft`, `.badge-danger-soft`, `.badge-warning-soft`, `.badge-info-soft`, `.badge-muted-soft`
  - `.status-badge` dan varian status transaksi
  - `.status-indicator`, `.dot`
- Menambahkan class Tailwind tambahan pada toast dinamis di:
  - `api/static/modules/utils.js`
  - `api/static/ts/utils.ts`
- Membersihkan selector legacy yang sudah digantikan Tailwind dari `api/static/style.css`:
  - toast,
  - badge umum,
  - badge soft CRM,
  - status badge transaksi,
  - status indicator.

### Validasi

- Problems check untuk file yang diubah: tidak ada error.
- `npm run build:css` berhasil.
- `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Help & Support: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Settings awal: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Diskon/Voucher: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi activation controls: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Services aman: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Services inline style: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Inventory form/helper: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi shared stock controls: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi tabel/workspace Herbal: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Analytics monitor grid/item: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Analytics header/filter periode: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Analytics KPI strip: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Analytics Neraca Laba Rugi: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah perbaikan alur prioritas tab Kunjungan/Herbal: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah perbaikan alur prioritas tab Inventory: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Terapis: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Patients awal: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah perbaikan layout Inventory: `npm run build:css` dan `npm run typecheck` berhasil.
- Validasi terbaru setelah migrasi Invoices lengkap: `npm run build:css` dan `npm run typecheck` berhasil.
- Warning Browserslist `caniuse-lite is outdated` masih muncul, tetapi tidak memblokir build.

### Catatan

- Tailwind tetap di-load sebelum `style.css` agar CSS legacy fitur khusus masih bisa menjadi fallback/override selama transisi.
- Migrasi `settings.js` belum dianggap penuh karena masih ada area besar seperti diskon/voucher, WhatsApp settings, import/export inline style, dan beberapa flow sensitif. Lanjutkan per subbagian agar mudah diuji visual.
- Bug ditemukan setelah migrasi shell: semua tab terlihat kosong karena `#display-area` masih punya class Tailwind `hidden` dari markup awal, sedangkan `loadTab()` hanya mengubah `style.display = 'block'`. Class `.hidden` memakai `display: none !important`, sehingga inline `display:block` tidak bisa menampilkan konten.
- Perbaikan sudah diterapkan di `api/static/app.js` dan source `api/static/ts/app.ts`: `loadTab()` sekarang selalu menghapus class `hidden` sebelum dan sesudah render tab, termasuk pada error state.
- Validasi perbaikan display area: `node --check api/static/app.js` dan `npm run typecheck` berhasil.
- Melanjutkan migrasi modul Invoices dengan mengganti semua inline styles menjadi komponen Tailwind:
  - Stats grid: `.invoice-stats-grid`, `.stat-card.total/.visits/.herbal/.income`
  - Header: `.invoice-header`, `.invoice-header-title`, `.invoice-header-meta`
  - Controls: `.invoice-controls`, `.invoice-search-input`, `.invoice-period-filter`
  - Empty state: `.invoice-empty-state`
  - Table: `.invoice-table`, `.invoice-table th`, `.invoice-table td`
  - Table rows: `.invoice-row-date`, `.invoice-row-client`, `.invoice-row-avatar`, `.invoice-row-name`, `.invoice-void-badge`, `.invoice-row-amount`
  - Payment meta: `.invoice-payment-meta`, `.invoice-provider-badge`, `.invoice-payment-ref`, `.invoice-payment-link`
  - Missing file badge: `.invoice-missing-file-badge`
  - Actions: `.invoice-actions`, `.invoice-action-btn`, `.invoice-action-btn-text`
  - Action button variants: `.invoice-action-btn-pdf`, `.invoice-action-btn-print`, `.invoice-action-btn-generate`, `.invoice-action-btn-generate-herbal`, `.invoice-action-btn-update`, `.invoice-action-btn-void`, `.invoice-action-btn-link`, `.invoice-action-btn-check`, `.invoice-action-btn-paid`, `.invoice-action-btn-partial`, `.invoice-gateway-create-btn`
  - Modals: `.invoice-modal-text`, `.invoice-modal-actions`, `.invoice-modal-btn-cancel`, `.invoice-modal-btn-danger`, `.invoice-modal-amount`
  - Pagination: `.invoice-pagination`
- Menghapus semua inline styles dari `api/static/ts/invoices.ts`:
  - Table row date, client, avatar, void badge, amount
  - Action buttons untuk PDF, print, generate, update, void
  - Gateway payment buttons (link, check status, create)
  - Manual payment buttons (tandai lunas, catat DP)
  - Pagination buttons
- Sinkronisasi dilakukan di file generated JS `api/static/modules/invoices.js` dan source TypeScript `api/static/ts/invoices.ts`.
- Menambahkan 40+ selector Invoices di `api/static/src/input.css`.
- Memperbaiki circular dependency error dengan mengganti `@apply text-right` menjadi `text-align: right` langsung di CSS.

## Log Progres 2026-05-19

### Selesai

- Menambahkan Tailwind build toolchain.
- Membuat `tailwind.config.js` dengan content scan untuk:
  - `api/templates/**/*.html`
  - `api/static/**/*.js`
  - `api/static/modules/**/*.js`
- Membuat `postcss.config.js`.
- Membuat `api/static/src/input.css`.
- Membuat component layer awal:
  - `.tw-card`
  - `.tw-btn`
  - `.tw-btn-primary`
  - `.tw-btn-secondary`
  - `.tw-loader`
  - `.tw-spinner`
- Menambahkan script ke `package.json`:
  - `build:css`
  - `watch:css`
  - `build:assets`
- Menghubungkan `api/static/tailwind.css` di `api/templates/index.html` sebelum `style.css`.
- Menambahkan class Tailwind awal ke loader global.
- Menambahkan class Tailwind awal ke first-run wizard di `api/static/app.js`.
- Generate `api/static/tailwind.css` berhasil.

### Validasi

- `npm run build:css` berhasil.
- `node --check api/static/app.js` berhasil.
- `npm run typecheck` berhasil.
- Pemeriksaan Problems untuk file yang diubah: tidak ada error.

### Catatan

- Ada warning `Browserslist: caniuse-lite is outdated`; tidak memblokir build.
- Tailwind saat ini masih fase berdampingan dengan `style.css`.
- `style.css` belum dihapus karena masih menjadi stylesheet utama untuk mayoritas UI.
- Build installer belum dijalankan ulang setelah migrasi Tailwind awal.

## Definition of Done

Migrasi dianggap selesai jika:

- Aplikasi tetap berjalan offline di desktop build.
- Semua tab bisa dibuka tanpa layout rusak.
- `style.css` hanya berisi override khusus/minimal.
- `tailwind.css` dibuild otomatis sebelum release.
- Installer final memuat `tailwind.css`.
- Tidak ada regresi pada tab Pasien, Kunjungan, Invoice, WhatsApp, dan Pengaturan.

## Rekomendasi Eksekusi Pertama

Langkah pertama yang paling aman:

1. Setup Tailwind tanpa mengubah tampilan.
2. Link `tailwind.css` sebelum `style.css`.
3. Build dan pastikan tidak ada perubahan visual besar.
4. Baru migrasi loader dan toast.
