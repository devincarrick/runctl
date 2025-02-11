"""
Prometheus metrics configuration and collection for the runctl application.
"""
from typing import Dict, List, Optional
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from prometheus_client.metrics import MetricWrapperBase


class MetricsRegistry:
    """Central registry for all Prometheus metrics in the application."""
    
    def __init__(self) -> None:
        """Initialize the metrics registry."""
        self.registry: CollectorRegistry = CollectorRegistry()
        self._setup_metrics()
    
    def _setup_metrics(self) -> None:
        """Set up all metrics collectors."""
        # Cache metrics
        self.cache_hits = Counter(
            'garmin_cache_hits_total',
            'Total number of cache hits',
            registry=self.registry
        )
        self.cache_misses = Counter(
            'garmin_cache_misses_total',
            'Total number of cache misses',
            registry=self.registry
        )
        self.cache_latency = Histogram(
            'garmin_cache_latency_seconds',
            'Cache operation latency in seconds',
            registry=self.registry
        )
        self.cache_errors = Counter(
            'garmin_cache_errors_total',
            'Total number of cache errors',
            ['operation', 'error_type'],
            registry=self.registry
        )
        self.cache_value_size = Histogram(
            'garmin_cache_value_size_bytes',
            'Size of cached values in bytes',
            ['key'],
            buckets=[1024, 4096, 16384, 65536, 262144],  # 1KB to 256KB
            registry=self.registry
        )
        
        # API metrics
        self.api_requests = Counter(
            'garmin_api_requests_total',
            'Total number of Garmin API requests',
            ['endpoint'],
            registry=self.registry
        )
        self.api_errors = Counter(
            'garmin_api_errors_total',
            'Total number of Garmin API errors',
            ['endpoint', 'error_type'],
            registry=self.registry
        )
        self.api_latency = Histogram(
            'garmin_api_latency_seconds',
            'Garmin API request latency in seconds',
            ['endpoint'],
            registry=self.registry
        )
        
        # Rate limiting metrics
        self.rate_limits_hit = Counter(
            'garmin_rate_limits_total',
            'Total number of rate limit hits',
            ['endpoint'],
            registry=self.registry
        )
        self.rate_limit_remaining = Gauge(
            'garmin_rate_limit_remaining',
            'Remaining rate limit quota',
            ['endpoint'],
            registry=self.registry
        )
        
        # Retry metrics
        self.retry_attempts = Counter(
            'garmin_retry_attempts_total',
            'Total number of retry attempts',
            ['endpoint'],
            registry=self.registry
        )
        self.retry_success = Counter(
            'garmin_retry_success_total',
            'Total number of successful retries',
            ['endpoint'],
            registry=self.registry
        )
    
    def get_metric(self, name: str) -> Optional[MetricWrapperBase]:
        """Get a metric by name.
        
        Args:
            name: The name of the metric to retrieve
            
        Returns:
            The metric if found, None otherwise
        """
        return getattr(self, name, None)
    
    def get_all_metrics(self) -> Dict[str, MetricWrapperBase]:
        """Get all registered metrics.
        
        Returns:
            Dictionary of metric name to metric object
        """
        return {
            name: metric for name, metric in vars(self).items()
            if isinstance(metric, MetricWrapperBase)
        }


# Global metrics registry instance
metrics = MetricsRegistry() 