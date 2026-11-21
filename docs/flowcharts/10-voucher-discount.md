# Flowchart 10 — Voucher / Discount Rule

## Scope

Logic diskon layanan, voucher campaign, voucher targeted patient, priority, stackable rule, quota, dan penggunaan voucher.

```mermaid
flowchart TD
    A[Admin konfigurasi discount/voucher] --> B[DiscountRule]
    B --> C{Tipe rule}
    C -->|Diskon layanan| D[Rule harga layanan]
    C -->|Voucher campaign| E[Voucher code / campaign]
    C -->|Target pasien| F[VoucherPatientTarget]

    G[Admin buat kunjungan] --> H[Pilih pasien + layanan]
    H --> I[Hitung original_price]
    I --> J[Ambil semua discount rule aktif]
    J --> K[Filter tanggal aktif]
    K --> L[Filter layanan]
    L --> M[Filter pasien / target patient]
    M --> N[Filter voucher code jika ada]
    N --> O[Filter quota + usage limit]
    O --> P{Ada rule eligible?}
    P -->|Tidak| Q[discount_amount = 0]
    P -->|Ya| R[Sort by priority]

    R --> S{Rule stackable?}
    S -->|Ya| T[Apply combined discount]
    T --> U[Apply max cap]
    S -->|Tidak| V[Pilih rule prioritas tertinggi atau diskon terbaik sesuai aturan]
    U --> W[Hitung discount_amount]
    V --> W
    Q --> X[final_price = original_price]
    W --> Y[final_price = original_price - discount_amount]
    Y --> Z{final_price < 0?}
    Z -->|Ya| AA[Set final_price = 0]
    Z -->|Tidak| AB[Lanjut]
    AA --> AC[Simpan visit]
    AB --> AC
    X --> AC

    AC --> AD{Voucher dipakai?}
    AD -->|Tidak| AE[Commit visit]
    AD -->|Ya| AF[Catat VoucherUsage]
    AF --> AG[Update quota/status target]
    AG --> AE
    AE --> AH[Invoice tampilkan original_price + discount_amount + final_price]
```

## Logic Notes

- Diskon mempengaruhi `final_price`, bukan menghapus `original_price`.
- `final_price` tidak boleh negatif.
- Voucher usage wajib dicatat agar voucher tidak dobel pakai.
- Target patient voucher harus dicek sebelum voucher dianggap eligible.
- Rule priority menentukan urutan evaluasi.
- Stackable discount harus punya max cap agar diskon gabungan tidak berlebihan.
- Invoice harus menampilkan `original_price`, `discount_amount`, dan `final_price`.
