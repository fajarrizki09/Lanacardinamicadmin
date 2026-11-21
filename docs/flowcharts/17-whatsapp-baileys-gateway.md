# Flowchart 17 — WhatsApp Baileys Gateway

## Scope

Alur WhatsApp Gateway lokal berbasis Baileys untuk login QR, penyimpanan session, sinkronisasi otomatis, pengiriman pesan CRM, queue follow-up, dan audit hasil kirim.

> Catatan penamaan: key konfigurasi lama masih memakai `openwa_*` agar kompatibel dengan setting dan endpoint yang sudah ada, tetapi engine lokal yang dipakai adalah Baileys (`@whiskeysockets/baileys`).

```mermaid
flowchart TD
    A[Admin buka Settings / WhatsApp Gateway] --> B[Install dependency server lokal]
    B --> C[Start server Baileys lokal]
    C --> D[FastAPI POST /whatsapp/server/start]
    D --> E[openwa_server/server.js]
    E --> F[Express API port 3000]
    E --> G[Dashboard lokal port 3000]

    F --> H{Session ID tersedia?}
    H -->|Tidak| I[Admin isi session ID default]
    H -->|Ya| J[POST /whatsapp/session/create]
    I --> J

    J --> K[Buat folder auth session]
    K --> L[POST /whatsapp/session/start]
    L --> M[Baileys makeWASocket]
    M --> N{Auth tersimpan?}
    N -->|Belum login| O[Generate QR]
    O --> P[GET /whatsapp/session/qr]
    P --> Q[Admin scan QR dari aplikasi / dashboard]
    Q --> R[Baileys connection.update]
    N -->|Sudah ada auth| R

    R --> S{Status koneksi}
    S -->|open| T[Session connected]
    S -->|qr| O
    S -->|close/loggedOut| U[Session disconnected]
    U --> V{Logged out?}
    V -->|Ya| W[Hapus auth session / login ulang]
    V -->|Tidak| X[Auto reconnect]
    X --> M

    T --> Y[Settings simpan openwa_enabled=true]
    Y --> Z[CRM / Queue siap kirim]

    Z --> AA[Admin review/edit pesan CRM]
    AA --> AB[POST /whatsapp/enqueue]
    AB --> AC[Simpan queue + chatId normalisasi nomor]
    AC --> AD[POST /whatsapp/process-queue]
    AD --> AE[OpenWAClient kompatibel memanggil Baileys API]
    AE --> AF[POST /api/sessions/:sid/messages/send-text]
    AF --> AG{Baileys session connected?}
    AG -->|Tidak| AH[Mark failed: belum login / disconnected]
    AG -->|Ya| AI[sock.sendMessage]
    AI --> AJ{Kirim sukses?}
    AJ -->|Ya| AK[mark_whatsapp_followup_sent + messageId]
    AJ -->|Tidak| AL[mark_whatsapp_followup_failed + retry]
    AH --> AM[Admin cek status / tampilkan QR]
    AK --> AN[Audit log / riwayat WA]
    AL --> AN
```

## Endpoint Aktif

- `GET /whatsapp/server/status` — cek API dan dashboard Node.js di port 3000.
- `POST /whatsapp/server/install` — install dependency `openwa_server`.
- `POST /whatsapp/server/start` — start server lokal Baileys.
- `POST /whatsapp/session/create` — siapkan session auth.
- `POST /whatsapp/session/start` — mulai koneksi Baileys dan generate QR bila belum login.
- `GET /whatsapp/session/qr` — ambil QR login.
- `GET /whatsapp/session/status` — cek status session.
- `POST /whatsapp/send-test` — kirim pesan test.
- `POST /whatsapp/enqueue` — masukkan pesan CRM/follow-up ke queue.
- `POST /whatsapp/process-queue` — proses queue via Baileys.

## Rule Implementasi

- Tidak membuka `web.whatsapp.com` untuk mode otomatis.
- Login tetap wajib melalui QR Baileys.
- Auth session tersimpan di `openwa_server/data/sessions/<session_id>/`.
- Jika session masih valid, Baileys otomatis reconnect tanpa scan QR ulang.
- Jika WhatsApp logout dari HP / device dicabut, status menjadi disconnected dan admin harus login ulang.
- CRM tetap harus meminta admin review/edit pesan sebelum kirim.
- Rate limit queue mengikuti `openwa_rate_limit_per_run`.
- Semua kegagalan kirim masuk retry/failed queue, bukan diam-diam dianggap sukses.
- Fallback `wa.me` hanya digunakan bila gateway Baileys belum aktif atau gagal, bukan alur utama.

## Status Session Baileys

- `idle` — session dibuat tetapi belum start.
- `connecting` — Baileys sedang menghubungkan.
- `qr` — QR login tersedia.
- `connected` — siap kirim pesan.
- `disconnected` — koneksi putus dan menunggu reconnect/login ulang.
- `logged_out` — session tidak valid, auth perlu dihapus/login ulang.

## Struktur Data Runtime

- Login WhatsApp memakai scan QR Baileys. Tidak ada API key untuk gateway lokal.
- `openwa_server/data/sessions/<session_id>/` — credential Baileys.
- `openwa_server/data/sessions/<session_id>/state.json` — status ringan dashboard/API.

## Checklist QA

1. Start server lokal tanpa membuka browser WhatsApp Web.
2. Buat session dan tampilkan QR di aplikasi.
3. Scan QR, status berubah menjadi `connected`.
4. Restart server, session reconnect otomatis tanpa QR baru.
5. Kirim pesan test ke nomor sendiri.
6. Kirim pesan CRM via queue.
7. Matikan koneksi/logout WhatsApp, queue gagal dengan error jelas.
8. Login ulang dan queue bisa diproses kembali.
