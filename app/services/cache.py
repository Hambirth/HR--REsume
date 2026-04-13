"""Simple in-memory cache for API responses."""

import hashlib
import json
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCache:
    """In-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, data: Any) -> str:
        """Generate cache key from data."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def get(self, key_data: Any) -> Optional[Any]:
        """Get cached value if exists and not expired."""
        key = self._get_key(key_data)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key_data: Any, value: Any):
        """Set cache value."""
        key = self._get_key(key_data)
        self.cache[key] = (value, datetime.now())
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()

# Global cache instances
embedding_cache = SimpleCache(ttl_seconds=3600)  # 1 hour
chat_cache = SimpleCache(ttl_seconds=1800)  # 30 minutes
