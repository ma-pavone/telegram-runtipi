import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

class APICache:
    """
    Gerencia um cache simples em memória com TTL (Time-To-Live).
    """
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}

    def cached(self, ttl: int = 60) -> Callable:
        """
        Decorador para adicionar cache a uma função.

        Args:
            ttl (int): Tempo de vida do cache em segundos.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                now = time.time()

                if key in self._cache:
                    cache_time = self._timestamps.get(key, 0)
                    if now - cache_time < ttl:
                        logger.debug(f"Retornando resultado do cache para '{key}'.")
                        return self._cache[key]

                logger.info(f"Cache expirado ou inexistente para '{key}'. Executando função.")
                result = func(*args, **kwargs)
                
                self._cache[key] = result
                self._timestamps[key] = now
                
                return result
            return wrapper
        return decorator