"""
Input sanitization utilities for security.

Provides functions to clean and validate user input to prevent XSS and injection attacks.
"""

import re
import html
from typing import Optional


def sanitize_html(text: str, allow_basic_formatting: bool = False) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        text: Input text that may contain HTML
        allow_basic_formatting: If True, allows <b>, <i>, <br> tags
        
    Returns:
        Sanitized text safe for HTML rendering
    """
    if not text:
        return ""
    
    # Escape all HTML entities
    sanitized = html.escape(str(text))
    
    if allow_basic_formatting:
        # Allow only safe basic formatting tags
        sanitized = sanitized.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        sanitized = sanitized.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
        sanitized = sanitized.replace("&lt;br&gt;", "<br>")
    
    return sanitized


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifier (table/column name).
    
    Args:
        identifier: SQL identifier to sanitize
        
    Returns:
        Sanitized identifier
        
    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")
    
    # Allow only alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    
    # Prevent SQL keywords (basic list)
    sql_keywords = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 
        'alter', 'table', 'from', 'where', 'union', 'exec', 'execute'
    }
    if identifier.lower() in sql_keywords:
        raise ValueError(f"SQL keyword not allowed as identifier: {identifier}")
    
    return identifier


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path separators and null bytes
    sanitized = filename.replace('/', '').replace('\\', '').replace('\0', '')
    
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"|?*]', '', sanitized)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:max_length]
    
    return sanitized or "unnamed"


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitize phone number to contain only digits and valid prefixes.
    
    Args:
        phone: Phone number to sanitize
        
    Returns:
        Sanitized phone number
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', str(phone))
    
    # Check if it's a TEMP- number (allow as-is)
    if str(phone).startswith('TEMP-'):
        return str(phone)
    
    # Validate Indonesian phone format
    if digits_only:
        # Convert 62xxx to 08xxx
        if digits_only.startswith('62'):
            digits_only = '0' + digits_only[2:]
        
        # Must start with 08 and be 10-13 digits
        if not digits_only.startswith('08'):
            raise ValueError("Nomor HP harus diawali 08")
        
        if not (10 <= len(digits_only) <= 13):
            raise ValueError("Nomor HP harus 10-13 digit")
        
        return digits_only
    
    return ""


def sanitize_text_input(text: str, max_length: Optional[int] = None, 
                       allow_newlines: bool = True) -> str:
    """
    Sanitize general text input.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    sanitized = str(text).strip()
    
    # Remove null bytes
    sanitized = sanitized.replace('\0', '')
    
    # Handle newlines
    if not allow_newlines:
        sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')
    
    # Remove control characters except newlines and tabs
    if allow_newlines:
        sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sanitized)
    else:
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
    
    # Limit length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email(email: str) -> str:
    """
    Validate and sanitize email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Sanitized email
        
    Raises:
        ValueError: If email is invalid
    """
    if not email:
        return ""
    
    email = str(email).strip().lower()
    
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValueError("Format email tidak valid")
    
    return email


def sanitize_numeric_input(value: str, allow_negative: bool = False, 
                          allow_decimal: bool = False) -> str:
    """
    Sanitize numeric input.
    
    Args:
        value: Input value
        allow_negative: Whether to allow negative numbers
        allow_decimal: Whether to allow decimal points
        
    Returns:
        Sanitized numeric string
        
    Raises:
        ValueError: If value is not numeric
    """
    if not value:
        return "0"
    
    value = str(value).strip()
    
    # Remove all non-numeric characters except minus and dot
    if allow_decimal:
        value = re.sub(r'[^\d.-]', '', value)
    else:
        value = re.sub(r'[^\d-]', '', value)
    
    # Handle negative
    if not allow_negative and value.startswith('-'):
        raise ValueError("Nilai negatif tidak diperbolehkan")
    
    # Validate format
    try:
        if allow_decimal:
            float(value)
        else:
            int(value)
    except ValueError:
        raise ValueError("Format angka tidak valid")
    
    return value
