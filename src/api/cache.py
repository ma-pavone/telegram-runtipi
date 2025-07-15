import time
import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

class APICache:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._rate_limits: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None
            
        return entry.data
    
    def set(self, key: str, data: Any, ttl: int = 60):
        self._cache[key] = CacheEntry(data, time.time(), ttl)
    
    def clear(self):
        self._cache.clear()
        self._rate_limits.clear()
    
    def can_call(self, key: str, min_interval: int = 5) -> bool:
        now = time.time()
        last_call = self._rate_limits.get(key, 0)
        
        if now - last_call >= min_interval:
            self._rate_limits[key] = now
            return True
            
        return False

api_cache = APICache()

def cached(ttl: int = 60, rate_limit: int = 5):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_result = api_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not api_cache.can_call(cache_key, rate_limit):
                return cached_result
            
            try:
                result = await func(self, *args, **kwargs) if asyncio.iscoroutinefunction(func) else await asyncio.to_thread(func, self, *args, **kwargs)
                api_cache.set(cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_result = api_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not api_cache.can_call(cache_key, rate_limit):
                return cached_result
            
            try:
                result = func(self, *args, **kwargs)
                api_cache.set(cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator