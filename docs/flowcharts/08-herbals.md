# Flowchart 08 — Produk / Herbal

## Scope

Logic stok herbal, penjualan herbal mandiri, herbal terkait kunjungan, invoice herbal, retur, koreksi, dan void.

```mermaid
flowchart TD
    A[Admin buka Herbal] --> B[api/static/modules/herbals.js]
    B --> C[GET /herbals]
    C --> D[(herbals table)]

    B --> E[Tambah/Edit Produk Herbal]
    E --> F{Validasi nama, harga, stok}
    F -->|Gagal| G[Tampilkan error aman]
    F -->|Valid| H[POST/PUT /herbals]
    H --> I[Audit herbal_saved]
    I --> D

    B --> J[Stok Masuk / Koreksi]
    J --> K[Input quantity + reason]
    K --> L{Reason ada dan stock valid?}
    L -->|Tidak| M[Tolak]
    L -->|Ya| N[Update stock]
    N --> O[Catat herbal_transactions correction]
    O --> P[Audit herbal_stock_corrected]

    B --> Q[Penjualan Herbal Mandiri]
    Q --> R[Pilih item + quantity]
    R --> S{Stok semua item cukup?}
    S -->|Tidak| T[Tolak dan rollback semua item]
    S -->|Ya| U[Begin DB transaction]
    U --> V[Kurangi stok]
    V --> W[Create sale_group_id]
    W --> X[Set payment_status]
    X --> Y[Catat herbal_transactions sale]
    Y --> Y1[visit_id = null]
    Y1 --> Z[Commit]
    Z --> AA[Muncul sebagai invoice herbal mandiri]

    AB[Kunjungan pasien] --> AC[Tambah herbal terkait visit]
    AC --> AD{Stok cukup?}
    AD -->|Tidak| AE[Rollback visit transaction]
    AD -->|Ya| AF[Kurangi stok]
    AF --> AG[Catat herbal_transactions sale]
    AG --> AH[visit_id = visit.id]
    AH --> AI[Nilai herbal ikut total invoice visit]

    AA --> AJ[Generate Herbal Invoice]
    AJ --> AK[helpers/invoice_helper.py]
    AK --> AL[PDF herbal invoice snapshot]

    AA --> AM[Void Invoice Herbal]
    AM --> AN[Set invoice_status = void]
    AN --> AO[Set payment_status = void]
    AO --> AP{Stok perlu dikembalikan?}
    AP -->|Ya| AQ[Create herbal return transaction]
    AQ --> AR[Tambah stok kembali]
    AR --> AS[Audit herbal_stock_returned]
    AP -->|Tidak| AT[Void hanya finansial]
    AS --> AU[Audit herbal_invoice_voided]
    AT --> AU
```

## Logic Notes

- Herbal mandiri: `visit_id = null`, punya `sale_group_id`, dan muncul sebagai invoice herbal mandiri.
- Herbal terkait kunjungan: `visit_id = visit.id` dan ikut total invoice visit.
- Void invoice herbal tidak otomatis selalu retur stok.
- Jika salah input, stok biasanya perlu kembali.
- Jika barang sudah dibawa pasien, stok tidak balik walaupun invoice void secara finansial.
- Jika barang rusak/expired, stok tidak balik dan perlu koreksi stok terpisah.
- Status pembayaran herbal bisa berubah; PDF perlu refresh jika sudah dibuat dan data berubah.
- Audit penting: `herbal_invoice_voided`, `herbal_stock_returned`, `herbal_stock_corrected`.
