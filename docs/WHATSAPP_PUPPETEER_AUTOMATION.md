# WhatsApp Puppeteer Automation

> Status: rencana teknis. Fitur belum diimplementasikan.  
> Prinsip utama: semi-manual tetap default/fallback, Puppeteer optional, disabled by default, dan hanya admin-triggered.

---

## 1. Tujuan Fitur

Fitur ini menambahkan opsi **Admin-triggered WhatsApp Puppeteer Send** pada tab Follow-up Pasien.

Tujuannya adalah membantu admin mengirim satu pesan WhatsApp ke satu pasien dari composer follow-up tanpa membuat sistem bulk blast, background sender, atau pengiriman tanpa aksi admin.

Fitur ini harus tetap:
- lokal/offline-first sesuai arsitektur desktop hybrid,
- patuh preferensi kontak pasien,
- aman dari pesan dobel,
- memiliki log yang jelas,
- punya fallback semi-manual.

---

## 2. Mode yang Didukung

### Mode 1 — Semi-manual Default

Flow:
1. Sistem generate pesan follow-up.
2. Admin review dan bisa edit pesan.
3. Admin copy pesan atau buka WhatsApp/WA Web.
4. Admin mengirim manual.
5. Admin klik **Sudah Dihubungi**.

Karakteristik:
- Selalu tersedia.
- Default untuk semua instalasi.
- Tidak membutuhkan Node/Puppeteer.
- Menjadi fallback jika Puppeteer disabled/gagal.

### Mode 2 — Puppeteer Optional

Flow:
1. Admin review pesan di modal Follow-up.
2. Admin klik **Kirim WhatsApp**.
3. Sistem menampilkan confirmation dialog.
4. Backend melakukan validasi guardrail.
5. Backend menjalankan Node Puppeteer script lokal.
6. Puppeteer memakai WhatsApp Web lokal yang login QR manual.
7. Sistem mencatat hasil ke `crm_whatsapp_logs`.

Karakteristik:
- Disabled by default.
- Harus diaktifkan lewat setting `enable_whatsapp_puppeteer=true`.
- Satu klik admin hanya boleh mengirim satu pesan ke satu pasien.
- Tidak boleh bulk, background, atau auto-send tanpa admin.

---

## 3. Non-scope

Fitur ini tidak mencakup:
- bulk send / blasting,
- background campaign sender,
- scheduler yang mengirim tanpa aksi admin,
- bypass QR WhatsApp Web,
- pengiriman tanpa review dan konfirmasi admin,
- WhatsApp Business API/provider resmi pada fase ini,
- cloud multi-device sender,
- scraping kontak massal,
- otomatis mengirim ke seluruh daftar follow-up.

---

## 4. Risiko

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Akun WhatsApp terkena limit | Nomor klinik bisa dibatasi | Tidak bulk, send lock, admin-triggered, satu pesan per klik |
| Selector WA Web berubah | Sender gagal | Puppeteer optional, fallback semi-manual, mock test, error sanitized |
| QR/session expired | Kirim gagal | Tampilkan instruksi scan QR, gunakan `userDataDir` lokal |
| Pesan dobel | Pasien menerima duplikasi | Tombol disabled saat sending, send lock, one-click-one-message guard |
| Nomor invalid | Pengiriman gagal/salah target | Normalisasi dan validasi format `62...` di backend |
| Preferensi kontak dilanggar | Risiko etika/kepercayaan pasien | Block JANGAN DIHUBUNGI/JANGAN PROMO di backend dan UI |
| Error subprocess bocor | Path lokal/stack trace tampil | Sanitized error response |
| Dependency Node/Puppeteer tidak ada | Fitur gagal | Disabled by default, setup guide, fallback copy pesan |

---

## 5. Arsitektur

Komponen rencana:

| Komponen | Lokasi | Peran |
|---|---|---|
| FastAPI endpoint | `api/routes/crm.py` | Menerima request admin-triggered send |
| Python helper | `helpers/whatsapp_puppeteer_helper.py` | Validasi teknis, panggil Node script, parse JSON result |
| CRM helper | `helpers/crm_analysis_helper.py` | Contact preference, normalisasi nomor, send lock, log |
| Node Puppeteer script | `tools/whatsapp_puppeteer/send_whatsapp.js` | Mengontrol WhatsApp Web lokal |
| Local profile | `.local/whatsapp-profile` | Session WhatsApp Web lokal, tidak masuk Git/build |
| CRM log | `crm_whatsapp_logs` | Status `sending`, `sent`, `failed`, `blocked` |
| UI composer | `api/static/modules/crm.js` | Tombol Kirim WhatsApp, status, fallback copy |

### Endpoint Rencana

`POST /api/crm/patient/{patient_id}/whatsapp-puppeteer-send`

Body:

```json
{
  "message": "...",
  "source": "followup_modal",
  "confirm": true
}
```

### Backend Flow

1. Validate `X-App-Token`.
2. Validate patient exists.
3. Normalize phone.
4. Check contact permission.
5. Check message.
6. Check send lock.
7. Create log status `sending`.
8. Call helper `whatsapp_puppeteer_helper.py`.
9. Helper calls Node script `tools/whatsapp_puppeteer/send_whatsapp.js`.
10. Node returns JSON.
11. Backend updates log `sent`/`failed`/`blocked`.
12. Frontend receives status.

### Node Script Design

File:

`tools/whatsapp_puppeteer/send_whatsapp.js`

Input JSON:

```json
{
  "phone": "628xxxx",
  "message": "text",
  "profileDir": ".local/whatsapp-profile",
  "headless": false
}
```

Output success:

```json
{
  "ok": true,
  "status": "sent"
}
```

Output login required:

```json
{
  "ok": false,
  "status": "login_required",
  "message": "WhatsApp Web belum login."
}
```

Output failed:

```json
{
  "ok": false,
  "status": "failed",
  "message": "Pesan gagal dikirim. Silakan coba mode semi-manual."
}
```

---

## 6. Flow Produk

1. Admin buka tab **Follow-up Pasien**.
2. Admin klik detail pasien.
3. Sistem generate pesan dari template.
4. Admin review dan edit pesan jika perlu.
5. Admin klik **Kirim WhatsApp**.
6. UI menampilkan confirmation dialog.
7. Backend validasi:
   - fitur enabled,
   - pasien ada,
   - nomor valid,
   - pesan tidak kosong,
   - contact preference aman,
   - send lock belum aktif.
8. Backend membuat log `sending`.
9. Backend menjalankan Node Puppeteer script via subprocess.
10. Node membuka WhatsApp Web memakai `userDataDir` lokal.
11. Jika belum login, Node mengembalikan `login_required`.
12. Jika login, Node mengirim pesan ke nomor target.
13. Node mengembalikan JSON result.
14. Backend update log ke `sent`, `failed`, atau `blocked`.
15. UI menampilkan status.
16. Jika gagal, admin tetap bisa copy pesan atau buka WA manual.

---

## 7. Safety Rules

Wajib sebelum real send:

1. `enable_whatsapp_puppeteer` default `false`.
2. Admin wajib klik tombol **Kirim WhatsApp**.
3. Admin wajib melihat confirmation dialog.
4. Satu request hanya boleh untuk satu `patient_id`.
5. Satu request hanya boleh membawa satu pesan.
6. Tidak ada endpoint bulk.
7. Tidak ada background sender.
8. Tidak ada scheduler otomatis.
9. Tidak bypass QR WhatsApp Web.
10. Nomor harus dinormalisasi ke `62...`.
11. Pasien **JANGAN DIHUBUNGI** harus diblokir.
12. Template promo harus diblokir untuk pasien **JANGAN PROMO**.
13. Pesan kosong harus ditolak.
14. Send lock mencegah pengiriman berulang dalam window tertentu.
15. Tombol UI disabled saat sending.
16. Backend tetap harus idempotent/anti-duplikasi walaupun UI gagal disable.
17. Semua hasil harus tercatat di `crm_whatsapp_logs`.
18. Error harus disanitasi.
19. Semi-manual fallback harus tetap tersedia.
20. Real-send test hanya lokal dan ke nomor test milik sendiri.

---

## 8. Test Plan

### Automated Backend Mock Tests

- `test_puppeteer_send_rejects_no_phone`
- `test_puppeteer_send_rejects_invalid_phone`
- `test_puppeteer_send_rejects_do_not_contact`
- `test_puppeteer_send_rejects_promo_when_no_promo`
- `test_puppeteer_send_rejects_empty_message`
- `test_puppeteer_send_lock_prevents_duplicate`
- `test_puppeteer_mock_success_creates_log`
- `test_puppeteer_mock_failure_creates_failed_log`
- `test_puppeteer_error_is_sanitized`

### Frontend/UI Mock Tests

- Modal CRM tampil.
- Pesan WhatsApp tergenerate.
- Tombol **Kirim WhatsApp** disabled saat sending.
- Jika mock success, status sent muncul.
- Jika mock failure, error aman muncul.
- Jika **JANGAN DIHUBUNGI**, tombol disabled atau request ditolak.
- Tidak ada double submit.
- Tidak ada browser/tab eksternal ganda pada mode mock.

### Manual Real-send Test

Syarat:
- hanya environment lokal,
- hanya nomor test milik sendiri,
- WhatsApp Web login via QR manual,
- kirim satu pesan,
- cek log `sent`/`failed`,
- jangan jalankan di CI.

---

## 9. Roadmap Implementasi

### CRM-A — WhatsApp Automation Readiness

- Tambah `data-testid` CRM.
- Rapikan modal WhatsApp composer.
- Pastikan tombol tidak dobel buka tab.
- Pastikan log WhatsApp ada.
- Pastikan contact preference valid.

### CRM-B — Puppeteer Mock Sender

- Tambah setting `enable_whatsapp_puppeteer=false`.
- Tambah backend endpoint mock.
- Simpan log `sent_mock`/`failed_mock` atau status mock yang disepakati.
- UI tombol **Kirim WhatsApp** bisa diuji tanpa kirim real.

### CRM-C — Puppeteer Local Prototype

- Tambah `tools/whatsapp_puppeteer/send_whatsapp.js`.
- Gunakan `userDataDir` lokal.
- Login QR manual.
- Kirim hanya ke nomor test sendiri.
- Jangan bulk.

### CRM-D — Backend Integration

- FastAPI memanggil Node script via subprocess.
- Tangani JSON result.
- Simpan log.
- Tampilkan status ke UI.

### CRM-E — QA & Guardrails

- Send lock.
- Admin confirmation.
- **JANGAN DIHUBUNGI** enforcement.
- **JANGAN PROMO** enforcement.
- Manual QA checklist.
- Puppeteer mock test.

---

## 10. Troubleshooting

### WhatsApp Web belum login

Gejala:
- Result `login_required`.
- UI meminta scan QR.

Solusi:
1. Jalankan mode lokal non-headless.
2. Scan QR WhatsApp Web secara manual.
3. Ulangi kirim satu pesan test.

### QR tidak muncul

Kemungkinan:
- Browser headless aktif.
- Window Puppeteer tertutup terlalu cepat.
- Dependency Chromium/Puppeteer belum benar.

Solusi:
- Pastikan `headless=false`.
- Tampilkan instruksi setup di UI.
- Cek instalasi dependency Node/Puppeteer.

### Selector gagal

Gejala:
- Result `failed` dengan pesan umum.
- WhatsApp Web berubah layout.

Solusi:
- Gunakan fallback semi-manual.
- Update selector di script.
- Tambah test lokal sebelum rilis.

### Timeout

Kemungkinan:
- Internet lambat.
- WhatsApp Web belum selesai load.
- Session expired.

Solusi:
- Tampilkan pesan aman: “WhatsApp Web timeout. Silakan coba lagi atau gunakan copy pesan.”
- Jangan retry otomatis berkali-kali.

### Pesan dobel

Pencegahan:
- Tombol disabled saat sending.
- Send lock backend.
- Log status `sending` sebelum subprocess.

Jika terjadi:
- Audit `crm_whatsapp_logs`.
- Periksa apakah request dobel masuk dari UI.
- Periksa apakah send lock terlalu longgar.

### Session rusak

Gejala:
- Login selalu gagal.
- QR berulang terus.

Solusi:
- Tutup proses Puppeteer.
- Backup lalu hapus `.local/whatsapp-profile`.
- Login ulang QR manual.
- Jangan commit folder `.local/`.
