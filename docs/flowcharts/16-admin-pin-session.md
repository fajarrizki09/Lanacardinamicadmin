# Flowchart 16 — Admin PIN Session

## Scope

Flow verifikasi admin PIN untuk operasi sensitif, session unlock, timeout, dan batas keamanan penyimpanan PIN.

```mermaid
flowchart TD
    A[Admin melakukan operasi sensitif] --> B{Admin PIN required?}
    B -->|Tidak| C[Lanjut operasi]
    B -->|Ya| D{PIN session masih aktif?}
    D -->|Ya| C
    D -->|Tidak| E[Minta input PIN]
    E --> F[POST validasi PIN ke backend]
    F --> G{PIN benar?}
    G -->|Tidak| H[Tolak operasi]
    G -->|Ya| I[Unlock session dengan timeout]
    I --> J[Set last_activity]
    J --> C

    C --> K[Monitor idle time]
    K --> L{Idle > 15 menit?}
    L -->|Tidak| M[Session tetap aktif]
    L -->|Ya| N[Expire PIN session]
    N --> O[Operasi sensitif berikutnya minta PIN ulang]
```

## Logic Notes

- Idle timeout default misalnya 15 menit.
- PIN tidak boleh disimpan di `localStorage`.
- Validasi PIN harus lewat backend.
- Jika perlu menyimpan session unlock di frontend, simpan hanya token/session state non-secret dengan expiry pendek.
- Operasi sensitif meliputi void invoice, update payment manual, restore database, perubahan license, dan operasi lain sesuai rule.
- Semua percobaan gagal dan sukses untuk operasi sensitif idealnya masuk audit log tanpa menyimpan nilai PIN.
