"""
Standardized Error Messages
Phase 4 Fix #13: Consistent error messages with error codes

This module provides standardized error messages and error codes
for consistent client-side error handling.
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException


class ErrorCode(str, Enum):
    """
    Standardized error codes for client-side handling.
    
    Format: CATEGORY_SPECIFIC_ERROR
    Categories: VALIDATION, AUTH, PERMISSION, NOT_FOUND, CONFLICT, SERVER, RATE_LIMIT
    """
    
    # Validation Errors (400)
    VALIDATION_REQUIRED_FIELD = "VALIDATION_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_OUT_OF_RANGE = "VALIDATION_OUT_OF_RANGE"
    VALIDATION_INVALID_TYPE = "VALIDATION_INVALID_TYPE"
    VALIDATION_TOO_LONG = "VALIDATION_TOO_LONG"
    VALIDATION_TOO_SHORT = "VALIDATION_TOO_SHORT"
    VALIDATION_INVALID_PHONE = "VALIDATION_INVALID_PHONE"
    VALIDATION_INVALID_DATE = "VALIDATION_INVALID_DATE"
    VALIDATION_DUPLICATE = "VALIDATION_DUPLICATE"
    
    # Authentication Errors (401)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    
    # Permission Errors (403)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PERMISSION_ADMIN_REQUIRED = "PERMISSION_ADMIN_REQUIRED"
    PERMISSION_PIN_REQUIRED = "PERMISSION_PIN_REQUIRED"
    PERMISSION_LICENSE_INVALID = "PERMISSION_LICENSE_INVALID"
    
    # Not Found Errors (404)
    NOT_FOUND_PATIENT = "NOT_FOUND_PATIENT"
    NOT_FOUND_VISIT = "NOT_FOUND_VISIT"
    NOT_FOUND_THERAPIST = "NOT_FOUND_THERAPIST"
    NOT_FOUND_HERBAL = "NOT_FOUND_HERBAL"
    NOT_FOUND_SERVICE = "NOT_FOUND_SERVICE"
    NOT_FOUND_RESOURCE = "NOT_FOUND_RESOURCE"
    
    # Conflict Errors (409)
    CONFLICT_DUPLICATE_PHONE = "CONFLICT_DUPLICATE_PHONE"
    CONFLICT_DUPLICATE_NAME = "CONFLICT_DUPLICATE_NAME"
    CONFLICT_ALREADY_EXISTS = "CONFLICT_ALREADY_EXISTS"
    CONFLICT_IDEMPOTENCY_PENDING = "CONFLICT_IDEMPOTENCY_PENDING"
    CONFLICT_RESOURCE_LOCKED = "CONFLICT_RESOURCE_LOCKED"
    
    # Business Logic Errors (422)
    BUSINESS_INSUFFICIENT_STOCK = "BUSINESS_INSUFFICIENT_STOCK"
    BUSINESS_INVALID_DISCOUNT = "BUSINESS_INVALID_DISCOUNT"
    BUSINESS_PAYMENT_FAILED = "BUSINESS_PAYMENT_FAILED"
    BUSINESS_INVALID_STATE = "BUSINESS_INVALID_STATE"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # Rate Limit Errors (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    RATE_LIMIT_QUOTA_EXCEEDED = "RATE_LIMIT_QUOTA_EXCEEDED"
    
    # Server Errors (500)
    SERVER_INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
    SERVER_DATABASE_ERROR = "SERVER_DATABASE_ERROR"
    SERVER_EXTERNAL_SERVICE_ERROR = "SERVER_EXTERNAL_SERVICE_ERROR"
    SERVER_CONFIGURATION_ERROR = "SERVER_CONFIGURATION_ERROR"


class StandardError:
    """
    Standardized error response structure.
    
    Phase 4 Fix #13: Consistent error format for client-side handling.
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[str] = None,
        field: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details
        self.field = field
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        result = {
            "error_code": self.code.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.field:
            result["field"] = self.field
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    def to_http_exception(self, status_code: int = 400) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status_code,
            detail=self.to_dict()
        )


# Predefined error messages in Indonesian
class ErrorMessages:
    """Predefined error messages in Indonesian for consistency."""
    
    # Validation errors
    REQUIRED_FIELD = "Field {field} wajib diisi."
    INVALID_FORMAT = "Format {field} tidak valid."
    OUT_OF_RANGE = "{field} harus antara {min} dan {max}."
    INVALID_TYPE = "{field} harus berupa {expected_type}."
    TOO_LONG = "{field} maksimal {max_length} karakter."
    TOO_SHORT = "{field} minimal {min_length} karakter."
    INVALID_PHONE = "Nomor HP harus diawali 08 dan berisi 10-13 digit."
    INVALID_DATE = "Format tanggal tidak valid."
    DUPLICATE = "{field} sudah terdaftar."
    
    # Authentication errors
    INVALID_CREDENTIALS = "PIN admin tidak valid."
    TOKEN_EXPIRED = "Sesi telah berakhir. Silakan login kembali."
    TOKEN_INVALID = "Token tidak valid."
    AUTH_REQUIRED = "Autentikasi diperlukan."
    
    # Permission errors
    PERMISSION_DENIED = "Anda tidak memiliki izin untuk operasi ini."
    ADMIN_REQUIRED = "Operasi ini memerlukan PIN admin."
    LICENSE_INVALID = "Lisensi tidak valid atau sudah kadaluarsa."
    
    # Not found errors
    PATIENT_NOT_FOUND = "Pasien tidak ditemukan."
    VISIT_NOT_FOUND = "Kunjungan tidak ditemukan."
    THERAPIST_NOT_FOUND = "Terapis tidak ditemukan."
    HERBAL_NOT_FOUND = "Herbal tidak ditemukan."
    SERVICE_NOT_FOUND = "Layanan tidak ditemukan."
    RESOURCE_NOT_FOUND = "{resource} tidak ditemukan."
    
    # Conflict errors
    DUPLICATE_PHONE = "Nomor HP {phone} sudah terdaftar untuk pasien lain."
    DUPLICATE_NAME = "{name} sudah terdaftar."
    ALREADY_EXISTS = "{resource} sudah ada."
    IDEMPOTENCY_PENDING = "Permintaan sedang diproses. Tunggu sebentar sebelum mencoba lagi."
    RESOURCE_LOCKED = "{resource} sedang digunakan. Coba lagi nanti."
    
    # Business logic errors
    INSUFFICIENT_STOCK = "Stok {item} tidak cukup. Tersedia {available}, perlu {required}."
    INVALID_DISCOUNT = "Diskon tidak valid atau tidak berlaku."
    PAYMENT_FAILED = "Pembayaran gagal: {reason}"
    INVALID_STATE = "Operasi tidak dapat dilakukan pada status saat ini."
    RULE_VIOLATION = "Operasi melanggar aturan bisnis: {rule}"
    
    # Rate limit errors
    RATE_LIMIT_EXCEEDED = "Terlalu banyak permintaan. Silakan coba lagi dalam {retry_after} detik."
    QUOTA_EXCEEDED = "Kuota penggunaan telah habis."
    
    # Server errors
    INTERNAL_ERROR = "Terjadi kesalahan internal. Silakan hubungi administrator."
    DATABASE_ERROR = "Kesalahan database. Silakan coba lagi."
    EXTERNAL_SERVICE_ERROR = "Layanan eksternal tidak tersedia."
    CONFIGURATION_ERROR = "Kesalahan konfigurasi sistem."


# Helper functions to create standardized errors
def validation_error(
    field: str,
    message: str,
    code: ErrorCode = ErrorCode.VALIDATION_INVALID_FORMAT,
    **kwargs
) -> StandardError:
    """Create validation error."""
    return StandardError(
        code=code,
        message=message.format(field=field, **kwargs),
        field=field,
        metadata=kwargs
    )


def not_found_error(
    resource: str,
    code: ErrorCode = ErrorCode.NOT_FOUND_RESOURCE
) -> StandardError:
    """Create not found error."""
    return StandardError(
        code=code,
        message=ErrorMessages.RESOURCE_NOT_FOUND.format(resource=resource),
        metadata={"resource": resource}
    )


def conflict_error(
    message: str,
    code: ErrorCode = ErrorCode.CONFLICT_ALREADY_EXISTS,
    **kwargs
) -> StandardError:
    """Create conflict error."""
    return StandardError(
        code=code,
        message=message.format(**kwargs),
        metadata=kwargs
    )


def business_error(
    message: str,
    code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
    **kwargs
) -> StandardError:
    """Create business logic error."""
    return StandardError(
        code=code,
        message=message.format(**kwargs),
        metadata=kwargs
    )


def server_error(
    message: str = ErrorMessages.INTERNAL_ERROR,
    code: ErrorCode = ErrorCode.SERVER_INTERNAL_ERROR,
    **kwargs
) -> StandardError:
    """Create server error."""
    return StandardError(
        code=code,
        message=message,
        metadata=kwargs
    )


# Convenience functions for common errors
def required_field_error(field: str) -> StandardError:
    """Field is required error."""
    return validation_error(
        field=field,
        message=ErrorMessages.REQUIRED_FIELD,
        code=ErrorCode.VALIDATION_REQUIRED_FIELD
    )


def invalid_phone_error() -> StandardError:
    """Invalid phone number error."""
    return validation_error(
        field="phone",
        message=ErrorMessages.INVALID_PHONE,
        code=ErrorCode.VALIDATION_INVALID_PHONE
    )


def duplicate_phone_error(phone: str) -> StandardError:
    """Duplicate phone number error."""
    return conflict_error(
        message=ErrorMessages.DUPLICATE_PHONE,
        code=ErrorCode.CONFLICT_DUPLICATE_PHONE,
        phone=phone
    )


def patient_not_found_error() -> StandardError:
    """Patient not found error."""
    return not_found_error(
        resource="Pasien",
        code=ErrorCode.NOT_FOUND_PATIENT
    )


def insufficient_stock_error(item: str, available: int, required: int) -> StandardError:
    """Insufficient stock error."""
    return business_error(
        message=ErrorMessages.INSUFFICIENT_STOCK,
        code=ErrorCode.BUSINESS_INSUFFICIENT_STOCK,
        item=item,
        available=available,
        required=required
    )


def rate_limit_error(retry_after: int = 60) -> StandardError:
    """Rate limit exceeded error."""
    return StandardError(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=ErrorMessages.RATE_LIMIT_EXCEEDED.format(retry_after=retry_after),
        metadata={"retry_after": retry_after}
    )


def admin_pin_required_error() -> StandardError:
    """Admin PIN required error."""
    return StandardError(
        code=ErrorCode.PERMISSION_ADMIN_REQUIRED,
        message=ErrorMessages.ADMIN_REQUIRED
    )


def license_invalid_error() -> StandardError:
    """License invalid error."""
    return StandardError(
        code=ErrorCode.PERMISSION_LICENSE_INVALID,
        message=ErrorMessages.LICENSE_INVALID
    )
