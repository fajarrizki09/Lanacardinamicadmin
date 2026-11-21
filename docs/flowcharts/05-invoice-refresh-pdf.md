# Flowchart 05 — Invoice & Refresh PDF

## Scope

Logic generate invoice, permanensi transaksi, status PDF, void invoice, dan refresh PDF setelah status pembayaran berubah.

```mermaid
flowchart TD
    A[Invoice tab dibuka] --> B[GET /invoices]
    B --> C[Gabungkan visit + herbal sale mandiri]
    C --> D[Tampilkan status transaksi + pdf_status]

    D --> E{invoice_status void?}
    E -->|Ya| F[pdf_status = void]
    F --> F1[Disable update payment]
    F1 --> F2[Disable refresh PDF]
    F2 --> F3[Tampilkan status void]

    E -->|Tidak| G{invoice_path ada?}
    G -->|Tidak| H[pdf_status = not_generated]
    H --> H1[Tombol Buat Invoice]
    G -->|Ya| I{File PDF ada?}
    I -->|Tidak| J[pdf_status = missing]
    J --> J1[Tampilkan File hilang + Buat Ulang]
    I -->|Ya| K{payment_updated_at > pdf_generated_at?}
    K -->|Ya| L[pdf_status = stale]
    L --> L1[Badge PDF perlu update]
    K -->|Tidak| M[pdf_status = fresh]
    M --> M1[Tombol Buka PDF / Print / Update PDF / Void]

    H1 --> N[POST generate invoice]
    J1 --> N
    L1 --> O[Admin klik Update PDF]
    M1 --> O
    O --> N

    N --> P{Invoice void?}
    P -->|Ya| Q[Tolak refresh/generate]
    P -->|Tidak| R[Ambil data transaksi terbaru]
    R --> S[Ambil payment_status terbaru]
    S --> T[Render PDF via helpers/invoice_helper.py]
    T --> U[Simpan invoice_path + pdf_generated_at]
    U --> V{Sebelumnya sudah ada PDF?}
    V -->|Tidak| W[Audit invoice_generated]
    V -->|Ya| X[Audit invoice_pdf_refreshed]
    W --> Y[Reload invoice list]
    X --> Y

    D --> Z[Admin ubah status bayar]
    Z --> AA[POST /update_invoice_payment]
    AA --> AB{Invoice void?}
    AB -->|Ya| AC[Tolak; void tidak boleh ditandai lunas]
    AB -->|Tidak| AD[Update payment_status + payment_updated_at]
    AD --> AE[Audit manual_payment_updated]
    AE --> AF{PDF sudah ada?}
    AF -->|Ya| L
    AF -->|Tidak| H

    M1 --> AG[Admin klik Void]
    AG --> AH[POST /void_invoice]
    AH --> AI[Set invoice_status = void]
    AI --> AJ[Set payment_status = void]
    AJ --> AK[Audit invoice_voided]
    AK --> F
```

## Metadata Invoice

- `invoice_path`
- `pdf_generated_at`
- `payment_updated_at`
- `invoice_status`
- `payment_status`

## Status PDF

- `fresh`: PDF sesuai data terbaru.
- `stale`: data transaksi/payment berubah setelah PDF dibuat.
- `missing`: `invoice_path` ada tetapi file PDF hilang.
- `not_generated`: belum pernah generate PDF.
- `void`: invoice/transaksi void.

## Logic Notes

- Invoice record/transaksi tidak dibuat dua kali.
- PDF invoice hanyalah snapshot dari transaksi pada waktu tertentu.
- Nomor invoice harus stabil; refresh PDF bukan invoice baru.
- Void invoice tidak boleh di-refresh dan tidak boleh ditandai lunas.
- Jika `payment_updated_at > pdf_generated_at`, PDF perlu update.
- Audit penting: `invoice_generated`, `invoice_pdf_refreshed`, `invoice_voided`, `manual_payment_updated`.
