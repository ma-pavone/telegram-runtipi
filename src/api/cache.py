# src/api/cache.py
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

class APICache:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._rate_limits: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém item do cache se ainda válido"""
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if time.time() - entry.timestamp > entry.ttl:
            del self._cache[key]
            return None
            
        return entry.data
    
    def set(self, key: str, data: Any, ttl: int = 60):
        """Adiciona item ao cache"""
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def clear(self):
        """Limpa todo o cache"""
        self._cache.clear()
    
    def can_call(self, key: str, min_interval: int = 5) -> bool:
        """Verifica se pode fazer nova chamada (rate limiting)"""
        now = time.time()
        if key not in self._rate_limits:
            self._rate_limits[key] = now
            return True
            
        if now - self._rate_limits[key] >= min_interval:
            self._rate_limits[key] = now
            return True
            
        return False

# Cache global
api_cache = APICache()

def cached(ttl: int = 60, rate_limit: int = 5):
    """Decorator para cache de métodos da API"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Gera chave única
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Verifica cache
            cached_result = api_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Verifica rate limit
            if not api_cache.can_call(cache_key, rate_limit):
                logger.warning(f"Rate limit exceeded for {cache_key}")
                return cached_result  # Retorna cache expirado se houver
            
            # Executa função
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(self, *args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, self, *args, **kwargs)
                
                # Armazena no cache
                api_cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")
                return result
                
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
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
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        # Retorna wrapper apropriado
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator