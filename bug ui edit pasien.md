**TUGAS: PERBAIKI BUG SCROLL MODAL EDIT PASIEN & RIWAYAT KUNJUNGAN**

Masalah:
Modal "Edit Pasien & Riwayat Kunjungan" pada aplikasi Lancar Dynamic Admin masih tidak bisa di-scroll. Konten riwayat kunjungan terpotong dan pengguna tidak bisa mengakses seluruh data kunjungan di bagian bawah.

**1. Investigasi terlebih dahulu**
- Temukan HTML/template modal Edit Pasien & Riwayat Kunjungan.
- Identifikasi CSS yang mengatur modal, modal body, container riwayat kunjungan, dan footer.
- Periksa seluruh parent element yang menggunakan `overflow: hidden`.
- Periksa konflik `height`, `max-height`, `min-height`, `position: fixed`, dan `display: flex`.
- Periksa apakah ada JavaScript event listener yang menghalangi scroll mouse atau wheel.

**2. Perbaikan yang diharapkan**

Gunakan struktur scroll yang benar:

- Modal memiliki tinggi maksimum sesuai viewport.
- Header modal tetap terlihat.
- Konten utama modal menjadi area scroll vertikal.
- Footer tetap terlihat dan tidak ikut menghilang.
- Gunakan `min-height: 0` pada flex child yang menjadi scroll container.
- Gunakan `overflow-y: auto` pada container konten utama yang tepat.
- Gunakan `overscroll-behavior: contain` jika diperlukan.
- Pastikan scroll tidak terkunci oleh parent element.

Contoh konsep CSS (sesuaikan dengan struktur aktual aplikasi):

```css
.modal-dialog {
    max-height: calc(100vh - 48px);
    display: flex;
    flex-direction: column;
}

.modal-header,
.modal-footer {
    flex-shrink: 0;
}

.modal-body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overscroll-behavior: contain;
}
```

Jangan menyalin CSS tersebut secara membabi buta. Sesuaikan dengan struktur modal yang ditemukan.

**3. Kriteria keberhasilan**
- Mouse wheel dapat menggulir seluruh konten modal.
- Scrollbar dapat digunakan untuk menggulir.
- Semua riwayat kunjungan bisa diakses.
- Tombol Hapus Pasien Secara Permanen tetap dapat diakses.
- Header dan tombol Simpan Semua Perubahan tetap terlihat.
- Tidak terjadi scroll ganda yang mengganggu.
- Tampilan tetap responsif pada layar kecil.
- Modal lain tidak mengalami regresi.

**4. Batasan pengerjaan**
- Jangan mengubah logika penyimpanan pasien.
- Jangan mengubah database atau struktur tabel.
- Jangan mengubah fitur riwayat kunjungan.
- Jangan mengubah logika lisensi.
- Jangan melakukan refactoring yang tidak diperlukan.
- Modifikasi hanya file yang benar-benar berkaitan dengan masalah ini.

**5. Pengujian**
Uji modal dengan:
- 1 riwayat kunjungan.
- 2 riwayat kunjungan.
- 10 atau lebih riwayat kunjungan.
- Resolusi layar rendah.
- Scroll menggunakan mouse wheel dan scrollbar.

Laporkan file yang diubah, penyebab utama bug, solusi, dan hasil pengujian.