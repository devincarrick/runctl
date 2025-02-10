"""Retry mechanism implementation for Garmin Connect API."""
import logging
from typing import Type, Optional, Callable, TypeVar, Any
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry mechanism."""
    
    MAX_RETRIES: int = 3
    INITIAL_DELAY: float = 1.0
    MAX_DELAY: float = 60.0
    BACKOFF_FACTOR: float = 2.0

class RetryableError(Exception):
    """Base class for retryable errors."""
    pass

class NetworkError(RetryableError):
    """Network-related errors that should be retried."""
    pass

class RateLimitError(RetryableError):
    """Rate limit errors that should be retried with backoff."""
    pass

class NonRetryableError(Exception):
    """Base class for non-retryable errors."""
    pass

class AuthenticationError(NonRetryableError):
    """Authentication errors that should not be retried."""
    pass

class ValidationError(NonRetryableError):
    """Data validation errors that should not be retried."""
    pass

def with_retry(
    retry_on: Optional[Type[Exception]] = RetryableError,
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    backoff_factor: Optional[float] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        retry_on: Exception type to retry on
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_config = RetryConfig()
            
            @retry(
                retry=retry_if_exception_type(retry_on),
                stop=stop_after_attempt(
                    max_retries or retry_config.MAX_RETRIES
                ),
                wait=wait_exponential(
                    multiplier=initial_delay or retry_config.INITIAL_DELAY,
                    min=initial_delay or retry_config.INITIAL_DELAY,
                    max=max_delay or retry_config.MAX_DELAY,
                    exp_base=backoff_factor or retry_config.BACKOFF_FACTOR
                ),
                before_sleep=before_sleep_log(logger, logging.INFO)
            )
            async def retryable_func(*retry_args: Any, **retry_kwargs: Any) -> T:
                try:
                    return await func(*retry_args, **retry_kwargs)
                except Exception as e:
                    # Map exceptions to retryable/non-retryable types
                    if isinstance(e, (ConnectionError, TimeoutError)):
                        raise NetworkError(str(e)) from e
                    elif str(e).startswith("429"):  # Rate limit error
                        raise RateLimitError(str(e)) from e
                    elif "authentication" in str(e).lower():
                        raise AuthenticationError(str(e)) from e
                    elif "validation" in str(e).lower():
                        raise ValidationError(str(e)) from e
                    else:
                        raise
            
            try:
                return await retryable_func(*args, **kwargs)
            except RetryError as e:
                logger.error(
                    f"Operation failed after {max_retries or retry_config.MAX_RETRIES} "
                    f"retries: {str(e)}"
                )
                raise
        
        return wrapper
    
    return decorator

def handle_retry_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for handling retry-related errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except RetryError as e:
            if isinstance(e.last_attempt.exception(), NetworkError):
                logger.error("Network error persisted after retries")
                raise NetworkError("Network error persisted after retries") from e
            elif isinstance(e.last_attempt.exception(), RateLimitError):
                logger.error("Rate limit error persisted after retries")
                raise RateLimitError("Rate limit error persisted after retries") from e
            else:
                raise
        except NonRetryableError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    return wrapper 