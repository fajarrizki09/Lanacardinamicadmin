# Implementasi Migrasi Tauri

> **Status:** Phase 3D-R3 REOPENED - Phase 4A-CSP R5 / Final Inline Handler Cleanup sebelum Manual Acceptance, 2026-05-29  
> **Keputusan gate:** `BLOCKED` untuk cutover produksi sampai uji interaktif WebView2 dan upgrade installer pada Windows VM/profil uji lulus.  
> **Rujukan scope:** `docs/PRD_MIGRASI_TAURI.md`

## Release Candidate Phase 3D-R3

Identitas artifact pengganti yang memuat patch Phase 3D-R3 reopened setelah artifact sebelumnya dibersihkan dan tidak dapat dipakai untuk acceptance:

| Item | Nilai |
| --- | --- |
| Installer | `Lancar Dynamic Admin_1.7.39_x64-setup.exe` |
| Lokasi build | `src-tauri\target\release\bundle\nsis\` |
| Lokasi artifact RC | `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe` (ignored, tidak di-commit) |
| Ukuran | 74.48 MiB (`78,097,966` byte) |
| SHA-256 | `5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E` |
| Shell / sidecar PE subsystem | `WINDOWS_GUI` / `WINDOWS_GUI` |

RC Phase 3D-R3 dengan SHA-256 `46F2F88CA213D38CADDBE8BF8ACAA9AD4935C545B73B25EA2E5C6F5835E043FF` berhasil untuk login dan kirim pesan WhatsApp menurut validasi manual, tetapi gagal gate UI lanjutan. RC `7CA841F8715CDBD8F38BEF678D4B1C8EB636F21BB64F780E309008F6A0D1F06D`, `3B662446859BBD8D2BF70FAFC42D6BE36A3328390B68F7C5998AC40BBA56021B`, `C9A2E0CF7CB7A9714586C98A6876C19CE1E90B6F56202B733A286B17A5590272`, `ED51ED2701559E789306E19D60ABECEEC7F2B0B100DB2491F633DEC660237E9B`, `AC0A156E3BC836F964F26165EF76F1C6756E562FC0F1B5F3FB315FFB7CA3FEE3`, `F21F1E2DEB923A58743E8E2DCE1170DF8296E8E75E5C0642509C2DF886E78E7E`, `FAF4482B4A78416A0AC8F120A10DE55E1BC22917A3E278E7BBF3F494367AB30E`, `0DAF92F425CC82F61B68550B1795A23B60A87D9B31106A3F1A6E0B36F35A57EA`, `7F8A2FFC4A409FD7F2FBD637259EB46E8907032B75FD1F5357C3663C3D182025`, `07941BBA37A1E8B0FB612B38EB785E303F333D4C80FD902E2EEACF4882041233`, `6DB3DB6A9A00694FA143EBC6D3FD99E396AD21656228BA6D62FA46C0957389F6`, `246FE3A472C1B47703B15B1859B757D6002C85D6FA7B1FEC0A9392918BB1D0FB`, `CD37BA0E23DCED733A0700EE30401716373ABCB841A78D2ED62D755950423CCC`, `A4A4295145F6C2F7844FC5A2B405638016191F6FA98EC592D667F36308B52A0D`, `3DF683B8C165B5C01EBACA4112FC28C91AE4A0AE41C9CCC784D04201CAD1908E`, `1BF27B0F15A790EAC17349252D2C8E7368C43C857DA620CF8999CE195CFD8CAC`, `21BF51CF1EEA664935D694CC0C6001681CAB0CB7FF54E214BE177FAC004756D7`, `8EFCD82B2C5913DAB51367989D017BBD915B84D073FA3648361702B8B0E36244`, `14A4B87ED3B5BCE434E5B30AC32FE98E5666F6F6CD5F4DF0A26F67FC35274F1E`, `58BC12F9DEC639C489F563AF080D5809D6EBC965CDE989062FD82A8C04133051`, `9290DA06B6BCE543B69537AC485D89B9AF9B12A3F3AC34FB98C9A7DCDDEDF2F3`, `A2B4631DEB26BCB2FC2CDCC713E45B4C7640D919F002586E7B357A351AF8CAD2`, dan `A031B6A0438D3D25C07E4BD52EAE83196E3D9A9E8F52B5C0AC7B5B64D1EE26E3` seluruhnya superseded. Untuk acceptance baru hanya gunakan RC `5E40E6A0...`; hash sebelumnya tidak lagi diterima collector.

## Reopened Phase 3D-R3: Bukti Gagal Installed App

RC `A6FF2647...` sempat dibangun setelah smoke runtime terisolasi lulus, tetapi validasi manual dari aplikasi Tauri terpasang tetap gagal. Log installed app pada 2026-05-26 menunjukkan:

| Bukti | Hasil |
| --- | --- |
| Path install yang diuji | `C:\Users\HP\AppData\Local\Lancar Dynamic Admin` |
| Command sidecar nyata | `lancar-api.exe --runtime-dir "\\?\C:\Users\HP\AppData\Local\Lancar Dynamic Admin\runtime"` |
| `desktop_sidecar.log`, 14:05:49 s.d. 14:12:12 | Setiap start WhatsApp mencatat `gateway_process_exited` |
| `whatsapp_gateway.log`, 14:12:11 | Node crash: `EISDIR: illegal operation on a directory, lstat 'C:'` |
| Reproduksi langsung | `node.exe --check C:\...\server.js` lulus; `node.exe --check \\?\C:\...\server.js` gagal dengan error yang sama |

Kesimpulan: patch absolut path R3 pertama belum menangani prefix extended-length `\\?\` yang diberikan Tauri kepada sidecar. QR tidak mungkin muncul karena Node mati sebelum health maupun endpoint QR tersedia.

## Patch Phase 3D-R3 Reopened

| Blocker | Perbaikan | File utama |
| --- | --- | --- |
| Gateway crash dari aplikasi terpasang | Normalisasi `\\?\C:\...`/`\\?\UNC\...` menjadi path Node-compatible sebelum runtime/entrypoint digunakan; log startup mencatat runtime dan entrypoint non-rahasia | `sidecar_main.py`, `api/routes/whatsapp.py`, `tests/test_tauri_sidecar.py`, `tests/test_tauri_openwa_lifecycle.py` |
| Pesan error WhatsApp masih terlalu umum | Pesan UI membedakan runtime hilang, dependency tidak lengkap, port conflict/stale process, child crash, dan timeout | `api/static/ts/settings.ts` |
| Filter periode Analitik menjatuhkan tombol **Semua** ke baris sendiri | Filter desktop dibuat `flex-nowrap` dengan tombol `shrink-0/whitespace-nowrap`, ruang kontrol diperbesar, dan overflow horizontal aman bila sempit | `api/static/src/input.css`, `api/static/ts/analytics.ts`, `tests/test_tauri_ui_regressions.py` |
| Dropdown pasien Catat Kunjungan tampil tetapi pilihan tidak masuk ke form | Pemilihan hasil dijalankan pada `pointerdown` sebelum input `blur` menutup dropdown; jalur keyboard tetap tersedia | `api/static/ts/patients.ts`, `tests/test_tauri_ui_regressions.py` |
| Tampilan akun WhatsApp setelah login masih datar | State connected/QR/idle memakai profile card terstruktur dengan status, nama akun, nomor, koneksi, action bar responsive, dan token dark mode | `api/static/ts/settings.ts`, `api/static/ts/whatsapp_gateway.ts`, `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Tombol Edit Pasien keluar jalur/tidak center | Cell aksi memakai wrapper compact/grouped yang tidak menyusut, tombol `inline-flex` dengan tinggi/lebar minimum, icon/text line-height stabil, dan focus/hover terlihat | `api/static/ts/patients.ts`, `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Tombol **Sudah Dihubungi** gagal parse body | Aksi manual memakai endpoint status khusus dengan JSON tervalidasi, tidak memerlukan log pesan, mengembalikan JSON aman, menyimpan status `contacted`, dan frontend menangani response non-JSON secara defensif | `api/static/ts/crm.ts`, `api/routes/crm.py`, `helpers/crm_analysis_helper.py`, `tests/test_crm.py`, `tests/test_tauri_ui_regressions.py` |
| Dark mode Dashboard dan tab lain tidak konsisten | Token `--color-*` dipakai untuk background/surface/border/text; override terakhir mencakup card statistik, list, kalender, diskon, DataTables, form, tab, badge, toast, WhatsApp/CRM, serta action Pengaturan | `api/static/style.css`, `api/static/ts/settings.ts`, `tests/test_tauri_ui_regressions.py` |
| Modal dark mode masih putih/teks kabur | Panel edit/generic/setup/PIN dan alert/confirm runtime mengganti surface inline putih dengan token tema dan class surface; modal header/input/action ikut dark override | `api/static/ts/modal.ts`, `api/static/ts/app.ts`, `api/static/ts/utils.ts`, `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Tab Herbal/Produk terlalu panjang karena form permanen | Form tambah dan koreksi dipindahkan ke modal; action bar kini berisi **Tambah Produk**, **Jual Produk**, **Koreksi Stok**, dan **Retur** sementara tabel tetap menjadi workspace utama | `api/static/ts/herbals.ts`, `api/static/src/input.css`, `api/static/style.css` |
| Tab Inventory/Peralatan terlalu ramai karena form permanen | Form tambah dan koreksi/update dipindahkan ke modal konsisten dengan Herbal; tabel, ringkasan stok, dan aksi row yang sudah ada tetap dipertahankan | `api/static/ts/inventory.ts`, `api/static/src/input.css`, `api/static/style.css` |
| Aksi stok sebelumnya bergantung pada klik row | Row terpilih diberi highlight/ringkasan dan mengisi modal otomatis; semua action tetap aktif tanpa row dan menyediakan picker pencarian keyboard-safe di dalam panel | `api/static/ts/herbals.ts`, `api/static/ts/inventory.ts`, `tests/test_tauri_ui_regressions.py` |
| Screenshot manual menunjukkan surface putih/terang masih lolos pada dark mode | Kontrak token `--color-*` dilengkapi untuk background/surface/elevated/input/table/modal/toast dan lapisan override akhir mengikat seluruh tab, DataTables, modal, badge, empty state, serta utility runtime terang hanya pada `body.theme-dark` | `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Pengaturan terlalu panjang dan sulit dijangkau | Settings memakai workspace kategori dengan search; hanya panel kategori aktif yang tampil dan tombol aksi tetap berdekatan dengan form terkait; tombol WhatsApp mengarah ke tab gateway yang sudah ada tanpa mengubah flownya | `api/static/ts/settings.ts`, `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Terapis dapat dipilih untuk layanan yang tidak dikuasai | Relasi `therapist_service_capabilities` menyimpan multi-layanan, modal Terapis menyediakan searchable checklist, form kunjungan memfilter/auto-select serta menampilkan helper, dan API menolak pasangan terpetakan yang tidak sesuai | `db_models.py`, `db_dataclasses.py`, `database.py`, `api/routes/therapists.py`, `api/routes/patients.py`, `api/static/ts/therapists.ts`, `api/static/ts/patients.ts`, `tests/test_therapist_services.py` |

UI tetap mengambil status/QR melalui proxy Python. Node API tetap memerlukan token internal dan menolak request browser ber-`Origin`/`Referer`; dashboard gateway publik tidak menerima detail QR/session.

### Redesign Herbal/Produk dan Inventory (2026-05-27)

Form permanen **Tambah Produk Baru**, **Koreksi Stok Manual**, dan padanannya pada Inventory tidak lagi dirender di bawah tabel. Modal action memakai surface bertema dan picker pencarian dengan tinggi terbatas agar aman pada WebView2/window kecil; mode gelap memakai token `--color-surface-*`/`--color-border`, bukan panel putih hardcoded.

Dua alur operasional yang tersedia:

1. Klik row produk/peralatan terlebih dahulu, lihat highlight dan ringkasan selection, lalu buka action; modal otomatis memilih item tersebut dan menampilkan stok, satuan, harga bila tersedia, serta status.
2. Klik action secara langsung tanpa memilih row; modal tetap terbuka dan user mencari item dari picker berdasarkan atribut yang tersedia di model. Produk mendukung nama, stok/status, satuan, dan harga; inventory mendukung nama, jenis, stok/status, dan satuan. SKU/kategori belum disajikan API model ini sehingga tidak ditambahkan pada scope redesign.

File produksi/guard/dokumentasi yang diubah untuk redesign: `api/static/ts/herbals.ts`, `api/static/ts/inventory.ts`, output `api/static/modules/herbals.js` dan `api/static/modules/inventory.js`, `api/static/src/input.css`, output `api/static/tailwind.css`, `api/static/style.css`, `tests/test_tauri_ui_regressions.py`, `tools/collect-tauri-phase3b-evidence.ps1`, dan `docs/TAURI_IMPLEMENTATION.md`.

### Audit Global Dark Mode (2026-05-27)

Screenshot validasi manual installed-app melaporkan panel terang dan kontras teks gagal pada Dashboard, Pasien, Kunjungan, Terapis/Layanan, Herbal/Inventory, Invoice, WhatsApp, Follow-up, Owner Report/Analytics, Voucher, serta Settings/Backup/Bantuan. Temuan tersebut membuktikan guard source sebelumnya belum cukup; acceptance visual lama dinyatakan gagal dan tidak dipakai untuk membuka gate.

Perbaikan ini memusatkan dark mode pada token `--color-bg`, `--color-bg-soft`, seluruh variasi `--color-surface-*`, border/text semantik, warna status beserta surface lunaknya, serta token khusus `--color-input-*`, `--color-table-*`, `--color-modal-bg`, dan `--color-toast-bg`. Lapisan dark terakhir mengoverride card, header/footer panel, empty state, form, DataTables, tabel domain, modal runtime, toast, badge, picker, dan utility `bg-white`/`bg-slate-50`/`bg-gray-50` hanya saat tema gelap aktif.

Surface yang dibersihkan dari jalur dark meliputi metric/summary/action cards, panel dashboard/kalender/diskon, form dan DataTables Pasien, seluruh panel input/riwayat Kunjungan, card Terapis/Layanan, workspace Herbal/Inventory, Invoice, WhatsApp status, kartu dan modal Follow-up, Owner Report/Analytics, Voucher, Settings/Backup/Bantuan, serta modal alert/confirm/edit/setup/PIN yang menggunakan class runtime. Tidak ada perubahan logic stok, penjualan, WhatsApp, atau gateway keamanan.

File yang berubah untuk audit dark mode: `api/static/style.css`, `tests/test_tauri_ui_regressions.py`, `tools/collect-tauri-phase3b-evidence.ps1`, dan `docs/TAURI_IMPLEMENTATION.md`; output asset tetap diregenerasi sebagai bagian build Tauri.

### Redesign Settings dan Mapping Terapis-Layanan (2026-05-27)

Tab Settings kini membuka workspace navigasi kategori di bagian atas: **Profil & Pembayaran**, **Lisensi**, **Keamanan / PIN**, **Ekspor**, **Impor**, **Backup & Data**, dan **Data Contoh**, ditambah pintasan menuju tab WhatsApp. Search settings dapat menemukan istilah seperti `Midtrans`, `Backup`, `PIN`, atau `tema`, dan hanya panel terkait yang ditampilkan. Endpoint penyimpanan serta proteksi secret tetap dipertahankan; `midtrans_server_key` tetap berupa input password kosong dan tidak diprefill dari nilai tersimpan.

Terapis memiliki mapping banyak-ke-banyak ke layanan aktif melalui tabel `therapist_service_capabilities`. Form Tambah/Edit Terapis memakai checklist yang dapat dicari dan card terapis menampilkan ringkasan layanan. Mapping kosong tetap valid untuk data lama. Layanan nonaktif tidak dapat ditambahkan sebagai mapping baru; mapping historis tidak mengubah data kunjungan lama.

Pada **Catat Kunjungan**, pemilihan terapis menerapkan aturan berikut:

1. Jika terapis memiliki tepat satu layanan aktif, layanan tersebut dipilih otomatis dan helper menampilkan bahwa pilihan berasal dari mapping.
2. Jika terapis memiliki beberapa layanan aktif, dropdown difilter hanya ke layanan tersebut dan menampilkan chip/helper daftar layanan tersedia.
3. Jika terapis belum memiliki mapping, semua layanan aktif tetap ditampilkan dengan warning ringan agar flow lama tetap kompatibel.
4. Jika layanan yang sudah terpilih tidak cocok setelah terapis berubah, pilihan direset dan user diberi pesan yang jelas.
5. Backend create/update kunjungan menolak pasangan tidak sesuai hanya bila terapis sudah memiliki mapping, dengan pesan aman `Layanan tidak sesuai dengan terapis yang dipilih.`

File yang berubah untuk pekerjaan ini: `db_models.py`, `db_dataclasses.py`, `database.py`, `api/routes/therapists.py`, `api/routes/patients.py`, `api/static/ts/therapists.ts`, `api/static/ts/patients.ts`, `api/static/ts/settings.ts`, `api/static/style.css`, `types/admin-globals.d.ts`, output `api/static/modules/*.js`, `tests/test_therapist_services.py`, `tests/test_tauri_ui_regressions.py`, `tools/collect-tauri-phase3b-evidence.ps1`, dan `docs/TAURI_IMPLEMENTATION.md`.

### Smoke Phase 3D-R3 Reopened

| ID | Skenario | Hasil | Status |
| --- | --- | --- | --- |
| P3D-R3-GW-01 | Runtime gateway dari folder install dengan argumen Tauri `\\?\...` dan data uji disposable | Normalized runtime biasa; health `ok`; proxy Python `qr_ready`; QR data URL tersedia; token tidak terekspos; shutdown stopped `true` | Lulus non-interaktif; install UI baru pending |
| P3D-R3-GW-02 | Binary sidecar hasil build dengan `--runtime-dir "\\?\...\src-tauri\runtime"` | Log startup mencatat runtime tanpa prefix `\\?\`; shutdown desktop bertoken mengembalikan exit `0` | Lulus non-interaktif |
| P3D-R3-UI-01 | Analitik: 7 Hari, 30 Hari, 6 Bulan, 1 Tahun, Semua | Semua tombol satu baris pada desktop normal; screenshot terang/gelap setelah pemasangan RC pengganti | Pending VM/WebView2; screenshot belum tersedia dari sesi build |
| P3D-R3-UI-02 | Catat Kunjungan dan Edit Pasien | Cari pasien, klik hasil masuk ke form; tombol Edit/Riwayat center pada window normal/kecil dan focus terlihat | Guard source lulus; pending VM/WebView2 |
| P3D-R3-UI-03 | Profile WhatsApp dan modal Follow-up, light/dark mode | Card status/action tampil rapi; **Sudah Dihubungi** sukses dan tetap berubah setelah refresh | Kontrak API otomatis lulus; inspeksi visual/persistensi UI pending VM/WebView2 |
| P3D-R3-UI-04 | Global dark mode: Dashboard, Pasien, Kunjungan, Terapis, Layanan, Herbal/Inventory, Invoice, WhatsApp, Follow-up, Owner Report/Analitik, Voucher, Settings/Backup/Bantuan dan semua modal; window normal/kecil | Surface/card/table/form/tab/badge/toast/modal terbaca tanpa panel putih menyilaukan | Screenshot manual lama gagal; token/guard baru lulus; recheck installed-app pending VM/WebView2 |
| P3D-R3-UI-05 | Herbal/Produk: tambah, koreksi, jual, retur dari row terpilih dan dari action langsung; light/dark/window kecil | Form hanya tampil dalam modal, picker/search berfungsi, stok refresh setelah submit | Regression guard/source build lulus; submit dan visual installed-app pending VM/WebView2 |
| P3D-R3-UI-06 | Inventory: tambah dan koreksi/update dari row terpilih dan dari action langsung; light/dark/window kecil | Form hanya tampil dalam modal, picker/search berfungsi, stok refresh setelah submit | Regression guard/source build lulus; submit dan visual installed-app pending VM/WebView2 |
| P3D-R3-UI-07 | Settings: pindah kategori, cari setting, simpan dummy, masking payment key, dark mode/window kecil | Panel kategori/search tidak memanjang, secret tetap masked, penyimpanan tidak berubah | Guard/source/test security lulus; visual installed-app pending VM/WebView2 |
| P3D-R3-UI-08 | Terapis dan Catat Kunjungan: mapping multi-layanan, auto-select, filter, warning unmapped, mismatch submit | Mapping tersimpan; layanan sesuai saja dapat disubmit jika mapping tersedia; unmapped tetap kompatibel | Test API/guard lulus; interaksi installed-app pending VM/WebView2 |
| P3D-R3-WA-01 | Start gateway, QR tampil, scan akun uji, status connected, kirim pesan, stop | Login dan kirim pesan berhasil pada RC `46F2F88C...`; perlu diulang pada RC terbaru setelah patch UI | Pending repeat pada RC `5E40E6A0...` |
| P3D-R3-PROC-01 | Tutup aplikasi | Tidak ada `lancar-api`/`node.exe` residual setelah close window | Pending VM/WebView2; host build memiliki aplikasi installed aktif yang tidak dimulai/dimatikan oleh sesi ini |

### RC Dark Mode Audit `F21F1E2D...` (2026-05-27)

Rebuild setelah audit dark mode menghasilkan installer `F21F1E2DEB923A58743E8E2DCE1170DF8296E8E75E5C0642509C2DF886E78E7E` (`78,010,068` byte). Validasi `pre-install` pada saat itu lulus dengan output disposable `C:\tmp\phase3d-r3-f21f-evidence\20260527-105500-pre_install.json`. RC ini telah digantikan oleh RC Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

Smoke manual yang membutuhkan interaksi aplikasi terpasang belum dijalankan ulang setelah RC ini: sesi ini tidak menyediakan kontrol WebView2/browser callable dan database/profile aplikasi aktif tidak dipakai untuk submit data uji. Karena itu inspeksi dark mode seluruh halaman/modal pada window normal/kecil serta smoke tambah/koreksi/jual/retur Herbal dan tambah/koreksi Inventory tetap `PENDING / BLOCKED` untuk profil atau VM disposable.

### RC Settings/Capability Mapping `FAF4482B...` (2026-05-27)

Rebuild setelah redesign Settings dan implementasi mapping Terapis-Layanan menghasilkan installer `FAF4482B4A78416A0AC8F120A10DE55E1BC22917A3E278E7BBF3F494367AB30E` (`78,024,477` byte). Validasi `pre-install` lulus dengan output disposable `C:\tmp\phase3d-r3-faf4482b-evidence\20260527-130047-pre_install.json`. RC ini sudah digantikan oleh RC Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Full Test Suite Stabilization RC `0DAF92F4...` (2026-05-28)

P0 owner report/revenue split sudah fixed: `Visit` menghitung revenue jasa saja, sedangkan `HerbalTransaction` menghitung revenue herbal termasuk item yang terhubung ke `visit_id`. Skenario visit 100k + herbal 50k dikunci regression sebagai `visit_revenue=100000`, `herbal_revenue=50000`, dan `total_revenue=150000`.

Error `TestPaymentGatewayMock` yang sempat terlihat pada full-suite triage tidak bereproduksi pada run isolated maupun sequential setelah tidak menjalankan proses unittest paralel terhadap database test yang sama. Root cause operasionalnya adalah kontensi proses test paralel pada state/database global test, bukan provider registry, AppSettings, environment variable, atau referensi pembayaran yang bocor antar-test. `TestPaymentGatewayMock` dan `TestHerbalGatewayMock` lulus saat dijalankan berurutan.

Failure hardening inventory TS berasal dari guard stale setelah redesign action-based Inventory/Herbal: test masih mencari badge/form lama (`name`, `qty`, `stock`, `unit`) yang tidak lagi ada. Saat audit, ditemukan juga bug hardening nyata: nama/unit dari dataset disisipkan ke inline `onclick` sebagai string JavaScript. Produksi diperbaiki dengan `jsStringLiteral(...)` di `api/static/ts/utils.ts`, lalu handler Inventory/Herbal memakai helper itu untuk argumen data; guard diperbarui agar tetap memverifikasi escaped summary dan JS-literal-safe handler.

Rebuild setelah stabilisasi full suite menghasilkan installer `0DAF92F425CC82F61B68550B1795A23B60A87D9B31106A3F1A6E0B36F35A57EA` (`78,009,973` byte / 74.40 MiB). RC ini sekarang superseded oleh Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-1 Read-Only Rust Helper RC `07941B...` (2026-05-28)

Phase 4A-1 menambahkan helper Rust read-only tanpa mengubah logic bisnis Python, database, payment, license, CRM/follow-up, invoice calculation, atau WhatsApp gateway:

- `native_get_paths`: menerima kind `app_data`, `exports`, `logs`, `config`, `invoices`; mengembalikan metadata path dan `exists`; kind lain ditolak.
- `native_get_diagnostics`: mengembalikan metadata non-rahasia seperti app version, platform, app data path, log path, config path, runtime path, backend port/running, dan timestamp.
- `native_get_process_status`: target `python-sidecar`, `tauri-shell`, dan `openwa`; OpenWA tetap `owner="python"` dengan `running=null` karena Rust belum mengambil lifecycle gateway.

Data yang boleh diekspos hanya metadata path/proses non-rahasia. Command tidak membaca isi file dan tidak mengembalikan shutdown token, app token, gateway token, session WhatsApp, API key, server key, isi database, cache, auth, credential, atau isi log mentah. Tidak ada command open/reveal/print/external URL pada tahap ini. Capability Tauri hanya menambahkan app-command allow spesifik untuk `start_backend`, `native_get_paths`, `native_get_diagnostics`, dan `native_get_process_status`; tidak ada akses broad shell/fs/opener ke frontend.

Verifikasi Phase 4A-1:

| Gate | Hasil |
| --- | --- |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Lulus |
| `cargo test --manifest-path src-tauri/Cargo.toml` | Lulus; 3 test helper Rust |
| `npm run typecheck` | Lulus |
| `npm run build:assets` | Lulus |
| `python -m unittest tests.test_payment_gateway` | Lulus; 38 test |
| `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 293 test |
| `npm run tauri:build` | Lulus |

Rebuild final setelah Phase 4A-1 dan capability app-command menghasilkan installer `07941BBA37A1E8B0FB612B38EB785E303F333D4C80FD902E2EEACF4882041233` (`78,031,619` byte / 74.42 MiB). RC `0DAF92F4...` dan intermediate `7F8A2F...` sekarang superseded oleh Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-2 Rust Native Open/Reveal Path RC `6DB3DB...` (2026-05-28)

Phase 4A-2 menambahkan helper native open/reveal path di Rust tanpa mengubah logic bisnis Python, database, invoice calculation/export generation, payment gateway, license, CRM/follow-up, atau WhatsApp gateway:

- `native_open_path`: menerima kind `exports`, `logs`, `app_data`, `invoices`, `backups` dan optional `path`. Jika `path` kosong, command membuka root folder kind tersebut. Jika `path` diberikan, path harus canonical dan berada di bawah root kind yang sama.
- `native_reveal_path`: menerima kind `exports`, `logs`, `invoices`, `backups` dan `path` wajib. Command hanya reveal file/folder yang valid di Explorer/file manager.
- Frontend wrapper `openDesktopPath`/`revealDesktopPath` memanggil Tauri command lebih dulu. Fallback Python lama hanya dipakai saat command tidak tersedia: `/support/open_folder?kind=...` untuk root folder dan `/open_invoice?path=...` untuk invoice PDF. Print tetap lewat endpoint Python karena `native_print_file` belum masuk scope.

Allowlist path:

| Kind | Root |
| --- | --- |
| `app_data` | Tauri app data dir |
| `exports` | app data `exports` |
| `logs` | Tauri app log dir |
| `invoices` | app data `invoices` |
| `backups` | app data `backups` |

Security rule:

- Semua root dan target harus `canonicalize`; path yang tidak ada menghasilkan `File tidak ditemukan.`.
- Target harus tetap berada di bawah root allowlist kind yang sama.
- Path traversal, UNC/network path, device/verbatim path input, null byte, dan komponen sensitif seperti `session`, `cache`, `auth`, `credential`, `token`, `key`, dan `secret` ditolak dengan `Path tidak diizinkan.`.
- Command tidak membaca isi file/folder dan tidak mengembalikan token, key, session, credential, isi log, atau isi database.
- Capability Tauri hanya menambahkan app-command allow spesifik untuk `native_open_path` dan `native_reveal_path`; tidak ada permission broad shell/fs/opener untuk frontend.

Verifikasi Phase 4A-2:

| Gate | Hasil |
| --- | --- |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Lulus |
| `cargo test --manifest-path src-tauri/Cargo.toml` | Lulus; 7 test helper Rust |
| `npm run typecheck` | Lulus |
| `npm run build:assets` | Lulus setelah satu retry karena write-lock sementara `audit.js`; rerun lulus |
| `python -m unittest tests.test_tauri_ui_regressions` | Lulus; 21 test |
| `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 294 test |
| `npm run tauri:build` | Lulus |

Rebuild setelah Phase 4A-2 menghasilkan installer `6DB3DB6A9A00694FA143EBC6D3FD99E396AD21656228BA6D62FA46C0957389F6` (`78,044,892` byte / 74.43 MiB). RC `07941B...` sekarang superseded oleh Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-3 Rust Native External URL Opener RC `246FE3A4...` (2026-05-28)

Phase 4A-3 menambahkan helper native open external URL di Rust tanpa mengubah payment gateway logic, database bisnis, invoice calculation, license, CRM/follow-up, WhatsApp gateway, process supervisor, atau flow print:

- `native_open_external_url`: menerima `url` dan `source` (`payment`, `whatsapp_help`, `gateway_dashboard`, `support`, `unknown`), memvalidasi allowlist di Rust, lalu membuka URL melalui OS default opener.
- Frontend wrapper `openDesktopExternalUrl` memanggil Tauri command lebih dulu dan hanya fallback ke endpoint Python `/support/open_external_url` bila command native tidak tersedia.
- Flow yang memakai wrapper: link pembayaran sandbox Midtrans, bantuan WhatsApp `wa.me`, dan dashboard gateway lokal `127.0.0.1:3000`.

Allowlist URL:

| Target | Aturan |
| --- | --- |
| Sandbox Midtrans | `https://app.sandbox.midtrans.com` tanpa port eksplisit selain default HTTPS |
| WhatsApp help | `https://wa.me` tanpa port eksplisit selain default HTTPS |
| Local gateway dashboard | `http://127.0.0.1:3000` saja |

URL yang ditolak: `javascript:`, `file:`, `data:`, `vbscript:`, URL dengan credential (`https://user:pass@...`), domain lookalike, domain di luar allowlist, `localhost`, port lokal selain `3000`, IP literal lain, URL kosong, dan URL invalid. Command hanya log `source`, `scheme`, `host`, serta keputusan allow/deny; full URL/query tidak dicatat agar token/payment reference tidak bocor. Capability Tauri hanya menambahkan app-command allow spesifik `native_open_external_url`; tidak ada broad shell/fs/opener permission.

Verifikasi Phase 4A-3:

| Gate | Hasil |
| --- | --- |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Lulus |
| `cargo test --manifest-path src-tauri/Cargo.toml` | Lulus; 11 test helper Rust |
| `npm run typecheck` | Lulus |
| `npm run build:assets` | Lulus |
| `python -m unittest tests.test_tauri_ui_regressions tests.test_payment_gateway tests.test_tauri_external_urls` | Lulus; 65 test |
| `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 295 test |
| `npm run tauri:build` | Lulus |

Rebuild setelah Phase 4A-3 menghasilkan installer `246FE3A472C1B47703B15B1859B757D6002C85D6FA7B1FEC0A9392918BB1D0FB` (`78,040,039` byte / 74.42 MiB). RC `6DB3DB...` sekarang superseded oleh Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-4 Rust Native Open Invoice/PDF Helper RC `CD37BA0E...` (2026-05-28)

Phase 4A-4 menambahkan helper native khusus invoice/PDF tanpa mengubah invoice calculation, PDF generation, payment gateway logic, database bisnis, license, CRM/follow-up, WhatsApp gateway, process supervisor, atau print flow:

- `native_open_invoice_file`: menerima `path` dan `action` (`open` atau `reveal`), memvalidasi path di Rust, lalu membuka PDF atau reveal lokasi file melalui OS default.
- Frontend wrapper `openDesktopInvoiceFile` memanggil Tauri command lebih dulu. Fallback Python `/open_invoice?path=...` hanya dipakai untuk action `open` saat command native tidak tersedia. Action `reveal` tidak memakai fallback Python karena tidak ada endpoint reveal lama yang cukup spesifik.
- Flow `openInvoice(...)` kini memakai helper invoice khusus. Tombol **Lokasi** ditambahkan untuk reveal PDF invoice/herbal yang sudah ada. Generate/update invoice tetap melalui endpoint Python yang sama, dan `printInvoice(...)` tetap memakai endpoint print Python.

Allowlist file invoice:

| Root | Aturan |
| --- | --- |
| app data `invoices` | File harus canonical, berada di bawah root, dan berupa file `.pdf` |
| app data `exports` | File PDF export/invoice yang tersimpan di export dir juga diizinkan dengan aturan yang sama |

Path yang ditolak: traversal `..`, path di luar allowlist, UNC/network path, device/verbatim path input, null byte, komponen sensitif seperti `session`, `cache`, `auth`, `credential`, `token`, `key`, `secret`, file tidak ada, folder, dan ekstensi selain `.pdf`. Command tidak membaca isi file dan tidak mengembalikan token, key, session, credential, isi log, atau isi database. Log hanya mencatat action, root allowlist, dan allow/deny.

Verifikasi Phase 4A-4:

| Gate | Hasil |
| --- | --- |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Lulus |
| `cargo test --manifest-path src-tauri/Cargo.toml` | Lulus; 15 test helper Rust |
| `npm run typecheck` | Lulus |
| `npm run build:assets` | Lulus |
| `python -m unittest tests.test_tauri_ui_regressions tests.test_invoices_security tests.test_payment_gateway` | Lulus; 62 test |
| `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 296 test |
| `npm run tauri:build` | Lulus |

Rebuild setelah Phase 4A-4 menghasilkan installer `CD37BA0E23DCED733A0700EE30401716373ABCB841A78D2ED62D755950423CCC` (`78,038,022` byte / 74.42 MiB). RC `246FE3A4...` sekarang superseded oleh Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-5 Rust Native Print File Helper RC `A4A42951...` (2026-05-28)

Phase 4A-5 menambahkan helper native print PDF tanpa mengubah invoice calculation, PDF generation, payment gateway logic, database bisnis, license, CRM/follow-up, WhatsApp gateway, process supervisor, atau status pembayaran:

- `native_print_file`: menerima `path` dan `source` (`invoice`, `herbal_invoice`, `export`, `receipt`), memvalidasi path di Rust, lalu mencoba print PDF melalui mekanisme OS yang fixed.
- Jika direct print tidak tersedia atau gagal, command membuka PDF di viewer default dan mengembalikan `status="open_fallback"` dengan pesan `Print langsung tidak tersedia. File dibuka di viewer.`. Command tidak mengklaim `printed` jika hanya membuka viewer.
- Frontend wrapper `printDesktopFile` memanggil Tauri command lebih dulu. Fallback Python `/print_invoice?path=...` hanya dipakai bila command native tidak tersedia.
- Flow print invoice/herbal invoice memakai `native_print_file`; generate/update invoice tetap melalui endpoint Python yang sama.

Allowlist path print sama dengan helper invoice: hanya file `.pdf` canonical di app data `invoices` atau app data `exports`. Path yang ditolak: traversal `..`, path di luar allowlist, UNC/network path, device/verbatim path input, null byte, komponen sensitif seperti `session`, `cache`, `auth`, `credential`, `token`, `key`, `secret`, file tidak ada, folder, dan ekstensi selain `.pdf` termasuk `.html`, `.exe`, `.bat`, `.cmd`, `.ps1`, dan `.lnk`. Command tidak membaca isi file, tidak mengembalikan isi file, dan tidak expose token/session/key/log/database. Capability Tauri hanya menambahkan app-command allow spesifik `native_print_file`; tidak ada broad shell/fs/opener permission.

Verifikasi Phase 4A-5:

| Gate | Hasil |
| --- | --- |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Lulus |
| `cargo test --manifest-path src-tauri/Cargo.toml` | Lulus; 19 test helper Rust |
| `npm run typecheck` | Lulus |
| `npm run build:assets` | Lulus |
| `python -m unittest tests.test_tauri_ui_regressions tests.test_invoices_security tests.test_payment_gateway` | Lulus; 63 test |
| `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 297 test |
| `npm run tauri:build` | Lulus |

Manual smoke print pada VM/profil disposable belum dijalankan dari sesi ini. Checklist acceptance tetap harus membuka invoice PDF, klik Print, memastikan print/dialog atau fallback viewer berjalan tanpa hang, menutup aplikasi, dan mengecek tidak ada orphan process.

Rebuild setelah Phase 4A-5 menghasilkan installer `A4A4295145F6C2F7844FC5A2B405638016191F6FA98EC592D667F36308B52A0D` (`78,042,781` byte / 74.43 MiB). RC `CD37BA0E...` saat itu superseded. RC `A4A42951...` kemudian superseded oleh Phase 4A-CSP `3DF683B8...`; `3DF683B8...`, R2 awal `1BF27B0F...`, R2 final `21BF51CF...`, R3 `8EFCD82B...`, R4 `14A4B87E...`, dan R5 awal `58BC12F9...` sekarang superseded oleh Phase 4A-CSP R5 rebuild `9290DA06...`.

### Artifact Recovery Historis RC `ED51ED27...` (2026-05-26)

**Keputusan manual acceptance: `FAILED / BLOCKED` (artifact pulih melalui rebuild; target Windows disposable untuk uji UI installed-app tidak tersedia pada sesi ini).**

Artifact installer `C9A2E0CF...` tidak ditemukan kembali pada workspace, `C:\tmp`, Downloads, maupun arsip `D:\codex-build`; installer arsip yang ditemukan memiliki hash lama yang berbeda. Rebuild saat itu menghasilkan RC `ED51ED2701559E789306E19D60ABECEEC7F2B0B100DB2491F633DEC660237E9B`, yang sekarang sudah digantikan RC Phase 4A-5 `A4A42951...` dan tidak boleh dipakai untuk acceptance baru.

Instalasi yang terdeteksi berada di `C:\Users\HP\AppData\Local\Lancar Dynamic Admin`, tetapi menggunakan application data aktif di `%APPDATA%\LancarDinamicAdmin` yang sudah berisi database, settings, logs, invoice, dan runtime WhatsApp. Sesuai batasan acceptance, instalasi tersebut tidak dipakai untuk aksi UI/data karena belum dibuktikan sebagai profil uji atau non-produksi.

Pemeriksaan environment acceptance pada host build hanya menemukan sesi console aktif user `HP`. Windows Sandbox/VM disposable tidak tersedia untuk dioperasikan dari sesi ini; query fitur Sandbox membutuhkan hak admin dan tidak menghasilkan target uji yang dapat digunakan. Karena itu installer `ED51ED27...` tidak dipasang ke profil aktif.

| Identitas host/evidence pre-install | Nilai |
| --- | --- |
| Windows host | Windows 10 Pro 22H2, build `19045.6466` |
| WebView2 Runtime | `148.0.3967.83` |
| Artifact yang diverifikasi | `D:\codex-build\lancar-tauri-phase3d-r3-final\Lancar Dynamic Admin_1.7.39_x64-setup.exe` |
| Evidence JSON ignored | `tmp\phase3d-r3-ed51-manual-acceptance\20260526-211243-pre_install.json` |
| App data yang diberikan ke collector | `tmp\phase3d-r3-ed51-disposable-appdata` (disposable; bukan `%APPDATA%\LancarDinamicAdmin`) |

| Validasi manual | Hasil sesi ini | Status |
| --- | --- | --- |
| Hash installer RC pada sesi historis | Rebuild menghasilkan `ED51ED2701559E789306E19D60ABECEEC7F2B0B100DB2491F633DEC660237E9B`; sekarang superseded oleh `A4A42951...` | Superseded |
| Tombol Edit Pasien | Regression guard source/build sebelumnya lulus; tidak dapat dinilai pada installed-app tanpa profil uji dan kontrol visual | `BLOCKED` |
| Dark mode global seluruh tab | Token/guard source sebelumnya lulus; tidak ada inspeksi installed-app interaktif | `BLOCKED` |
| Modal dark mode | Guard modal runtime sebelumnya lulus; tidak ada inspeksi visual installed-app | `BLOCKED` |
| Follow-up **Sudah Dihubungi** | Kontrak API otomatis sebelumnya lulus; persistensi lewat UI installed-app tidak dijalankan | `BLOCKED` |
| WhatsApp profile/login/kirim pesan | Keberhasilan manual hanya tercatat pada RC lama `46F2F88C...`; RC `ED51ED27...` belum diuji pada profil uji | `BLOCKED` |
| Analitik filter | Guard layout source sebelumnya lulus; resize/dark-mode installed-app belum dijalankan | `BLOCKED` |
| Orphan process setelah close | Snapshot baca-saja tidak menunjukkan `lancar-api`/`node.exe` saat pemeriksaan, tetapi bukan hasil close dari sesi acceptance terisolasi | `BLOCKED` |

Tidak ada screenshot kegagalan UI karena aplikasi installed tidak dibuka terhadap application data aktif dan sesi ini tidak menyediakan kontrol UI/WebView2 callable untuk menjalankan checklist secara aman.

Untuk membuka gate manual, gunakan hanya installer yang hash-nya persis `5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E` pada VM/profil Windows disposable, jalankan collector `pre-install`, selesaikan seluruh checklist UI/WhatsApp/Follow-up/Settings/mapping-terapis/dark-mode/close-app pada instalasi tersebut, lalu simpan evidence non-sensitif. Phase 3C tetap tidak boleh dimulai sebelum baris-baris di atas menjadi lulus.

## Riwayat Patch Phase 3D-R2: UI, QR, dan Mode Malam

Patch R2 menindaklanjuti regresi yang masih ditemukan setelah RC Phase 3D:

| Blocker | Perbaikan | File utama |
| --- | --- | --- |
| Tombol/status pembayaran menimpa icon dan teks pada kartu sempit | Quick action memakai flex wrap, gap, ukuran minimum fleksibel, wrapping teks, dan tinggi adaptif | `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |
| Badge terapis dan layanan tampil ganda | Jumlah hanya ditampilkan pada tab filter; tombol tambah dirapikan dan tetap responsif | `api/static/ts/therapists.ts`, `api/static/ts/services.ts`, `api/static/style.css` |
| Card/angka Analitik Klinik terpotong atau melebar sebelah | Grid final memakai `auto-fit/minmax`, konten angka dapat wrap, dan test menolak override grid fixed 4/5 kolom | `api/static/src/input.css`, `api/static/tailwind.css`, `tests/test_tauri_ui_regressions.py` |
| QR WhatsApp masih kosong | UI membaca payload QR nested dari proxy Python dan hanya merender data URL/URL gambar valid; raw QR tidak dianggap PNG | `api/static/ts/settings.ts`, `api/routes/whatsapp.py`, `tests/test_whatsapp_gateway.py` |
| Error QR tidak membantu diagnosa | State menunggu/error dibuat eksplisit; backend mencatat alasan aman tanpa token/session | `api/static/ts/settings.ts`, `api/routes/whatsapp.py` |
| Mode malam tidak konsisten pada halaman blocker | Token surface/text/border/status dark theme dan override card/input/tab/table/modal/toast/gateway ditambahkan | `api/static/style.css`, `tests/test_tauri_ui_regressions.py` |

Keamanan gateway tetap dipertahankan: UI mengambil QR melalui Python sidecar, API Node tetap memerlukan token internal dan menolak request browser ber-`Origin`/`Referer`, serta dashboard publik tidak menampilkan QR/session.

### Smoke Manual Phase 3D-R2 Yang Wajib Dilakukan Di VM

| ID | Skenario blocker | Verifikasi | Status |
| --- | --- | --- | --- |
| P3D-R2-UI-01 | Pembayaran | Kartu normal/sempit: Tunai Lunas, QRIS Manual, Belum Dibayar, Catat DP terbaca tanpa overlap | Pending VM/WebView2 |
| P3D-R2-UI-02 | Terapis/Layanan | Badge hanya pada tab filter; tombol tambah rapi saat resize | Pending VM/WebView2 |
| P3D-R2-UI-03 | Analitik | 7 Hari/30 Hari/6 Bulan/1 Tahun, nominal panjang dan resize tanpa truncate merusak informasi | Pending VM/WebView2 |
| P3D-R2-DARK-01 | Mode malam | Semua halaman utama, modal/dropdown/toast/table/input/tab serta QR tetap terbaca | Pending VM/WebView2 |
| P3D-R2-WA-01 | WhatsApp QR login | Start gateway, QR tampil via proxy, scan akun uji, connected, lalu stop | Pending VM/WebView2 + akun uji |
| P3D-R2-PROC-01 | Tutup aplikasi | Tidak ada `lancar-api`, `node.exe`, atau proses gateway residual | Gateway smoke lulus; close-window VM pending |

## Patch Phase 3D: UI / QR Login Blocker

Tiga blocker yang ditemukan pada RC sebelumnya telah ditambal dalam source dan asset terkompilasi:

| Blocker | Perbaikan | File utama |
| --- | --- | --- |
| Panel **Cari Pasien untuk Kunjungan** terbawa scroll | Kartu pencarian/form tidak lagi `sticky`; dropdown dibatasi pada wrapper dan ditutup saat input kehilangan fokus | `api/static/style.css`, `api/static/ts/patients.ts` |
| Teks pembayaran overlap di ukuran WebView2 | Sel dinamis dan tombol aksi memakai wrapping, `min-width: 0`, line-height aman, serta tidak lagi dibatasi tinggi/lebar teks sempit | `api/static/style.css`, `api/static/src/input.css` |
| QR login WhatsApp kosong | Renderer menerima QR string dari proxy Python; sidecar menunggu gateway API bertoken siap dan menolak gateway stale/tanpa ownership token | `api/static/ts/settings.ts`, `api/routes/whatsapp.py` |

Keamanan gateway tidak dilonggarkan: UI tetap memakai endpoint Python `/whatsapp/session/status` dan `/whatsapp/session/qr`, token internal tidak dikembalikan dalam payload UI, sedangkan API Node tetap menolak request browser ber-`Origin`/`Referer`.

### Smoke Manual Phase 3D Yang Wajib Dilakukan Di VM

| ID | Skenario blocker | Verifikasi | Status |
| --- | --- | --- | --- |
| P3D-UI-01 | Catat Kunjungan | Scroll, cari/clear/pilih pasien; panel dan empty state tidak menimpa form | Pending VM/WebView2 |
| P3D-UI-02 | Pembayaran | Uji nominal besar, metode/status/catatan panjang, invoice, resize window | Pending VM/WebView2 |
| P3D-WA-01 | WhatsApp QR login | Start gateway, QR tampil, scan akun uji, refresh menjadi connected, lalu stop | Pending VM/WebView2 + akun uji |
| P3D-PROC-01 | Tutup aplikasi | Setelah close tidak ada `lancar-api`, `node.exe`, atau proses gateway residual | Backend smoke lulus; close-window VM pending |

## Patch Phase 3

### External URL Controlled Opener

- Semua penggunaan UI untuk URL eksternal pembayaran, bantuan WhatsApp, dan dashboard gateway diarahkan ke endpoint backend `/support/open_external_url`.
- Output frontend terkompilasi sudah diaudit: tidak ditemukan `window.open(...)` maupun `target="_blank"`.
- Endpoint tetap dilindungi token aplikasi localhost dan melakukan validasi allowlist sebelum menyerahkan URL ke OS.
- Allowlist saat ini:

| Target | Keperluan |
| --- | --- |
| `https://app.sandbox.midtrans.com` | Link Snap Midtrans sandbox |
| `https://wa.me` | Bantuan WhatsApp |
| `http://127.0.0.1:3000` | Dashboard status gateway lokal |

Domain pembayaran produksi harus ditambahkan melalui review eksplisit sebelum environment produksi diaktifkan. Scheme seperti `javascript:` dan `file:`, URL ber-credential, port nonstandar, host lookalike, dan host lain ditolak.

### Shutdown dan Orphan Process

- Sidecar meminta gateway WhatsApp berhenti secara graceful menggunakan token internal.
- Gateway memiliki fallback kill process tree jika Node tidak berhenti dalam timeout.
- Shell Tauri sekarang juga memakai fallback `taskkill /T /F` tersembunyi pada Windows untuk sidecar. Patch ini diperlukan karena smoke test menemukan worker PyInstaller one-file dapat tertinggal bila hanya parent process yang dihentikan setelah graceful shutdown gagal.
- Sidecar dan Node dibangun/dijalankan tanpa console window.

### Security Localhost dan Gateway

- API gateway Node tidak lagi membuka CORS umum dan mewajibkan `X-Gateway-Token` untuk `/api/*`, kecuali endpoint shutdown yang memakai token shutdown terpisah.
- Request gateway API dengan `Origin` atau `Referer` browser ditolak walaupun membawa token.
- Halaman status gateway tidak lagi menampilkan QR/session detail; detail login hanya dilayani melalui aplikasi.
- Endpoint sidecar `/_desktop/shutdown` tetap menolak request ber-`Origin`/`Referer` dan memerlukan `X-Shutdown-Token`.
- HTML bisnis sekarang membawa CSP bertahap `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' http://127.0.0.1:*; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`, plus `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, dan `Referrer-Policy: no-referrer`.

### Packaging dan Logging

- `tools/stage-tauri-runtime.ps1` mengecualikan state runtime gateway: `data/`, `.node-persist/`, `.wwebjs_auth/`, `.wwebjs_cache/`, `sessions/`, `logs/`, cache/tmp, log/backup, dan file alternatif development `server.new*.js`.
- Runtime user tetap berada di `%APPDATA%\LancarDinamicAdmin\whatsapp_gateway`, bukan resource installer.
- Log diagnosa:

| Komponen | Lokasi log |
| --- | --- |
| Rust/Tauri shell | folder log aplikasi Tauri, `desktop_shell.log` |
| Python sidecar | `%APPDATA%\LancarDinamicAdmin\logs\desktop_sidecar.log` |
| Node/OpenWA gateway | `%APPDATA%\LancarDinamicAdmin\logs\whatsapp_gateway.log` |

Loading screen shell sekarang menunjukkan error startup sidecar dan lokasi log sidecar kepada user.

## Checklist Validasi Otomatis

Hasil terbaru pada Windows build host, 2026-05-29:

| Area | Bukti | Status |
| --- | --- | --- |
| TypeScript dan asset | `npm run typecheck`, `npm run build:assets` | Lulus |
| Guard UI dan keamanan Tauri yang diminta | `python -m unittest tests.test_tauri_ui_regressions tests.test_crm tests.test_whatsapp_gateway tests.test_tauri_openwa_lifecycle tests.test_tauri_sidecar tests.test_tauri_external_urls tests.test_tauri_localhost_security` | Lulus; 62 test, termasuk workspace Settings, capability UI, token/coverage dark mode, modal/DataTables/form, action-based stock, dan kontrak follow-up |
| Audit pembukaan URL langsung | `rg` pada output modules/templates | Lulus; 0 `window.open(...)` / `target="_blank"` |
| Terapis, kunjungan, dan Settings security | `python -m unittest tests.test_patients tests.test_therapist_services tests.test_settings_security` | Lulus; 41 test, termasuk mapping multi-layanan, update legacy preserve, mismatch backend, unmapped compatibility, layanan nonaktif, dan filtering secret Settings |
| Gateway installed-runtime/Tauri path Phase 3D-R3 | `python tools\smoke-tauri-whatsapp-runtime.py --runtime-dir "\\?\C:\...\runtime" --data-dir <disposable>` | Lulus; health `ok`, proxy `qr_ready`, QR data URL `true`, token exposed `false`, shutdown stopped `true` |
| Sidecar packaged dengan runtime arg Tauri | `lancar-api-x86_64-pc-windows-msvc.exe --runtime-dir "\\?\...\runtime"` pada port uji, lalu `/_desktop/shutdown` bertoken | Lulus; log runtime normal tanpa `\\?\`, exit `0` |
| Suite Python penuh (rerun 2026-05-29) | `python -m unittest discover -s tests -p "test_*.py"` | Lulus; 300 test. P0 revenue split fixed, `TestPaymentGatewayMock` isolated/sequential lulus, dan guard CSP final sudah kosong |
| Regression owner report/payment | `python -m unittest tests.test_p0_regressions`, `python -m unittest tests.test_core_business_flows tests.test_payment_gateway` | Lulus; revenue split tetap jasa di visit dan herbal di `HerbalTransaction` |
| Node syntax | `node --check openwa_server\server.js` | Lulus |
| Rust shell fallback | `cargo check --manifest-path src-tauri\Cargo.toml` | Lulus |
| Runtime staging | `npm run tauri:stage-runtime` selama build | Lulus |
| Exclusion state/dev gateway | Inspeksi `src-tauri\runtime\openwa_server` | Lulus; tidak ada folder state atau `server.new*.js` |
| Installer NSIS | `npm run tauri:build` | Lulus; artifact RC `5E40E6A0...` di atas dihasilkan |
| Console suppression | Inspeksi PE subsystem | Lulus; shell dan sidecar `WINDOWS_GUI` |
| Sidecar packaged | GET `/license`, shutdown bertoken, Origin negatif, log | Lulus; `200`, Origin `403`, log terbentuk, residual process `0` |
| Gateway staged | health bertoken, token/origin negatif, shutdown pada port uji terisolasi | Lulus; tanpa token `403`, browser Origin `403`, residual process `0` |
| Dashboard gateway exposure | Inspeksi respons status gateway staged | Lulus; QR/session detail tidak tampil |

Peringatan build `Browserslist: caniuse-lite is outdated` tidak menggagalkan build, tetapi perlu dibersihkan sebelum release final.

## Smoke Test WebView2 Interaktif

Validasi interaktif belum dapat dijalankan dari sesi ini karena tidak tersedia kontrol browser/WebView2 callable maupun Windows VM/profil uji yang aman. Checklist berikut wajib dieksekusi terhadap installer dengan SHA-256 RC di atas, bukan profil produksi:

| ID | Skenario | Hasil wajib | Status |
| --- | --- | --- | --- |
| WV-01 | Login/license flow | License valid membuka dashboard di shell Tauri | Belum diuji di VM |
| WV-02 | Dashboard utama | Navigasi utama berfungsi tanpa error localhost | Belum diuji di VM |
| WV-03 | External URL pembayaran/WA | Hanya URL allowlist dibuka melalui OS; target lain ditolak | Otomatis lulus, interaktif pending |
| WV-04 | Open folder export/log/backup | Explorer membuka folder aplikasi yang benar | Belum diuji di VM |
| WV-05 | Open invoice | PDF invoice uji terbuka dari application data | Belum diuji di VM |
| WV-06 | Print invoice | Print/viewer OS berjalan tanpa hang | Belum diuji di VM |
| WV-07 | Download/export | XLSX/JSON terbentuk dan dapat dibuka | Belum diuji di VM |
| WV-08 | WhatsApp gateway start/stop | Gateway berjalan dari UI dan tidak mematikan app utama saat gagal | Backend smoke lulus, UI pending |
| WV-09 | Close aplikasi | Tidak ada `lancar-api` atau `node.exe` orphan | Binary smoke lulus, close-window UI pending |

Untuk setiap baris VM, catat versi Windows/WebView2, path installer, SHA-256, screenshot bila gagal, PID sebelum/sesudah tutup aplikasi, dan lokasi file/log yang diverifikasi.

## Phase 3B VM Evidence Collector

Collector `tools\collect-tauri-phase3b-evidence.ps1` tetap dipakai untuk gate VM/profil uji. Collector ini tidak memasang atau menghapus aplikasi; fungsinya menangkap bukti pada titik validasi yang ditentukan. Script telah dipin ke RC Phase 4A-CSP R5 PDF resolver fix terbaru dan berhenti dengan error jika installer bukan SHA-256 `5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E`.

Evidence yang direkam:

- versi Windows, profil user VM, dan versi WebView2 Runtime dari registry;
- hash dan ukuran installer RC/installer lama;
- ukuran folder install serta application data dan sepuluh child directory terbesar;
- daftar proses kandidat Lancar/Node sebelum dan setelah close;
- keberadaan log `desktop_shell.log`, `desktop_sidecar.log`, dan `whatsapp_gateway.log`;
- shortcut dan uninstall entry yang berhubungan dengan Lancar;
- hash file fixture application data, tanpa membaca atau memasukkan state `whatsapp_gateway`, session, auth, cache, atau log.

Contoh eksekusi di VM:

```powershell
$rc = "C:\RC\Lancar Dynamic Admin_1.7.39_x64-setup.exe"
$old = "C:\RC\LancarDinamicAdmin_Setup_v1.7.39.exe"
$evidence = "C:\Phase3B\Evidence"
$appData = Join-Path $env:APPDATA "LancarDinamicAdmin"

.\tools\collect-tauri-phase3b-evidence.ps1 -Stage pre-install -InstallerPath $rc -OutputDir $evidence -AppDataPath $appData
# Install bersih RC dan selesaikan WV-01 sampai WV-09 secara interaktif.
.\tools\collect-tauri-phase3b-evidence.ps1 -Stage before-close -InstallerPath $rc -OutputDir $evidence -AppDataPath $appData
# Tutup aplikasi dari window Tauri.
.\tools\collect-tauri-phase3b-evidence.ps1 -Stage after-close -InstallerPath $rc -OutputDir $evidence -AppDataPath $appData

# Pada snapshot/revert VM terpisah: install versi lama dan isi fixture uji.
.\tools\collect-tauri-phase3b-evidence.ps1 -Stage pre-upgrade -InstallerPath $rc -LegacyInstallerPath $old -OutputDir $evidence -AppDataPath $appData
# Tutup app lama, install RC, lalu verifikasi fixture melalui UI.
.\tools\collect-tauri-phase3b-evidence.ps1 -Stage post-upgrade -InstallerPath $rc -LegacyInstallerPath $old -OutputDir $evidence -AppDataPath $appData
```

Validasi collector host untuk SHA-256 RC `0DAF92F4...` sebelumnya dijalankan dengan app-data/output disposable `.local\phase3d-r3-0daf92f-*`; collector menerima artifact dan menyimpan evidence `pre-install` di `.local\phase3d-r3-0daf92f-evidence\20260528-094703-pre_install.json`. RC `0DAF92F4...`, `FAF4482B...`, intermediate `7F8A2F...`, `07941B...`, `6DB3DB...`, `246FE3A4...`, `CD37BA0E...`, `A4A42951...`, `3DF683B8...`, `1BF27B0F...`, `21BF51CF...`, `8EFCD82B...`, `14A4B87E...`, `58BC12F9...`, `9290DA06...`, `A2B4631D...`, dan `A031B6A0...` sekarang superseded oleh `5E40E6A0...`. Hasil collector host historis hanya memvalidasi hash/evidence awal dan bukan pengganti clean install, smoke UI, atau upgrade pada VM.

## Upgrade Installer Lama ke Tauri

Installer lama tetap tersedia dan tidak dihapus:

| Installer lama | Ukuran | SHA-256 |
| --- | --- | --- |
| `dist\LancarDinamicAdmin_Setup_v1.7.39.exe` | 153.65 MiB | `88F6E5E2989344EFA0F4DC278D6F64AD8CADBEEF840F29C476208A7A0462BD8A` |

Upgrade belum dijalankan pada sesi ini karena instalasi ke profil aktif dapat mengubah data, shortcut, registry uninstall, dan state user. Jalankan hanya pada VM/profil uji:

1. Install Inno/PyInstaller lama dan isi fixture: lisensi uji aktif, data pasien/invoice, konfigurasi, export, dan session gateway uji.
2. Rekam hash file penting dalam `%APPDATA%\LancarDinamicAdmin`, install path, shortcut, uninstall entries, serta PID proses.
3. Tutup versi lama dan pastikan tidak ada leftover process sebelum pemasangan RC.
4. Install RC Tauri dengan SHA-256 yang tercatat di dokumen ini.
5. Buka aplikasi dan verifikasi license, dashboard, invoice, export, serta start/stop gateway dengan fixture lama.
6. Bandingkan data/hash, shortcut, uninstall entry, app path, app-data path, dan daftar proses setelah close.
7. Uji uninstall pada clone VM; user data tidak boleh hilang tanpa tindakan eksplisit.

| Gate upgrade | Status |
| --- | --- |
| Install bersih RC di profil uji | Belum diuji |
| Upgrade dari Inno/PyInstaller | Belum diuji |
| Preservasi data dan lisensi | Belum diuji |
| Konflik shortcut/uninstall/path | Belum diuji |
| Leftover process setelah upgrade | Belum diuji |

## Ukuran Install

| Komponen | Ukuran |
| --- | ---: |
| Installer lama v1.7.39 | 153.65 MiB |
| Installer Tauri RC Phase 3D-R3 | 74.42 MiB |
| Selisih installer | -79.22 MiB (-51.56%) |
| Staged Node runtime | 98.19 MiB |
| Staged OpenWA gateway/dependencies | 47.35 MiB |
| Sidecar packaged | 39.62 MiB |

Ukuran folder setelah instalasi belum diukur karena installer belum dijalankan pada VM. Kandidat optimasi terbesar bila diperlukan adalah runtime Node dan dependencies OpenWA.

## CSP Ketat Yang Masih Terblokir

Strict `script-src` belum aman diterapkan karena UI existing masih menghasilkan inline handler. Phase 4A-CSP mulai mengurangi permukaan ini secara incremental tanpa rewrite UI besar.

### Phase 4A-CSP: CSP Hardening Incremental (2026-05-28)

Status gate produksi tetap `BLOCKED`. Phase 3C dan cutover produksi belum boleh dijalankan sampai manual installed-app/WebView2/orphan-process/upgrade installer acceptance lulus pada VM/profil disposable.

Audit inline handler dilakukan pada `api/templates/index.html`, `api/templates/license.html`, `api/static/ts/**/*.ts`, `api/static/modules/**/*.js`, dan `api/static/**/*.html`. Baseline terbesar sebelum patch:

| File | Temuan sebelum | Temuan setelah |
| --- | --- | --- |
| `api/templates/index.html` | 1 executable inline bootstrap script; 1 JSON config script; external scripts | 0 executable inline script; JSON config tetap non-executable |
| `api/templates/license.html` | 1 executable inline bootstrap script; 1 JSON config script; external license script | 0 executable inline script; JSON config tetap non-executable |
| `api/static/modules/invoices.js` | `onclick=26`, `oninput=1` | 0 inline handler |
| `api/static/modules/settings.js` | `onclick=31`, `onsubmit=6`, `onchange=7`, `oninput=1` | 0 inline handler |

Perubahan yang sudah dipindahkan ke event delegation:

- Template bootstrap dipindahkan ke `api/static/ts/app_config.ts` dan output `api/static/modules/app_config.js`. Template hanya menyimpan config awal di `<script type="application/json" id="app-config">`.
- `api/static/ts/invoices.ts` memakai `data-invoice-action` untuk search, periode, pagination, open/reveal/print invoice, generate, void, status gateway, create payment link, dan pembayaran manual. Listener dijaga dengan `invoiceDelegationReady` supaya tidak dobel saat tab dirender ulang.
- `api/static/ts/settings.ts` memakai `data-settings-action` dan `data-settings-form-action` untuk kategori Settings, search, upload logo, lisensi, PIN admin, import/export, backup, demo data, discount/voucher, dan promo gratis. Listener dijaga dengan `settingsDelegationReady`.

Legacy inline handler yang masih tersisa setelah R1 dan menjadi allowlist sementara regression guard sebelum R2:

| File | Sisa inline handler |
| --- | --- |
| `analytics.js` | `onclick=1`, `oninput=1` |
| `audit.js` | `onclick=5` |
| `crm.js` | `onclick=9`, `onchange=2` |
| `help.js` | `onclick=2` |
| `herbals.js` | `onclick=21`, `onsubmit=3`, `onchange=2`, `oninput=4` |
| `inventory.js` | `onclick=13`, `onsubmit=3`, `onchange=2`, `oninput=2` |
| `modal.js` | `onclick=11`, `onchange=1` |
| `owner_report.js` | `onclick=3`, `onchange=2` |
| `patients.js` | `onclick=13`, `onsubmit=1`, `onchange=5`, `oninput=4`, `onfocus=1` |
| `services.js` | `onclick=13`, `onsubmit=2`, `onchange=2` |
| `therapists.js` | `onclick=11`, `onchange=1`, `oninput=1` |
| `whatsapp_gateway.js` | `onclick=3`, `onsubmit=1` |

Pada akhir R1, strict `script-src 'self'` belum bisa diaktifkan karena file legacy di atas masih menghasilkan inline event handler. CSP incremental yang aktif masih `frame-ancestors 'none'; base-uri 'self'; object-src 'none'`. Target R2 adalah mengurangi allowlist modul terbesar `herbals`, `inventory`, dan `patients`.

Regression guard baru: `tests/test_csp_inline_handlers.py` memindai `api/static/modules/*.js` dan `api/templates/*.html`, menolak inline handler baru, menolak executable inline script di template, dan memastikan delegation guard untuk `invoices`/`settings` tetap ada. Allowlist hanya untuk legacy count di tabel di atas dan harus turun pada patch berikutnya, tidak naik.

### Phase 4A-CSP R2: Herbal, Inventory, dan Patients (2026-05-29)

Scope R2 dibatasi ke `api/static/ts/herbals.ts`, `api/static/ts/inventory.ts`, dan `api/static/ts/patients.ts` plus output build-nya. Tidak ada perubahan logic payment, invoice calculation, database, license validation, CRM/follow-up, WhatsApp gateway, atau supervisor.

Temuan inline handler pada tiga modul target:

| File output | Sebelum R2 | Setelah R2 |
| --- | --- | --- |
| `api/static/modules/herbals.js` | `onclick=21`, `onsubmit=3`, `onchange=2`, `oninput=4` | 0 inline handler |
| `api/static/modules/inventory.js` | `onclick=13`, `onsubmit=3`, `onchange=2`, `oninput=2` | 0 inline handler |
| `api/static/modules/patients.js` | `onclick=13`, `onsubmit=1`, `onchange=5`, `oninput=4`, `onfocus=1` | 0 inline handler |

Perubahan R2 yang sudah dipindahkan ke event delegation:

- `api/static/ts/herbals.ts` memakai `data-herbal-action` dan `data-herbal-form-action` untuk modal tambah, jual, koreksi stok, retur, picker produk, pagination, close modal, submit form, dan aksi edit/delete. Tombol row hanya membawa `data-id`; nama/unit/stok diambil dari cache katalog.
- `api/static/ts/inventory.ts` memakai `data-inventory-action` dan `data-inventory-form-action` untuk modal tambah/koreksi, picker item, pagination, close modal, submit form, dan aksi edit/delete. Tombol row hanya membawa `data-id`; nama/unit/stok diambil dari cache katalog.
- `api/static/ts/patients.ts` memakai `data-patient-action` dan `data-patient-form-action` untuk tambah/edit/riwayat pasien, pencarian pasien Catat Kunjungan, clear/focus search, perubahan therapist/service/herbal/payment, input harga/qty, tombol pembayaran cepat, dan validasi submit kunjungan. Listener dijaga dengan `patientsDelegationReady`.

Modul yang sudah 0 inline handler setelah R2: `invoices.js`, `settings.js`, `herbals.js`, `inventory.js`, dan `patients.js`. Template `api/templates/index.html` dan `api/templates/license.html` tetap 0 executable inline script; config awal hanya melalui JSON script non-executable.

Legacy inline handler yang masih tersisa di output build dan menjadi allowlist sementara regression guard setelah R2:

| File | Sisa inline handler |
| --- | --- |
| `analytics.js` | `onclick=1`, `oninput=1` |
| `audit.js` | `onclick=5` |
| `crm.js` | `onclick=9`, `onchange=2` |
| `help.js` | `onclick=2` |
| `modal.js` | `onclick=11`, `onchange=1` |
| `owner_report.js` | `onclick=3`, `onchange=2` |
| `services.js` | `onclick=13`, `onsubmit=2`, `onchange=2` |
| `therapists.js` | `onclick=11`, `onchange=1`, `oninput=1` |
| `whatsapp_gateway.js` | `onclick=3`, `onsubmit=1` |

Strict `script-src 'self'` belum diaktifkan karena file legacy di atas masih menghasilkan inline event handler. CSP incremental yang aktif tetap `frame-ancestors 'none'; base-uri 'self'; object-src 'none'`; target berikutnya adalah `services`, `modal`, `therapists`, dan `crm` sebelum menaikkan CSP ke `default-src 'self'` lalu `script-src 'self'`.

Regression guard `tests/test_csp_inline_handlers.py` diperbarui agar `herbals.js`, `inventory.js`, dan `patients.js` keluar dari allowlist. Guard sekarang juga memastikan `herbalDelegationReady`, `inventoryDelegationReady`, dan `patientsDelegationReady` tetap ada sehingga listener tidak dipasang berulang saat tab dirender ulang.

Verifikasi sesi ini:

- `npm run build:assets` lulus setelah output JS/CSS diregenerasi.
- `python -m unittest tests.test_csp_inline_handlers` lulus.
- `npm run typecheck` lulus.
- `python -m unittest tests.test_tauri_ui_regressions tests.test_tauri_external_urls tests.test_tauri_localhost_security tests.test_csp_inline_handlers` lulus.
- `python -m unittest discover -s tests -p "test_*.py"` lulus.
- `cargo check --manifest-path src-tauri/Cargo.toml` lulus.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,050,104` byte / 74.43 MiB, SHA-256 `21BF51CF1EEA664935D694CC0C6001681CAB0CB7FF54E214BE177FAC004756D7`.

Setelah R2, collector `tools\collect-tauri-phase3b-evidence.ps1` sempat dipin ke SHA-256 `21BF51CF1EEA664935D694CC0C6001681CAB0CB7FF54E214BE177FAC004756D7`. RC `3DF683B8...` dan `1BF27B0F...` superseded pada titik itu; RC `21BF51CF...` kemudian superseded oleh R3.

### Phase 4A-CSP R3: Services, Therapists, dan Modal (2026-05-29)

Scope R3 dibatasi ke `api/static/ts/services.ts`, `api/static/ts/therapists.ts`, dan `api/static/ts/modal.ts` plus output build-nya. Tidak ada perubahan logic payment, invoice calculation, database, license validation, CRM/follow-up, WhatsApp gateway, security gateway, atau supervisor.

Temuan inline handler pada tiga modul target:

| File output | Sebelum R3 | Setelah R3 |
| --- | --- | --- |
| `api/static/modules/services.js` | `onclick=13`, `onsubmit=2`, `onchange=2` | 0 inline handler |
| `api/static/modules/therapists.js` | `onclick=11`, `onchange=1`, `oninput=1` | 0 inline handler |
| `api/static/modules/modal.js` | `onclick=11`, `onchange=1` | 0 inline handler |

Perubahan R3 yang sudah dipindahkan ke event delegation:

- `api/static/ts/services.ts` memakai `data-service-action`, `data-service-form-action`, `data-service-id`, dan state `window._serviceMap` untuk filter Aktif/Nonaktif/Semua, tambah/edit layanan, aktif/nonaktif, hapus, picker satuan, mode harga, serta editor pemakaian inventaris otomatis. Nama/harga/kategori tidak lagi disisipkan ke JavaScript string inline.
- `api/static/ts/therapists.ts` memakai `data-therapist-action`, `data-therapist-id`, dan state `window._therapistMap` untuk filter, tambah/edit, aktif/nonaktif, hapus, modal mapping layanan, searchable checklist, dan sinkronisasi pilihan layanan. Nama/kontak/catatan tidak lagi disisipkan ke JavaScript string inline.
- `api/static/ts/modal.ts` memakai `data-modal-action` dan `ensureRuntimeModalEventDelegation()` untuk overlay close, tombol close/cancel/submit, delete pasien, delete kunjungan, refresh pilihan terapis full-edit, generic modal, dan edit modal runtime. Listener dijaga oleh `runtimeModalDelegationReady` agar tidak dobel saat modal dibuka berulang.

Modul yang sudah 0 inline handler setelah R3: `invoices.js`, `settings.js`, `herbals.js`, `inventory.js`, `patients.js`, `services.js`, `therapists.js`, dan `modal.js`. Template `api/templates/index.html` dan `api/templates/license.html` tetap 0 executable inline script; config awal hanya melalui JSON script non-executable.

Legacy inline handler yang masih tersisa di output build dan menjadi allowlist sementara regression guard setelah R3:

| File | Sisa inline handler |
| --- | --- |
| `analytics.js` | `onclick=1`, `oninput=1` |
| `audit.js` | `onclick=5` |
| `crm.js` | `onclick=9`, `onchange=2` |
| `help.js` | `onclick=2` |
| `owner_report.js` | `onclick=3`, `onchange=2` |
| `whatsapp_gateway.js` | `onclick=3`, `onsubmit=1` |

Strict `script-src 'self'` belum diaktifkan karena file legacy di atas masih menghasilkan inline event handler. CSP incremental yang aktif tetap `frame-ancestors 'none'; base-uri 'self'; object-src 'none'`; target berikutnya adalah `crm`, `audit`, `owner_report`, `whatsapp_gateway`, `help`, dan `analytics` sebelum menaikkan CSP ke `default-src 'self'` lalu `script-src 'self'`.

Regression guard `tests/test_csp_inline_handlers.py` diperbarui agar `services.js`, `therapists.js`, dan `modal.js` keluar dari allowlist. Guard sekarang juga memastikan `serviceDelegationReady`, `therapistDelegationReady`, dan `runtimeModalDelegationReady` tetap ada.

Verifikasi R3:

- `npm run typecheck` lulus.
- `npm run build:assets` lulus setelah output JS/CSS diregenerasi.
- `python -m unittest tests.test_csp_inline_handlers tests.test_tauri_ui_regressions` lulus; 27 test.
- `python -m unittest discover -s tests -p "test_*.py"` lulus; 300 test.
- `cargo check --manifest-path src-tauri/Cargo.toml` lulus.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,059,236` byte / 74.44 MiB, SHA-256 `8EFCD82B2C5913DAB51367989D017BBD915B84D073FA3648361702B8B0E36244`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sudah dipin ke SHA-256 `8EFCD82B2C5913DAB51367989D017BBD915B84D073FA3648361702B8B0E36244`. RC `21BF51CF...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-CSP R4: CRM, WhatsApp Gateway, Analytics, dan Help (2026-05-29)

Scope R4 dibatasi ke `api/static/ts/crm.ts`, `api/static/ts/whatsapp_gateway.ts`, `api/static/ts/analytics.ts`, dan `api/static/ts/help.ts` plus output build-nya. `audit.ts` dan `owner_report.ts` sengaja belum disentuh. Tidak ada perubahan logic payment, invoice calculation, database, license validation, CRM backend, WhatsApp gateway Node/OpenWA, token gateway, security gateway, atau supervisor.

Temuan inline handler pada empat modul target:

| File output | Sebelum R4 | Setelah R4 |
| --- | --- | --- |
| `api/static/modules/crm.js` | `onclick=9`, `onchange=2` | 0 inline handler |
| `api/static/modules/whatsapp_gateway.js` | `onclick=3`, `onsubmit=1` | 0 inline handler |
| `api/static/modules/analytics.js` | `onclick=1`, `oninput=1` | 0 inline handler |
| `api/static/modules/help.js` | `onclick=2` | 0 inline handler |

Perubahan R4 yang sudah dipindahkan ke event delegation:

- `api/static/ts/crm.ts` memakai `data-crm-action` dan `data-crm-form-action` untuk filter follow-up, refresh list, buka detail follow-up, simpan tag/izin kontak, voucher follow-up, generate/copy/kirim pesan WhatsApp, **Sudah Dihubungi**, hasil follow-up, dan submit modal detail. UI tetap memakai endpoint/proxy Python yang sudah ada dan tidak menampilkan token/session/stack trace.
- `api/static/ts/whatsapp_gateway.ts` memakai `data-whatsapp-action` dan `data-whatsapp-form-action` untuk refresh status, proses antrean follow-up, logout, dan kirim pesan uji. Flow tetap lewat fungsi proxy Python existing; tidak ada akses langsung browser ke Node/OpenWA atau token gateway.
- `api/static/ts/analytics.ts` memakai `data-analytics-action` untuk filter periode 7 Hari, 30 Hari, 6 Bulan, 1 Tahun, Semua, serta preview laba rugi. Perhitungan laporan tidak diubah.
- `api/static/ts/help.ts` memakai `data-help-action` untuk tautan bantuan WhatsApp dan buka folder support. Tautan eksternal tetap melalui `openDesktopExternalUrl(..., 'whatsapp_help')`; tidak memakai `window.open` atau `target="_blank"`.

Modul yang sudah 0 inline handler setelah R4: `invoices.js`, `settings.js`, `herbals.js`, `inventory.js`, `patients.js`, `services.js`, `therapists.js`, `modal.js`, `crm.js`, `whatsapp_gateway.js`, `analytics.js`, dan `help.js`. Template `api/templates/index.html` dan `api/templates/license.html` tetap 0 executable inline script; config awal hanya melalui JSON script non-executable.

Legacy inline handler yang masih tersisa di output build dan menjadi allowlist sementara regression guard setelah R4:

| File | Sisa inline handler |
| --- | --- |
| `audit.js` | `onclick=5` |
| `owner_report.js` | `onclick=3`, `onchange=2` |

Strict `script-src 'self'` belum diaktifkan karena `audit.js` dan `owner_report.js` masih menghasilkan inline event handler. CSP incremental yang aktif tetap `frame-ancestors 'none'; base-uri 'self'; object-src 'none'`; target berikutnya adalah dua modul legacy terakhir sebelum menaikkan CSP ke `default-src 'self'` lalu `script-src 'self'`.

Regression guard `tests/test_csp_inline_handlers.py` diperbarui agar `crm.js`, `whatsapp_gateway.js`, `analytics.js`, dan `help.js` keluar dari allowlist. Allowlist sementara sekarang hanya `audit.js` dan `owner_report.js`. Guard juga memastikan `crmDelegationReady`, `whatsappGatewayDelegationReady`, `analyticsDelegationReady`, dan `helpDelegationReady` tetap ada.

Verifikasi R4:

- `npm run typecheck` lulus.
- `npm run build:assets` lulus setelah output JS/CSS diregenerasi.
- `python -m unittest tests.test_csp_inline_handlers tests.test_tauri_ui_regressions tests.test_whatsapp_gateway tests.test_crm` lulus; 45 test.
- `python -m unittest discover -s tests -p "test_*.py"` lulus; 300 test.
- `cargo check --manifest-path src-tauri/Cargo.toml` lulus.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,061,309` byte / 74.45 MiB, SHA-256 `14A4B87ED3B5BCE434E5B30AC32FE98E5666F6F6CD5F4DF0A26F67FC35274F1E`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sudah dipin ke SHA-256 `14A4B87ED3B5BCE434E5B30AC32FE98E5666F6F6CD5F4DF0A26F67FC35274F1E`. RC `8EFCD82B...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru.

### Phase 4A-CSP R5 / Final Inline Handler Cleanup (2026-05-29)

Scope R5 dibatasi ke `api/static/ts/audit.ts`, `api/static/ts/owner_report.ts`, output build JS terkait, CSP header bertahap, dan regression guard. R4 tetap khusus `crm`, `whatsapp_gateway`, `analytics`, dan `help`; audit/owner report dicatat sebagai R5/Final.

Temuan inline handler dua modul terakhir:

| File output | Sebelum R5 | Setelah R5 |
| --- | --- | --- |
| `api/static/modules/audit.js` | `onclick=5` | 0 inline handler |
| `api/static/modules/owner_report.js` | `onclick=3`, `onchange=2` | 0 inline handler |

Semua modul `api/static/modules/*.js` sekarang 0 untuk pola `onclick=`, `onsubmit=`, `onchange=`, `oninput=`, `onkeydown=`, `onkeyup=`, `onblur=`, `onfocus=`, dan `href="javascript:`. Template `api/templates/index.html` dan `api/templates/license.html` tetap tidak memiliki executable inline script; `<script type="application/json" id="app-config">` adalah config JSON non-executable dan tetap diperbolehkan.

Regression guard `tests/test_csp_inline_handlers.py` sekarang memakai allowlist legacy kosong (`LEGACY_INLINE_HANDLER_ALLOWLIST = {}`). Guard juga memastikan `auditDelegationReady`/`ensureAuditEventDelegation` dan `ownerReportDelegationReady`/`ensureOwnerReportEventDelegation` tetap ada.

Tombol aksi Audit/Owner Report hanya menyimpan action/id/index/key di `data-*`; detail audit tetap diambil dari cache `window._audit_rows`, sehingga tidak ada data mentah yang disisipkan ke string handler JavaScript.

CSP final yang dievaluasi dan diaktifkan bertahap pada HTML FastAPI:

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self' data:;
connect-src 'self' http://127.0.0.1:*;
object-src 'none';
base-uri 'self';
frame-ancestors 'none'
```

`script-src 'self'` aktif tanpa `unsafe-inline`. `style-src 'self'` murni belum bisa dipakai karena `license.html`, `app.js`, `modal.js`, `settings.js`, `analytics.js`, `herbals.js`, dan beberapa modul runtime lain masih menghasilkan inline `<style>`/`style=` untuk layout modal, wizard, chart, dan status. Pengecualian `style-src 'unsafe-inline'` bersifat sementara untuk kompatibilitas UI, bukan solusi permanen untuk script. `img-src` mengizinkan `data:`/`blob:` untuk QR/logo/download object URL, `font-src` mengizinkan font lokal/data, dan `connect-src` mengizinkan origin aplikasi serta localhost sidecar `127.0.0.1:*`.

Verifikasi R5/Final:

- `npm run typecheck` lulus.
- `npm run build:assets` lulus setelah output JS/CSS diregenerasi.
- `python tests\test_csp_inline_handlers.py` lulus; `pytest` tidak tersedia di environment ini, sehingga CSP guard dijalankan via direct Python/unittest.
- `python -m unittest tests.test_csp_inline_handlers tests.test_tauri_ui_regressions` lulus; 27 test.
- `python -m unittest tests.test_csp_inline_handlers tests.test_tauri_ui_regressions tests.test_tauri_localhost_security` lulus; 28 test setelah CSP header diperbarui.
- `python -m unittest discover -s tests -p "test_*.py"` lulus; 300 test.
- `cargo check --manifest-path src-tauri\Cargo.toml` lulus.
- Audit `rg -n "onclick=|onsubmit=|onchange=|oninput=|onkeydown=|onkeyup=|onblur=|onfocus=|href=\"javascript:" api\static\modules api\templates` tidak menemukan sisa inline handler.
- In-app browser/WebView smoke tidak dapat dijalankan dari sesi ini karena bridge Node REPL untuk plugin Browser tidak tersedia; manual installed-app/WebView2 tetap gate wajib.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,056,505` byte / 74.44 MiB, SHA-256 `58BC12F9DEC639C489F563AF080D5809D6EBC965CDE989062FD82A8C04133051`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` saat itu dipin ke SHA-256 `58BC12F9DEC639C489F563AF080D5809D6EBC965CDE989062FD82A8C04133051`. Validasi collector `pre-install` berhasil menulis evidence disposable `C:\tmp\phase4a-csp-final-evidence\20260529-113921-pre_install.json`. RC `14A4B87E...` superseded pada titik itu.

Rebuild R5 dilakukan ulang karena production asset `api/static/modules/audit.js` dan `api/static/modules/owner_report.js` berubah setelah cleanup dataset Audit/Owner Report. RC aktif baru:

- `npm run typecheck` lulus.
- `npm run build:assets` lulus.
- `python tests\test_csp_inline_handlers.py` lulus; 3 test.
- `python -m unittest tests.test_csp_inline_handlers tests.test_tauri_ui_regressions tests.test_tauri_localhost_security` lulus; 28 test.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,053,104` byte / 74.44 MiB, SHA-256 `9290DA06B6BCE543B69537AC485D89B9AF9B12A3F3AC34FB98C9A7DCDDEDF2F3`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sekarang dipin ke SHA-256 `9290DA06B6BCE543B69537AC485D89B9AF9B12A3F3AC34FB98C9A7DCDDEDF2F3` dan akan menolak RC lama `58BC12F9DEC639C489F563AF080D5809D6EBC965CDE989062FD82A8C04133051`. Validasi collector `pre-install` terhadap RC baru berhasil menulis evidence disposable `C:\tmp\phase4a-csp-r5-rebuild-evidence\20260529-142657-pre_install.json`. RC `58BC12F9...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru. Status produksi tetap `BLOCKED`; rebuild dan test otomatis bukan pengganti manual installed-app/WebView2, orphan process, WhatsApp UI smoke, dan upgrade installer acceptance.

Patch ACL native invoice ditambahkan setelah installed-app masih menolak klik **Lihat PDF**, **Print**, dan **Lihat lokasi** dengan pesan `Command native_open_invoice_file not allowed by ACL`. Root cause: UI berpindah dari bootstrap `index.html` ke backend lokal `http://127.0.0.1:<port>`, sementara capability Tauri belum memberikan izin command ke origin loopback tersebut. `src-tauri/capabilities/default.json` sekarang menambahkan `remote.urls = ["http://127.0.0.1:*"]` saja, tetap terbatas ke loopback dan tidak mengizinkan `localhost` maupun origin remote lain.

Verifikasi ACL fix:

- `python -m unittest tests.test_tauri_ui_regressions tests.test_tauri_localhost_security` lulus; 26 test.
- `cargo check --manifest-path src-tauri\Cargo.toml` lulus.
- `npm run typecheck` lulus.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,103,333` byte / 74.49 MiB, SHA-256 `A2B4631DEB26BCB2FC2CDCC713E45B4C7640D919F002586E7B357A351AF8CAD2`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sekarang dipin ke SHA-256 `A2B4631DEB26BCB2FC2CDCC713E45B4C7640D919F002586E7B357A351AF8CAD2` dan akan menolak RC lama `9290DA06B6BCE543B69537AC485D89B9AF9B12A3F3AC34FB98C9A7DCDDEDF2F3`. Validasi collector `pre-install` terhadap RC baru berhasil menulis evidence disposable `C:\tmp\phase4a-csp-r5-aclfix-evidence\20260529-154146-pre_install.json`. RC `9290DA06...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru. Status produksi tetap `BLOCKED`; fix ACL dan rebuild bukan pengganti manual installed-app/WebView2, orphan process, WhatsApp UI smoke, dan upgrade installer acceptance.

Patch mapping Terapis-Layanan ditambahkan setelah installed-app menunjukkan checklist layanan tidak bisa dipilih dan state terpilih tidak terlihat jelas. Root cause: click delegation Terapis memanggil `preventDefault()` pada checkbox `capability-sync`, sehingga browser tidak pernah mencentang input saat diklik langsung. Handler sekarang membiarkan checkbox menjalankan default click/change, lalu `syncTherapistCapabilitySelection()` mengisi hidden `service_ids` dan menandai opsi dengan class `is-selected`. UI checklist juga memakai indikator centang visual `therapist-capability-check`.

Verifikasi mapping fix:

- `npm run typecheck` lulus.
- `npm run build:assets` lulus.
- `python -m unittest tests.test_tauri_ui_regressions tests.test_therapist_services` lulus; 31 test.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,109,504` byte / 74.49 MiB, SHA-256 `A031B6A0438D3D25C07E4BD52EAE83196E3D9A9E8F52B5C0AC7B5B64D1EE26E3`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sekarang dipin ke SHA-256 `A031B6A0438D3D25C07E4BD52EAE83196E3D9A9E8F52B5C0AC7B5B64D1EE26E3` dan akan menolak RC lama `A2B4631DEB26BCB2FC2CDCC713E45B4C7640D919F002586E7B357A351AF8CAD2`. Validasi collector `pre-install` terhadap RC baru berhasil menulis evidence disposable `C:\tmp\phase3d-r3-mappingfix-evidence\20260529-161328-pre_install.json`. RC `A2B4631D...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru. Status produksi tetap `BLOCKED`; fix mapping dan rebuild bukan pengganti manual installed-app/WebView2, orphan process, WhatsApp UI smoke, dan upgrade installer acceptance.

Patch native PDF resolver ditambahkan setelah installed-app masih menampilkan `File tidak ditemukan` saat klik **Lihat**, **Lokasi**, atau **Print** pada invoice yang sudah punya path. Root cause: backend menerima path tersimpan seperti `invoices\nama.pdf` relatif terhadap app data, tetapi resolver Rust native menjalankannya dari root `app_data\invoices`, sehingga path menjadi `app_data\invoices\invoices\nama.pdf`. Resolver native sekarang menerima prefix root tersimpan (`invoices/...` atau `exports/...`) dengan cara menghapus prefix hanya ketika sedang memvalidasi root yang sama; traversal, path absolut di luar root, UNC/device path, komponen sensitif, dan ekstensi selain `.pdf` tetap ditolak.

Verifikasi PDF resolver fix:

- `cargo test --manifest-path src-tauri\Cargo.toml invoice_file_resolver_accepts_pdf_in_allowed_roots` lulus.
- `cargo check --manifest-path src-tauri\Cargo.toml` lulus.
- `python -m unittest tests.test_tauri_ui_regressions tests.test_tauri_localhost_security` lulus; 26 test.
- `npm run tauri:build` lulus dan menghasilkan installer `src-tauri\target\release\bundle\nsis\Lancar Dynamic Admin_1.7.39_x64-setup.exe`, ukuran `78,097,966` byte / 74.48 MiB, SHA-256 `5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E`.

Collector `tools\collect-tauri-phase3b-evidence.ps1` sekarang dipin ke SHA-256 `5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E` dan akan menolak RC lama `A031B6A0438D3D25C07E4BD52EAE83196E3D9A9E8F52B5C0AC7B5B64D1EE26E3`. Validasi collector `pre-install` terhadap RC baru berhasil menulis evidence disposable `C:\tmp\phase3d-r3-pdfresolver-evidence\20260529-163356-pre_install.json`. RC `A031B6A0...` sekarang superseded dan tidak boleh dipakai untuk acceptance baru. Status produksi tetap `BLOCKED`; fix resolver PDF dan rebuild bukan pengganti manual installed-app/WebView2, orphan process, WhatsApp UI smoke, dan upgrade installer acceptance.

## Phase 4 Planning: Rust Native Optimization & Backend Reduction

Phase 4 belum boleh mengubah gate Phase 3D-R3. Phase 3C, cutover produksi, dan migrasi logic bisnis besar tetap ditahan sampai manual installed-app acceptance, WebView2 smoke, orphan-process check, dan upgrade installer lulus pada VM/profil disposable. Tujuan Phase 4 adalah mengecilkan permukaan backend desktop secara bertahap, bukan rewrite Python.

### Keputusan Arsitektur

| Komponen | Keputusan Phase 4 | Alasan |
| --- | --- | --- |
| TypeScript UI | Tetap di TypeScript/static assets | UI sudah terpisah dari shell dan punya guard typecheck/build. |
| Rust/Tauri shell | Fokus native desktop helper dan process supervisor | Rust paling cocok untuk operasi OS, lifecycle proses, path/log native, dan permission Tauri. |
| Python/FastAPI | Tetap sebagai backend bisnis | Database, transaksi, laporan, invoice calculation, license, payment, dan CRM masih risk tinggi untuk dipindah. |
| Node/OpenWA | Tetap sebagai WhatsApp gateway | OpenWA bergantung ekosistem Node/Chromium; jangan ubah flow yang sudah berjalan. |
| PySide6/Qt legacy | Kandidat legacy removal dari distribusi Tauri | `tools\build-tauri-sidecar.ps1` sudah `--exclude-module PySide6`; dependency ini tidak boleh masuk bundle Tauri. |

### Audit Kandidat Migrasi Rust

| Area | Status target | Catatan |
| --- | --- | --- |
| Rendering UI, state UI, form, table, modal | Tetap TypeScript | Jangan pindah ke Rust; cukup panggil Tauri command untuk native helper. |
| `Database.add_visit`, transaksi herbal, laporan owner, payment, license, CRM/follow-up | Tetap Python | High-risk bisnis; baru dievaluasi setelah Phase 4 stabil dan gate produksi selesai. |
| Node/OpenWA session, QR, send message, queue delivery | Tetap Node/OpenWA + Python proxy | Jangan ubah token/session flow; Rust hanya boleh supervise proses bila sudah dirancang. |
| Open folder, reveal file, open PDF/invoice, open external URL allowlist, print PDF fallback | Kandidat Rust command Phase 4A | Saat ini masih ada helper Python di `/support/open_folder`, `/support/open_external_url`, `/invoices/open_invoice`, `/invoices/print_invoice`. |
| App data path, log path, config path, version/metadata, WebView2/runtime diagnostics | Kandidat Rust command Phase 4A/4D | Aman karena read-only/OS metadata; tetap jaga path allowlist. |
| Start/stop Python sidecar, start/stop Node/OpenWA, readiness/health, shutdown, kill tree | Kandidat Rust supervisor Phase 4B | Lifecycle desktop lebih tepat di shell daripada route Python. Python tetap dapat expose health/business API. |
| Export/download helper, open generated export folder | Kandidat Rust helper | Generate file tetap Python bila data bisnis; open/reveal/download UX bisa Rust. |
| Shortcut/uninstall/install diagnostics | Kandidat Rust diagnostics | Read-only evidence helper; jangan mengubah installer compatibility. |
| Legacy PySide6 windows/dialogs, Qt launcher, native widget archive | Kandidat hapus/arsip setelah audit | Jangan hapus sebelum memastikan tidak ada import aktif di entrypoint Tauri/backend. |

### Phase 4A Native Helper Audit

Status 2026-05-28: audit/desain saja. Tidak ada perubahan production code, route bisnis, database, payment, license, CRM, atau WhatsApp gateway. Rust/Tauri saat ini sudah mengelola start/stop Python sidecar (`start_backend`, shutdown token, log `desktop_shell.log`, dan fallback kill process tree). Helper native lain masih lewat endpoint Python atau browser UI.

| Helper native | Pemilik saat ini | Implementasi saat ini | Klasifikasi | Keputusan Phase 4A |
| --- | --- | --- | --- | --- |
| Start Python sidecar | Rust/Tauri | `src-tauri/src/main.rs` memilih port, menjalankan sidecar, menunggu readiness | Sudah di Rust/Tauri | Jangan ubah di 4A; hardening lanjut masuk 4B. |
| Stop Python sidecar / kill tree | Rust/Tauri | Shutdown endpoint bertoken, wait, lalu `taskkill /T /F` di Windows | Sudah di Rust/Tauri | Jangan ubah di 4A kecuali test/read-only diagnostics. |
| Open folder exports/data/logs | Python backend | `/support/open_folder` -> `helpers.support_helper.open_local_folder` | Aman dipindah ke Rust | Prioritas awal; command Rust harus allowlist `app_data`, `exports`, `logs`, `backups`. |
| Reveal file | Belum konsisten/tersebar | Belum ada helper Rust standar | Aman dipindah ke Rust | Tambah sebagai mode `reveal`, khusus file di root allowlist. |
| Open invoice/PDF | Python backend | `/open_invoice` -> `_resolve_invoice_path` + OS opener | Aman dipindah ke Rust | Pindah setelah allowlist path invoice/export identik atau lebih ketat dari Python. |
| Print invoice/PDF | Python backend | `/print_invoice`, Windows optional `win32api/win32print`, fallback open viewer | Aman tetapi lebih berisiko | Implementasi setelah open/reveal stabil; fallback wajib membuka viewer, bukan silent success. |
| Export/save file generation | Python backend + browser | `/export/save`, `/reports/export_excel`, blob download di UI | Jangan pindah dulu | Data generation tetap Python; hanya open/reveal folder/file hasil export yang boleh Rust. |
| Open external URL | Python backend | `/support/open_external_url` dengan validasi URL | Aman dipindah ke Rust | Command Rust harus allowlist scheme/domain dan menolak token/localhost arbitrary. |
| App data/log/config path | Python support route | `/support/app_info` dari `helpers.support_helper` | Aman dipindah ke Rust | Read-only command; jangan expose credential, auth token, atau session file content. |
| Diagnostics path | Python support + evidence script | App info/log path sebagian di Python, evidence di PowerShell | Aman dipindah bertahap | Rust boleh expose metadata non-rahasia: path, exists, size, modified time. |
| Process status | Rust untuk Python sidecar, Python untuk OpenWA | Rust menyimpan sidecar PID; `api/routes/whatsapp.py` menyimpan OpenWA PID/state | Campuran | 4A hanya read-only; lifecycle OpenWA tetap tidak disentuh sampai 4B. |
| WebView2/runtime check | Manual/evidence script | Collector dan checklist manual | Kandidat diagnostics Rust | Read-only diagnostics; tidak mengubah installer/runtime behavior. |
| WhatsApp gateway lifecycle | Python backend + Node/OpenWA | `api/routes/whatsapp.py` start/stop/readiness/token/session | Jangan dipindah dulu | Phase 4B desain supervisor; 4A tidak menyentuh flow WhatsApp. |

### Desain Command Rust Phase 4A

Command berikut adalah proposal kontrak. Implementasi harus dimulai dari read-only atau helper yang paling kecil, dengan fallback Python hanya selama transisi.

| Command | Input payload | Output payload | Permission/capability | Error, logging, fallback |
| --- | --- | --- | --- | --- |
| `native_get_paths` | `{ "kinds": ["app_data", "exports", "logs", "config", "invoices"] }` | `{ "paths": [{"kind": "...", "path": "...", "exists": true}] }` | Custom Tauri command; tidak perlu shell/fs broad permission | Error `unsupported path kind`; log kind saja, bukan full secret content. |
| `native_open_path` | `{ "kind": "exports", "path": null, "mode": "open" }` atau `{ "path": "...", "mode": "reveal" }` | `{ "status": "opened", "normalized_path": "..." }` | Custom command; jika memakai opener plugin, scope root allowlist | Error `path outside allowed roots`, `path does not exist`, `unsupported open mode`; fallback ke endpoint Python hanya saat transisi. |
| `native_open_invoice_file` | `{ "path": "...", "action": "open" }` atau `{ "action": "reveal" }` | `{ "status": "opened", "normalized_path": "..." }` | Custom command dengan allowlist invoice/export/app-data | Error harus menyebut kategori aman, bukan path mentah bila mengandung user data sensitif; fallback `/open_invoice` sementara. |
| `native_print_file` | `{ "path": "...", "source": "invoice" }` | `{ "status": "printed" }` atau `{ "status": "open_fallback", "message": "..." }` | Custom command; jangan expose broad shell command execution ke frontend | Log printer error ringkas; jika print API tidak tersedia, buka viewer dan return `open_fallback`. |
| `native_open_external_url` | `{ "url": "https://...", "source": "support" }` | `{ "status": "opened", "url": "https://..." }` | Custom command/opener plugin dengan allowlist scheme/domain | Tolak `javascript:`, `file:`, local arbitrary, credential-bearing URL; log host + source saja. |
| `native_get_diagnostics` | `{ "include_processes": true }` | `{ "app_version": "...", "paths": {...}, "backend": {"pid": 123, "port": 8000, "running": true}, "openwa": {"owner": "python", "known": false} }` | Read-only custom command | Jangan log atau return shutdown token, auth token, session, credential, or raw log content. |
| `native_get_process_status` | `{ "target": "python-sidecar" }` atau `{ "target": "openwa" }` | `{ "running": true, "pid": 123, "owner": "rust", "log_path": "..." }` | Read-only custom command | 4A hanya observasi; OpenWA boleh `owner: "python"` sampai Phase 4B. |

Capability prinsip:

- Frontend tidak boleh diberi akses langsung ke broad shell/fs plugin. UI memanggil custom Tauri command yang melakukan allowlist internal.
- `tauri_plugin_shell` tetap untuk sidecar/bundled binary; jangan perluas permission shell ke arbitrary command dari frontend.
- Path operation hanya boleh di root yang sudah dikenal: app data, exports, invoices, logs, backups/config yang non-rahasia.
- URL opener hanya boleh `https://` untuk domain yang disetujui atau scheme eksplisit yang sudah diaudit.

Prioritas implementasi 4A:

1. `native_get_paths` dan diagnostics read-only.
2. `native_open_path` untuk exports/logs/app-data dengan allowlist.
3. `native_open_invoice_file` untuk open/reveal PDF/invoice.
4. `native_open_external_url` dengan allowlist ketat.
5. `native_print_file` dengan fallback viewer.
6. `native_get_process_status` read-only; lifecycle OpenWA tetap Phase 4B.

Risiko khusus 4A:

- Arbitrary file open/reveal bila normalisasi path lemah.
- URL scheme abuse bila command menerima `file:`, `javascript:`, credential-bearing URL, atau localhost arbitrary.
- Print command memiliki side effect fisik; wajib eksplisit dari UI dan fallback jelas.
- Diagnostics dapat membocorkan token/session/log sensitif bila terlalu banyak mengembalikan isi file.
- Menambah capability Tauri terlalu luas dapat melemahkan security gateway walaupun logic bisnis tidak berubah.
- Behavior OS berbeda: Windows `explorer /select`, macOS `open -R`, Linux file manager fallback harus gagal dengan pesan jelas.

Test plan khusus 4A:

- Unit test Rust untuk canonicalize path, traversal rejection, unsupported kind, nonexistent file/folder, URL scheme/domain rejection, dan output error yang konsisten.
- Test transisi frontend: action open folder/open invoice/open URL memanggil Tauri command bila tersedia dan fallback Python hanya saat command tidak tersedia.
- Regression Python tetap lulus: `python -m unittest discover -s tests -p "test_*.py"`.
- Frontend/Rust gates: `npm run typecheck`, `npm run build:assets`, `cargo check --manifest-path src-tauri/Cargo.toml`.
- Build smoke bila production code berubah: `npm run tauri:build`.
- Manual installed-app pada VM/profil disposable: open exports/logs folder, reveal invoice/export file, open PDF, print fallback, URL allowlist, URL/path negatif, close app tanpa orphan process.

Dampak ukuran 4A:

- Migrasi helper native ke Rust diperkirakan berdampak kecil langsung pada installer, sekitar 0-2 MiB, karena Python sidecar, Node runtime, dan OpenWA tetap dibundel.
- Manfaat utama 4A adalah security boundary dan stabilitas desktop helper, bukan pengurangan ukuran besar.
- Pengurangan ukuran signifikan baru realistis di 4C setelah dependency Python legacy/desktop-only terbukti tidak dipakai dan aman dipisahkan.
- Batas bawah ukuran tetap ditahan Node/OpenWA selama WhatsApp gateway masih bundled.

### Quick Wins

1. Tambah Tauri commands untuk `open_path`, `reveal_path`, `open_external_url`, dan `print_file` dengan allowlist path/URL yang sama atau lebih ketat dari Python.
2. Ganti frontend action yang murni native helper agar memanggil Tauri command lebih dulu, lalu fallback ke endpoint Python hanya selama transisi.
3. Tambah command read-only `get_app_paths`, `get_log_paths`, `get_app_version`, dan `diagnostics_summary`.
4. Pindahkan ownership log lokasi proses ke Rust shell agar loading/error screen bisa menunjuk log tanpa bertanya ke Python.
5. Audit PyInstaller spec untuk dependency yang ikut karena import desktop/legacy; pertahankan `--exclude-module PySide6` dan tambahkan exclude legacy lain setelah test.

### Area High-Risk Yang Tidak Disentuh Dulu

- Database schema, migration, ORM model, transaksi pasien/kunjungan/herbal/inventory.
- Invoice calculation/PDF content, owner report, analytics, COGS, dan revenue rules.
- Payment gateway, invoice payment status, Midtrans/mock provider, callback/status simulation.
- License flow, hardware fingerprint, offline grace, settings secret filtering.
- CRM/follow-up, WhatsApp queue, send-lock, contact preference.
- Node/OpenWA API, auth/session/cache layout, token internal, browser Origin/Referer rejection.
- Upgrade installer behavior, user data directory, backup/restore semantics.

### Roadmap Bertahap

| Phase | Scope | Output wajib | Non-goal |
| --- | --- | --- | --- |
| 4A - Rust native helper migration | Open folder/file/PDF, reveal file, external URL allowlist, print fallback, app/log/config paths | Tauri commands kecil, frontend fallback aman, regression guard path/URL | Tidak ubah database atau logic bisnis. |
| 4B - Rust process supervisor hardening | Rust mengelola Python sidecar dan Node/OpenWA lifecycle: start, readiness, health, graceful shutdown, kill tree, log path | Orphan prevention, deterministic shutdown, diagnostics proses, token tidak bocor | Tidak ubah OpenWA protocol/queue/session logic. |
| 4C - Python dependency slimming | Audit PyInstaller import graph, hapus desktop/legacy-only deps dari Tauri bundle, ukur sidecar/installer | Build size report, PySide6/Qt tetap excluded, dependency backend bisnis tetap ada | Tidak menghapus pandas/reportlab/openpyxl bila masih dipakai export/PDF/report. |
| 4D - Endpoint kecil ke Rust | Metadata, app paths, log viewer helper, diagnostics, bootstrap health, native file operations | Endpoint Python kecil diganti Tauri command atau Rust local API bila perlu | Tidak pindahkan transaksi, laporan, payment, license, CRM, database. |
| 5 - Evaluasi partial backend Rust | Baru setelah Phase 4 stabil dan acceptance/cutover gate selesai | RFC teknis per bounded context | Tidak ada full rewrite otomatis. |

### Rust Process Supervisor Target

Rust/Tauri sebaiknya menjadi pemilik proses desktop:

- Start Python sidecar dengan port/token terkontrol, tunggu `/license` atau health bootstrap.
- Start Node/OpenWA dari runtime packaged atau memerintah Python hanya selama transisi; target akhir Rust menyimpan PID dan token shutdown.
- Readiness check eksplisit untuk Python dan Node, dengan timeout dan pesan error yang menunjuk log.
- Graceful shutdown berurutan: request shutdown endpoint bertoken, wait, lalu fallback kill process tree.
- Simpan process metadata non-rahasia untuk diagnostics: PID, command basename, log path, runtime path normalized, last health.
- Cegah orphan dengan cleanup pada `RunEvent::ExitRequested`/window close dan watchdog untuk child process.
- Python tidak lagi bertanggung jawab atas lifecycle desktop yang murni shell; Python tetap menjalankan business route dan health.

### Audit Dependency Python

| Dependency | Kategori | Keputusan Phase 4 |
| --- | --- | --- |
| `fastapi`, `uvicorn[standard]`, `python-multipart`, `SQLAlchemy` | Wajib backend bisnis/API | Tetap. |
| `reportlab` | Wajib invoice PDF | Tetap sampai generator invoice dievaluasi terpisah. |
| `pandas`, `openpyxl` | Export/report spreadsheet | Tetap sementara; audit pemakaian detail pada 4C. |
| `matplotlib` | Chart/report legacy atau export visual | Audit 4C; kandidat slim bila tidak dipakai backend aktif. |
| `bleach`, `slowapi` | Security hardening | Tetap jika route/helper aktif memakainya. |
| `PySide6` | Desktop legacy/PySide shell | Tidak boleh masuk bundle Tauri; kandidat hapus dari requirements Tauri setelah entrypoint legacy dipisah. |
| `win32api/win32print` implicit | Print helper Windows | Kandidat diganti Rust print/open helper; saat ini fallback Python menangani import optional. |

### Estimasi Ukuran Aplikasi

Pengukuran host build RC `5E40E6A0...`:

| Komponen | Ukuran |
| --- | ---: |
| Installer NSIS | 74.48 MiB (`78,097,966` byte) |
| Rust shell release exe | 10.50 MiB |
| Python sidecar onefile | 39.64 MiB |
| Runtime staged total | 145.54 MiB |
| Node runtime staged | 98.19 MiB |
| OpenWA server staged | 47.35 MiB |
| OpenWA `node_modules` staged | 47.23 MiB |
| Frontend `api/static` | 2.92 MiB |
| Frontend modules JS | 0.53 MiB |
| `tailwind.css` | 0.17 MiB |
| PySide6 di `.venv` | 449.97 MiB, tetapi sudah excluded dari sidecar Tauri |
| pandas / numpy / matplotlib di `.venv` | 63.00 / 31.69 / 25.43 MiB sebelum PyInstaller compression/pruning |

Estimasi dampak:

- PySide6/Qt sudah tidak ikut bundle Tauri; pengurangan tambahan dari sisi installer kemungkinan kecil, tetapi requirements/dev env bisa jauh lebih ringan bila dependency legacy dipisah.
- Native helper ke Rust memberi pengurangan kecil langsung, terutama menghapus kebutuhan optional desktop Python seperti print/open helper, tetapi manfaat utama adalah stabilitas dan security boundary.
- Dependency slimming Python realistis dapat mengurangi beberapa MiB sampai belasan MiB bila matplotlib/unused libs terbukti tidak aktif; jangan targetkan penghapusan pandas/openpyxl/reportlab tanpa pengganti.
- Batas bawah ukuran tetap ditahan Node/OpenWA: Node runtime + OpenWA dependencies sekitar 145 MiB staged sebelum kompresi, sehingga installer tidak akan menjadi sangat kecil selama WhatsApp gateway tetap bundled.

### Risk Register Phase 4

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Rewrite backend terlalu cepat | Regression transaksi/laporan/payment | Batasi Phase 4 ke helper native dan supervisor; RFC terpisah untuk Phase 5. |
| Payment gateway rusak | Invoice/payment gagal atau status salah | Jangan pindahkan payment route; test `tests.test_payment_gateway` wajib lulus. |
| WhatsApp gateway terganggu | QR/session/send gagal | Rust hanya supervise proses; jangan ubah Node API/token/session. |
| Installer upgrade gagal | Data user/shortcut/uninstall conflict | Jalankan matrix upgrade VM sebelum cutover; jangan ubah app data path. |
| Data user hilang | Kerusakan produksi | Semua native file operation harus allowlist dan tidak delete user data. |
| Security token bocor | Gateway/API dapat diakses pihak lain | Jangan log token; Rust diagnostics hanya metadata non-rahasia. |
| Rust command permission terlalu longgar | Arbitrary file/URL open | Allowlist path roots dan URL scheme/domain; unit test negatif. |
| Dependency slimming salah | Fitur export/PDF/report hilang | Gunakan import graph + full suite + manual export/PDF before/after. |

### Test Plan Phase 4

Setiap migrasi kecil ke Rust wajib menjalankan:

- Unit test Rust untuk path allowlist, URL allowlist, command errors, process metadata, dan shutdown fallback bila memungkinkan.
- Regression Python: `python -m unittest discover -s tests -p "test_*.py"`.
- Revenue/payment guard: `python -m unittest tests.test_p0_regressions tests.test_core_business_flows tests.test_payment_gateway`.
- Frontend gates: `npm run typecheck`, `npm run build:assets`.
- Rust gate: `cargo check --manifest-path src-tauri/Cargo.toml`.
- Build smoke: `npm run tauri:build` bila production code berubah.
- Manual installed-app: open folder, reveal invoice/export, open/print PDF, external URL allowlist, export/download, gateway start/stop, close window orphan-process check.
- Collector evidence pada VM/profil disposable; jangan gunakan profil produksi.

### Rekomendasi Urutan Implementasi

1. 4A-1: Tambah command Rust read-only/native open dengan allowlist dan frontend fallback.
2. 4A-2: Pindahkan open folder/open invoice/open external URL dari Python path ke Rust command secara bertahap.
3. 4B-1: Tambah process metadata/readiness di Rust tanpa mengubah OpenWA flow.
4. 4B-2: Pindahkan shutdown orchestration ke Rust, Python tetap expose health/shutdown endpoint bertoken.
5. 4C-1: Audit PyInstaller graph dan ukur size before/after; baru pisahkan requirements legacy.
6. 4D-1: Pindahkan endpoint metadata/paths/diagnostics kecil setelah helper native stabil.

## Risiko dan Keputusan

| Risiko tersisa | Dampak | Gate berikutnya |
| --- | --- | --- |
| WebView2 interaktif belum dijalankan | Integrasi OS/UI dapat gagal pada install nyata | Jalankan WV-01 s.d. WV-09 di VM |
| Upgrade installer belum divalidasi | Data/lisensi/shortcut dapat konflik | Jalankan matriks upgrade di VM dengan hash fixture |
| Folder installed size belum diukur | Footprint install belum pasti | Ukur setelah install RC di VM |
| Style CSP murni tertunda | UI localhost masih bergantung inline `<style>`/`style=` walaupun `script-src 'self'` sudah aktif | Jadwalkan cleanup inline style terpisah dan regression test |
| Domain pembayaran produksi belum masuk allowlist | Link pembayaran produksi akan ditolak secara benar sampai direview | Tambah domain production hanya saat konfigurasi/provider disetujui |
| Gateway lama yang masih berjalan di port lokal tidak memiliki token baru | Transisi upgrade dapat gagal mengakses gateway stale | Pastikan leftover process check pada uji upgrade |
| QR/layout/dark mode/Settings/mapping terapis/pemilihan pasien/follow-up/action-based stok/CRM/WhatsApp Gateway/Analytics/Help/Owner Report/Audit belum dilihat di WebView2 installer pengganti | Perbaikan source dapat masih berbeda pada lingkungan install | Jalankan checklist P3D-R3 pada RC hash `5E40E6A0...` |

**Keputusan akhir Phase 3D-R3 saat ini: `BLOCKED`.** RC terbaru `5E40E6A0...` memuat full-suite stabilization, P0 revenue split, redesign Settings, mapping Terapis-Layanan dan validasi Catat Kunjungan, audit global dark mode, redesign action-based Herbal/Inventory, helper Rust read-only Phase 4A-1, native open/reveal path Phase 4A-2, native external URL opener Phase 4A-3, native invoice/PDF opener Phase 4A-4, native print file Phase 4A-5, Phase 4A-CSP hardening sampai R5 / Final Inline Handler Cleanup dengan `script-src 'self'` aktif, ACL loopback fix untuk native invoice/print/reveal dari backend lokal, checklist mapping Terapis-Layanan yang bisa dicentang jelas, serta native PDF resolver yang kompatibel dengan path tersimpan `invoices/...` dan `exports/...`. Validasi otomatis dan build lulus, tetapi bukan pengganti uji UI WebView2. Jangan lanjut Phase 3C atau cutover sampai Settings, mapping Terapis/Kunjungan, action Herbal/Inventory, WhatsApp UI, modal Follow-up, CRM, WhatsApp Gateway, filter Analitik, Owner Report, Audit, Help/support opener, dark mode seluruh tab, print fallback, CSP-touched invoice/settings/license flows, orphan process, dan upgrade installer lulus pada VM/profil uji.
