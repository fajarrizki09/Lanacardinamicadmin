"""
Enhanced Audit Logging Helper
Phase 4 Fix #17: Add request context (IP address, user agent) to audit logs

This module provides enhanced audit logging with request context.
"""

from typing import Optional, Dict, Any
from fastapi import Request
import logging

logger = logging.getLogger("lancar.audit_helper")


def log_audit_with_request(
    db,
    action: str,
    entity_type: str,
    entity_id: Optional[Any],
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    actor: str = "admin",
    required: bool = False
) -> Optional[int]:
    """
    Log audit event with request context (IP address, user agent).
    
    Phase 4 Fix #17: Enhanced audit logging with request metadata.
    
    Args:
        db: Database instance
        action: Action performed (e.g., "patient_created")
        entity_type: Type of entity (e.g., "patient")
        entity_id: ID of the entity
        description: Human-readable description
        metadata: Additional metadata dictionary
        request: FastAPI Request object (optional)
        actor: Actor performing the action
        required: Whether audit log is required (raises on failure)
        
    Returns:
        Audit log ID or None if failed
    """
    # Initialize metadata if None
    if metadata is None:
        metadata = {}
    
    # Add request context if available
    if request:
        try:
            # Add IP address
            if hasattr(request, 'client') and request.client:
                metadata['ip_address'] = request.client.host
                if hasattr(request.client, 'port'):
                    metadata['ip_port'] = request.client.port
            
            # Add user agent
            if hasattr(request, 'headers'):
                user_agent = request.headers.get('user-agent', '')
                if user_agent:
                    metadata['user_agent'] = user_agent[:200]  # Limit length
                
                # Add referer if available
                referer = request.headers.get('referer', '')
                if referer:
                    metadata['referer'] = referer[:200]
            
            # Add request method and path
            if hasattr(request, 'method'):
                metadata['request_method'] = request.method
            if hasattr(request, 'url') and hasattr(request.url, 'path'):
                metadata['request_path'] = request.url.path
            
        except Exception as e:
            logger.warning(f"Failed to extract request context: {e}")
    
    # Call original log_audit with enhanced metadata
    try:
        return db.log_audit(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata=metadata,
            actor=actor,
            required=required
        )
    except Exception as e:
        logger.exception(f"Audit logging failed: {action} on {entity_type}")
        if required:
            raise
        return None


def get_client_ip(request: Optional[Request]) -> str:
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client IP address or "unknown"
    """
    if not request:
        return "unknown"
    
    try:
        # Check X-Forwarded-For header (for proxied requests)
        if hasattr(request, 'headers'):
            forwarded_for = request.headers.get('x-forwarded-for', '')
            if forwarded_for:
                # Take first IP in the chain
                return forwarded_for.split(',')[0].strip()
            
            # Check X-Real-IP header
            real_ip = request.headers.get('x-real-ip', '')
            if real_ip:
                return real_ip.strip()
        
        # Fall back to direct client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
    except Exception as e:
        logger.warning(f"Failed to extract client IP: {e}")
    
    return "unknown"


def get_user_agent(request: Optional[Request]) -> str:
    """
    Extract user agent from request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User agent string or "unknown"
    """
    if not request:
        return "unknown"
    
    try:
        if hasattr(request, 'headers'):
            return request.headers.get('user-agent', 'unknown')
    except Exception as e:
        logger.warning(f"Failed to extract user agent: {e}")
    
    return "unknown"


def create_audit_metadata(
    base_metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create audit metadata dictionary with request context.
    
    Args:
        base_metadata: Base metadata dictionary
        request: FastAPI Request object
        **kwargs: Additional metadata key-value pairs
        
    Returns:
        Complete metadata dictionary
    """
    metadata = base_metadata.copy() if base_metadata else {}
    
    # Add request context
    if request:
        metadata['ip_address'] = get_client_ip(request)
        metadata['user_agent'] = get_user_agent(request)
        
        if hasattr(request, 'method'):
            metadata['request_method'] = request.method
        if hasattr(request, 'url') and hasattr(request.url, 'path'):
            metadata['request_path'] = request.url.path
    
    # Add additional kwargs
    metadata.update(kwargs)
    
    return metadata


# Convenience wrapper for common audit operations
class AuditLogger:
    """
    Convenience class for audit logging with request context.
    
    Usage:
        audit = AuditLogger(db, request)
        audit.log("patient_created", "patient", patient_id, "Patient added")
    """
    
    def __init__(self, db, request: Optional[Request] = None, actor: str = "admin"):
        self.db = db
        self.request = request
        self.actor = actor
    
    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[Any],
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        required: bool = False
    ) -> Optional[int]:
        """Log audit event with stored request context."""
        return log_audit_with_request(
            db=self.db,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata=metadata,
            request=self.request,
            actor=self.actor,
            required=required
        )
    
    def log_security_event(
        self,
        action: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log security-related event."""
        return self.log(
            action=action,
            entity_type="security",
            entity_id="system",
            description=description,
            metadata=metadata,
            required=True  # Security events are required
        )
    
    def log_data_change(
        self,
        action: str,
        entity_type: str,
        entity_id: Any,
        description: str,
        old_value: Any = None,
        new_value: Any = None,
        **kwargs
    ) -> Optional[int]:
        """Log data change with old and new values."""
        metadata = kwargs.copy()
        if old_value is not None:
            metadata['old_value'] = str(old_value)
        if new_value is not None:
            metadata['new_value'] = str(new_value)
        
        return self.log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata=metadata
        )
