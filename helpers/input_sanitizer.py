"""
Input Sanitization Helper
Phase 4 Fix #14: Sanitize user inputs to prevent XSS and injection attacks

This module provides utilities for sanitizing user input before storing
or displaying it. Uses bleach library for HTML sanitization.
"""

import re
import html
from typing import Optional


def sanitize_text(text: str, allow_newlines: bool = True) -> str:
    """
    Sanitize text input by removing HTML tags and escaping special characters.
    
    Args:
        text: Input text to sanitize
        allow_newlines: Whether to preserve newline characters
        
    Returns:
        Sanitized text safe for storage and display
    """
    if not text:
        return ""
    
    # Convert to string and strip
    text = str(text).strip()
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace (but preserve newlines if allowed)
    if allow_newlines:
        # Collapse multiple spaces but keep newlines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
    else:
        # Collapse all whitespace to single space
        text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def sanitize_name(name: str) -> str:
    """
    Sanitize name input (patient, therapist, etc).
    Allows letters, spaces, hyphens, apostrophes.
    
    Args:
        name: Name to sanitize
        
    Returns:
        Sanitized name
    """
    if not name:
        return ""
    
    # Basic sanitization
    name = sanitize_text(name, allow_newlines=False)
    
    # Remove characters that are not letters, spaces, hyphens, or apostrophes
    # Allow Indonesian characters
    name = re.sub(r'[^a-zA-Z\s\-\'\.]+', '', name)
    
    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name)
    
    # Remove leading/trailing special chars
    name = name.strip(' -\'.')
    
    return name


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number input.
    Allows only digits, plus sign, and hyphens.
    
    Args:
        phone: Phone number to sanitize
        
    Returns:
        Sanitized phone number
    """
    if not phone:
        return ""
    
    # Keep only digits, plus, and hyphens
    phone = re.sub(r'[^0-9+\-]', '', str(phone).strip())
    
    # Remove multiple consecutive hyphens
    phone = re.sub(r'-+', '-', phone)
    
    # Remove leading/trailing hyphens
    phone = phone.strip('-')
    
    return phone


def sanitize_address(address: str) -> str:
    """
    Sanitize address input.
    More permissive than name, allows numbers and common punctuation.
    
    Args:
        address: Address to sanitize
        
    Returns:
        Sanitized address
    """
    if not address:
        return ""
    
    # Basic sanitization with newlines allowed
    address = sanitize_text(address, allow_newlines=True)
    
    # Remove excessive punctuation
    address = re.sub(r'[^\w\s\-\.,/()#]+', '', address)
    
    # Collapse multiple spaces
    address = re.sub(r' +', ' ', address)
    
    return address.strip()


def sanitize_notes(notes: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize medical notes or general notes.
    Preserves newlines and basic formatting.
    
    Args:
        notes: Notes to sanitize
        max_length: Optional maximum length
        
    Returns:
        Sanitized notes
    """
    if not notes:
        return ""
    
    # Basic sanitization with newlines
    notes = sanitize_text(notes, allow_newlines=True)
    
    # Truncate if needed
    if max_length and len(notes) > max_length:
        notes = notes[:max_length].rsplit(' ', 1)[0] + '...'
    
    return notes


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Safe filename
    """
    if not filename:
        return ""
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
    
    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')
    
    # Collapse multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def validate_and_sanitize_input(
    value: str,
    input_type: str = "text",
    max_length: Optional[int] = None,
    required: bool = False
) -> str:
    """
    Validate and sanitize input based on type.
    
    Args:
        value: Input value to sanitize
        input_type: Type of input (text, name, phone, address, notes, filename)
        max_length: Optional maximum length
        required: Whether the field is required
        
    Returns:
        Sanitized value
        
    Raises:
        ValueError: If required field is empty or validation fails
    """
    if not value or not str(value).strip():
        if required:
            raise ValueError(f"Field is required")
        return ""
    
    # Choose sanitization function based on type
    sanitizers = {
        "text": sanitize_text,
        "name": sanitize_name,
        "phone": sanitize_phone,
        "address": sanitize_address,
        "notes": sanitize_notes,
        "filename": sanitize_filename,
    }
    
    sanitizer = sanitizers.get(input_type, sanitize_text)
    sanitized = sanitizer(value)
    
    # Check length
    if max_length and len(sanitized) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")
    
    # Check if sanitization removed everything
    if required and not sanitized:
        raise ValueError("Input contains only invalid characters")
    
    return sanitized


# Convenience functions for common use cases
def sanitize_patient_name(name: str) -> str:
    """Sanitize patient name."""
    return validate_and_sanitize_input(name, "name", max_length=200, required=True)


def sanitize_patient_phone(phone: str) -> str:
    """Sanitize patient phone number."""
    return validate_and_sanitize_input(phone, "phone", max_length=20, required=False)


def sanitize_patient_address(address: str) -> str:
    """Sanitize patient address."""
    return validate_and_sanitize_input(address, "address", max_length=500, required=False)


def sanitize_medical_notes(notes: str) -> str:
    """Sanitize medical notes."""
    return validate_and_sanitize_input(notes, "notes", max_length=5000, required=False)
