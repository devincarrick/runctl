"""
Metrics decorator for tracking Garmin Connect API calls.
"""
from functools import wraps
from datetime import datetime
from typing import Any, Callable, TypeVar
import inspect

from src.infra.monitoring.metrics import metrics
from .retry import RetryableError, NonRetryableError

T = TypeVar('T')


def track_metrics(endpoint: str):
    """
    Decorator to track metrics for Garmin Connect API calls.
    
    Args:
        endpoint: The name of the API endpoint being called
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Get the original function name for better error tracking
        func_name = func.__name__
        
        # Handle both async and sync functions
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                start_time = datetime.now()
                
                try:
                    # Track API request
                    metrics.api_requests.labels(endpoint=endpoint).inc()
                    
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Track latency
                    duration = (datetime.now() - start_time).total_seconds()
                    metrics.api_latency.labels(endpoint=endpoint).observe(duration)
                    
                    return result
                    
                except RetryableError as e:
                    # Track retryable errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="retryable"
                    ).inc()
                    metrics.retry_attempts.labels(endpoint=endpoint).inc()
                    raise
                    
                except NonRetryableError as e:
                    # Track non-retryable errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="non_retryable"
                    ).inc()
                    raise
                    
                except Exception as e:
                    # Track unexpected errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="unexpected"
                    ).inc()
                    raise
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                start_time = datetime.now()
                
                try:
                    # Track API request
                    metrics.api_requests.labels(endpoint=endpoint).inc()
                    
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Track latency
                    duration = (datetime.now() - start_time).total_seconds()
                    metrics.api_latency.labels(endpoint=endpoint).observe(duration)
                    
                    return result
                    
                except RetryableError as e:
                    # Track retryable errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="retryable"
                    ).inc()
                    metrics.retry_attempts.labels(endpoint=endpoint).inc()
                    raise
                    
                except NonRetryableError as e:
                    # Track non-retryable errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="non_retryable"
                    ).inc()
                    raise
                    
                except Exception as e:
                    # Track unexpected errors
                    metrics.api_errors.labels(
                        endpoint=endpoint,
                        error_type="unexpected"
                    ).inc()
                    raise
            
            return sync_wrapper
    
    return decorator 