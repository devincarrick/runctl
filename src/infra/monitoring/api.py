"""
FastAPI router for health check endpoints.
"""
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from src.infra.monitoring.health import HealthCheck
from src.infra.monitoring.config import MonitoringConfig
from src.services.garmin.garth_client import GarthClient
from src.services.garmin.cache import Cache

# Create router
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# API key security
api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(
    api_key: str = Security(api_key_header),
    config: MonitoringConfig = Depends(MonitoringConfig)
) -> None:
    """
    Verify the API key for monitoring endpoints.
    
    Args:
        api_key: API key from request header
        config: Monitoring configuration
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not config.health_checks.enabled:
        raise HTTPException(
            status_code=503,
            detail="Health checks are disabled"
        )
    
    if api_key != config.health_checks.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


@router.get(
    "/health",
    response_model=Dict[str, Any],
    dependencies=[Depends(verify_api_key)]
)
async def health_check(
    component: str = None,
    cache: Cache = Depends(Cache),
    garmin_client: GarthClient = Depends(GarthClient)
) -> Dict[str, Any]:
    """
    Get health status of system components.
    
    Args:
        component: Optional component to check
        cache: Redis cache instance
        garmin_client: Garmin client instance
        
    Returns:
        Health check results
    """
    health = HealthCheck(cache._redis, garmin_client)
    return await health.check_health(component)


@router.get(
    "/metrics",
    dependencies=[Depends(verify_api_key)]
)
async def metrics() -> Response:
    """
    Get Prometheus metrics.
    
    Returns:
        Prometheus metrics in text format
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    ) 