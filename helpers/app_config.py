"""
Application Configuration Helper
Phase 4 Fix #16: Centralize hardcoded configuration values

This module provides a centralized configuration system that can be
overridden via environment variables or configuration files.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    visit_idempotency_ttl_seconds: int = field(default=600)  # 10 minutes
    herbal_idempotency_ttl_seconds: int = field(default=600)  # 10 minutes
    cache_max_size: int = field(default=1000)
    cache_cleanup_interval: int = field(default=60)  # 1 minute
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Load configuration from environment variables."""
        return cls(
            visit_idempotency_ttl_seconds=int(os.getenv('VISIT_IDEMPOTENCY_TTL', 600)),
            herbal_idempotency_ttl_seconds=int(os.getenv('HERBAL_IDEMPOTENCY_TTL', 600)),
            cache_max_size=int(os.getenv('CACHE_MAX_SIZE', 1000)),
            cache_cleanup_interval=int(os.getenv('CACHE_CLEANUP_INTERVAL', 60)),
        )


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    admin_idle_lock_ms: int = field(default=900000)  # 15 minutes
    session_timeout_seconds: int = field(default=3600)  # 1 hour
    max_login_attempts: int = field(default=5)
    lockout_duration_seconds: int = field(default=300)  # 5 minutes
    rate_limit_per_minute: int = field(default=60)
    rate_limit_burst: int = field(default=10)
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Load configuration from environment variables."""
        return cls(
            admin_idle_lock_ms=int(os.getenv('ADMIN_IDLE_LOCK_MS', 900000)),
            session_timeout_seconds=int(os.getenv('SESSION_TIMEOUT', 3600)),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', 5)),
            lockout_duration_seconds=int(os.getenv('LOCKOUT_DURATION', 300)),
            rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', 60)),
            rate_limit_burst=int(os.getenv('RATE_LIMIT_BURST', 10)),
        )


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    connection_timeout: int = field(default=10)  # seconds
    query_timeout: int = field(default=30)  # seconds
    max_connections: int = field(default=10)
    backup_retention_days: int = field(default=30)
    max_backups: int = field(default=10)
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables."""
        return cls(
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', 10)),
            query_timeout=int(os.getenv('DB_QUERY_TIMEOUT', 30)),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', 10)),
            backup_retention_days=int(os.getenv('BACKUP_RETENTION_DAYS', 30)),
            max_backups=int(os.getenv('MAX_BACKUPS', 10)),
        )


@dataclass
class ValidationConfig:
    """Validation configuration settings."""
    max_price: float = field(default=99999999.99)  # Based on Numeric(10,2)
    min_price: float = field(default=0.0)
    max_quantity: int = field(default=1000)
    min_quantity: int = field(default=1)
    max_name_length: int = field(default=200)
    max_phone_length: int = field(default=20)
    max_address_length: int = field(default=500)
    max_notes_length: int = field(default=5000)
    
    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        """Load configuration from environment variables."""
        return cls(
            max_price=float(os.getenv('MAX_PRICE', 99999999.99)),
            min_price=float(os.getenv('MIN_PRICE', 0.0)),
            max_quantity=int(os.getenv('MAX_QUANTITY', 1000)),
            min_quantity=int(os.getenv('MIN_QUANTITY', 1)),
            max_name_length=int(os.getenv('MAX_NAME_LENGTH', 200)),
            max_phone_length=int(os.getenv('MAX_PHONE_LENGTH', 20)),
            max_address_length=int(os.getenv('MAX_ADDRESS_LENGTH', 500)),
            max_notes_length=int(os.getenv('MAX_NOTES_LENGTH', 5000)),
        )


@dataclass
class APIConfig:
    """API configuration settings."""
    request_timeout_seconds: int = field(default=30)
    max_page_size: int = field(default=250)
    default_page_size: int = field(default=100)
    max_upload_size_mb: int = field(default=10)
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Load configuration from environment variables."""
        return cls(
            request_timeout_seconds=int(os.getenv('API_REQUEST_TIMEOUT', 30)),
            max_page_size=int(os.getenv('API_MAX_PAGE_SIZE', 250)),
            default_page_size=int(os.getenv('API_DEFAULT_PAGE_SIZE', 100)),
            max_upload_size_mb=int(os.getenv('MAX_UPLOAD_SIZE_MB', 10)),
        )


class AppConfig:
    """
    Centralized application configuration.
    
    Phase 4 Fix #16: Replace hardcoded values with configurable settings.
    Settings can be overridden via environment variables.
    """
    
    def __init__(self):
        self.cache = CacheConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.validation = ValidationConfig.from_env()
        self.api = APIConfig.from_env()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'cache': self.cache.__dict__,
            'security': self.security.__dict__,
            'database': self.database.__dict__,
            'validation': self.validation.__dict__,
            'api': self.api.__dict__,
        }
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.cache
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        return self.security
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.database
    
    def get_validation_config(self) -> ValidationConfig:
        """Get validation configuration."""
        return self.validation
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration."""
        return self.api


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get global configuration instance.
    Creates instance on first call.
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """
    Reload configuration from environment.
    Useful for testing or runtime configuration changes.
    """
    global _config
    _config = AppConfig()
    return _config


# Convenience functions for common config access
def get_visit_idempotency_ttl() -> int:
    """Get visit idempotency TTL in seconds."""
    return get_config().cache.visit_idempotency_ttl_seconds


def get_herbal_idempotency_ttl() -> int:
    """Get herbal idempotency TTL in seconds."""
    return get_config().cache.herbal_idempotency_ttl_seconds


def get_admin_idle_lock_ms() -> int:
    """Get admin idle lock timeout in milliseconds."""
    return get_config().security.admin_idle_lock_ms


def get_max_price() -> float:
    """Get maximum allowed price."""
    return get_config().validation.max_price


def get_rate_limit_per_minute() -> int:
    """Get rate limit per minute."""
    return get_config().security.rate_limit_per_minute


def validate_price(price: float, field_name: str = "price") -> float:
    """
    Validate price against configured limits.
    
    Phase 4 Fix #18: Prevent integer overflow on large numbers.
    
    Args:
        price: Price to validate
        field_name: Name of field for error messages
        
    Returns:
        Validated price
        
    Raises:
        ValueError: If price is out of range
    """
    config = get_config().validation
    
    if price < config.min_price:
        raise ValueError(f"{field_name} tidak boleh kurang dari {config.min_price}")
    
    if price > config.max_price:
        raise ValueError(
            f"{field_name} melebihi maksimum {config.max_price:,.2f}. "
            f"Nilai maksimum berdasarkan tipe data database Numeric(10,2)."
        )
    
    return price


def validate_quantity(quantity: int, field_name: str = "quantity") -> int:
    """
    Validate quantity against configured limits.
    
    Args:
        quantity: Quantity to validate
        field_name: Name of field for error messages
        
    Returns:
        Validated quantity
        
    Raises:
        ValueError: If quantity is out of range
    """
    config = get_config().validation
    
    if quantity < config.min_quantity:
        raise ValueError(f"{field_name} minimal {config.min_quantity}")
    
    if quantity > config.max_quantity:
        raise ValueError(f"{field_name} maksimal {config.max_quantity}")
    
    return quantity
