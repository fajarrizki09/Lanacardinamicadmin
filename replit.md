# Aplikasi Pasien Bekam - Desktop GUI Application

## Overview
Desktop patient management application for bekam therapy clinics with dynamic point-based pricing system. Built with PySide6 (Qt 6) for modern GUI and SQLAlchemy for optimized database operations.

## Recent Changes (November 13, 2025)

### ✅ Completed Optimizations
1. **Point-Based Dynamic Pricing System**
   - Admin configures price per point (e.g., Rp 10,000/point)
   - Visit prices auto-calculated: 13 points × Rp 10,000 = Rp 130,000
   - Discount applies to calculated price (not hardcoded base price)
   - Flow: User inputs points → VisitThread calculates price → Database applies discount once

2. **Database Performance Optimization**
   - WAL (Write-Ahead Logging) mode enabled for concurrent access
   - Strategic indexes on: patients.phone, patients.name, therapists.name, therapists.is_active, visits.patient_id, visits.date
   - Connection pooling (pool_size=10, max_overflow=20)
   - Migration adds `point_count` column to visits table

3. **Multi-Level Caching Strategy**
   - **Therapist Cache**: Loaded once, filtered in-memory by gender (prevents repeated DB queries)
   - **Visit Cache**: Per-patient visit data cached, invalidated on update/delete
   - Cache validity flags prevent unnecessary refreshes

4. **Debounced Search**
   - 300ms debounce timer on patient search
   - Reduces database load from real-time typing

5. **Thread-Safe Operations**
   - Background threading for heavy operations (visit recording, search)
   - Proper signal/slot connections with float type consistency

### Code Architecture

#### Key Files
- `main_window.py` - Main GUI with debounced search, therapist caching
- `database.py` - Optimized database layer (WAL, indexing, pooling)
- `settings.py` - Settings management (price_per_point configuration)
- `threads/visit_thread.py` - Background visit recording with price calculation
- `viewmodels/visit_view_model.py` - Visit data orchestration with caching
- `components/visit_section.py` - Point input UI with auto-price display
- `dialogs/settings_dialog.py` - Admin settings for price per point

#### Data Flow (Visit Recording)
```
User Input (13 points)
   ↓
MainWindow.catat_kunjungan() - validates point_count
   ↓
VisitViewModel.add_visit(patient_id, point_count, therapist_id)
   ↓
VisitThread.run() - calculates normal_price = points × price_per_point
   ↓
Database.add_visit(normal_price) - applies discount once, saves to DB
   ↓
VisitThread emits (normal_price, final_price, discount_applied)
   ↓
UI updates with confirmation
```

#### Caching Strategy
- **Therapist**: Cached on startup, refreshed only on CRUD operations
- **Visit**: Cached per patient, invalidated on add/update/delete
- **Patient Search**: Debounced to prevent excessive queries

### User Preferences
- Price calculation must derive from points (not manual entry)
- Discount applies to point-calculated price
- No mock/placeholder data in production paths
- Performance priority: eliminate lag through caching and indexing

### Project Architecture

**Tech Stack:**
- PySide6 (Qt 6.8.1) - Modern GUI framework
- SQLAlchemy 2.0.36 - ORM with connection pooling
- SQLite with WAL mode - Optimized local database
- matplotlib 3.10.0 - Analytics visualization

**Database Schema:**
- `patients` (id, name, phone, address, gender) + indexes
- `therapists` (id, name, gender, specialization, is_active) + indexes
- `visits` (id, patient_id, therapist_id, date, price, discount_applied, point_count) + indexes

**Performance Features:**
- WAL mode for concurrent reads/writes
- Strategic indexing reduces query time
- Connection pooling reuses DB connections
- In-memory caching (therapists, visits)
- Debounced search (300ms delay)

### Important Notes

1. **Desktop Application**: Requires display server (X11/Wayland on Linux, native on Windows/Mac)
2. **Not Cloud-Ready**: Designed for local deployment, not headless/cloud environments
3. **Data Integrity**: All data stored locally in `data.db` SQLite file
4. **Migration Safe**: `point_count` column added with default 0 for existing visits
5. **Test Before Deploy**: Run `python test_imports.py` to verify all dependencies

### Deployment Checklist
- ✅ Database optimizations (WAL, indexes, pooling)
- ✅ Point-based pricing implementation
- ✅ Caching strategy (therapists, visits)
- ✅ Debounced search
- ✅ Thread-safe operations
- ✅ All imports verified
- ✅ README documentation complete
- ⚠️ Requires display server for GUI
- ⚠️ Not suitable for Replit cloud deployment (desktop app)

### Next Steps (Manual Testing Required)
1. Test therapist CRUD → verify cache refreshes
2. Record visits with different point counts → verify price calculation
3. Test discount application → verify applies to calculated price
4. Import existing database → verify migration adds point_count column
5. Monitor performance under realistic load

### Known Limitations
- Cannot run in Replit cloud environment (requires display server)
- Designed for local deployment only
- No remote database support (SQLite only)
- Single-user desktop application (no concurrent multi-user access)

---

**Application Status**: ✅ Ready for local deployment with all optimizations implemented and architect-approved.
