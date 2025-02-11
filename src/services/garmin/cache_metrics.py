"""
Metrics tracking for cache operations.
"""
from functools import wraps
from datetime import datetime
from typing import Any, Callable, TypeVar, Optional

from src.infra.monitoring.metrics import metrics

T = TypeVar('T')


def track_cache_metrics(operation: str):
    """
    Decorator to track cache operation metrics.
    
    Args:
        operation: The type of cache operation (get, set, delete)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = datetime.now()
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Track latency
                duration = (datetime.now() - start_time).total_seconds()
                metrics.cache_latency.observe(duration)
                
                # Track operation-specific metrics
                if operation == "get":
                    if result is not None:
                        metrics.cache_hits.inc()
                    else:
                        metrics.cache_misses.inc()
                
                return result
                
            except Exception as e:
                # Track errors
                metrics.cache_errors.labels(
                    operation=operation,
                    error_type=type(e).__name__
                ).inc()
                raise
        
        return wrapper
    
    return decorator


def track_cache_size(key: str, value: Any) -> None:
    """
    Track the size of cached values.
    
    Args:
        key: Cache key
        value: Value being cached
    """
    try:
        # Estimate size in bytes
        size = len(str(value).encode('utf-8'))
        metrics.cache_value_size.labels(key=key).observe(size)
    except Exception:
        pass  # Ignore size tracking errors 