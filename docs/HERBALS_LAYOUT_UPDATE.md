# Update Layout Tab Herbal

## Tanggal: 20 Mei 2026

## Perubahan yang Dilakukan

Layout tab Herbal telah diubah agar sama dengan layout tab Inventory untuk konsistensi UI/UX.

### Struktur Layout Baru

1. **Stat Cards** (paling atas)
   - Tersedia (hijau)
   - Menipis (kuning)
   - Habis (merah)

2. **Action Buttons** (di bawah stat cards)
   - Jual Produk (hijau gradient)
   - Retur (abu-abu)

3. **Tabel Monitoring Produk/Herbal** (tengah)
   - Pagination 10 items per halaman
   - Kolom: Produk, Stok/Kemasan, Harga, Margin, Status, Aksi
   - Klik baris untuk select
   - Tombol navigasi halaman jika data > 10 items

4. **Forms Bersebelahan** (bawah)
   - **Kiri**: Form Tambah Produk Baru
   - **Kanan**: Form Koreksi Stok Manual
   - Menggunakan class `.inventory-forms-grid`

### Detail Perubahan Teknis

#### File: `api/static/ts/herbals.ts`

1. **Pagination Logic**
   ```typescript
   const currentPage = (window as any)._herbalPage || 1;
   const itemsPerPage = 10;
   const totalPages = Math.ceil(data.length / itemsPerPage);
   const startIndex = (currentPage - 1) * itemsPerPage;
   const endIndex = startIndex + itemsPerPage;
   const paginatedData = data.slice(startIndex, endIndex);
   ```

2. **Pagination Buttons**
   - Tombol "Sebelumnya" dan "Selanjutnya"
   - Disabled state untuk halaman pertama/terakhir
   - Onclick: `(window as any)._herbalPage=${page}; loadTab('herbals')`

3. **Helper Text Update**
   - Sebelumnya: "Klik baris produk/herbal di tabel"
   - Sekarang: "Klik baris di tabel atas"

4. **Form Layout**
   - Dihapus: Layout `.herbal-workspace` dengan tabel kiri dan form kanan
   - Ditambahkan: Layout `.inventory-forms-grid` dengan form bersebelahan di bawah

5. **Stock Preview**
   - Sekarang menggunakan `display: none` saat tidak ada data
   - Muncul otomatis saat ada input valid

### Struktur HTML Baru

```
┌─────────────────────────────────────────────┐
│  Stat Cards (3 kolom)                       │
├─────────────────────────────────────────────┤
│  Action Buttons (Jual | Retur)              │
├─────────────────────────────────────────────┤
│                                             │
│  Tabel Monitoring (10 items/page)          │
│  [Pagination buttons jika perlu]           │
│                                             │
├──────────────────────┬──────────────────────┤
│  Form Tambah Produk  │  Form Koreksi Stok  │
│                      │                      │
└──────────────────────┴──────────────────────┘
│  Riwayat Koreksi                            │
└─────────────────────────────────────────────┘
```

### Fitur yang Tetap Berfungsi

✅ Klik baris tabel untuk select produk
✅ Edit dan hapus produk dari tabel
✅ Form tambah produk baru
✅ Form koreksi stok dengan preview
✅ Modal jual produk
✅ Modal retur penjualan
✅ Riwayat koreksi stok
✅ Validasi form dan stock
✅ Toast notifications

### Testing Checklist

- [ ] Pagination berfungsi (prev/next)
- [ ] Select row dari tabel mengisi form koreksi
- [ ] Form tambah produk submit berhasil
- [ ] Form koreksi stok submit berhasil
- [ ] Modal jual produk berfungsi
- [ ] Modal retur berfungsi
- [ ] Edit produk dari tabel
- [ ] Hapus produk dari tabel
- [ ] Stat cards menampilkan angka yang benar
- [ ] Responsive di berbagai ukuran layar

### Catatan

- Variable pagination: `(window as any)._herbalPage`
- Reload tab: `loadTab('herbals')`
- Items per page: 10 (hardcoded)
- Layout class: `.inventory-forms-grid` (shared dengan inventory)

### File yang Diubah

1. `api/static/ts/herbals.ts` - Source TypeScript
2. `api/static/app.js` - Compiled JavaScript (auto-generated)

### Compile Command

```bash
npm run build:ts
```
