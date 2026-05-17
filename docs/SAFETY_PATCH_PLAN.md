# Safety Patch Plan - LancarDinamicAdmin

> Setiap patch kecil, bisa di-commit terpisah, tidak rewrite besar.  
> Urutan = urutan prioritas. P0 dulu, lalu P1.

---

## Fase 1: Patch Keamanan Kritis Tambahan (P0)

### 1. [DONE] Prevent Negative `final_price`
**Tujuan:** Mencegah kasir atau malicious input menyimpan kunjungan dengan harga/total akhir negatif (merusak laporan pendapatan & cash flow). Ini menyebabkan laporan pendapatan salah.  
**Aman dilakukan sekarang:** Ya — tambahan validasi, tidak mengubah schema atau logic lain.

**File yang perlu dicek:**
- `api/routes/patients.py` (route pencatatan kunjungan)
- `database.py` fungsi `add_visit`

**Perubahan:**
```python
# Di route atau fungsi add_visit, sebelum simpan:
if float(final_price or 0) < 0:
    raise HTTPException(status_code=400, detail="Harga akhir kunjungan tidak boleh negatif.")
```

**Cara test:**
- `test_discount_never_negative`: input diskon > harga → expect HTTP 400

**Commit message:** `fix: prevent negative visit final price`

**Potensi efek samping:** Tidak ada — ini validasi baru. Kunjungan normal tidak terpengaruh.

---

## Patch 2 — Require Reason for Free Visit (di route utama)

**Kenapa penting:** Validasi `free_visit_reason` hanya ada di route import data (`data.py`). Route pencatatan kunjungan biasa belum tentu memvalidasi ini.  
**Aman dilakukan sekarang:** Ya — validasi tambahan, tidak mengubah schema.

**File yang perlu dicek:**
- `api/routes/patients.py` (endpoint pencatatan kunjungan)
- Perlu audit apakah sudah ada atau belum

**Perubahan:**
```python
if is_free_visit and not str(free_visit_reason or "").strip():
    raise HTTPException(status_code=400, detail="Alasan kunjungan gratis wajib diisi.")
```

**Cara test:**
- `test_free_visit_requires_reason`: submit kunjungan gratis tanpa alasan → expect HTTP 400

**Commit message:** `fix: require reason for free visits in main route`

**Potensi efek samping:** Kunjungan gratis lama yang tersimpan tanpa alasan tidak terpengaruh (validasi hanya untuk create baru).

---

## Patch 3 — Prevent Herbal Stock from Going Negative

**Kenapa penting:** Jika tidak ada validasi stok di route sale herbal, kasir bisa menjual herbal sebanyak apapun dan stok jadi minus.  
**Aman dilakukan sekarang:** Ya — cek stok sebelum simpan.

**File yang perlu dicek:**
- `api/routes/herbals.py` (endpoint penjualan herbal)

**Perubahan:**
```python
if herbal.stock < quantity:
    raise HTTPException(status_code=400, detail=f"Stok {herbal.name} tidak mencukupi.")
```

**Cara test:**
- `test_herbal_sale_deducts_stock`: stok = 1, jual 1 → berhasil, stok = 0
- `test_herbal_sale_insufficient`: stok = 1, jual 2 → expect HTTP 400

**Commit message:** `fix: prevent herbal stock from going negative`

**Potensi efek samping:** Tidak ada untuk flow normal. Jika ada edge case stok = 0 yang sengaja, perlu dikecualikan.

---

## Patch 4 — Prevent Inventory Stock from Going Negative

**Kenapa penting:** Stok alat habis pakai (consumable) bisa minus jika tidak ada validasi sebelum deduct.  
**Aman dilakukan sekarang:** Ya — validasi sebelum deduct.

**File yang perlu dicek:**
- `database.py` atau tempat deduct inventory dipanggil
- `api/routes/inventory.py`

**Perubahan:**
```python
if inventory_item.quantity < deduct_quantity:
    raise HTTPException(status_code=400, detail=f"Stok {inventory_item.item_name} tidak mencukupi.")
```

**Cara test:**
- `test_inventory_not_negative`: kunjungan dengan stok alat = 0 → expect ditolak

**Commit message:** `fix: prevent inventory stock from going negative`

**Potensi efek samping:** Kunjungan yang membutuhkan alat dengan stok 0 akan ditolak — ini perilaku yang diinginkan. Pastikan pesan error ditampilkan dengan jelas ke kasir.

---

## Patch 5 — Herbal Multi-Item Sale: Atomic Rollback

**Kenapa penting:** Jika herbal-only sale berisi 3 item dan item ke-2 stok kurang, yang sudah terkurangi harus dikembalikan. Tanpa rollback, stok item ke-1 berkurang tapi transaksi gagal.  
**Aman dilakukan sekarang:** Agak kompleks, tapi aman jika dibungkus dalam transaction block.

**File yang perlu dicek:**
- `api/routes/herbals.py` (endpoint herbal-only multi-item)

**Perubahan:**
```python
# Cek SEMUA stok dulu sebelum kurangi satu pun
for item in items:
    if herbal.stock < item.quantity:
        raise HTTPException(400, detail=f"Stok {herbal.name} tidak cukup.")
# Baru kurangi semua
for item in items:
    herbal.stock -= item.quantity
session.commit()
```

**Cara test:**
- `test_herbal_sale_group_id_multi_item`: stok madu=1, stok jintan=3: jual madu 2 + jintan 1 → semua ditolak, stok jintan tetap 3

**Commit message:** `fix: ensure herbal multi-item sale is atomic`

**Potensi efek samping:** Perlu memastikan `sale_group_id` dibuat sebelum loop. Jangan buat ID baru per item.

---

## Patch 6 — Standardize Return in Revenue Reports

**Kenapa penting:** Formula `herbal_revenue` harus selalu = sale - return. Jika `transaction_type` tidak konsisten (`return` vs `retur`), ada yang tidak terhitung.  
**Aman dilakukan sekarang:** Ya — saat ini `owner_report_helper.py` sudah handle keduanya (`in_(["return", "retur"])`). Perlu pastikan semua tempat lain juga konsisten.

**File yang perlu dicek:**
- `api/routes/herbals.py` (pastikan transaction_type yang dipakai = `return`)
- `helpers/owner_report_helper.py` (sudah OK, handle keduanya)
- `api/routes/analytics.py`

**Perubahan:**
- Standarkan ke `return` (bukan `retur`) untuk semua transaksi baru
- `owner_report_helper` tetap handle keduanya untuk data lama

**Cara test:**
- `test_herbal_return_adds_stock`: buat return → stok bertambah + revenue berkurang

**Commit message:** `fix: standardize herbal return transaction type`

**Potensi efek samping:** Data lama dengan `retur` tetap terbaca karena owner_report sudah handle — aman.

---

## Patch 7 — Exclude Void from Revenue Reports

**Kenapa penting:** Laporan pendapatan tidak boleh menghitung transaksi yang sudah di-void.  
**Aman dilakukan sekarang:** Owner report sudah handle ini. Perlu cek `analytics.py` dan `dashboard_stats_helper.py`.

**File yang perlu dicek:**
- `helpers/dashboard_stats_helper.py`
- `api/routes/analytics.py`

**Perubahan:**
```python
# Tambahkan filter di semua query revenue:
.filter(Visit.invoice_status != 'void')
```

**Cara test:**
- `test_void_excluded_from_revenue`: void visit → owner report tidak menghitungnya

**Commit message:** `fix: exclude voided visits from all revenue reports`

**Potensi efek samping:** Angka dashboard mungkin berubah jika sebelumnya void dihitung. Ini perubahan yang benar.

---

## Patch 8 — Escape Input in Mock Payment Page

**Kenapa penting:** Payment reference atau nama pasien yang muncul di HTML tanpa escape bisa menyebabkan XSS. Meski aplikasi lokal, ini tetap praktik keamanan yang harus ada.  
**Aman dilakukan sekarang:** Ya — escape saja semua output user data di template HTML.

**File yang perlu dicek:**
- `api/templates/` (template HTML jika ada)
- `helpers/payment_gateway.py` (jika ada render HTML)
- `api/static/app.js` / modul lain yang `innerHTML` dengan data API

**Perubahan:**
- Pastikan semua `element.innerHTML = data.someField` diganti dengan `element.textContent` atau lewat `escapeHtml()`
- Di template Jinja2: pastikan `{{ variable }}` (bukan `{{ variable | safe }}`) untuk field user

**Cara test:**
- Input payment_reference dengan `<script>alert(1)</script>` → tidak boleh execute

**Commit message:** `fix: escape user input in payment and invoice displays`

**Potensi efek samping:** Tidak ada untuk text biasa. Hanya mempengaruhi string yang sebelumnya dirender sebagai raw HTML.

---

## Patch 9 — Invoice Path Traversal Prevention

**Kenapa penting:** Jika nama file invoice mengandung `../`, path bisa keluar dari folder `invoices/` dan menimpa file sistem.  
**Aman dilakukan sekarang:** Ya — sanitasi nama file.

**File yang perlu dicek:**
- `helpers/invoice_helper.py`

**Perubahan:**
```python
import re
def sanitize_invoice_filename(name: str) -> str:
    # Hapus karakter tidak aman Windows
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    # Hapus path traversal
    name = name.replace('..', '_')
    return name.strip('._') or 'invoice'

# Validasi path setelah join:
full_path = os.path.abspath(os.path.join(invoice_dir, filename))
if not full_path.startswith(os.path.abspath(invoice_dir)):
    raise ValueError("Path invoice tidak valid.")
```

**Cara test:**
- `test_invoice_path_traversal_blocked`: nama file `../../etc/passwd` → harus di-sanitize

**Commit message:** `fix: prevent path traversal in invoice file generation`

**Potensi efek samping:** Invoice yang nama filenya mengandung karakter aneh akan di-rename otomatis — ini perilaku yang diinginkan.

---

## Patch 10 — Admin PIN Required for Adjustment and Void

**Kenapa penting:** Koreksi stok dan void transaksi adalah aksi ireversibel. Harus membutuhkan Admin PIN.  
**Aman dilakukan sekarang:** Perlu audit dulu apakah Admin PIN sudah dipanggil di route terkait atau belum.

**File yang perlu dicek:**
- `api/routes/inventory.py` (endpoint adjustment stok)
- `api/routes/herbals.py` (endpoint adjustment herbal)
- `api/routes/patients.py` atau `invoices.py` (endpoint void)
- `api/admin_pin.py` (sudah ada)

**Perubahan:**
```python
# Di setiap route aksi sensitif:
from api.admin_pin import require_admin_pin
require_admin_pin(request)  # Sudah ada fungsi ini
```

**Cara test:**
- `test_admin_pin_required_for_adjustment`: panggil adjustment tanpa PIN → expect 403

**Commit message:** `fix: enforce admin pin for adjustment and void actions`

**Potensi efek samping:** Kasir yang tidak tahu PIN tidak bisa adjustment — ini yang diinginkan. Pastikan UI menampilkan form PIN dengan benar.

---

## Patch 11 — Runtime Artifacts Excluded from Build

**Kenapa penting:** `data.db`, `settings.json`, `invoices/`, `backups/` tidak boleh masuk ke EXE installer.  
**Aman dilakukan sekarang:** Ya — edit PyInstaller spec dan `.gitignore`.

**File yang perlu dicek:**
- `LancarDinamicAdmin.spec`
- `build.bat`
- `.gitignore`

**Perubahan:**
- Audit `datas` di spec: hapus entri `data.db`, `settings.json`, folder dinamis
- Update `.gitignore` dengan pola lengkap

**Cara test:**
- Jalankan build
- Unzip EXE dan periksa: tidak ada `data.db` atau `settings.json`

**Commit message:** `chore: exclude runtime artifacts from build and git`

**Potensi efek samping:** Jika aplikasi bergantung pada `data.db` yang di-bundle, perlu pastikan ada inisialisasi DB otomatis saat pertama kali jalan.

---

## Patch 12 — Double Submit Guard for Visit and Herbal Sale

**Kenapa penting:** Klik ganda tombol simpan bisa membuat dua kunjungan atau dua transaksi herbal yang identik.  
**Aman dilakukan sekarang:** Ya — disable tombol saat loading adalah UI-only change.

**File yang perlu dicek:**
- `api/static/app.js` atau modul kunjungan
- `api/static/ts/services.ts` (sudah ada contoh pola `btn.disabled = true`)

**Perubahan:**
```javascript
// Pola yang sudah ada di services.ts — terapkan ke submit visit dan herbal sale:
btn.disabled = true;
btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
try {
    // ... submit
} finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
}
```

**Cara test:**
- Klik tombol simpan dua kali cepat → hanya satu kunjungan yang tersimpan

**Commit message:** `fix: prevent double submit on visit and herbal sale forms`

**Potensi efek samping:** Tidak ada — ini UI guard.
