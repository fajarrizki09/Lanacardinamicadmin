"""
Custom exception classes for Lancar Dynamic Admin.

Provides structured error handling with proper error codes and messages.
"""

class LancarBaseException(Exception):
    """Base exception for all Lancar-specific errors."""
    error_code = "LANCAR_ERROR"
    default_message = "An error occurred"
    
    def __init__(self, message=None, details=None):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(LancarBaseException):
    """Raised when input validation fails."""
    error_code = "VALIDATION_ERROR"
    default_message = "Validasi data gagal"


class DatabaseError(LancarBaseException):
    """Raised when database operations fail."""
    error_code = "DATABASE_ERROR"
    default_message = "Operasi database gagal"


class PaymentError(LancarBaseException):
    """Raised when payment operations fail."""
    error_code = "PAYMENT_ERROR"
    default_message = "Operasi pembayaran gagal"


class StockError(LancarBaseException):
    """Raised when stock operations fail."""
    error_code = "STOCK_ERROR"
    default_message = "Operasi stok gagal"


class AuthenticationError(LancarBaseException):
    """Raised when authentication fails."""
    error_code = "AUTH_ERROR"
    default_message = "Autentikasi gagal"


class LicenseError(LancarBaseException):
    """Raised when license validation fails."""
    error_code = "LICENSE_ERROR"
    default_message = "Validasi lisensi gagal"


class IdempotencyError(LancarBaseException):
    """Raised when idempotency check fails."""
    error_code = "IDEMPOTENCY_ERROR"
    default_message = "Request sedang diproses"


class ConcurrencyError(LancarBaseException):
    """Raised when concurrent operation conflicts occur."""
    error_code = "CONCURRENCY_ERROR"
    default_message = "Konflik operasi concurrent"


class ResourceNotFoundError(LancarBaseException):
    """Raised when requested resource is not found."""
    error_code = "NOT_FOUND"
    default_message = "Resource tidak ditemukan"


class BusinessRuleError(LancarBaseException):
    """Raised when business rule validation fails."""
    error_code = "BUSINESS_RULE_ERROR"
    default_message = "Aturan bisnis tidak terpenuhi"
