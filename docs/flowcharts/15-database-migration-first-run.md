# Flowchart 15 — Database Migration & First Run

## Scope

Flow database first run, schema version, migration, backup pre-migration, dan wizard awal aplikasi.

```mermaid
flowchart TD
    A[App start] --> B[Resolve DB path]
    B --> C{DB exists?}
    C -->|Tidak| D[Create DB baru]
    C -->|Ya| E[Open DB]
    D --> F[Create base schema]
    E --> G[Read app_meta.db_version]
    F --> G

    G --> H[Compare dengan DB_SCHEMA_VERSION]
    H --> I{Perlu migration?}
    I -->|Tidak| J[Check first_run/status]
    I -->|Ya| K[Create pre-migration backup]
    K --> L[Run migrations step by step]
    L --> M{Step sukses?}
    M -->|Tidak| N[Rollback/restore backup]
    N --> O[Log migration error]
    O --> P[Show safe error]
    M -->|Ya| Q[Update db_version]
    Q --> R[Log migration success]
    R --> J

    J --> S{First run complete?}
    S -->|Ya| T[Continue startup]
    S -->|Tidak| U[Tampilkan first-run wizard]
    U --> V[Setup profil klinik]
    V --> W{Seed demo data?}
    W -->|Ya| X[Optional seed demo data]
    W -->|Tidak| Y[Skip seed]
    X --> Z[Mark first_run complete]
    Y --> Z
    Z --> T
```

## Logic Notes

- Migration harus step-by-step dan idempotent jika memungkinkan.
- Pre-migration backup wajib sebelum mengubah schema database lama.
- Jika migration gagal, restore backup atau pertahankan backup dan blok startup dengan pesan aman.
- `app_meta.db_version` menjadi sumber versi schema lokal.
- First-run wizard hanya berjalan jika setup awal belum complete.
- Seed demo data harus opsional agar data produksi tidak tercampur data contoh.
