"""Caching implementation for Garmin Connect API."""
import json
import logging
import zlib
from typing import Any, Optional, TypeVar, Callable
from functools import wraps
from datetime import datetime

import aioredis
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheKey:
    """Cache key templates for different data types."""
    
    SLEEP = "garmin:sleep:{user_id}:{date}"
    STRESS = "garmin:stress:{user_id}:{date}"
    BODY_BATTERY = "garmin:body_battery:{user_id}:{date}"

class CacheTTL:
    """Time-to-live values for different data types."""
    
    SLEEP = 3600  # 1 hour
    STRESS = 1800  # 30 minutes
    BODY_BATTERY = 1800  # 30 minutes

class CacheSettings(BaseModel):
    """Settings for Redis cache."""
    
    url: str = "redis://localhost:6379"
    compress: bool = True
    compression_threshold: int = 1024  # Compress if larger than 1KB

class Cache:
    """Redis cache implementation."""
    
    def __init__(self, settings: Optional[CacheSettings] = None):
        """
        Initialize cache.
        
        Args:
            settings: Cache settings, uses defaults if not provided
        """
        self.settings = settings or CacheSettings()
        self._redis: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if not self._redis:
            try:
                self._redis = await aioredis.from_url(self.settings.url)
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            await self.connect()
        
        try:
            data = await self._redis.get(key)
            if not data:
                return None
            
            # Handle compression
            if self.settings.compress and data.startswith(b'\x1f\x8b'):  # gzip magic number
                data = zlib.decompress(data)
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            # Convert to JSON
            data = json.dumps(value)
            
            # Compress if needed
            if (
                self.settings.compress
                and len(data) > self.settings.compression_threshold
            ):
                data = zlib.compress(data.encode())
            
            # Set in Redis
            await self._redis.set(key, data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set in cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False

def cached(
    key_template: str,
    ttl: Optional[int] = None,
    user_id_arg: str = 'user_id',
    date_arg: str = 'target_date'
):
    """
    Decorator for caching function results.
    
    Args:
        key_template: Cache key template
        ttl: Time-to-live in seconds
        user_id_arg: Name of user ID argument
        date_arg: Name of date argument
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get cache instance
            if not hasattr(self, '_cache'):
                self._cache = Cache()
            
            # Build cache key
            key_args = {
                'user_id': kwargs.get(user_id_arg, 'default'),
                'date': kwargs[date_arg].date().isoformat()
                if isinstance(kwargs.get(date_arg), datetime)
                else kwargs[date_arg].isoformat()
            }
            cache_key = key_template.format(**key_args)
            
            # Try to get from cache
            cached_value = await self._cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Get fresh value
            value = await func(self, *args, **kwargs)
            
            # Cache the value
            await self._cache.set(cache_key, value, ttl)
            logger.debug(f"Cached value for {cache_key}")
            
            return value
        
        return wrapper
    
    return decorator 