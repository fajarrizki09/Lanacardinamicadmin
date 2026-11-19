# Perbandingan Layout Tab Herbal

## SEBELUM (Layout Lama)

```
┌─────────────────────────────────────────────────────────────┐
│  Stat Cards (3 kolom: Tersedia | Menipis | Habis)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Form Tambah Produk Baru (di paling atas)            │   │
│  │ - Nama, Satuan, Stok, Harga, dll                    │   │
│  │ - Tombol: Jual Produk | Retur (di header form)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────┬──────────────────────────┐   │
│  │ TABEL PRODUK (KIRI)      │ FORMS (KANAN)            │   │
│  │ - Semua data tanpa       │ ┌──────────────────────┐ │   │
│  │   pagination             │ │ Form Koreksi Stok    │ │   │
│  │ - Klik untuk select      │ │ (klik baris di kiri) │ │   │
│  │ - Scroll jika banyak     │ └──────────────────────┘ │   │
│  │                          │                          │   │
│  │                          │ ┌──────────────────────┐ │   │
│  │                          │ │ Form Registrasi      │ │   │
│  │                          │ │ (hidden/tidak pakai) │ │   │
│  │                          │ └──────────────────────┘ │   │
│  └──────────────────────────┴──────────────────────────┘   │
│                                                             │
│  Riwayat Koreksi                                            │
└─────────────────────────────────────────────────────────────┘
```

**Masalah:**
- Form tambah di atas membuat user harus scroll untuk lihat tabel
- Tabel tidak ada pagination, sulit navigasi jika data banyak
- Layout tidak konsisten dengan tab Inventory
- Form koreksi di kanan, tabel di kiri (berbeda dengan inventory)

---

## SESUDAH (Layout Baru - Sama dengan Inventory)

```
┌─────────────────────────────────────────────────────────────┐
│  Stat Cards (3 kolom: Tersedia | Menipis | Habis)          │
├─────────────────────────────────────────────────────────────┤
│  Action Buttons: [Jual Produk] [Retur]                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ TABEL MONITORING PRODUK/HERBAL                       │   │
│  │ - Pagination 10 items per halaman                    │   │
│  │ - Klik baris untuk select                            │   │
│  │ - Kolom: Produk | Stok/Kemasan | Harga | Margin |   │   │
│  │          Status | Aksi                               │   │
│  │                                                       │   │
│  │ [< Sebelumnya]  Halaman 1 dari 3  [Selanjutnya >]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────┬──────────────────────────┐   │
│  │ Form Tambah Produk Baru  │ Form Koreksi Stok Manual │   │
│  │ - Nama Produk            │ - Produk Terpilih        │   │
│  │ - Satuan Dasar           │ - Jenis Pergerakan       │   │
│  │ - Satuan Kemasan         │ - Jumlah                 │   │
│  │ - Stok Awal              │ - Satuan Transaksi       │   │
│  │ - Isi per Kemasan        │ - Alasan Koreksi         │   │
│  │ - Harga Modal            │ - Preview                │   │
│  │ - Harga Jual             │ [Terapkan Koreksi]       │   │
│  │ - Batas Aman             │                          │   │
│  │ [Simpan]                 │                          │   │
│  └──────────────────────────┴──────────────────────────┘   │
│                                                             │
│  Riwayat Koreksi                                            │
└─────────────────────────────────────────────────────────────┘
```

**Keuntungan:**
✅ Tabel langsung terlihat tanpa scroll
✅ Pagination 10 items - mudah navigasi
✅ Action buttons di atas - akses cepat
✅ Forms di bawah bersebelahan - efisien space
✅ Konsisten dengan layout Inventory
✅ Helper text lebih jelas: "Klik baris di tabel atas"

---

## Detail Perubahan

### 1. Urutan Komponen
| Sebelum | Sesudah |
|---------|---------|
| 1. Stat Cards | 1. Stat Cards |
| 2. Form Tambah (atas) | 2. Action Buttons |
| 3. Tabel (kiri) + Form Koreksi (kanan) | 3. Tabel (tengah, full width) |
| 4. Riwayat | 4. Form Tambah (kiri) + Form Koreksi (kanan) |
| | 5. Riwayat |

### 2. Pagination
- **Sebelum:** Tidak ada, semua data ditampilkan
- **Sesudah:** 10 items per halaman dengan tombol navigasi

### 3. Action Buttons
- **Sebelum:** Di dalam header form tambah
- **Sesudah:** Standalone di bawah stat cards

### 4. Form Layout
- **Sebelum:** Tabel kiri (besar) + Form kanan (kecil)
- **Sesudah:** Tabel atas (full width) + Forms bawah (bersebelahan)

### 5. Helper Text
- **Sebelum:** "Klik baris produk/herbal di tabel"
- **Sesudah:** "Klik baris di tabel atas"

### 6. CSS Class
- **Sebelum:** `.herbal-workspace` (custom)
- **Sesudah:** `.inventory-forms-grid` (shared dengan inventory)

---

## Kode Pagination

```typescript
// Pagination logic
const currentPage = (window as any)._herbalPage || 1;
const itemsPerPage = 10;
const totalPages = Math.ceil(data.length / itemsPerPage);
const startIndex = (currentPage - 1) * itemsPerPage;
const endIndex = startIndex + itemsPerPage;
const paginatedData = data.slice(startIndex, endIndex);

// Pagination buttons
${totalPages > 1 ? `
<div style="display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-top:1px solid var(--border-color);">
    <span style="font-size:12px; color:var(--text-muted);">Halaman ${currentPage} dari ${totalPages}</span>
    <div style="display:flex; gap:8px;">
        <button type="button" class="btn btn-secondary" style="width:auto;" ${currentPage <= 1 ? 'disabled' : ''} onclick="(window as any)._herbalPage=${currentPage - 1}; loadTab('herbals')">
            <i class="fas fa-chevron-left"></i> Sebelumnya
        </button>
        <button type="button" class="btn btn-secondary" style="width:auto;" ${currentPage >= totalPages ? 'disabled' : ''} onclick="(window as any)._herbalPage=${currentPage + 1}; loadTab('herbals')">
            Selanjutnya <i class="fas fa-chevron-right"></i>
        </button>
    </div>
</div>
` : ''}
```

---

## Testing Scenarios

### Scenario 1: Pagination
1. Buka tab Herbal
2. Jika data > 10, cek tombol pagination muncul
3. Klik "Selanjutnya" → halaman 2
4. Klik "Sebelumnya" → kembali halaman 1
5. Tombol disabled di halaman pertama/terakhir

### Scenario 2: Select Row
1. Klik baris di tabel
2. Form Koreksi Stok terisi otomatis
3. Badge menampilkan nama produk dan stok
4. Dropdown satuan terisi (dasar + kemasan jika ada)

### Scenario 3: Form Tambah
1. Isi semua field di Form Tambah Produk
2. Submit → produk baru muncul di tabel
3. Jika data > 10, produk baru di halaman terakhir

### Scenario 4: Form Koreksi
1. Select produk dari tabel
2. Pilih jenis pergerakan (Tambah/Keluar)
3. Isi jumlah → preview muncul
4. Submit → stok terupdate, tabel reload

### Scenario 5: Action Buttons
1. Klik "Jual Produk" → modal terbuka
2. Klik "Retur" → modal terbuka
3. Kedua modal berfungsi normal

---

## Responsive Behavior

Layout menggunakan `.inventory-forms-grid` yang sudah responsive:

```css
.inventory-forms-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

@media (max-width: 1200px) {
    .inventory-forms-grid {
        grid-template-columns: 1fr;
    }
}
```

Pada layar kecil (<1200px), forms akan stack vertikal.
