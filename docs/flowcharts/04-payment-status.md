# Flowchart 04 — Payment Status

## Scope

Logic status pembayaran manual dan gateway. Sumber aturan utama adalah `helpers/payment_rules.py`.

```mermaid
flowchart TD
    A[Transaksi visit / herbal dibuat atau diupdate] --> B[Input payment_status + payment_method + amount_paid]
    B --> C[Normalize via helpers/payment_rules.py]
    C --> D{Status pembayaran}

    D -->|paid| E[Wajib ada payment_method]
    E --> F[amount_paid = total]
    F --> G[paid_at = now]

    D -->|partial| H[Wajib ada payment_method]
    H --> I[amount_paid > 0 dan < total]
    I --> J[paid_at = now]

    D -->|unpaid| K[amount_paid = 0]
    K --> L[paid_at = null]
    L --> M[payment_method tidak boleh cash/debit/credit_card]

    D -->|pending| N[Gateway payment]
    N --> O[amount_paid = 0]
    O --> P[paid_at = null]
    P --> Q[payment_method harus kanal gateway]

    D -->|failed / expired| R[Payment gagal/kedaluwarsa]
    R --> S[amount_paid = 0]
    S --> T[Tidak masuk revenue]

    D -->|void| U[Transaksi/invoice dibatalkan]
    U --> V[Tidak masuk revenue aktif]
    V --> W[Tidak boleh diubah paid kecuali ada flow unvoid khusus]

    G --> X[DB update]
    J --> X
    M --> X
    Q --> X
    T --> X
    W --> X

    X --> Y[Recalculate payment summary]
    Y --> Z{PDF invoice sudah ada?}
    Z -->|Tidak| AA[pdf_status = not_generated]
    Z -->|Ya| AB[Set payment_updated_at = now]
    AB --> AC{payment_updated_at > pdf_generated_at?}
    AC -->|Ya| AD[pdf_status = stale]
    AC -->|Tidak| AE[pdf_status = fresh]
    AD --> AF[Audit manual_payment_updated]
    AE --> AF
    AA --> AF
    AF --> AG[Refresh invoice list / KPI]
```

## Logic Notes

- `helpers/payment_rules.py` adalah sumber aturan status pembayaran.
- `paid`: wajib ada `payment_method`, `amount_paid = total`, `paid_at = now`.
- `partial`: wajib ada `payment_method`, `amount_paid > 0` dan `< total`, `paid_at = now`.
- `unpaid`: `amount_paid = 0`, `paid_at = null`, metode tidak boleh `cash`, `debit`, atau `credit_card`.
- `pending`: hanya untuk gateway payment, `amount_paid = 0`, `paid_at = null`, metode harus kanal gateway.
- `failed` / `expired`: `amount_paid = 0` dan tidak masuk revenue.
- `void`: tidak masuk revenue aktif dan tidak boleh diubah kembali menjadi paid tanpa flow unvoid khusus.
- Jika `payment_updated_at > pdf_generated_at`, PDF invoice dianggap `stale` dan perlu update.
- Perubahan payment status bukan transaksi baru; ia hanya mengubah status pembayaran transaksi yang sudah ada.
