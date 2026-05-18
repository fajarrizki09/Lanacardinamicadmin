# Flowchart 06 — Payment Gateway

## Scope

Logic pembuatan link pembayaran, pengecekan status gateway, callback idempotent, dan stale PDF setelah status berubah.

```mermaid
flowchart TD
    A[Admin klik Buat Link Pembayaran] --> B[Check payment gateway enabled]
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
