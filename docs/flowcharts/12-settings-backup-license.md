# Flowchart 12 — Settings / Backup / License

## Scope

Logic pengaturan aplikasi, backup database, restore database, export data, dan license/admin PIN guard.

```mermaid
flowchart TD
    A[Admin buka Settings] --> B[api/static/modules/settings.js]
    B --> C[GET /settings]
    C --> D[settings.json / AppSettings]

    B --> E[Update clinic profile / invoice footer]
    E --> F[POST /settings]
    F --> G[Validasi input]
    G -->|Tidak valid| H[Tampilkan error aman]
    G -->|Valid| I[Simpan settings]
    I --> J[Audit settings_changed]

    B --> K[Payment Gateway settings]
    K --> L[Enable/disable gateway + provider config]
    L --> I

    B --> M[Backup database]
    M --> N[Require valid license/admin PIN sesuai rule]
    N --> O[helpers/backup_helper.py]
    O --> P[Copy SQLite DB read-safe]
    P --> Q[backups/ folder]
    Q --> R[Rotating backup policy]
    R --> S[Audit database_backup_created]

    B --> T[Restore database]
    T --> U[Wajib license valid + admin PIN]
    U --> V[Admin pilih file backup]
    V --> W[Validasi file backup]
    W --> X{SQLite valid?}
    X -->|Tidak| Y[Tolak restore]
    X -->|Ya| Z[Buat pre-restore backup DB aktif]
    Z --> AA[Stop/block write operation sementara]
    AA --> AB[Replace SQLite DB]
    AB --> AC[Run migration check]
    AC --> AD{Restore sukses?}
    AD -->|Tidak| AE[Rollback ke pre-restore backup]
    AE --> AF[Tampilkan error aman + log detail]
    AD -->|Ya| AG[Reopen DB session]
    AG --> AH[Reload app/server jika perlu]
    AH --> AI[Audit database_restored]

    B --> AJ[Export data]
    AJ --> AK[helpers/export_helper.py]
    AK --> AL[exports/ folder]
    AL --> AM[Audit data_exported]

    AN[Operasi sensitif] --> AO[require_valid_license]
    AO --> AP{License valid?}
    AP -->|Tidak| AQ[Tolak operasi]
    AP -->|Ya| AR{Butuh admin PIN?}
    AR -->|Ya| AS[require_admin_pin]
    AS --> AT{PIN valid?}
    AT -->|Tidak| AU[Tolak]
    AT -->|Ya| AV[Lanjut]
    AR -->|Tidak| AV
    AV --> AW[Audit log]
```

## Logic Notes

- Settings mempengaruhi profil klinik, invoice footer, dan payment gateway.
- Backup database tidak boleh merusak database aktif.
- Restore lebih berisiko daripada backup, sehingga wajib admin PIN dan license valid.
- Export data berbeda dari backup database: export untuk laporan/portable data, backup untuk pemulihan DB penuh.
- Saat restore, write operation harus diblok sementara agar tidak ada transaksi masuk ketika file DB diganti.
- Jika restore gagal, rollback ke pre-restore backup.
- Operasi sensitif seperti void invoice, update payment manual, restore DB, dan license event perlu license guard dan/atau admin PIN.
