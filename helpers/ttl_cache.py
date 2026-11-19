"""
TTL Cache implementation for idempotency with automatic cleanup.

Prevents memory leaks by implementing time-based expiration and size limits.
"""

import threading
import time
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict


class TTLCache:
    """
    Thread-safe cache with Time-To-Live (TTL) and size limit.
    
    Features:
    - Automatic expiration of old entries
    - Maximum size limit with LRU eviction
    - Thread-safe operations
    - Background cleanup thread
    """
    
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 600, 
                 cleanup_interval: int = 60):
        """
        Initialize TTL cache.
        
        Args:
            maxsize: Maximum number of entries
            ttl_seconds: Time-to-live for entries in seconds
            cleanup_interval: How often to run cleanup in seconds
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # Start background cleanup
        self._start_cleanup_thread()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, timestamp = self._cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.maxsize and key not in self._cache:
                self._cache.popitem(last=False)
            
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > self.ttl_seconds
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for _, timestamp in self._cache.values()
                if current_time - timestamp > self.ttl_seconds
            )
            
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "expired_count": expired_count,
                "ttl_seconds": self.ttl_seconds,
                "utilization": len(self._cache) / self.maxsize if self.maxsize > 0 else 0
            }
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._stop_cleanup.wait(self.cleanup_interval):
            try:
                removed = self.cleanup_expired()
                if removed > 0:
                    # Optional: log cleanup activity
                    pass
            except Exception:
                # Silently continue on errors
                pass
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="TTLCache-Cleanup"
            )
            self._cleanup_thread.start()
    
    def stop_cleanup(self) -> None:
        """Stop background cleanup thread."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
    
    def __len__(self) -> int:
        """Get cache size."""
        return self.size()
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.stop_cleanup()
