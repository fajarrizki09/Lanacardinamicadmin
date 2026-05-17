# AI Context

- Project: Python FastAPI + PySide6 WebEngine + frontend static JS/TS.
- Source TS ada di `api/static/ts`; output JS ada di `api/static/modules`.
- Jangan edit JS hasil build jika source TS sudah ada.
- Worktree masih kotor; jangan pernah pakai `git add .`.
- Semua batch harus kecil, scoped, dan mudah direview.
- Jangan commit otomatis.
- Jangan audit seluruh repo kecuali diminta.
- Payment provider available: `gateway_mock`/Pembayaran Internal dan `midtrans`.
- Provider coming soon: `xendit`, `duitku`, `doku`, `tripay`; tidak boleh dipakai transaksi.
- Revenue rule: `paid`/`partial` masuk revenue; `unpaid`/`pending`/`void`/`free` tidak masuk paid revenue.
- License rule: fail-closed; `status == "active"` saja tidak valid; expiry wajib untuk offline grace.
- Delete therapist/service: boleh hard delete hanya jika belum punya riwayat kunjungan.
- Sisa area berisiko: `patients.js`, `modal.js`, `style.css`, CRM, settings/payment leftover, build/release files.
- Mode hemat token: baca hanya file scope, output pendek, command terbatas.
