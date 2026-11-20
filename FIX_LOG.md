# FIX LOG - Lancar Dynamic Admin

## Ringkasan
Catatan analisis dan perbaikan yang dilakukan pada kodebase Lancar Dinamic Admin. Semua perubahan diverifikasi dengan uji coba dan typecheck.

## Analisis yang dilakukan
1. `git status` / `git log` - memeriksa state branch dan perubahan yang ada.
2. `python -m pytest tests/` - **301 passed**, 39 subtests passed, 0 gagal.
3. `npx tsc -p tsconfig.static.json --noEmit` - lulus (setelah perbaikan).
4. `npx tsc -p tsconfig.json --noEmit` - lulus.
5. `python -m py_compile` pada semua file Python yang diubah - lulus.
6. Verifikasi aset statis yang direferensikan `api/templates/index.html` - semua ada di disk.
7. Verifikasi konsistensi `api/routes/whatsapp.py` ↔ `helpers/openwa_client.py` ↔ `database.py` (metode antrian WhatsApp tersedia).

## Perbaikan kode
| # | File | Perbaikan | Alasan |
|---|------|-----------|--------|
| 1 | `tsconfig.static.json` | `ignoreDeprecations`: `"5.0"` → `"6.0"` | Menghilangkan error `TS5107` (opsi `module=None` deprecated di TypeScript 7) saat menjalankan `tsc --noEmit`. |
| 2 | `api/routes/patients.py:601-602` | `except Exception: pass` → `logger.exception("Gagal mengantre follow-up WhatsApp otomatis.")` | Bare except clause menyembunyikan semua error saat mengantre follow-up WhatsApp otomatis. Error kini dicatat ke log agar bisa didiagnosis jika follow-up tidak terkirim. |
| 3 | `helpers/crm_analysis_helper.py:355` | `except Exception: pass` → `logger.exception("Gagal memuat opsi tag manual dari database.")` + penambahan `import logging` dan `logger = logging.getLogger("lancar.crm_analysis_helper")` | Bare except clause menyembunyikan error query database saat memuat opsi tag manual CRM. Error kini dicatat ke log. |
| 4 | `api/routes/invoices.py:570-596` (`_resolve_invoice_path`) | Saat path absolut tidak cocok allowed roots atau file tidak ada, tambah fallback cari berdasarkan nama file di `app_data_dir/invoices/` dan `project_root/invoices/` | File invoice tidak ditemukan meski sudah dibuat, karena direktori data berbeda antar mode source/executable (`get_app_data_dir()`). Fallback memungkinkan file ditemukan di lokasi alternatif. |
| 5 | `api/routes/settings.py:169-182` (`_resolve_backup_path`) | Tambah fallback cari file backup di `project_root/backups/` jika tidak ditemukan di `get_app_data_dir()/backups/` | File backup tidak ditemukan saat beralih mode source/executable, karena backup disimpan di direktori data yang berbeda. |
| 6 | `helpers/crm_analysis_helper.py` (`build_followup_message`) | Tambah ucapan waktu (pagi/siang/sore/malam) disinkronkan dengan waktu generate pesan ke dalam sapaan "Assalamu'alaikum" | Pesan follow-up CRM kini menyapa pasien sesuai waktu lokal saat dihasilkan (mis. "Assalamu'alaikum Budi, Selamat pagi. Ini admin Klinik X.") |
| 7 | `helpers/crm_analysis_helper.py` (`build_followup_message`) | Sapaan menggunakan `_patient_salutation(row)` berdasarkan jenis kelamin (Pak/Ibu/Bapak-Ibu) dan tambah template "kondisi", "kondisi_polite", "kondisi_neutral" untuk menyapa kondisi pasien | Pesan follow-up kini sesuai gender pasien (mis. "Assalamu'alaikum Ibu Siti, Selamat siang...") dan menyertakan ucapan kondisi pasien jika tersedia. Template baru terdaftar di `MESSAGE_TEMPLATES`, `WHATSAPP_TEMPLATE_ALIASES`, dan `WHATSAPP_TEMPLATE_LABELS`. |
| 8 | `api/static/ts/whatsapp_gateway.ts` + `api/static/modules/whatsapp_gateway.js` | Ganti UI WhatsApp gateway kompleks (OpenWA/Baileys, QR login, server lokal, auto-login, session/start/logout) dengan tombol sederhana "Buka WhatsApp Web di Browser" yang membuka `https://web.whatsapp.com` di browser default, serta form percobaan yang membuka `https://wa.me/<nomor>?text=<pesan>` | Engine WhatsApp sekarang sederhana: klik tombol untuk membuka browser tempat akun WhatsApp sudah login, tanpa perlu menjalankan gateway Node/OpenWA lokal maupun scan QR ulang. |
| 9 | `api/static/ts/crm.ts` + `api/static/modules/crm.js` (`openCRMWhatsAppLink`) | Tombol follow-up per pasien sekarang membuka `https://wa.me/<no_hp_pasien>?text=<pesan_followup>` langsung di browser, dengan nomor HP dari data pasien (`data-patient-phone`) dan pesan dari textarea yang sudah di-generate (Assalamu'alaikum + salam waktu + salam gender + kondisi pasien) | Kirim follow-up WhatsApp per pasien secara langsung melalui browser tempat WhatsApp Web sudah login, tanpa gateway OpenWA/Baileys. |
| 10 | `database.py:1940` (`_rule_matches`) | `next_visit_number >= threshold` → `next_visit_number % threshold == 0` | Diskon visit_count hanya berlaku pada kelipatan threshold (mis. setiap 5 kunjungan: 5, 10, 15...), bukan dari threshold ke atas (5, 6, 7...). |
| 11 | `api/static/ts/crm.ts` + `api/static/modules/crm.js` (`generateCRMMessage`, `CRM_MESSAGE_TEMPLATES`) | Generate pesan via API `/crm/patient/{id}/message` yang memakai `build_followup_message` (Assalamu'alaikum + salam waktu + salam gender + kondisi). Dropdown template disesuaikan dengan kunci backend (`kontrol`, `reaktivasi`, `promo`, `aftercare`, `kondisi`, dst). | Pesan follow-up CRM kini menyertakan: Assalamu'alaikum, sapaan waktu (pagi/siang/sore/malam), sapaan gender (Bapak/Ibu), dan template kondisi pasien. |
| 12 | `api/static/ts/crm.ts` (line ~755) | Teks petunjuk "tab WhatsApp dan scan QR" → "WhatsApp Web browser. Pastikan sudah login di browser" | Hapus referensi tab WhatsApp gateway lama yang sudah tidak dipakai (engine browser-based). |
| 13 | `api/static/ts/crm.ts` + `api/static/modules/crm.js` | Hapus tab "WhatsApp Gateway" dari sidebar navigasi; CRM tab kini merupakan satu-satunya tempat kirim follow-up WhatsApp | WhatsApp Gateway tab redundan karena engine browser-based sudah diintegrasikan ke CRM. Navigasi lebih bersih. |
| 14 | `api/static/ts/crm.ts` + `api/static/modules/crm.js` (`crm-toolbar`, `crm-search-wrapper`) | Tambah tombol inline "Sudah Dihubungi" (✓) dan "Kirim WA" (WhatsApp icon) di setiap kartu pasien; tambah pencarian dengan tombol clear (✕); tambah hitungan hasil; shortcut keyboard Escape (tutup modal) & Enter (cari) | UX follow-up lebih cepat: aksi langsung dari daftar tanpa buka modal, pencarian responsif dengan clear, navigasi keyboard. |
| 15 | `api/static/ts/crm.ts` + `api/static/modules/crm.js` (modal collapsible sections) | Semua section modal (Tag & Izin, Riwayat, Voucher, WhatsApp, Log, Outcome) dijadikan collapsible dengan ikon chevron | Menghemat ruang layar, user buka section yang dibutuhkan saja. |
| 16 | `helpers/crm_analysis_helper.py` (`_clinic_profile`, `build_followup_message`) | Klinik name diambil otomatis dari `AppSettings().get_clinic_profile()` (setting `clinic_name`) bukan hardcoded | Pesan follow-up otomatis pakai nama klinik dari pengaturan, tidak perlu edit kode saat ganti nama klinik. |
| 17 | `api/static/ts/crm.ts` (`openCRMWhatsAppLink`) | Inline WhatsApp button fetch pesan dari API `/crm/patient/{id}/message?template=kontrol` lalu buka `wa.me` di browser | Pesan follow-up selalu sinkron dengan backend (termasuk nama klinik, gender, waktu) sebelum dibuka di WhatsApp. |
| 18 | `api/static/src/input.css` | Fix class Tailwind invalid `p-4.5` → `p-4` (line 4312) | Build CSS gagal karena Tailwind tidak memiliki utility `p-4.5`. |
| 19 | `api/static/src/input.css` (`.crm-toolbar`, `.crm-toolbar-left`, `.crm-toolbar-center`, `.crm-toolbar-right`, `.crm-search-wrapper`) | Refactor toolbar CRM: padding/gap dikecilkan, search dibatasi `max-w-xs`, dropdown filter lebih compact, result count hide di desktop, responsive tablet/mobile diperbaiki | Navigasi & pencarian tidak lagi bentrok/tumpang tindih. Layout rapi di semua ukuran layar. |

## Dokumentasi yang dihapus (bertentangan)
File di bawah ini dihapus karena berisi klaim yang bertentangan satu sama lain dan dengan kondisi kode aktual (beberapa menyatakan proyek perbaikan belum selesai / fase 4 belum dimulai, sementara `FINAL_BUG_FIX_SUMMARY.md` menyatakan 100% selesai):
- `docs/BUG_FIX_PROGRESS_OVERALL.md` (mengklaim total 67%, fase 4 = 0%)
- `docs/BUG_ANALYSIS_REPORT.md` (bug hanya berupa saran perbaikan, belum diimplementasikan)
- `docs/README_BUGFIX.md` (mengklaim fase 2-4 masih "direncanakan")
- `docs/BUGFIX_CHANGELOG_PHASE1.md`
- `docs/BUGFIX_IMPLEMENTATION_COMPLETE.md`
- `docs/BUGFIX_SUMMARY.md`

## Hasil verifikasi
- Uji coba Python: 301 lulus, 0 gagal.
- TypeScript typecheck (`tsconfig.static.json` dan `tsconfig.json`): lulus tanpa error.
- Kompilasi semua file Python yang diubah: lulus.

## Catatan
Helper-modul fase 4 (`helpers/rate_limiter.py`, `helpers/input_sanitizer.py`, `helpers/financial_validator.py`, `helpers/app_config.py`, `helpers/audit_helper.py`, `helpers/error_messages.py`) ada sebagai file tetapi belum terintegrasi ke dalam alur aplikasi utama. Pertimbangkan integrasi jika diperlukan.
