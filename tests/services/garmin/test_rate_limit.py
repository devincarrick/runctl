"""Tests for rate limiting implementation."""
import time
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.services.garmin.rate_limit import (
    RateLimitSettings,
    TokenBucket,
    RateLimiter,
    rate_limit
)

@pytest.fixture
def settings():
    """Rate limit settings for testing."""
    return RateLimitSettings(
        requests_per_minute=60,
        burst_limit=10,
        cooldown_seconds=60
    )

@pytest.fixture
def token_bucket():
    """Token bucket for testing."""
    return TokenBucket(
        capacity=10,
        fill_rate=1.0,  # 1 token per second
        tokens=10.0
    )

@pytest.fixture
def rate_limiter(settings):
    """Rate limiter for testing."""
    return RateLimiter(settings)

@pytest.mark.asyncio
async def test_token_bucket_initialization():
    """Test token bucket initialization."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0)
    assert bucket.capacity == 10
    assert bucket.fill_rate == 1.0
    assert bucket.tokens == 0.0
    assert isinstance(bucket.last_update, float)

@pytest.mark.asyncio
async def test_token_bucket_acquire():
    """Test token acquisition from bucket."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0, tokens=5.0)
    
    # Should be able to acquire 5 tokens
    assert await bucket.acquire(5)
    assert bucket.tokens == 0.0
    
    # Should not be able to acquire more tokens
    assert not await bucket.acquire(1)

@pytest.mark.asyncio
async def test_token_bucket_refill():
    """Test token bucket refill over time."""
    bucket = TokenBucket(capacity=10, fill_rate=1.0, tokens=0.0)
    
    # Wait for 2 seconds
    bucket.last_update = time.monotonic() - 2
    
    # Should have 2 new tokens
    assert await bucket.acquire(2)
    assert bucket.tokens == 0.0

@pytest.mark.asyncio
async def test_rate_limiter_initialization(settings):
    """Test rate limiter initialization."""
    limiter = RateLimiter(settings)
    assert limiter.settings == settings
    assert isinstance(limiter._buckets, dict)

@pytest.mark.asyncio
async def test_rate_limiter_acquire(rate_limiter):
    """Test token acquisition through rate limiter."""
    # First acquisition should succeed
    assert await rate_limiter.acquire("test")
    
    # Get the bucket and check its tokens
    bucket = rate_limiter._get_bucket("test")
    assert bucket.tokens == rate_limiter.settings.burst_limit - 1

@pytest.mark.asyncio
async def test_rate_limiter_wait_for_token(rate_limiter):
    """Test waiting for token availability."""
    # Use up all tokens
    for _ in range(rate_limiter.settings.burst_limit):
        assert await rate_limiter.acquire("test")
    
    # Next acquisition should wait
    start_time = time.monotonic()
    await rate_limiter.wait_for_token("test")
    elapsed = time.monotonic() - start_time
    
    # Should have waited about 1 second for a new token
    assert elapsed >= 1.0

class TestClass:
    """Test class for rate limit decorator."""
    
    def __init__(self):
        self.call_count = 0
    
    @rate_limit("test")
    async def rate_limited_method(self):
        """Test method with rate limiting."""
        self.call_count += 1
        return self.call_count

@pytest.mark.asyncio
async def test_rate_limit_decorator():
    """Test rate limit decorator."""
    test_obj = TestClass()
    
    # First call should succeed immediately
    result = await test_obj.rate_limited_method()
    assert result == 1
    
    # Multiple rapid calls
    results = await asyncio.gather(
        *[test_obj.rate_limited_method() for _ in range(5)]
    )
    
    # All calls should have completed
    assert len(results) == 5
    assert all(r > 0 for r in results)

@pytest.mark.asyncio
async def test_rate_limit_decorator_error_handling():
    """Test error handling in rate limit decorator."""
    class ErrorClass:
        @rate_limit("test")
        async def error_method(self):
            raise ValueError("Test error")
    
    test_obj = ErrorClass()
    
    with pytest.raises(ValueError) as exc_info:
        await test_obj.error_method()
    
    assert str(exc_info.value) == "Test error" 