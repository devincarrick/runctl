"""Tests for retry mechanism implementation."""
import pytest
import time
from unittest.mock import MagicMock, patch

from src.services.garmin.retry import (
    RetryConfig,
    RetryableError,
    NetworkError,
    RateLimitError,
    NonRetryableError,
    AuthenticationError,
    ValidationError,
    with_retry,
    handle_retry_errors
)

@pytest.fixture
def mock_function():
    """Mock function for testing retries."""
    return MagicMock()

class TestClass:
    """Test class for retry decorators."""
    
    def __init__(self):
        self.call_count = 0
    
    @with_retry()
    async def retryable_method(self):
        """Test method with retry."""
        self.call_count += 1
        raise NetworkError("Test network error")
    
    @with_retry(max_retries=2)
    async def custom_retry_method(self):
        """Test method with custom retry settings."""
        self.call_count += 1
        raise NetworkError("Test network error")
    
    @with_retry()
    async def non_retryable_method(self):
        """Test method with non-retryable error."""
        self.call_count += 1
        raise AuthenticationError("Test auth error")
    
    @handle_retry_errors
    @with_retry()
    async def handled_method(self):
        """Test method with error handling."""
        self.call_count += 1
        raise NetworkError("Test network error")

@pytest.mark.asyncio
async def test_retry_config():
    """Test retry configuration."""
    config = RetryConfig()
    assert config.MAX_RETRIES == 3
    assert config.INITIAL_DELAY == 1.0
    assert config.MAX_DELAY == 60.0
    assert config.BACKOFF_FACTOR == 2.0

@pytest.mark.asyncio
async def test_retry_on_network_error():
    """Test retry on network error."""
    test_obj = TestClass()
    
    with pytest.raises(NetworkError):
        await test_obj.retryable_method()
    
    assert test_obj.call_count == RetryConfig.MAX_RETRIES

@pytest.mark.asyncio
async def test_custom_retry_settings():
    """Test retry with custom settings."""
    test_obj = TestClass()
    
    with pytest.raises(NetworkError):
        await test_obj.custom_retry_method()
    
    assert test_obj.call_count == 2  # Custom max_retries=2

@pytest.mark.asyncio
async def test_no_retry_on_auth_error():
    """Test no retry on authentication error."""
    test_obj = TestClass()
    
    with pytest.raises(AuthenticationError):
        await test_obj.non_retryable_method()
    
    assert test_obj.call_count == 1  # Should not retry

@pytest.mark.asyncio
async def test_retry_backoff():
    """Test exponential backoff between retries."""
    test_obj = TestClass()
    start_time = time.monotonic()
    
    with pytest.raises(NetworkError):
        await test_obj.retryable_method()
    
    elapsed = time.monotonic() - start_time
    # Should take at least the sum of initial delays
    # 1 + 2 + 4 = 7 seconds with default settings
    assert elapsed >= 7.0

@pytest.mark.asyncio
async def test_retry_error_handling():
    """Test retry error handling decorator."""
    test_obj = TestClass()
    
    with pytest.raises(NetworkError) as exc_info:
        await test_obj.handled_method()
    
    assert "persisted after retries" in str(exc_info.value)
    assert test_obj.call_count == RetryConfig.MAX_RETRIES

@pytest.mark.asyncio
async def test_retry_on_rate_limit():
    """Test retry on rate limit error."""
    class RateLimitTest:
        def __init__(self):
            self.call_count = 0
        
        @with_retry()
        async def method(self):
            """Test method that hits rate limit."""
            self.call_count += 1
            raise RateLimitError("429 Too Many Requests")
    
    test_obj = RateLimitTest()
    
    with pytest.raises(RateLimitError):
        await test_obj.method()
    
    assert test_obj.call_count == RetryConfig.MAX_RETRIES

@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test successful retry after failures."""
    class EventualSuccess:
        def __init__(self):
            self.call_count = 0
        
        @with_retry()
        async def method(self):
            """Test method that succeeds after failures."""
            self.call_count += 1
            if self.call_count < 3:
                raise NetworkError("Test network error")
            return "success"
    
    test_obj = EventualSuccess()
    result = await test_obj.method()
    
    assert result == "success"
    assert test_obj.call_count == 3

@pytest.mark.asyncio
async def test_retry_with_validation_error():
    """Test no retry on validation error."""
    class ValidationTest:
        def __init__(self):
            self.call_count = 0
        
        @with_retry()
        async def method(self):
            """Test method with validation error."""
            self.call_count += 1
            raise ValidationError("Invalid data")
    
    test_obj = ValidationTest()
    
    with pytest.raises(ValidationError):
        await test_obj.method()
    
    assert test_obj.call_count == 1  # Should not retry

@pytest.mark.asyncio
async def test_retry_exception_mapping():
    """Test exception mapping to retry categories."""
    class ExceptionTest:
        def __init__(self):
            self.call_count = 0
        
        @with_retry()
        async def method(self, error_type: str):
            """Test method with different error types."""
            self.call_count += 1
            if error_type == "connection":
                raise ConnectionError("Connection failed")
            elif error_type == "timeout":
                raise TimeoutError("Request timed out")
            elif error_type == "rate_limit":
                raise Exception("429 Too Many Requests")
            elif error_type == "auth":
                raise Exception("Authentication failed")
            else:
                raise Exception("Unknown error")
    
    test_obj = ExceptionTest()
    
    # Test connection error
    with pytest.raises(NetworkError):
        await test_obj.method("connection")
    assert test_obj.call_count == RetryConfig.MAX_RETRIES
    
    # Reset call count
    test_obj.call_count = 0
    
    # Test timeout error
    with pytest.raises(NetworkError):
        await test_obj.method("timeout")
    assert test_obj.call_count == RetryConfig.MAX_RETRIES
    
    # Reset call count
    test_obj.call_count = 0
    
    # Test rate limit error
    with pytest.raises(RateLimitError):
        await test_obj.method("rate_limit")
    assert test_obj.call_count == RetryConfig.MAX_RETRIES
    
    # Reset call count
    test_obj.call_count = 0
    
    # Test authentication error
    with pytest.raises(AuthenticationError):
        await test_obj.method("auth")
    assert test_obj.call_count == 1  # Should not retry 