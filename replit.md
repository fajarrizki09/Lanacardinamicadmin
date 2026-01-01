# Aplikasi Pasien Bekam - Desktop GUI Application

## Overview
Desktop patient management application for bekam therapy clinics with dynamic point-based pricing system. Built with PySide6 (Qt 6) for modern GUI and SQLAlchemy for optimized database operations.

## Recent Changes (January 1, 2026)

### ✅ Completed Updates & Improvements
1. **Intelligent Import/Export System**
   - Robust JSON export for patients, therapists, and visits.
   - Smart matching logic: Automaps therapists by name and assigns patients to their "usual" therapist if data is missing.
   - Seamless handling of empty or null therapist columns.

2. **Windows Desktop UX Optimization**
   - Modernized UI with a fresh color palette (soft pastels) and rounded corners.
   - Professional dashboard layout with improved spacing and responsiveness.
   - **New**: Added address display in patient list and automatic daily database backups.

3. **Islamic Healing (Sunnah) Calendar 2026**
   - Integrated Hijri sunnah dates (17th, 19th, 21st) into the dashboard.
   - Real-time notification and countdown for upcoming sunnah healing days.

4. **Smart Patient Identifier**
   - Automatic generation of temporary IDs (`TEMP-XXXXXX`) for patients without phone numbers.
   - Simplified registration flow while maintaining database integrity.

5. **Automated Invoice System**
   - Generation of professional PDF invoices for every visit.
   - Automatic linkage between visit records and their respective invoice files.
   - Searchable invoices directly through Windows Search.

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
