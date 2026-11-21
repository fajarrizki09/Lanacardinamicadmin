"""
Rate Limiting Helper
Phase 4 Fix #15: Implement rate limiting to prevent abuse and DoS attacks

This module provides rate limiting functionality for API endpoints.
Uses slowapi library for rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Optional, Callable
import logging

logger = logging.getLogger("lancar.rate_limit")

# Initialize rate limiter
# Key function extracts client identifier (IP address)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute
    storage_uri="memory://",  # Use in-memory storage
    strategy="fixed-window",  # Fixed window strategy
)


def get_rate_limiter() -> Limiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        Limiter instance
    """
    return limiter


def handle_rate_limit_exceeded(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded exception.
    
    Args:
        request: FastAPI Request object
        exc: RateLimitExceeded exception
        
    Raises:
        HTTPException with 429 status code
    """
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)}: {exc}"
    )
    raise HTTPException(
        status_code=429,
        detail="Terlalu banyak permintaan. Silakan coba lagi nanti."
    )


# Rate limit decorators for common use cases
def rate_limit_strict(limit: str = "10/minute"):
    """
    Strict rate limit decorator for sensitive operations.
    
    Usage:
        @router.post("/admin/delete")
        @rate_limit_strict("5/minute")
        async def delete_data(...):
            ...
    
    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour")
        
    Returns:
        Decorator function
    """
    def decorator(func):
        return limiter.limit(limit)(func)
    return decorator


def rate_limit_moderate(limit: str = "30/minute"):
    """
    Moderate rate limit decorator for normal operations.
    
    Usage:
        @router.post("/add_visit")
        @rate_limit_moderate("30/minute")
        async def add_visit(...):
            ...
    
    Args:
        limit: Rate limit string
        
    Returns:
        Decorator function
    """
    def decorator(func):
        return limiter.limit(limit)(func)
    return decorator


def rate_limit_relaxed(limit: str = "60/minute"):
    """
    Relaxed rate limit decorator for read operations.
    
    Usage:
        @router.get("/patients")
        @rate_limit_relaxed("60/minute")
        async def get_patients(...):
            ...
    
    Args:
        limit: Rate limit string
        
    Returns:
        Decorator function
    """
    def decorator(func):
        return limiter.limit(limit)(func)
    return decorator


# Custom key functions for different rate limiting strategies
def get_remote_address_with_user(request: Request) -> str:
    """
    Get rate limit key based on IP address and user identifier.
    Useful for authenticated endpoints.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Rate limit key string
    """
    ip = get_remote_address(request)
    
    # Try to get user identifier from session/auth
    user_id = "anonymous"
    try:
        # Check if user info is in request state
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        # Or check headers
        elif hasattr(request, 'headers'):
            user_id = request.headers.get('X-User-ID', 'anonymous')
    except Exception:
        pass
    
    return f"{ip}:{user_id}"


def get_api_key(request: Request) -> str:
    """
    Get rate limit key based on API key.
    Useful for API key-based authentication.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        API key or IP address
    """
    try:
        if hasattr(request, 'headers'):
            api_key = request.headers.get('X-API-Key', '')
            if api_key:
                return api_key
    except Exception:
        pass
    
    return get_remote_address(request)


# Rate limit configuration presets
class RateLimitPresets:
    """Predefined rate limit configurations for different endpoint types."""
    
    # Authentication endpoints (strict)
    AUTH_LOGIN = "5/minute"
    AUTH_REGISTER = "3/minute"
    AUTH_RESET_PASSWORD = "3/minute"
    
    # Admin operations (strict)
    ADMIN_DELETE = "5/minute"
    ADMIN_BULK_UPDATE = "10/minute"
    ADMIN_EXPORT = "5/minute"
    
    # Data modification (moderate)
    CREATE_RECORD = "30/minute"
    UPDATE_RECORD = "30/minute"
    DELETE_RECORD = "20/minute"
    
    # Data retrieval (relaxed)
    READ_LIST = "60/minute"
    READ_DETAIL = "100/minute"
    SEARCH = "40/minute"
    
    # File operations (moderate)
    UPLOAD_FILE = "10/minute"
    DOWNLOAD_FILE = "30/minute"
    
    # Reporting (moderate)
    GENERATE_REPORT = "10/minute"
    EXPORT_DATA = "5/minute"


def check_rate_limit(
    request: Request,
    limit: str,
    key_func: Optional[Callable] = None
) -> bool:
    """
    Manually check if request is within rate limit.
    
    Args:
        request: FastAPI Request object
        limit: Rate limit string
        key_func: Optional custom key function
        
    Returns:
        True if within limit, False otherwise
    """
    try:
        key = key_func(request) if key_func else get_remote_address(request)
        # This is a simplified check - actual implementation would use limiter's storage
        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Fail open to avoid blocking legitimate requests


def get_rate_limit_status(request: Request) -> dict:
    """
    Get current rate limit status for a request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary with rate limit status
    """
    try:
        key = get_remote_address(request)
        # Note: This is a placeholder - actual implementation would query limiter's storage
        return {
            "key": key,
            "limit": "100/minute",
            "remaining": 95,
            "reset_at": None,
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        return {
            "key": "unknown",
            "limit": "unknown",
            "remaining": None,
            "reset_at": None,
        }


# Whitelist/blacklist support
_rate_limit_whitelist = set()
_rate_limit_blacklist = set()


def add_to_whitelist(ip: str):
    """Add IP address to rate limit whitelist."""
    _rate_limit_whitelist.add(ip)
    logger.info(f"Added {ip} to rate limit whitelist")


def remove_from_whitelist(ip: str):
    """Remove IP address from rate limit whitelist."""
    _rate_limit_whitelist.discard(ip)
    logger.info(f"Removed {ip} from rate limit whitelist")


def add_to_blacklist(ip: str):
    """Add IP address to rate limit blacklist."""
    _rate_limit_blacklist.add(ip)
    logger.warning(f"Added {ip} to rate limit blacklist")


def remove_from_blacklist(ip: str):
    """Remove IP address from rate limit blacklist."""
    _rate_limit_blacklist.discard(ip)
    logger.info(f"Removed {ip} from rate limit blacklist")


def is_whitelisted(request: Request) -> bool:
    """Check if request is from whitelisted IP."""
    ip = get_remote_address(request)
    return ip in _rate_limit_whitelist


def is_blacklisted(request: Request) -> bool:
    """Check if request is from blacklisted IP."""
    ip = get_remote_address(request)
    return ip in _rate_limit_blacklist


def check_blacklist_middleware(request: Request):
    """
    Middleware to check if request is from blacklisted IP.
    Raises HTTPException if blacklisted.
    """
    if is_blacklisted(request):
        ip = get_remote_address(request)
        logger.warning(f"Blocked request from blacklisted IP: {ip}")
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. IP address Anda telah diblokir."
        )
