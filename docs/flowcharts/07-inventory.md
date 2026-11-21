# Flowchart 07 — Inventory Alat

## Scope

Logic stok alat, transaksi inventory, minimum stock, koreksi stok, dan pemakaian stok oleh layanan.

```mermaid
flowchart TD
    A[Admin buka Inventory] --> B[api/static/modules/inventory.js]
    B --> C[GET /inventory]
    C --> D[(inventory table)]

    B --> E[Tambah/Edit Item]
    E --> F{Validasi nama, unit, qty, min_stock}
    F -->|Gagal| G[Tampilkan error aman]
    F -->|Valid| H[POST/PUT /inventory]
    H --> I[Jika qty berubah, catat inventory_transactions]
    I --> J[Audit inventory_item_saved]
    J --> D

    B --> K[Tambah Stok / Koreksi Stok]
    K --> L[Input quantity_change + note/reason]
    L --> M{Note/reason ada?}
    M -->|Tidak| N[Tolak koreksi]
    M -->|Ya| O{Stock setelah perubahan negatif?}
    O -->|Ya| P[Tolak negative stock]
    O -->|Tidak| Q[Update quantity]
    Q --> R[Catat inventory_transactions]
    R --> S[Audit inventory_correction]

    T[Kunjungan dibuat] --> U[Begin transaction visit]
    U --> V{Layanan punya service inventory usage?}
    V -->|Tidak| W[Lanjut simpan visit]
    V -->|Ya| X[Hitung kebutuhan stok]
    X --> Y{Stok cukup?}
    Y -->|Tidak| Z[Rollback visit + stok + logs transaksi]
    Y -->|Ya| AA[Kurangi inventory]
    AA --> AB[Catat inventory_transactions dengan visit_id jika ada]
    AB --> W
    W --> AC[Commit bersama visit]

    D --> AD{quantity <= min_stock?}
    AD -->|Ya| AE[Tampilkan low stock alert]
    AD -->|Tidak| AF[Normal]
```

## Logic Notes

- Inventory alat berbeda dari herbal/produk jual.
- Setiap perubahan stok harus punya `inventory_transactions`.
- Koreksi stok wajib punya note/reason.
- Negative stock harus ditolak.
- Pemakaian stok oleh layanan harus terkait `visit_id` jika tersedia.
- Jika visit gagal disimpan, pengurangan stok alat harus rollback.
- Low stock alert muncul saat `quantity <= min_stock`.
