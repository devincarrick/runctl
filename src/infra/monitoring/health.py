"""
Health check implementations for the runctl application.
"""
from typing import Dict, Any, Callable, Awaitable
import asyncio
from datetime import datetime
import aioredis
from loguru import logger

from src.services.garmin.interface import GarminClientInterface
from src.infra.monitoring.metrics import metrics


class HealthCheck:
    """Health check implementation for system components."""
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        garmin_client: GarminClientInterface
    ) -> None:
        """Initialize the health check.
        
        Args:
            redis_client: Redis client instance
            garmin_client: Garmin client instance
        """
        self.redis = redis_client
        self.garmin = garmin_client
        self._checks: Dict[str, Callable[[], Awaitable[Dict[str, Any]]]] = {
            'redis': self._check_redis,
            'garmin': self._check_garmin_api,
            'rate_limits': self._check_rate_limits
        }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity.
        
        Returns:
            Health check result
        """
        try:
            await self.redis.ping()
            return {
                'status': 'healthy',
                'latency_ms': await self._measure_redis_latency()
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_garmin_api(self) -> Dict[str, Any]:
        """Check Garmin API connectivity.
        
        Returns:
            Health check result
        """
        try:
            # Use a lightweight API call to check connectivity
            await self.garmin.check_auth()
            return {
                'status': 'healthy',
                'latency_ms': await self._measure_garmin_latency()
            }
        except Exception as e:
            logger.error(f"Garmin API health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_rate_limits(self) -> Dict[str, Any]:
        """Check rate limit status.
        
        Returns:
            Health check result
        """
        try:
            # Get current rate limit status from metrics
            endpoints = ['sleep', 'stress', 'body_battery']
            status = {}
            for endpoint in endpoints:
                remaining = metrics.rate_limit_remaining.labels(endpoint=endpoint)._value.get()
                status[endpoint] = {
                    'remaining': remaining,
                    'status': 'healthy' if remaining > 10 else 'warning'
                }
            return {
                'status': 'healthy' if all(s['status'] == 'healthy' for s in status.values()) else 'warning',
                'endpoints': status
            }
        except Exception as e:
            logger.error(f"Rate limit health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _measure_redis_latency(self) -> float:
        """Measure Redis operation latency.
        
        Returns:
            Latency in milliseconds
        """
        start = datetime.now()
        await self.redis.ping()
        return (datetime.now() - start).total_seconds() * 1000
    
    async def _measure_garmin_latency(self) -> float:
        """Measure Garmin API latency.
        
        Returns:
            Latency in milliseconds
        """
        start = datetime.now()
        await self.garmin.check_auth()
        return (datetime.now() - start).total_seconds() * 1000
    
    async def check_health(self, component: str = None) -> Dict[str, Any]:
        """Run health checks.
        
        Args:
            component: Optional component to check. If None, checks all components.
            
        Returns:
            Health check results
        """
        if component and component not in self._checks:
            raise ValueError(f"Unknown component: {component}")
        
        checks_to_run = [component] if component else self._checks.keys()
        results = {}
        
        for check in checks_to_run:
            results[check] = await self._checks[check]()
        
        overall_status = 'healthy'
        if any(r['status'] == 'unhealthy' for r in results.values()):
            overall_status = 'unhealthy'
        elif any(r['status'] == 'warning' for r in results.values()):
            overall_status = 'warning'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': results
        } 