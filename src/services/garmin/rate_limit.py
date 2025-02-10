"""Rate limiting implementation for Garmin Connect API."""
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from functools import wraps

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class RateLimitSettings(BaseModel):
    """Settings for rate limiting."""
    
    requests_per_minute: int = 60
    burst_limit: int = 10
    cooldown_seconds: int = 60

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    
    capacity: int
    fill_rate: float
    tokens: float = 0.0
    last_update: float = time.monotonic()
    
    def _update_tokens(self) -> None:
        """Update the number of tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        new_tokens = elapsed * self.fill_rate
        
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        self._update_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False

class RateLimiter:
    """Rate limiter for Garmin Connect API."""
    
    def __init__(self, settings: Optional[RateLimitSettings] = None):
        """
        Initialize rate limiter.
        
        Args:
            settings: Rate limit settings, uses defaults if not provided
        """
        self.settings = settings or RateLimitSettings()
        self._buckets: Dict[str, TokenBucket] = {}
    
    def _get_bucket(self, key: str) -> TokenBucket:
        """
        Get or create a token bucket for the given key.
        
        Args:
            key: Bucket identifier
            
        Returns:
            TokenBucket instance
        """
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self.settings.burst_limit,
                fill_rate=self.settings.requests_per_minute / 60.0
            )
        return self._buckets[key]
    
    async def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens for the given key.
        
        Args:
            key: Resource identifier
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        bucket = self._get_bucket(key)
        return await bucket.acquire(tokens)
    
    async def wait_for_token(self, key: str, tokens: int = 1) -> None:
        """
        Wait until tokens are available.
        
        Args:
            key: Resource identifier
            tokens: Number of tokens to acquire
        """
        while not await self.acquire(key, tokens):
            await asyncio.sleep(1)

def rate_limit(key: str, tokens: int = 1):
    """
    Decorator for rate limiting.
    
    Args:
        key: Resource identifier
        tokens: Number of tokens required
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_rate_limiter'):
                self._rate_limiter = RateLimiter()
            
            await self._rate_limiter.wait_for_token(key, tokens)
            
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Rate limited operation failed: {e}")
                raise
        
        return wrapper
    return decorator 