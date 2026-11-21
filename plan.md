# Rencana Perbaikan Aplikasi Lancar Dynamic Admin

## 1. Frontend & UI
- [ ] Migrasi ke framework modern (React/Vue/Svelte + Vite) di folder `ui/` terpisah
- [ ] State management: Pinia/Zustand/Redux untuk state global
- [ ] Component library: shadcn/ui, Radix UI, atau PrimeVue
- [ ] TypeScript strict mode: `strict: true`, `noUncheckedIndexedAccess: true`

## 2. Backend (FastAPI)
- [ ] Dependency injection dengan `Depends()` untuk DB session, auth, settings
- [ ] Pydantic v2: `model_config = ConfigDict(from_attributes=True)`
- [ ] Async SQLAlchemy: migrasi ke `asyncpg` + `async_sessionmaker`
- [ ] Rate limiting per-endpoint (sudah pakai `slowapi`)
- [ ] OpenAPI docs hanya di dev mode

## 3. Database
- [ ] Migrasi Alembic untuk schema changes
- [ ] Connection pooling: `pool_pre_ping=True`, `pool_recycle=3600`
- [ ] Indexes pada kolom sering query (patient.nik, invoice.date, dll)

## 4. Desktop (Tauri/PySide6)
- [ ] Sidecar communication via Tauri `invoke`/`listen` (bukan HTTP localhost)
- [ ] Auto-update via Tauri updater (GitHub releases)
- [ ] System tray: minimize to tray + background sync WhatsApp
- [ ] Code signing untuk distribusi production

## 5. WhatsApp Gateway (Baileys)
- [ ] Multi-device support dengan reconnection robust
- [ ] Session persistence ke SQLite (bukan file system)
- [ ] Queue system: Redis/BullMQ untuk antrian pesan (retry, scheduling)

## 6. Security
- [ ] CSP ketat dengan `nonce` untuk inline scripts
- [ ] Input sanitization `bleach` di semua endpoint
- [ ] Audit log immutable append-only

## 7. Testing & Quality
- [ ] E2E tests: Playwright untuk flow kritis
- [ ] Contract tests: Pact untuk API frontend-backend
- [ ] Load test: k6/Locust untuk API endpoints

## 8. DevOps
- [ ] Docker Compose untuk local dev (PostgreSQL + Redis + API + WhatsApp)
- [ ] Staging environment untuk UAT
- [ ] Monitoring: Sentry (error tracking), Prometheus/Grafana (metrics)

---

## Prioritas Tinggi (Quick Wins)
1. [ ] Pisah frontend ke folder `ui/` dengan Vite + React
2. [ ] Setup Alembic untuk DB migration
3. [ ] Enable Tauri auto-updater
4. [ ] Tambah Docker Compose untuk dev

## Status CI/CD (Selesai)
- [x] GitHub Actions workflow untuk Tauri build (`.github/workflows/tauri-build.yml`)
- [x] Auto-build NSIS installer pada push ke main/release/tag `v*`
- [x] Upload artifact (30 hari retention)
- [x] Auto-create GitHub Release dengan `.exe` pada tag push
- [x] Python virtualenv setup untuk PyInstaller sidecar
- [x] openwa_server npm install step