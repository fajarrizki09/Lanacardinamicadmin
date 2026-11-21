# Flowchart 06 — Payment Gateway

## Scope

Logic pembuatan payment gateway dari pencatatan transaksi/keterangan pembayaran, pengecekan status gateway, callback idempotent, dan stale PDF setelah status berubah.

Gateway tersambung ke **transaksi visit/herbal**, bukan ke file PDF invoice. Tab invoice hanya menjadi layar operasional untuk melihat transaksi, membuat/membuka link pembayaran, refresh PDF, dan cek status.

```mermaid
flowchart TD
    A[Visit/herbal sudah tercatat dengan metode gateway] --> B[Check payment gateway enabled]
    B -->|Tidak| C[Tolak / fallback manual]
    B -->|Ya| D[Ambil provider default dari settings]
    D --> E{Provider valid?}
    E -->|Tidak| F[Tolak provider]
    E -->|Ya| G[Create payment reference]
    G --> H[Call provider create payment]
    H --> I[Simpan payment_provider]
    I --> J[Simpan payment_reference + payment_url]
    J --> K[Set payment_status = pending]
    K --> L[Audit gateway_payment_created]
    L --> M[Reload invoice list]

    M --> N[Admin/user bayar]
    N --> O[Admin klik cek status atau callback gateway masuk]
    O --> P[Lookup transaksi by payment_reference]
    P --> Q{Reference ditemukan?}
    Q -->|Tidak| R[Return safe no-op / 404 sesuai endpoint]
    Q -->|Ya| S{Status sudah final?}
    S -->|paid/failed/expired| T[Ignore duplicate callback]
    T --> U[No duplicate audit]
    S -->|Belum final| V[Map gateway status]

    V -->|paid| W[Set payment_status = paid]
    W --> X[amount_paid = total]
    X --> Y[paid_at = now]
    Y --> Z[Mark PDF stale jika PDF sudah ada]
    Z --> AA[Audit gateway_payment_paid]

    V -->|failed| AB[Set payment_status = failed]
    AB --> AC[amount_paid = 0]
    AC --> AD[Audit gateway_payment_failed]

    V -->|expired| AE[Set payment_status = expired]
    AE --> AF[amount_paid = 0]
    AF --> AG[Audit gateway_payment_expired]

    V -->|pending| AH[Tidak ubah final payment]
    AH --> AI[Audit optional atau no-op]
```

## Logic Notes

- Gateway tidak membuat transaksi baru.
- Gateway hanya mengubah status pembayaran transaksi yang sudah ada.
- Callback/status check gateway harus idempotent agar status dan audit tidak dobel.
- Status final: `paid`, `failed`, `expired`.
- Jika transaksi sudah final, duplicate callback harus diabaikan.
- Jika gateway menjadi `paid`, PDF invoice yang sudah ada harus ditandai stale/perlu refresh.
- Provider aktif dan kredensialnya diambil dari settings.

---

## Flowchart Saat Catat Kunjungan Memilih Metode Gateway

```mermaid
flowchart TD
     A[Admin buka form Catat Kunjungan] --> B[Pilih pasien + layanan + terapis + item herbal jika ada]
     B --> C[Sistem hitung total/final_price]
     C --> D[Pilih status pembayaran]
     D --> E{Metode pembayaran dipilih}

     E -->|Cash / transfer manual / debit manual| F[Jalur manual]
     F --> G[Validasi payment_rules]
     G --> H[Simpan visit dengan status paid/partial/unpaid]
     H --> I[Audit visit_created]
     I --> J[Invoice tab menampilkan transaksi]

     E -->|QRIS / ewallet / virtual_account / credit_card| K[Jalur payment gateway]
     K --> L[Ambil setting payment_gateway_enabled]
     L --> M{Gateway aktif?}
     M -->|Tidak| N[Tolak atau simpan unpaid/pending manual sesuai rule UI]
     M -->|Ya| O[Ambil default provider dari settings]
     O --> P{Provider tersedia?}
     P -->|Tidak| Q[Tolak: provider belum didukung]
     P -->|Ya| R[Simpan visit sebagai transaksi utama]
     R --> S[Set payment_status=pending]
     S --> T[Set payment_method=channel gateway]
     T --> U[Set amount_paid=0]
     U --> V[Commit visit + stok + herbal terkait]
     V --> W[Create gateway payment otomatis atau tampilkan tombol Buat Link]
     W --> X[POST /payments/gateway/create]
     X --> Y[Provider kosong di request]
     Y --> Z[Backend pakai default provider dari settings]
     Z --> AA[Create payment Midtrans/provider aktif]
     AA --> AB[Simpan payment_reference + payment_url]
     AB --> AC[Invoice tab/response menampilkan Link Pembayaran]
     AC --> AD[Pasien bayar]
     AD --> AE[Cek status/callback update paid/expired/failed]
```

## Catatan Alur Kunjungan vs Invoice

- Saat catat kunjungan, admin memang memilih `payment_status`, `payment_method`, dan nominal pembayaran jika manual.
- Jika metode yang dipilih adalah kanal gateway (`qris`, `ewallet`, `virtual_account`, `credit_card`), status yang benar adalah `pending` sampai gateway mengonfirmasi.
- Provider seperti Midtrans tidak perlu dipilih di form kunjungan. Provider diambil otomatis dari Settings: `payment_gateway_default_provider`.
- Invoice bukan sumber transaksi. Invoice tab membaca data visit/herbal yang sudah tercatat.
- Payment gateway menempel ke record `Visit` atau `HerbalTransaction` melalui:
  - `payment_provider`
  - `payment_reference`
  - `payment_url`
  - `payment_channel`
  - `payment_gateway_status`
- PDF invoice hanya snapshot. Jika status payment berubah setelah PDF dibuat, PDF menjadi `stale` dan perlu refresh.

## Target UX yang Disarankan

Jika admin memilih metode gateway saat catat kunjungan:

1. Sistem simpan kunjungan sebagai `pending`.
2. Sistem otomatis pakai provider aktif dari Settings, misalnya `midtrans`.
3. Sistem langsung membuat payment link Midtrans.
4. Setelah sukses, UI menampilkan:
    - tombol buka link pembayaran;
    - tombol copy/kirim link ke WhatsApp Follow-up;
    - status `Menunggu pembayaran`.
5. Jika create gateway gagal, visit tidak boleh dianggap lunas. Opsi aman:
    - rollback seluruh pencatatan; atau
    - simpan visit `unpaid/pending_without_link` dengan error jelas dan tombol retry create link.

Implementasi saat ini masih dominan membuat link dari tab invoice melalui tombol **Buat Link Pembayaran**. Target flow lanjutan adalah membuat link otomatis setelah catat kunjungan jika metode gateway dipilih.

---

## Flowchart Midtrans — QRIS, Payment Link, Konfirmasi Nominal, dan WhatsApp Follow-up

```mermaid
flowchart TD
     A[Admin buka invoice / transaksi] --> B[Admin pilih metode pembayaran]
     B --> C{Metode gateway?}
     C -->|Cash / transfer manual / debit manual| D[Jalur pembayaran manual]
     D --> D1[Admin input status + nominal manual]
     D1 --> D2{Nominal valid sesuai transaksi?}
     D2 -->|Tidak| D3[Tolak update pembayaran]
     D2 -->|Ya| D4[Update payment_status paid/partial]
     D4 --> D5[Audit manual_payment_updated]

     C -->|QRIS / ewallet / virtual_account / credit_card| E[Validasi gateway aktif]
     E --> F{Provider = Midtrans?}
     F -->|Tidak / belum aktif| G[Tolak / fallback provider aktif]
     F -->|Ya| H[Ambil total dari DB]
     H --> I{Amount request == total DB?}
     I -->|Tidak| J[Tolak: total pembayaran tidak sesuai]
     I -->|Ya| K[Generate order_id Midtrans]
     K --> L[Build Snap payload]
     L --> L1[transaction_details.gross_amount = total DB]
     L --> L2[enabled_payments sesuai metode]

     L2 --> M{Metode QRIS?}
     M -->|Ya| N[enabled_payments = qris]
     N --> O[Create Snap transaction ke Midtrans]
     O --> P[Midtrans return token + redirect_url]
     P --> Q[Simpan payment_url + reference + channel=qris]
     Q --> R[Set payment_status=pending]
     R --> S[UI tampilkan tombol/link bayar]
     S --> T[Pasien buka halaman Midtrans]
     T --> U[Midtrans menampilkan QRIS]
     U --> V[Pasien scan QRIS]
     V --> W[Nominal QR berasal dari gross_amount]

     M -->|Virtual account / ewallet / credit card| X[enabled_payments sesuai channel]
     X --> Y[Create Snap transaction ke Midtrans]
     Y --> Z[Midtrans return token + redirect_url]
     Z --> AA[Simpan payment_url + reference + channel]
     AA --> AB[Set payment_status=pending]
     AB --> AC[Pasien bayar lewat channel pilihan]

     W --> AD[Admin klik cek status / callback diterima]
     AC --> AD
     AD --> AE[Query Midtrans status by order_id]
     AE --> AF{Status Midtrans}
     AF -->|settlement/capture| AG[Map ke paid]
     AG --> AH[Set amount_paid = total DB]
     AH --> AI[Set paid_at + payment_updated_at]
     AI --> AJ[Audit gateway_payment_paid]
     AJ --> AK[Invoice PDF lama menjadi stale]

     AF -->|pending| AL[Tetap pending]
     AF -->|expire| AM[Set expired + amount_paid=0]
     AF -->|cancel/deny/failure| AN[Set failed + amount_paid=0]

     S --> AO{Kirim link/QR ke pasien via Follow-up?}
     AO -->|Saat ini| AP[Kirim/copy payment_url Midtrans via WhatsApp Follow-up]
     AO -->|Jika ingin QR image langsung| AQ[Perlu endpoint generate/ambil QR image dari payment_url/Midtrans]
     AP --> AR[Composer Follow-up berisi link bayar + nominal]
     AQ --> AS[Composer Follow-up attach/kirim gambar QR jika gateway WhatsApp mendukung attachment]
```

## Jawaban Rule Midtrans

### 1. Jika pilih QRIS, apakah menampilkan QR code yang di-scan pasien dengan nominal sesuai?

Ya, target flow Midtrans QRIS adalah:

1. Sistem mengambil nominal dari DB, bukan dari input bebas UI.
2. Sistem menolak request jika `amount` dari UI tidak sama dengan total transaksi DB.
3. Backend membuat transaksi Snap Midtrans dengan:
    - `transaction_details.order_id = payment_reference`
    - `transaction_details.gross_amount = total transaksi DB`
    - `enabled_payments = ["qris"]`
4. Pasien membuka `payment_url` Midtrans.
5. QRIS ditampilkan oleh halaman Midtrans/Snap.
6. Nominal QRIS mengikuti `gross_amount`, sehingga harus sama dengan nominal invoice/transaksi.

Catatan implementasi saat ini: aplikasi menyimpan `payment_url` Snap. QR image langsung belum disimpan sebagai file/attachment lokal. Jadi yang paling aman dikirim ke pasien saat ini adalah link pembayaran Midtrans, bukan gambar QR mentah.

### 2. Jika pilih pembayaran lain, apakah sukses terkonfirmasi nominal harganya?

Ya, untuk channel gateway seperti `virtual_account`, `ewallet`, dan `credit_card`, flow nominal tetap sama:

- total diambil dari DB;
- request ditolak jika nominal tidak cocok;
- Midtrans menerima `gross_amount` sesuai total;
- saat status Midtrans menjadi `settlement` atau `capture`, sistem mengubah status menjadi `paid` dan mengisi `amount_paid = total DB`.

Untuk pembayaran manual seperti `cash` atau transfer manual, tidak lewat Midtrans. Konfirmasi dilakukan lewat update manual dengan validasi payment rule aplikasi.

### 3. Saat QR code muncul, apakah bisa dikirim langsung ke pasien lewat WhatsApp Gateway tab Follow-up?

Ada dua level:

1. **Aman untuk sekarang:** kirim `payment_url` Midtrans lewat WhatsApp Follow-up. Pasien klik link, lalu melihat QRIS/VA/ewallet di halaman Midtrans.
2. **Jika wajib kirim QR image langsung:** perlu tambahan fitur khusus:
    - backend mengambil/generate QR image dari transaksi Midtrans;
    - simpan QR image sementara dengan expiry;
    - composer Follow-up mendukung attachment gambar;
    - WhatsApp gateway/Puppeteer mendukung kirim media, bukan hanya teks;
    - guardrail tetap aktif: consent/preference pasien, send-lock, satu klik satu pasien, audit log.

Rekomendasi rilis aman: kirim link bayar + nominal lewat Follow-up terlebih dahulu. Kirim QR image langsung dibuat sebagai fase lanjutan setelah attachment WhatsApp gateway stabil.

## Acceptance Criteria Midtrans Gateway

- QRIS request wajib memakai `enabled_payments = ["qris"]`.
- `gross_amount` wajib sama dengan total invoice/transaksi DB.
- Request gateway ditolak jika amount dari UI berbeda dari total DB.
- Payment status awal setelah create gateway adalah `pending`.
- Status `settlement`/`capture` dari Midtrans menjadi `paid`.
- Saat `paid`, `amount_paid` harus sama dengan total DB.
- Callback/status check duplicate untuk status final tidak boleh membuat audit/payment dobel.
- Follow-up WhatsApp minimal bisa mengirim teks berisi link bayar, nominal, dan instruksi pembayaran.
- Kirim QR image langsung hanya boleh aktif jika fitur attachment sudah ada dan sudah diuji.
