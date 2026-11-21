# Flowchart 09 — CRM Follow-up WhatsApp

## Scope

Logic CRM follow-up, segmentasi pasien, contact preference, send lock, pesan WhatsApp semi-manual, dan audit log WA.

```mermaid
flowchart TD
    A[Admin buka CRM Follow-up] --> B[api/static/modules/crm.js]
    B --> C[GET /crm/patients]
    C --> D[helpers/crm_analysis_helper.py]
    D --> E[Ambil patient + visits + followup + tags]
    E --> F[Hitung segment]

    F --> G{Segment pasien}
    G -->|Belum follow-up| H[Perlu follow-up]
    G -->|Lama tidak datang| I[Reaktivasi]
    G -->|Voucher cocok| J[Promo/voucher]
    G -->|Sudah follow-up| K[Monitoring]

    B --> L[Admin buka detail CRM pasien]
    L --> M[Load contact_preference]
    M --> N{Preference}
    N -->|Jangan dihubungi| O[Block semua WA action]
    O --> O1[Log skipped_preference]
    N -->|Jangan promo| P{Pesan promo?}
    P -->|Ya| O
    P -->|Tidak| Q[Cek send lock]
    N -->|Boleh| Q

    Q --> R[Cek last_contacted_at]
    R --> S{Sudah dihubungi dalam X hari?}
    S -->|Ya| T[Tampilkan warning/block default 7 hari]
    T --> T1{Override diizinkan?}
    T1 -->|Tidak| T2[Log skipped_send_lock]
    T1 -->|Ya| T3[Require permission/admin PIN]
    T3 --> Q1[Generate template message]
    S -->|Tidak| Q1

    Q1 --> U[Admin review/edit pesan]
    U --> V[Log drafted]
    V --> W{Mode WhatsApp}
    W -->|Default semi-manual| X[Generate wa.me URL]
    X --> Y[Open WhatsApp Web]
    Y --> Z[Log opened]
    Z --> AA[Admin kirim manual]
    AA --> AB[Admin klik konfirmasi terkirim]
    AB --> AC[Log confirmed_sent]

    W -->|Future optional Puppeteer| AD{enable_whatsapp_puppeteer?}
    AD -->|False| X
    AD -->|True| AE[Admin klik Send untuk 1 pasien]
    AE --> AF[Validate phone + preference + send lock]
    AF --> AG[Manual QR login WA Web jika perlu]
    AG --> AH[Send message]
    AH --> AI{Send sukses?}
    AI -->|Ya| AC
    AI -->|Tidak| AJ[Log failed]

    AC --> AK[Update patient_followups]
    AJ --> AK
```

## Status Log

- `drafted`
- `opened`
- `confirmed_sent`
- `failed`
- `skipped_preference`
- `skipped_send_lock`

## Logic Notes

- Default mode tetap semi-manual.
- Tidak ada bulk blasting.
- Tidak ada auto-send background.
- Tidak bypass QR WhatsApp.
- Admin tetap review/edit pesan sebelum kirim.
- Contact preference harus dihormati.
- Jika `contact_preference = jangan dihubungi`, semua WA action diblokir.
- Jika `contact_preference = jangan promo`, pesan promo diblokir tetapi pesan non-promo seperti follow-up kesehatan boleh lanjut.
- Send lock default misalnya 7 hari dari `last_contacted_at`.
- Override send lock hanya boleh jika ada permission/admin PIN, bila fitur override disediakan.
- Semua action harus masuk `crm_whatsapp_logs`.
