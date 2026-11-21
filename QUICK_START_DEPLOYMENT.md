# Quick Start Guide - Bug Fix Deployment
## Panduan Cepat Deploy Semua Bug Fixes

**Estimasi Waktu:** 30 menit  
**Tingkat Kesulitan:** Mudah  
**Status:** ✅ Siap Deploy

---

## Langkah 1: Install Dependencies (5 menit)

```bash
# Install dependencies baru
pip install bleach==6.1.0 slowapi==0.1.9

# Atau install semua dari requirements.txt
pip install -r requirements.txt
```

**Verifikasi:**
```bash
python -c "import bleach; import slowapi; print('✓ Dependencies installed')"
```

---

## Langkah 2: Run Database Migration (2 menit)

```bash
# Jalankan migration untuk membuat indexes
python scripts/migrate_phase3_indexes.py
```

**Expected Output:**
```
Phase 3 Database Migration
==================================================
Creating indexes...
✓ Created index: idx_visit_service_name
✓ Created index: idx_visit_payment_status
✓ Created index: idx_herbal_tx_visit_group
✓ Created index: idx_herbal_tx_date_type

Verifying indexes...
✓ Verified: idx_visit_service_name
✓ Verified: idx_visit_payment_status
✓ Verified: idx_herbal_tx_visit_group
✓ Verified: idx_herbal_tx_date_type

Summary:
Created: 4 indexes
Skipped: 0 indexes
==================================================
Migration completed successfully!
```

---

## Langkah 3: Test Financial Validator (2 menit)

```bash
# Test overflow validation
python helpers/financial_validator.py
```

**Expected Output:**
```
Financial Validator Tests
==================================================
✓ Valid price: Rp 50.000,50
✓ Overflow detected: price tidak boleh lebih dari 99.999.999,99
✓ Valid total: Rp 450.000,00
✓ Overflow detected: total (Rp 199.999.998,00) melebihi batas maksimum Rp 99.999.999,99
✓ Safe add: Rp 60.000,00
==================================================
```

---

## Langkah 4: Verify All Fixes (5 menit)

### Test 1: Database Precision (Phase 1)
```python
from database import DatabaseManager
from decimal import Decimal

db = DatabaseManager()

# Test Numeric precision
price = Decimal("12345.67")
print(f"✓ Price precision: {price}")  # Should be exact
```

### Test 2: Error Logging (Phase 2)
```python
# Check logs for stack traces
# Logs should now include full exception details with logger.exception()
```

### Test 3: Database Indexes (Phase 3)
```bash
# Verify indexes exist
sqlite3 rumahsehat.db "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"
```

**Expected Output:**
```
idx_visit_service_name
idx_visit_payment_status
idx_herbal_tx_visit_group
idx_herbal_tx_date_type
```

### Test 4: Input Sanitization (Phase 4)
```python
from helpers.input_sanitizer import sanitize_name, sanitize_phone

# Test XSS prevention
dirty = "<script>alert('XSS')</script>John Doe"
clean = sanitize_name(dirty)
print(f"✓ Sanitized: {clean}")  # Should be "John Doe"

# Test phone validation
phone = sanitize_phone("081234567890")
print(f"✓ Valid phone: {phone}")  # Should pass
```

---

## Langkah 5: Optional - Apply Rate Limiting (10 menit)

**File:** `api/main.py`

```python
from fastapi import FastAPI, Request
from helpers.rate_limiter import limiter, get_limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI()

# Add rate limiter to app state
app.state.limiter = limiter

# Add exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to sensitive endpoints
@app.post("/api/admin/verify-pin")
@limiter.limit("10/minute")  # Max 10 PIN attempts per minute
async def verify_pin(request: Request, pin: str):
    ...

@app.post("/api/patients")
@limiter.limit("60/minute")  # Max 60 patient additions per minute
async def add_patient(request: Request, data: dict):
    ...
```

---

## Langkah 6: Optional - Apply Input Sanitization (10 menit)

**File:** `api/routes/patients.py`

```python
from helpers.input_sanitizer import sanitize_name, sanitize_phone, sanitize_address

@router.post("/patients")
async def add_patient(data: dict):
    # Sanitize input before database insertion
    clean_name = sanitize_name(data["name"])
    clean_phone = sanitize_phone(data["phone"])
    clean_address = sanitize_address(data.get("address", ""))
    
    # Use sanitized data
    patient = db.add_patient(
        name=clean_name,
        phone=clean_phone,
        address=clean_address
    )
    return patient
```

---

## Langkah 7: Optional - Apply Financial Validation (10 menit)

**File:** `api/routes/herbals.py`

```python
from helpers.financial_validator import (
    validate_price, validate_quantity, validate_total,
    FinancialValidationError
)
from helpers.error_messages import validation_error, ErrorCode

@router.post("/herbal-sales")
async def add_herbal_sale(data: dict):
    try:
        # Validate financial data
        price = validate_price(data["price"])
        quantity = validate_quantity(data["quantity"])
        total = validate_total(price, quantity, data.get("discount", 0))
        
        # Use validated data
        sale = db.add_herbal_sale(
            price=price,
            quantity=quantity,
            total=total
        )
        return sale
    except FinancialValidationError as e:
        error = validation_error(
            field="price",
            message=str(e),
            code=ErrorCode.VALIDATION_OUT_OF_RANGE
        )
        raise error.to_http_exception(status_code=400)
```

---

## Langkah 8: Optional - Apply Standardized Errors (10 menit)

**File:** `api/routes/patients.py`

```python
from helpers.error_messages import (
    patient_not_found_error,
    duplicate_phone_error,
    invalid_phone_error
)

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    patient = db.get_patient(patient_id)
    if not patient:
        error = patient_not_found_error()
        raise error.to_http_exception(status_code=404)
    return patient

@router.post("/patients")
async def add_patient(data: dict):
    # Check duplicate phone
    existing = db.get_patient_by_phone(data["phone"])
    if existing:
        error = duplicate_phone_error(data["phone"])
        raise error.to_http_exception(status_code=409)
    
    # Add patient
    patient = db.add_patient(**data)
    return patient
```

---

## Langkah 9: Optional - Apply Enhanced Audit Logging (5 menit)

**File:** `api/routes/patients.py`

```python
from helpers.audit_helper import log_audit_with_request

@router.post("/patients")
async def add_patient(request: Request, data: dict):
    patient = db.add_patient(**data)
    
    # Log with IP and user agent
    log_audit_with_request(
        request=request,
        action="add_patient",
        entity_type="patient",
        entity_id=patient.id,
        details=f"Added patient: {patient.name}",
        metadata={"phone": patient.phone}
    )
    
    return patient
```

---

## Langkah 10: Restart Application (1 menit)

```bash
# Stop current application
# Ctrl+C or kill process

# Start application
python main.py

# Or with uvicorn
uvicorn api.main:app --reload
```

---

## Verification Checklist

### Phase 1: Critical Bugs ✅
- [ ] Database uses `Numeric(10,2)` for prices
- [ ] All database operations have rollback handlers
- [ ] All queries use parameterized queries (no string concatenation)
- [ ] Phone validation enforced at all entry points

### Phase 2: High Priority Bugs ✅
- [ ] Error logs include stack traces with `logger.exception()`
- [ ] Database sessions are thread-local
- [ ] Phone validation comprehensive (08xxxxxxxxxx format)
- [ ] TTLCache configured with maxsize=1000, ttl=600s

### Phase 3: Medium Priority Bugs ✅
- [ ] Backup restore validates integrity before restore
- [ ] 4 database indexes created and verified
- [ ] Therapist assignment uses row-level locking
- [ ] Herbal items validated with Pydantic schemas

### Phase 4: Low Priority Bugs ✅
- [ ] Dependencies installed (bleach, slowapi)
- [ ] Helper modules created (6 files)
- [ ] Rate limiting configured (optional)
- [ ] Input sanitization applied (optional)
- [ ] Financial validation applied (optional)
- [ ] Standardized errors applied (optional)
- [ ] Enhanced audit logging applied (optional)

---

## Testing Recommendations

### Test 1: Add Patient with XSS Payload
```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<script>alert(\"XSS\")</script>John Doe",
    "phone": "081234567890"
  }'
```

**Expected:** Name sanitized to "John Doe"

### Test 2: Test Rate Limiting
```bash
# Send 61 requests in 1 minute
for i in {1..61}; do
  curl -X POST http://localhost:8000/api/patients \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Test$i\",\"phone\":\"08123456789$i\"}"
done
```

**Expected:** 60 succeed, 61st returns 429 (Rate Limit Exceeded)

### Test 3: Test Financial Overflow
```bash
curl -X POST http://localhost:8000/api/herbal-sales \
  -H "Content-Type: application/json" \
  -d '{
    "price": 100000000,
    "quantity": 2
  }'
```

**Expected:** 400 error with message "price tidak boleh lebih dari 99.999.999,99"

### Test 4: Test Standardized Errors
```bash
curl -X GET http://localhost:8000/api/patients/999999
```

**Expected:**
```json
{
  "error_code": "NOT_FOUND_PATIENT",
  "message": "Pasien tidak ditemukan."
}
```

---

## Rollback Plan

### If Issues Occur

**Quick Rollback (Langkah 1-2 only):**
```bash
# Uninstall dependencies
pip uninstall bleach slowapi -y

# Drop indexes
sqlite3 rumahsehat.db "DROP INDEX IF EXISTS idx_visit_service_name;"
sqlite3 rumahsehat.db "DROP INDEX IF EXISTS idx_visit_payment_status;"
sqlite3 rumahsehat.db "DROP INDEX IF EXISTS idx_herbal_tx_visit_group;"
sqlite3 rumahsehat.db "DROP INDEX IF EXISTS idx_herbal_tx_date_type;"

# Restart application
python main.py
```

**Full Rollback (All changes):**
```bash
# Revert to previous commit
git checkout HEAD~1

# Restart application
python main.py
```

---

## Environment Variables (Optional)

Create `.env` file for configuration:

```bash
# Idempotency cache TTL (default: 600 seconds)
IDEMPOTENCY_TTL_SECONDS=600

# Admin idle lock timeout (default: 300000 ms)
ADMIN_IDLE_LOCK_MS=300000

# Rate limit per minute (default: 60 requests/minute)
RATE_LIMIT_PER_MINUTE=60

# Maximum price (default: 99999999.99)
MAX_PRICE=99999999.99
```

---

## Support

### Documentation
- [Final Summary](FINAL_BUG_FIX_SUMMARY.md) - Complete overview
- [Phase 1 Report](PHASE1_IMPLEMENTATION_REPORT.md) - Critical bugs
- [Phase 2 Report](PHASE2_IMPLEMENTATION_REPORT.md) - High priority bugs
- [Phase 3 Report](PHASE3_IMPLEMENTATION_REPORT.md) - Medium priority bugs
- [Phase 4 Report](PHASE4_IMPLEMENTATION_REPORT.md) - Low priority bugs

### Troubleshooting

**Issue:** Dependencies installation fails
```bash
# Solution: Upgrade pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Issue:** Migration script fails
```bash
# Solution: Check database file exists
ls -la rumahsehat.db

# If not exists, create database first
python main.py  # This will create database
python scripts/migrate_phase3_indexes.py
```

**Issue:** Rate limiting not working
```bash
# Solution: Verify slowapi installed
python -c "import slowapi; print(slowapi.__version__)"

# Verify limiter added to app state
# Check api/main.py has: app.state.limiter = limiter
```

---

## Success Criteria

✅ **Deployment Successful If:**
- All dependencies installed without errors
- Database migration completed (4 indexes created)
- Application starts without errors
- All endpoints respond correctly
- Error logs include stack traces
- Audit logs include IP addresses (if applied)
- Rate limiting works (if applied)
- Input sanitization works (if applied)
- Financial validation works (if applied)

---

## Next Steps After Deployment

1. **Monitor logs** for any errors or warnings
2. **Monitor performance** (query times should be faster)
3. **Monitor memory usage** (should be stable)
4. **Monitor rate limit metrics** (if applied)
5. **Collect user feedback** on error messages
6. **Plan Phase 4 optional features** (rate limiting, sanitization, etc.)

---

**Deployment Status:** ✅ **READY**  
**Estimated Time:** 30 minutes (mandatory steps only)  
**Risk Level:** Low (all changes backward compatible)  
**Recommended Approach:** Deploy mandatory steps (1-4), then optional steps (5-9) gradually

---

**Good luck with deployment! 🚀**
