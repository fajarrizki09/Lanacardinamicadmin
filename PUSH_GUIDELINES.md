# Aturan Push ke GitHub & Rilis Versi

File ini adalah panduan otomatis yang harus diikuti setiap kali ada perubahan kode yang akan di-push dan di-release ke GitHub.

## Alur Wajib (Checklist)

1. **Baca file tugas/bug** terlebih dahulu (mis. `bug ui edit pasien.md`, `bug lisensi.md`, `ui_terapi.md`)
2. **Analisa kode** terkait sebelum mengubah apa pun
3. **Lakukan perbaikan/fitur** pada file sumber yang relevan
4. **Jangan ubah** fungsi penyimpanan, perhitungan harga, API, database, atau modul lain yang tidak terkait
5. **Uji coba** jika ada tes (mis. `python -m pytest tests/`)
6. **Naikan versi aplikasi** di semua file versi:
   - `version.py` → `APP_VERSION = "X.Y.Z"`
   - `version.iss` → `#define MyAppVersion "X.Y.Z"`
   - `src-tauri/tauri.conf.json` → `"version": "X.Y.Z"`
   - `src-tauri/Cargo.toml` → `version = "X.Y.Z"`
   - `src-tauri/src/main.rs` → `app_version: "X.Y.Z"`
   - Gunakan `python tools/bump-version.py` untuk bump otomatis
7. **Update `CHANGELOG.md`** dengan entri rinci di paling atas:
   - Tanggal rilis
   - Judul perbaikan/fitur
   - Daftar perubahan detail dengan file yang diubah
   - Prioritas (CRITICAL / HIGH / MEDIUM / LOW)
8. **Commit** dengan pesan deskriptif yang menyebutkan versi dan inti perubahan
9. **Buat tag Git** berformat `vX.Y.Z` dengan pesan anotasi
10. **Push commit dan tag** ke GitHub (`origin`)
11. **Buat GitHub Release** via `gh release create` dengan catatan rilis rinci

## Format Entri CHANGELOG.md

```markdown
## 2026-11-21 - Judul Perbaikan (vX.Y.Z)

**🔴 PRIORITAS - KETERANGAN**

### Nama Perbaikan
- **FIXED/ADDED/IMPROVED:** Keterangan rinci apa yang diubah
- File: `path/to/file.js`
```

## Format Pesan Commit

```
type: deskripsi singkat (vX.Y.Z)

- Detail perubahan 1
- Detail perubahan 2
- chore: bump version to X.Y.Z
```

Contoh:
```
fix: edit pasien modal tidak bisa scroll (v1.7.50)

- Modal Edit Pasien & Riwayat Kunjungan: layout tiga area (header/content/footer)
- Konten: flex:1, min-height:0, overflow-y-aktif agar scrollbar muncul
- Footer: tombol Hapus Pasien selalu terlihat, tidak tertutup scroll
- chore: bump version to 1.7.50
```

## Format Tag Git

```
vX.Y.Z
```

Pesan anotasi tag:
```
Release vX.Y.Z - Judul Singkat Perubahan
```

## Format GitHub Release Notes

```markdown
## Judul Rilis (vX.Y.Z)

- Poin perubahan 1
- Poin perubahan 2
- Version: X.Y.W → X.Y.Z
```

## File Versi yang Harus Sinkron

Selalu periksa setelah bump:
- `version.py`
- `version.iss`
- `src-tauri/tauri.conf.json`
- `src-tauri/Cargo.toml`
- `src-tauri/src/main.rs`

Semua harus memiliki versi yang sama (X.Y.Z).

## Contoh Selesai

Lihat riwayat commit dan tag yang sudah ada:
- `v1.7.48` — License Lifetime Regression Fixes
- `v1.7.49` — UI/UX Polish Halaman Layanan Terapi
- `v1.7.50` — Perbaiki Scroll Edit Pasien & Riwayat Kunjungan