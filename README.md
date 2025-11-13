# 🏥 Aplikasi Pasien Bekam - Versi Optimasi Pro

Aplikasi desktop untuk manajemen data pasien bekam dengan sistem harga dinamis berbasis titik dan performa tinggi.

## ✨ Fitur Utama

### 🆕 Fitur Baru (Versi Optimasi Pro)
- ✅ **Sistem Harga Dinamis Per Titik**: Admin dapat mengatur harga per titik (misal: Rp 10.000/titik, sehingga 13 titik = Rp 130.000)
- ✅ **Auto-Calculate Harga**: Input jumlah titik, harga otomatis terhitung
- ✅ **Database Optimization**: SQLite dengan WAL mode, indexing, dan connection pooling untuk performa maksimal
- ✅ **Debounced Search**: Search dengan debouncing 300ms untuk mengurangi lag
- ✅ **Caching System**: Cache data terapis dan kunjungan untuk menghindari query berulang
- ✅ **Point Tracking**: Setiap kunjungan tercatat dengan jumlah titik

### 📋 Fitur Existing
- **Data Pasien Lengkap**: Nama, nomor HP, jenis kelamin, alamat
- **Manajemen Terapis**: CRUD terapis dengan spesialisasi
- **Auto-Filter Terapis**: Filter otomatis berdasarkan jenis kelamin pasien
- **Sistem Diskon Dinamis**: Konfigurasi diskon melalui pengaturan
- **Riwayat Kunjungan**: Track semua kunjungan dengan detail terapis dan titik
- **Analitik & Grafik**: Visualisasi data kunjungan dan pemasukan
- **Export/Import**: Backup dan restore data

## 🚀 Cara Menjalankan

### Persyaratan Sistem
- **Python 3.11+**
- **Display Server**: X11 atau Wayland untuk GUI (Windows/Mac sudah include)
- **OS**: Linux, Windows, atau MacOS

### Instalasi

1. **Clone atau Download Project**
```bash
git clone <repository-url>
cd <project-folder>
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

Dependencies yang diperlukan:
- **PySide6** (6.8.1) - Qt 6 framework untuk GUI modern
- **SQLAlchemy** (2.0.36) - ORM database dengan optimasi connection pooling
- **matplotlib** (3.10.0) - Visualisasi grafik analitik

3. **Jalankan Aplikasi**
```bash
python main.py
```

**Note**: Aplikasi ini adalah **desktop application** yang dirancang untuk running local dengan GUI. Tidak support headless/cloud deployment tanpa display server.

## 💰 Sistem Harga Dinamis

### Konfigurasi Harga Per Titik

1. Buka aplikasi
2. Klik tombol **"Pengaturan"**
3. Atur **"Harga per Titik"** (default: Rp 10.000)
4. Contoh otomatis ditampilkan: "13 titik = Rp 130.000"
5. Klik **"Simpan"**

### Cara Kerja

- Admin mengatur harga per titik (misal: Rp 10.000)
- Saat catat kunjungan:
  1. Pilih pasien
  2. Input jumlah titik (misal: 13)
  3. Harga otomatis terhitung: 13 × Rp 10.000 = Rp 130.000
  4. Pilih terapis (otomatis filtered by gender)
  5. Klik "Catat Kunjungan"
- Sistem otomatis apply diskon jika pasien sudah mencapai minimum kunjungan

### Contoh Pengaturan

```json
{
    "price_per_point": 10000,
    "base_price": 100000,
    "discount_percentage": 50,
    "min_visits_for_discount": 5
}
```

- **price_per_point**: Harga per 1 titik
- **base_price**: Harga dasar (opsional, untuk backward compatibility)
- **discount_percentage**: Persentase diskon setelah minimum kunjungan
- **min_visits_for_discount**: Jumlah kunjungan minimum untuk dapat diskon

## 📁 Struktur Proyek

```
├── main.py                     # Entry point aplikasi
├── main_window.py              # Main window dengan debouncing
├── database.py                 # Database layer (optimized dengan WAL, indexing)
├── settings.py                 # Manajemen pengaturan (price per point)
├── models/                     # Data models
│   └── patient.py
├── components/                 # UI components
│   ├── patient_form.py
│   ├── patient_list.py
│   ├── visit_section.py        # Updated dengan point input
│   ├── patient_item_widget.py
│   └── action_buttons.py
├── dialogs/                    # Dialog windows
│   ├── edit_patient_dialog.py
│   ├── settings_dialog.py      # Updated dengan price per point
│   ├── therapist_dialog.py
│   └── analytics_dialog.py
├── viewmodels/                 # View models dengan caching
│   └── visit_view_model.py     # ViewModel dengan visit caching
├── threads/                    # Background threads
│   ├── search_thread.py        # Optimized search
│   └── visit_thread.py         # Updated dengan point count
├── helpers/                    # Helper classes
│   └── import_export.py
└── utils/                      # Utilities
    └── styles.py
```

## 🗄️ Database Schema

### Tabel `patients`
- `id`: Integer (Primary Key, indexed)
- `name`: String (Nama pasien, indexed)
- `phone`: String (Nomor HP, indexed, unique)
- `address`: String (Alamat lengkap)
- `gender`: String (Jenis kelamin: Laki-laki/Perempuan)

### Tabel `therapists`
- `id`: Integer (Primary Key)
- `name`: String (Nama terapis, indexed)
- `gender`: String (Jenis kelamin, indexed)
- `specialization`: String (Spesialisasi)
- `is_active`: Boolean (Status aktif, indexed)

### Tabel `visits`
- `id`: Integer (Primary Key)
- `patient_id`: Integer (Foreign Key, indexed)
- `therapist_id`: Integer (Foreign Key)
- `date`: DateTime (Tanggal kunjungan, indexed)
- `price`: Numeric (Harga setelah diskon)
- `discount_applied`: Boolean
- `point_count`: Integer **[BARU]** - Jumlah titik kunjungan

**Indexes untuk Performa:**
- `idx_patient_date`: Composite index pada (patient_id, date)
- Individual indexes pada: patients.phone, patients.name, therapists.name, therapists.is_active

## ⚡ Optimasi Performa

### Database
- **WAL Mode**: Write-Ahead Logging untuk concurrent access
- **Connection Pooling**: Pool size 10, max overflow 20
- **Indexing**: Strategic indexes untuk query cepat
- **Lazy Loading**: Minimize database hits dengan caching

### UI
- **Debounced Search**: 300ms debounce untuk menghindari search berlebihan
- **Cached Data**: Therapists dan visits di-cache untuk avoid repeated queries
- **Background Threading**: Semua operasi berat di background thread

### Memory
- **Expire on Commit**: False untuk reduce refresh overhead
- **Session Scoped**: Proper session management
- **Cache Strategy**: LRU cache untuk visit data per patient

## 🎯 Workflow Penggunaan

### 1. Menambah Pasien Baru
1. Isi form "Tambah Pasien":
   - Nama
   - Nomor HP
   - Jenis Kelamin (dropdown)
   - Alamat
2. Klik **"Tambah Pasien"**

### 2. Mencatat Kunjungan dengan Sistem Titik
1. Pilih pasien dari daftar
2. Input **Jumlah Titik** (misal: 13)
3. Harga otomatis terhitung (13 × harga per titik)
4. Pilih terapis (otomatis filtered by gender)
5. Klik **"Catat Kunjungan"**
6. Sistem otomatis apply diskon jika eligible

### 3. Mengatur Harga Per Titik (Admin)
1. Klik **"Pengaturan"**
2. Ubah **"Harga per Titik"**
3. Lihat contoh perhitungan otomatis
4. Klik **"Simpan"**

### 4. Melihat Analitik
1. Klik **"Analitik"**
2. Filter berdasarkan tanggal
3. Lihat:
   - Total pasien
   - Total kunjungan
   - Total titik
   - Total pemasukan
   - Grafik per bulan

## 📊 Analitik

Fitur analitik mencakup:
- **Total Pasien**: Jumlah pasien terdaftar
- **Total Kunjungan**: Dalam periode tertentu
- **Total Titik**: Aggregate titik dari semua kunjungan
- **Total Pemasukan**: Total revenue
- **Grafik Kunjungan**: Per bulan
- **Grafik Pemasukan**: Per bulan

Filter berdasarkan range tanggal untuk melihat statistik periode specific.

## 🔧 Troubleshooting

### Import Error
Jika mendapat error saat import modules:
```bash
python test_imports.py
```

### Display Error
Jika mendapat error `cannot connect to X server`:
- **Linux**: Pastikan DISPLAY environment variable di-set
- **Windows/Mac**: Pastikan menjalankan dari terminal dengan GUI support
- **Headless Server**: Gunakan virtual display (Xvfb)

### Database Error
Jika database error:
1. Backup file `data.db` jika ada data penting
2. Hapus file `data.db`
3. Restart aplikasi - database akan otomatis dibuat ulang

### Performance Issues
- Aplikasi sudah dioptimasi dengan WAL mode dan indexing
- Jika masih lag, cek:
  - Ukuran database (vacuum jika perlu)
  - RAM available
  - Disk I/O performance

## 🔐 Data & Privacy

- ✅ Semua data disimpan lokal di file `data.db`
- ✅ Tidak ada koneksi ke server eksternal
- ✅ Backup data dengan fitur Export
- ✅ Password dan secrets di-manage dengan aman

## 📝 Catatan Teknis

### Optimasi yang Diterapkan
1. **Database Layer**:
   - SQLite WAL mode untuk concurrent access
   - Strategic indexing untuk query performance
   - Connection pooling untuk reuse connections
   - Lazy loading untuk minimize queries

2. **UI Layer**:
   - Debounced search (300ms) untuk reduce overhead
   - Background threading untuk operations berat
   - Cached therapists data untuk avoid repeated DB calls

3. **Business Logic**:
   - Point-based pricing calculation
   - Automatic discount application
   - Visit caching per patient

### Tech Stack
- **PySide6 (Qt 6)**: Modern, future-proof GUI framework
- **SQLAlchemy 2.0**: Modern ORM dengan async support
- **matplotlib**: Professional data visualization

## 📄 Lisensi

Aplikasi internal untuk manajemen pasien bekam dengan sistem harga dinamis.

---

## 🎉 Fitur Premium

**Sistem Harga Per Titik** adalah fitur premium yang memungkinkan:
- ✅ Fleksibilitas pricing berdasarkan jumlah titik
- ✅ Transparansi harga untuk pasien
- ✅ Mudah adjust pricing tanpa hardcode
- ✅ Tracking akurat berapa titik yang sudah dikerjakan
- ✅ Auto-calculation untuk menghindari human error

**Contoh Penggunaan Real:**
- Admin set: Rp 10.000 per titik
- Pasien A: 13 titik = Rp 130.000
- Pasien B: 20 titik = Rp 200.000
- Pasien C: 15 titik = Rp 150.000

Semua otomatis terhitung, no manual calculation needed!
