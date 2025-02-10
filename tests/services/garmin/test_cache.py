"""Tests for caching implementation."""
import json
import zlib
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.services.garmin.cache import (
    Cache,
    CacheSettings,
    CacheKey,
    CacheTTL,
    cached
)

@pytest.fixture
def settings():
    """Cache settings for testing."""
    return CacheSettings(
        url="redis://localhost:6379",
        compress=True,
        compression_threshold=1024
    )

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock

@pytest.fixture
async def cache(settings, mock_redis):
    """Cache instance for testing."""
    with patch("src.services.garmin.cache.aioredis") as mock_aioredis:
        mock_aioredis.from_url.return_value = mock_redis
        cache = Cache(settings)
        await cache.connect()
        yield cache
        await cache.disconnect()

@pytest.mark.asyncio
async def test_cache_initialization(settings):
    """Test cache initialization."""
    cache = Cache(settings)
    assert cache.settings == settings
    assert cache._redis is None

@pytest.mark.asyncio
async def test_cache_connect(cache, mock_redis):
    """Test Redis connection."""
    assert cache._redis == mock_redis

@pytest.mark.asyncio
async def test_cache_disconnect(cache):
    """Test Redis disconnection."""
    await cache.disconnect()
    assert cache._redis is None

@pytest.mark.asyncio
async def test_cache_get(cache, mock_redis):
    """Test getting value from cache."""
    # Test cache miss
    assert await cache.get("test_key") is None
    
    # Test cache hit
    mock_redis.get.return_value = json.dumps({"test": "data"}).encode()
    result = await cache.get("test_key")
    assert result == {"test": "data"}
    
    # Test compressed data
    compressed = zlib.compress(json.dumps({"test": "data"}).encode())
    mock_redis.get.return_value = compressed
    result = await cache.get("test_key")
    assert result == {"test": "data"}

@pytest.mark.asyncio
async def test_cache_set(cache, mock_redis):
    """Test setting value in cache."""
    # Test normal set
    value = {"test": "data"}
    assert await cache.set("test_key", value)
    mock_redis.set.assert_called_once()
    
    # Test compressed set
    large_value = {"test": "x" * 2000}  # Exceeds compression threshold
    assert await cache.set("test_key", large_value)

@pytest.mark.asyncio
async def test_cache_delete(cache, mock_redis):
    """Test deleting value from cache."""
    assert await cache.delete("test_key")
    mock_redis.delete.assert_called_once_with("test_key")

class TestClass:
    """Test class for cache decorator."""
    
    def __init__(self):
        self.call_count = 0
    
    @cached(CacheKey.SLEEP, ttl=CacheTTL.SLEEP)
    async def cached_method(self, target_date: datetime, user_id: str = "default"):
        """Test method with caching."""
        self.call_count += 1
        return {
            "date": target_date.isoformat(),
            "user_id": user_id,
            "count": self.call_count
        }

@pytest.mark.asyncio
async def test_cached_decorator(mock_redis):
    """Test cache decorator."""
    with patch("src.services.garmin.cache.aioredis") as mock_aioredis:
        mock_aioredis.from_url.return_value = mock_redis
        
        test_obj = TestClass()
        test_date = datetime(2024, 2, 7)
        
        # First call should miss cache
        result1 = await test_obj.cached_method(test_date)
        assert result1["count"] == 1
        
        # Set up cache hit for second call
        mock_redis.get.return_value = json.dumps(result1).encode()
        
        # Second call should hit cache
        result2 = await test_obj.cached_method(test_date)
        assert result2 == result1  # Should get cached value
        assert test_obj.call_count == 1  # Method should not be called again

@pytest.mark.asyncio
async def test_cache_error_handling(cache, mock_redis):
    """Test cache error handling."""
    # Test get error
    mock_redis.get.side_effect = Exception("Redis error")
    assert await cache.get("test_key") is None
    
    # Test set error
    mock_redis.set.side_effect = Exception("Redis error")
    assert not await cache.set("test_key", {"test": "data"})
    
    # Test delete error
    mock_redis.delete.side_effect = Exception("Redis error")
    assert not await cache.delete("test_key")

@pytest.mark.asyncio
async def test_cache_compression(cache, mock_redis):
    """Test cache compression."""
    # Small data should not be compressed
    small_value = {"test": "data"}
    await cache.set("test_key", small_value)
    set_call = mock_redis.set.call_args[0]
    assert not set_call[1].startswith(b'\x1f\x8b')  # Not compressed
    
    # Large data should be compressed
    large_value = {"test": "x" * 2000}
    await cache.set("test_key", large_value)
    set_call = mock_redis.set.call_args[0]
    assert isinstance(set_call[1], bytes)  # Should be compressed

@pytest.mark.asyncio
async def test_cache_ttl(cache, mock_redis):
    """Test cache TTL handling."""
    value = {"test": "data"}
    ttl = 3600
    
    await cache.set("test_key", value, ttl=ttl)
    mock_redis.set.assert_called_with("test_key", mock_redis.set.call_args[0][1], ex=ttl) 