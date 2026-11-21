# Flowchart 14 — Error Handling Global

## Scope

Flow global penanganan error dari request FastAPI sampai pesan error tampil di UI.

```mermaid
flowchart TD
    A[Request masuk ke FastAPI] --> B[Route handler]
    B --> C[Validasi input]
    C --> D{Validation valid?}
    D -->|Tidak| E[Return 422/400 safe user message]
    D -->|Ya| F[Business rule check]

    F --> G{Business rule valid?}
    G -->|Tidak| H[Return 400/409 pesan aman]
    G -->|Ya| I[DB operation]

    I --> J{DB operation sukses?}
    J -->|Ya| K[Success response]
    J -->|Tidak expected| L[Map known DB/business error]
    L --> H
    J -->|Unexpected error| M[Log detail teknis ke logs/api_errors.log]
    M --> N[Return generic error ke UI]

    E --> O[UI tampilkan toast/modal mudah dipahami]
    H --> O
    N --> O
    K --> P[UI update state / reload data]
```

## Logic Notes

- Pesan untuk user harus aman dan mudah dipahami.
- Detail teknis seperti traceback, SQL, path internal, token, atau secret hanya boleh masuk log teknis.
- Business rule error memakai status seperti 400 atau 409 sesuai konteks.
- Validation error tidak boleh menjalankan DB write.
- Unexpected error harus dicatat ke `logs/api_errors.log` atau log error terstruktur lain.
- UI sebaiknya menampilkan toast/modal dengan aksi yang jelas: ulangi, cek input, atau hubungi support.
