"""
Configuration settings for monitoring and metrics collection.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field, SecretStr, ConfigDict


class AlertThresholds(BaseModel):
    """Alert threshold configuration."""
    
    model_config = ConfigDict(
        title="Alert Thresholds",
        frozen=True
    )
    
    error_rate: float = Field(
        default=0.05,
        description="Error rate threshold (5%)"
    )
    cache_miss_rate: float = Field(
        default=0.20,
        description="Cache miss rate threshold (20%)"
    )
    api_latency_seconds: float = Field(
        default=2.0,
        description="API latency threshold in seconds"
    )
    rate_limit_buffer: float = Field(
        default=0.80,
        description="Rate limit buffer threshold (80%)"
    )


class MetricsConfig(BaseModel):
    """Metrics collection configuration."""
    
    model_config = ConfigDict(
        title="Metrics Configuration",
        frozen=True
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether metrics collection is enabled"
    )
    push_gateway_url: str = Field(
        default="",
        description="Prometheus push gateway URL (if using push model)"
    )
    collection_interval_seconds: int = Field(
        default=15,
        description="Metrics collection interval in seconds"
    )


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    
    model_config = ConfigDict(
        title="Health Check Configuration",
        frozen=True
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether health checks are enabled"
    )
    check_interval_seconds: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    endpoints: Dict[str, bool] = Field(
        default={
            "redis": True,
            "garmin": True,
            "rate_limits": True
        },
        description="Enabled health check endpoints"
    )
    api_key: SecretStr = Field(
        ...,
        description="API key for accessing monitoring endpoints",
        json_schema_extra={"env": "MONITORING_API_KEY"}
    )


class MonitoringConfig(BaseModel):
    """Main monitoring configuration."""
    
    model_config = ConfigDict(
        title="Monitoring Configuration",
        frozen=True,
        env_prefix="MONITORING_"
    )
    
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig,
        description="Metrics collection configuration"
    )
    health_checks: HealthCheckConfig = Field(
        default_factory=HealthCheckConfig,
        description="Health check configuration"
    )
    alert_thresholds: AlertThresholds = Field(
        default_factory=AlertThresholds,
        description="Alert threshold configuration"
    ) 