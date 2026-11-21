# Rencana Staging & Restrukturisasi Commit

> **Status Saat Ini:** Perubahan antara `main` dan cabang `codex-p1-secure-settings` terlalu banyak dan bercampur.  
> **Tindakan yang Disarankan kepada User:**  
> Lakukan `git reset --soft main` (di lokal Anda) untuk meng-uncommit semua perubahan tanpa menghilangkan file, lalu staging sesuai urutan perintah di bawah.

Berikut adalah pengelompokan file berdasarkan tema untuk commit kecil:

---

### 1. Secure Settings & License Sensitive Data
**File yang masuk:**
- `api/license_guard.py`
- `api/routes/settings.py`
- `helpers/secure_settings.py`
- `helpers/license.py`
- `settings.py`
- `tests/test_license_hardening.py`
- `tests/test_settings_security.py`

**Alasan dikelompokkan:** Berisi logika inti pengerasan lisensi, enkripsi, dan pembacaan token yang menjadi tujuan utama branch ini.  
**Risiko jika dicampur:** Sulit di-review atau di-rollback jika ada bug di enkripsi license jika tercampur dengan refactor CSS atau frontend lain.  
**Command Git Add:**
```bash
git add api/license_guard.py api/routes/settings.py helpers/secure_settings.py helpers/license.py settings.py tests/test_license_hardening.py tests/test_settings_security.py
```
**Commit Message:** `feat(security): harden settings persistence and license activation`

---

### 2. Invoice Path & Security
**File yang masuk:**
- `api/routes/invoices.py`
- `helpers/invoice_helper.py`
- `tests/test_invoices_security.py`

**Alasan dikelompokkan:** Isolasi perbaikan keamanan directory traversal pada sub-sistem pembuatan PDF.  
**Risiko jika dicampur:** Invoice security adalah prioritas tinggi. Menyatukannya dengan fitur lain mengaburkan jejak audit keamanan.  
**Command Git Add:**
```bash
git add api/routes/invoices.py helpers/invoice_helper.py tests/test_invoices_security.py
```
**Commit Message:** `fix(invoice): prevent path traversal and secure invoice file generation`

---

### 3. Backup & Restore Safety
**File yang masuk:**
- `helpers/backup_helper.py`
- `tests/test_backup_restore.py`
- `threads/backup_thread.py`
- `legacy_ui/threads/backup_thread.py` (jendela legacy)

**Alasan dikelompokkan:** Operasi kritis yang melibatkan I/O langsung ke file `data.db`. Harus direview terpisah.  
**Risiko jika dicampur:** Kesalahan di backup bisa menghapus data asli. Reviewernya butuh fokus murni di logic SQLite restore.  
**Command Git Add:**
```bash
git add helpers/backup_helper.py tests/test_backup_restore.py threads/backup_thread.py legacy_ui/threads/backup_thread.py
```
**Commit Message:** `fix(backup): harden database backup and restore safety`

---

### 4. Admin PIN & Basic Security Tokens
**File yang masuk:**
- `api/admin_pin.py`
- `helpers/local_token.py`
- `tests/test_admin_pin.py`
- `tests/test_security_token.py`

**Alasan dikelompokkan:** Penambahan layer autentikasi via PIN untuk aksi khusus.  
**Risiko jika dicampur:** Logika PIN ini mempengaruhi banyak sistem. Jika direview bersamaan dengan file UI, berpotensi logic holenya terlewat.  
**Command Git Add:**
```bash
git add api/admin_pin.py helpers/local_token.py tests/test_admin_pin.py tests/test_security_token.py
```
**Commit Message:** `feat(security): enforce admin pin and local token validation`

---

### 5. Frontend Utility Refactor (Types & Utils)
**File yang masuk:**
- `api/static/modules/utils.js`, `api/static/modules/api.js`, `api/static/modules/dom.js`, `api/static/modules/formatters.js`
- `api/static/ts/utils.ts`, `api/static/ts/api.ts`, `api/static/ts/dom.ts`, `api/static/ts/formatters.ts`
- `types/types.ts`
- `types/admin-globals.d.ts`

**Alasan dikelompokkan:** Core infrastruktur JS ke TS. Ini pondasi sebelum library komponen lain dibangun.  
**Risiko jika dicampur:** Perubahan tipe mendasar jika digabung dengan logic form besar membuat review syntax TS sangat berat.  
**Command Git Add:**
```bash
git add api/static/modules/utils.js api/static/modules/api.js api/static/modules/dom.js api/static/modules/formatters.js api/static/ts/utils.ts api/static/ts/api.ts api/static/ts/dom.ts api/static/ts/formatters.ts types/types.ts types/admin-globals.d.ts
```
**Commit Message:** `refactor(frontend): migrate core utilities and api layers to TypeScript`

---

### 6. CSS & Layout Changes
**File yang masuk:**
- `api/static/style.css`
- `api/static/vendor/*`

**Alasan dikelompokkan:** Perubahan assets pihak ketiga dan style murni.  
**Risiko jika dicampur:** File CSS dan vendor biasanya memuat puluhan ribu baris. Mencampurnya akan "menenggelamkan" perubahan kode backend di layar diff GitHub.  
**Command Git Add:**
```bash
git add api/static/style.css api/static/vendor/
```
**Commit Message:** `style: update main css layouts and vendor assets`

---

### 7. Frontend Module Updates & UI
**File yang masuk:**
- Sisa file di `api/static/modules/*.js`
- Sisa file di `api/static/ts/*.ts`
- `api/static/app.js`
- `api/templates/index.html`, `api/templates/license.html`

**Alasan dikelompokkan:** Migrasi komponen web modern (dashboard, form, modals).  
**Risiko jika dicampur:** Komponen interaktif ini bergantung pada Utils yang sudah diset di commit sebelumnya.  
**Command Git Add:**
```bash
git add api/static/modules/ api/static/ts/ api/static/app.js api/templates/
```
**Commit Message:** `feat(frontend): update component modules to typescript architecture`

---

### 8. Build & Protection Tooling
**File yang masuk:**
- `LancarDinamicAdmin.spec`, `RumahSehat*.spec`
- `*.iss` (installer inno setup)
- `build.bat`, `build_protected.bat`
- `download_assets.bat`, `download_assets.ps1`, `download_offline_assets.py`
- `.gitignore`
- `requirements.txt`, `package.json`, `package-lock.json`, `tsconfig.json`, `tsconfig.static.json`
- `icon.ico`, `lancar_icon_preview.png`

**Alasan dikelompokkan:** Ini adalah lingkungan CI/build untuk membuat EXE. Tidak menyentuh bisnis aplikasi sama sekali.  
**Risiko jika dicampur:** Perubahan dependensi package atau build config yang digabung dengan kode produk mempersulit revert jika terjadi build patah.  
**Command Git Add:**
```bash
git add *.spec *.iss build*.bat download_assets.* download_offline_assets.py .gitignore requirements.txt package*.json tsconfig*.json *.ico *.png
```
**Commit Message:** `build: update pyinstaller specs, tsconfig, and asset pipelines`

---

### 9. Version Bump & Changelog
**File yang masuk:**
- `version.py`
- `version.iss`
- `CHANGELOG.md`
- `scripts/bump_version.py`

**Alasan dikelompokkan:** Hanya berisi metadata versi produk. Biasa dilakukan di akhir rilis otomatis/manual.  
**Command Git Add:**
```bash
git add version.py version.iss CHANGELOG.md scripts/bump_version.py
```
**Commit Message:** `chore: bump version and update changelog`

---

### 10. Dokumentasi & Perencanaan (Dibuat AI)
**File yang masuk:**
- `docs/*`
- `README.md`, `BUILD_EXE.md`, `INSTALL*.md`, `QA_CHECKLIST.md`, `RELEASE_CHECKLIST.md`, `WEB_DESKTOP_ARCHITECTURE.md`, `app_structure.md`, `LEGACY_UI_AUDIT.md`

**Alasan dikelompokkan:** Dokumen project management dan referensi arsitektur.  
**Command Git Add:**
```bash
git add docs/ README.md BUILD_EXE.md INSTALL*.md QA_CHECKLIST.md RELEASE_CHECKLIST.md WEB_DESKTOP_ARCHITECTURE.md app_structure.md LEGACY_UI_AUDIT.md
```
**Commit Message:** `docs: add comprehensive prd, gap analysis, and refactor roadmaps`

---

## 🚫 File yang Sebaiknya Dipisah ke Branch Lain (OUT OF SCOPE MURNI)

Ada perubahan besar yang masuk ke branch ini, yang mana **tidak masuk akal** berada di branch `codex-p1-secure-settings` karena porsinya terlalu besar dan berkaitan dengan bisnis transaksi. Sangat disarankan untuk memasukkannya jadi commit tersendiri (`feat: migrate core REST business logic`) ATAU memindahkannya ke branch baru seperti `feature/api-migration`.

**File Rest API & Bisnis Transaksi:**
- `api/main.py`
- `database.py`, `db_models.py`, `db_mixin_*.py`
- Kumpulan `api/routes/` (analytics, audit, crm, data, herbals, inventory, owner_report, patients, payments, reports, services, support, therapists)
- Kumpulan `helpers/` transaksi bisnis (crm_analysis_helper, dashboard_stats_helper, owner_report_helper, payment_gateway, payment_providers/*, payment_rules)
- Kumpulan tests sisa (`test_batch*`, `test_core_business_flows`, `test_crm`, `test_delete_safety`, `test_herbals`, `test_patients`, `test_payment_gateway`)
- Penyingkiran Folder `legacy_ui/` dan MVC lama (semua file viewmodels, dialogs lama).

**Saran Staging untuk File di atas (Jika Tetap Mau Di-Push di Branch Ini):**
```bash
# Semua business REST routes dan helpers
git add api/main.py database.py db_*.py api/routes/ helpers/ tests/

commit message: "feat(api): implement comprehensive fastapi integration and business logic refactor"

# Semua pembersihan folder lama legacy
git add legacy_ui/ dialogs/ viewmodels/ threads/ main.py

commit message: "refactor: deprecate thick-client qwidgets in favor of web-based architecture"
```
