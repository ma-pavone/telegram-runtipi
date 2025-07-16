# src/api/cache.py
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

class APICache:
    """Cache thread-safe com rate limiting integrado"""
    
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, CacheEntry] = {}
        self._rate_limits: Dict[str, float] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry or entry.is_expired:
            self._cache.pop(key, None)
            return None
        return entry.data
    
    def set(self, key: str, data: Any, ttl: int = 60):
        # Limpa cache se exceder tamanho máximo
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[key] = CacheEntry(data, time.time(), ttl)
    
    def can_call(self, key: str, min_interval: int = 5) -> bool:
        now = time.time()
        last_call = self._rate_limits.get(key, 0)
        
        if now - last_call >= min_interval:
            self._rate_limits[key] = now
            return True
        return False
    
    def _evict_oldest(self):
        """Remove 20% dos itens mais antigos"""
        if not self._cache:
            return
            
        sorted_items = sorted(
            self._cache.items(), 
            key=lambda x: x[1].timestamp
        )
        
        evict_count = max(1, len(sorted_items) // 5)
        for key, _ in sorted_items[:evict_count]:
            self._cache.pop(key, None)
    
    def clear(self):
        self._cache.clear()
        self._rate_limits.clear()

# Instância global
api_cache = APICache()

def cached(ttl: int = 60, rate_limit: int = 5):
    """Decorator para cache com rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Tenta cache primeiro
            cached_result = api_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Verifica rate limit
            if not api_cache.can_call(cache_key, rate_limit):
                logger.warning(f"Rate limit hit for {cache_key}")
                return cached_result  # Retorna None se não há cache
            
            try:
                # Executa função
                if asyncio.iscoroutinefunction(func):
                    result = await func(self, *args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, self, *args, **kwargs)
                
                api_cache.set(cache_key, result, ttl)
                return result
                
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator