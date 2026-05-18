# Test Plan - LancarDinamicAdmin

> Dipakai untuk QA manual dan automated testing.  
> Fase 7 QA harus melewati semua checklist ini.

---

## A. Manual Test — Service Generic

| # | Skenario | Langkah | Expected Result |
|---|---|---|---|
| A1 | Bekam Basah per titik | Tambah layanan "Bekam Basah", pricing_type=per_unit, unit_label=titik, price_per_unit=25000 | Layanan tersimpan. UI menampilkan "titik". Invoice menampilkan "Detail Layanan" |
| A2 | Pijat Terapi fixed | Tambah "Pijat Terapi", pricing_type=fixed, unit_label=sesi, fixed_price=100000 | Harga otomatis 100000 saat dipilih di form kunjungan |
| A3 | Refleksi manual | Tambah "Refleksi", pricing_type=manual, unit_label=menit | Kasir bisa input harga manual di form kunjungan |
| A4 | Konsultasi Herbal free/manual | Tambah "Konsultasi Herbal", pricing_type=free | Harga otomatis 0. Free visit reason wajib |
| A5 | Paket Terapi | Tambah "Paket Relaksasi", pricing_type=package, unit_label=paket | Package ditampilkan sebagai satu unit |
| A6 | Layanan nonaktif | Nonaktifkan satu layanan → buka form kunjungan | Layanan nonaktif tidak muncul di dropdown |

---

## B. Manual Test — Kunjungan

| # | Skenario | Expected Result |
|---|---|---|
| B1 | Kunjungan normal (cash, paid) | Visit tersimpan, stok alat berkurang, invoice dibuat |
| B2 | Kunjungan dengan diskon | `original_price`, `discount_amount`, `final_price` tersimpan dengan benar |
| B3 | Kunjungan gratis dengan alasan | `final_price = 0`, `is_free_visit = true`, `free_visit_reason` terisi |
| B4 | Kunjungan gratis tanpa alasan | Sistem menolak, pesan wajib isi alasan |
| B5 | Diskon > harga asli | Sistem menolak, `final_price` tidak boleh negatif |
| B6 | Stok alat cukup | Kunjungan berhasil, stok berkurang sesuai `service_inventory_usage` |
| B7 | Stok alat kurang | Kunjungan ditolak sebelum tersimpan, pesan stok tidak cukup |
| B8 | Terapis nonaktif | Tidak muncul di dropdown pilih terapis |
| B9 | Klik tombol simpan dua kali cepat | Hanya satu kunjungan yang tersimpan (double submit guard) |
| B10 | Kunjungan layanan non-bekam | Invoice menampilkan nama layanan dan unit_label dari service, bukan "titik bekam" |

---

## C. Manual Test — Herbal

| # | Skenario | Expected Result |
|---|---|---|
| C1 | Herbal ikut kunjungan | `herbal_transaction.visit_id` terisi. Invoice gabungan tampil layanan + herbal |
| C2 | Herbal-only satu item (tunai) | Transaksi tersimpan, stok berkurang, invoice herbal-only dibuat |
| C3 | Herbal-only multi-item (semua stok cukup) | Semua item tersimpan dengan `sale_group_id` sama, stok berkurang semua |
| C4 | Herbal-only multi-item (satu stok kurang) | Seluruh transaksi ditolak, stok semua item tetap tidak berubah |
| C5 | Stok herbal = 0, jual 1 | Sistem menolak, pesan stok tidak cukup |
| C6 | Retur herbal | Stok bertambah, `transaction_type = return`, transaksi sale lama tidak dihapus |
| C7 | Herbal nonaktif dijual | Sistem menolak |

---

## D. Manual Test — Invoice

| # | Skenario | Expected Result |
|---|---|---|
| D1 | Invoice layanan terapi saja | PDF berisi "Detail Layanan", nama layanan, terapis, harga, total |
| D2 | Invoice herbal-only | PDF berisi semua item dalam sale_group_id |
| D3 | Invoice gabungan | PDF berisi layanan + herbal dalam satu dokumen |
| D4 | Invoice terapi non-bekam | Tidak ada kata "bekam" atau "titik bekam" di PDF |
| D5 | Void invoice | Invoice ditandai void. Tidak masuk revenue di laporan |
| D6 | PDF gagal dibuat (simulasi) | Visit tetap tersimpan, status invoice = `pdf_failed` atau pesan error jelas |
| D7 | Nama file invoice aneh (`../../../test`) | Nama file di-sanitize, tidak ada path traversal |

---

## E. Manual Test — Laporan & Owner Report

| # | Skenario | Expected Result |
|---|---|---|
| E1 | visit_revenue bulan ini | = sum(final_price) dari visit aktif (non-void) bulan ini |
| E2 | herbal_revenue bulan ini | = sum(sale) - sum(return) dari herbal_transactions aktif |
| E3 | Return mengurangi revenue | Buat return herbal → herbal_revenue berkurang |
| E4 | Void tidak masuk revenue | Void visit → tidak muncul di owner report |
| E5 | Free visit tidak menambah revenue | Free visit dengan final_price=0 → revenue tidak bertambah |
| E6 | Herbal ikut kunjungan tidak double count | Herbal yang punya visit_id tidak dihitung dua kali |
| E7 | Top layanan muncul dengan benar | Top 5 layanan berdasarkan jumlah kunjungan atau revenue |
| E8 | Dashboard tidak crash saat data kosong | Buka dashboard di database baru tanpa data → tidak ada error JS |

---

## F. Manual Test — Security

| # | Skenario | Expected Result |
|---|---|---|
| F1 | Adjustment stok tanpa Admin PIN | Sistem menolak (HTTP 403 atau prompt PIN) |
| F2 | Void tanpa Admin PIN | Sistem menolak |
| F3 | X-App-Token hilang di request | Request ditolak (jika endpoint dilindungi) |
| F4 | Path invoice aneh | Ditolak atau di-sanitize |
| F5 | Error internal server | Response tidak mengandung stack trace atau path file |
| F6 | `data.db` tidak ikut build EXE | Periksa isi EXE installer |

---

## G. Automated Tests

### Test Suite Baru yang Harus Dibuat

#### `tests/test_visit_pricing.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_create_visit_per_unit_service` | Visit dengan per_unit service | Service unit_label=titik, qty=3, price_per_unit=25000 | `original_price=75000`, `final_price=75000` |
| `test_create_visit_fixed_service` | Visit dengan fixed service | Service fixed_price=100000 | `final_price=100000` tanpa perlu input qty |
| `test_create_visit_manual_price` | Visit dengan manual price | Manual input 80000 | `final_price=80000` |
| `test_free_visit_requires_reason` | Free visit tanpa alasan → tolak | `is_free_visit=True`, `free_visit_reason=None` | HTTP 400 |
| `test_free_visit_saves_original_price` | Free visit tetap simpan original_price | Harga asli 70000, free | `original_price=70000`, `final_price=0` |
| `test_discount_never_negative` | Diskon > harga asli → tolak | `price=50000`, `discount=60000` | HTTP 400 |

#### `tests/test_inventory_safety.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_service_usage_deducts_consumable` | Visit → stok consumable berkurang | Layanan punya usage: sarung tangan 2. Stok = 5 | Stok jadi 3 setelah kunjungan |
| `test_inventory_not_negative` | Stok tidak boleh minus | Stok = 1, butuh 2 | HTTP 400, stok tetap 1 |
| `test_non_consumable_not_auto_deducted` | Non-consumable tidak auto-deduct | Item type = non_consumable | Stok tidak berubah setelah kunjungan |

#### `tests/test_herbal_safety.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_herbal_sale_deducts_stock` | Sale → stok berkurang | Stok=5, jual 2 | Stok jadi 3 |
| `test_herbal_sale_insufficient` | Stok tidak cukup → tolak | Stok=1, jual 2 | HTTP 400, stok tetap 1 |
| `test_herbal_sale_group_id_multi_item` | Multi-item punya sale_group_id sama | 2 item sale | Keduanya punya sale_group_id yang sama |
| `test_herbal_sale_rollback_if_one_item_out_of_stock` | Satu item stok kurang → semua batal | Item A stok=5, Item B stok=0, jual A2+B1 | HTTP 400, stok A tetap 5 |
| `test_herbal_return_adds_stock` | Return → stok bertambah | Stok=3, return 1 | Stok jadi 4, transaction_type=return |

#### `tests/test_invoice_safety.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_visit_invoice_total` | Total invoice = layanan + herbal | Visit 100000 + herbal 30000 | Total invoice = 130000 |
| `test_herbal_invoice_group_total` | Invoice herbal-only = semua item dalam group | 3 item dalam sale_group_id | Invoice total = sum semua item |
| `test_combined_invoice_total` | Invoice gabungan | Visit + herbal | Total benar, tidak double |
| `test_invoice_path_traversal_blocked` | Path traversal dicegah | Nama file `../../test.pdf` | Nama di-sanitize atau ditolak |

#### `tests/test_revenue_reports.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_void_excluded_from_revenue` | Void tidak masuk revenue | Visit paid, lalu di-void | Revenue = 0 |
| `test_return_reduces_net_herbal_sales` | Return mengurangi herbal revenue | Sale 100000, return 30000 | Net herbal revenue = 70000 |
| `test_dashboard_no_double_count` | Tidak ada double count | Herbal ikut kunjungan | Herbal tidak dihitung dua kali |
| `test_free_visit_zero_revenue` | Free visit = 0 revenue | Free visit final_price=0 | Revenue tidak bertambah |

#### `tests/test_security.py`

| Test | Tujuan | Data Dummy | Expected |
|---|---|---|---|
| `test_admin_pin_required_for_adjustment` | Tanpa PIN → ditolak | Adjustment tanpa header PIN | HTTP 403 |
| `test_admin_pin_required_for_void` | Void tanpa PIN → ditolak | Void tanpa header PIN | HTTP 403 |

---

## H. Checklist Sebelum Fase 7 QA Dimulai

- [ ] Semua patch Fase 2 sudah di-apply dan di-commit
- [ ] Semua test otomatis baru sudah dibuat
- [ ] Database test selalu dibersihkan setelah setiap test case
- [ ] Tidak ada hardcode data developer di test (gunakan fixture)
- [ ] `pytest tests/ -v` berjalan tanpa error di lingkungan bersih

---

## I. CRM WhatsApp Puppeteer Automation Test Plan

Automation WhatsApp memakai Puppeteer hanya boleh diuji otomatis melalui mock. Real-send hanya boleh manual di lingkungan lokal dan ke nomor test milik sendiri.

### Backend Tests

| Test | Tujuan | Expected |
|---|---|---|
| `test_puppeteer_send_rejects_no_phone` | Pasien tanpa nomor tidak boleh dikirim | HTTP 400, log `blocked` atau tidak membuat send real |
| `test_puppeteer_send_rejects_invalid_phone` | Nomor tidak valid ditolak | HTTP 400, pesan error aman |
| `test_puppeteer_send_rejects_do_not_contact` | Preferensi **JANGAN DIHUBUNGI** enforce di backend | HTTP 400/403, tidak memanggil sender |
| `test_puppeteer_send_rejects_promo_when_no_promo` | Template promo ditolak jika pasien **JANGAN PROMO** | HTTP 400/403, tidak memanggil sender |
| `test_puppeteer_send_rejects_empty_message` | Pesan kosong ditolak | HTTP 400 |
| `test_puppeteer_send_lock_prevents_duplicate` | Send lock mencegah spam/duplikasi | Request kedua dalam lock window ditolak |
| `test_puppeteer_mock_success_creates_log` | Mock success mencatat log | Log status `sent_mock`/`sent` sesuai desain mock |
| `test_puppeteer_mock_failure_creates_failed_log` | Mock failure mencatat log gagal | Log status `failed_mock`/`failed` dan error aman |
| `test_puppeteer_error_is_sanitized` | Error subprocess tidak bocor stack/path | Response tidak mengandung stack trace/path lokal |

### Frontend/Puppeteer UI Tests

| Skenario | Expected Result |
|---|---|
| Modal CRM tampil | Composer WhatsApp bisa dibuka dan field utama punya selector stabil |
| Pesan WhatsApp tergenerate | Textarea berisi pesan sesuai template/pasien |
| Tombol **Kirim WhatsApp** disabled saat sending | Tidak bisa double submit |
| Mock success | Status `sent`/success muncul di UI dan log refresh |
| Mock failure | Error aman muncul, fallback **Copy Pesan** tetap tersedia |
| Pasien **JANGAN DIHUBUNGI** | Tombol kirim disabled atau backend menolak |
| Tidak ada double submit | Klik cepat berkali-kali hanya menghasilkan satu request |
| Mode mock | Tidak ada browser/tab eksternal ganda dan tidak ada real send |

### Manual Real-send Test

Syarat:
- Hanya di environment lokal developer/admin.
- Hanya ke nomor test milik sendiri.
- WhatsApp Web login via QR manual.
- Jangan jalankan di CI.
- Jangan bulk.

Langkah:
1. Aktifkan `enable_whatsapp_puppeteer=true` di environment lokal test.
2. Buka tab Follow-up Pasien.
3. Pilih pasien test dengan nomor sendiri.
4. Generate pesan singkat.
5. Klik **Kirim WhatsApp**.
6. Konfirmasi dialog.
7. Jika belum login, scan QR WhatsApp Web secara manual.
8. Kirim satu pesan.
9. Cek log `sent`/`failed` di `crm_whatsapp_logs`.
10. Matikan kembali setting setelah test.
