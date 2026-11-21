# Flowchart 02 — Startup Desktop & Server

## Scope

Alur aplikasi saat dibuka dari desktop shell PySide6 WebEngine sampai FastAPI local server, database, license, dan UI siap dipakai.

```mermaid
flowchart TD
    A[User menjalankan aplikasi] --> B[main.py / desktop entry]
    B --> C[Resolve app paths]
    C --> D[Create missing runtime folders]
    D --> D1[invoices/]
    D --> D2[backups/]
    D --> D3[exports/]
    D --> D4[logs/]
    D --> D5[.local/]

    D --> E[Load settings.json / default settings]
    E --> F{Database SQLite ada?}
    F -->|Tidak| G[Create database baru]
    F -->|Ya| H[Open database]
    G --> I[Run migration check]
    H --> I
    I --> J{Migration needed?}
    J -->|Tidak| M[Start FastAPI local server]
    J -->|Ya| K[Backup DB sebelum migration]
    K --> L[Run database migration]
    L --> L1{Migration sukses?}
    L1 -->|Tidak| L2[Restore/keep backup + tampilkan error aman]
    L2 --> L3[Tulis detail teknis ke logs/]
    L1 -->|Ya| M

    M --> N[Register routes]
    N --> N1[patients / visits]
    N --> N2[invoices / payments]
    N --> N3[inventory / herbals]
    N --> N4[crm / reports]
    N --> N5[settings / license]
    N --> O{Server aktif?}
    O -->|Tidak| P[Jangan buka UI kosong]
    P --> P1[Tampilkan error screen]
    P1 --> P2[Tulis detail ke logs/api_errors.log]
    O -->|Ya| Q[Open PySide6 WebEngine]

    Q --> R[Load local URL FastAPI]
    R --> S[api/templates/index.html]
    S --> T[Load CSS + api/static/modules/*.js]
    T --> U[Initial dashboard/API calls]
    U --> V[Check license]
    V --> W{License valid?}
    W -->|Tidak| X[Limited / block mode]
    W -->|Ya| Y[App ready]
```

## Logic Notes

- Desktop shell PySide6 WebEngine hanya container UI; logic utama tetap di FastAPI local server.
- UI web modular aktif berada di `api/static/modules/*.js` hasil build dari TypeScript.
- Runtime output berada di `invoices/`, `backups/`, `exports/`, `logs/`, dan `.local/`.
- Migration harus didahului backup agar database aktif bisa dipulihkan jika migration gagal.
- Jika server gagal start, WebEngine tidak boleh dibuka kosong; tampilkan error screen/log yang aman untuk user.
- Jika license tidak valid, aplikasi masuk limited/block mode sesuai rule fitur.
- Operasi sensitif tetap perlu license guard dan/atau admin PIN walaupun aplikasi sudah ready.
