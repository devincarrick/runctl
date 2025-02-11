"""Garth-based client for Garmin Connect API."""
import logging
from datetime import datetime, date
from typing import Optional, List

import garth

from .config import get_settings
from .rate_limit import rate_limit
from .cache import cached, CacheKey, CacheTTL
from .retry import with_retry, handle_retry_errors
from .metrics_decorator import track_metrics

logger = logging.getLogger(__name__)

class GarthClient:
    """Client for Garmin Connect API using garth library."""
    
    def __init__(self):
        self._settings = get_settings()
        self._initialized = False
        self._client = None
    
    async def __aenter__(self):
        await self.init_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # garth handles session cleanup internally
        pass
    
    @handle_retry_errors
    @track_metrics("init")
    async def init_client(self):
        """Initialize the garth client and authenticate."""
        if not self._initialized:
            try:
                logger.info("Initializing Garth client...")
                self._client = garth.Client()
                self._client.configure(domain="garmin.com")
                
                # Try to load saved tokens first
                try:
                    await self._client.load()
                except FileNotFoundError:
                    # If no saved tokens, authenticate with credentials
                    await self._authenticate()
                
                self._initialized = True
                logger.info("Garth client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Garth client: {e}")
                raise
    
    @rate_limit("auth", tokens=5)  # Higher token cost for authentication
    @with_retry(max_retries=2)  # Fewer retries for auth
    @track_metrics("auth")
    async def _authenticate(self):
        """Authenticate with Garmin Connect using email and password."""
        try:
            logger.info("Authenticating with Garmin Connect...")
            await self._client.login(self._settings.email, self._settings.password)
            # Save tokens for future use
            await self._client.save()
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    @rate_limit("sleep")
    @cached(CacheKey.SLEEP, ttl=CacheTTL.SLEEP)
    @with_retry()
    @handle_retry_errors
    @track_metrics("sleep")
    async def get_sleep_data(self, *, target_date: datetime, user_id: str = "default"):
        """
        Fetch sleep data for a specific date.
        
        Args:
            target_date: The date to fetch sleep data for
            user_id: User identifier for caching
            
        Returns:
            Sleep data for the specified date
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching sleep data for {target_date.date()}")
            # Convert datetime to date if needed
            if isinstance(target_date, datetime):
                target_date = target_date.date()
            
            sleep_data = await self._client.get_sleep_data(target_date)
            return sleep_data
        except Exception as e:
            logger.error(f"Failed to fetch sleep data for {target_date}: {e}")
            raise
    
    @rate_limit("sleep", tokens=2)  # Higher token cost for date range
    @with_retry()
    @handle_retry_errors
    @track_metrics("sleep_range")
    async def get_sleep_data_range(
        self, 
        start_date: datetime,
        end_date: datetime,
        user_id: str = "default"
    ):
        """
        Fetch sleep data for a date range.
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            user_id: User identifier for caching
            
        Returns:
            List of sleep data objects
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching sleep data from {start_date.date()} to {end_date.date()}")
            # Convert datetimes to dates if needed
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
                
            sleep_data = await self._client.get_sleep_data(start_date, end_date)
            return sleep_data
        except Exception as e:
            logger.error(f"Failed to fetch sleep data range: {e}")
            raise
    
    @rate_limit("stress")
    @cached(CacheKey.STRESS, ttl=CacheTTL.STRESS)
    @with_retry()
    @handle_retry_errors
    @track_metrics("stress")
    async def get_stress_data(self, *, target_date: datetime, user_id: str = "default"):
        """
        Fetch stress data for a specific date.
        
        Args:
            target_date: The date to fetch stress data for
            user_id: User identifier for caching
            
        Returns:
            StressData object containing stress metrics for the specified date
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching stress data for {target_date.date()}")
            # Convert datetime to date if needed
            if isinstance(target_date, datetime):
                target_date = target_date.date()
            
            stress_data = await self._client.get_stress_data(target_date)
            return stress_data
        except Exception as e:
            logger.error(f"Failed to fetch stress data for {target_date}: {e}")
            raise
    
    @rate_limit("stress", tokens=2)  # Higher token cost for date range
    @with_retry()
    @handle_retry_errors
    @track_metrics("stress_range")
    async def get_stress_data_range(
        self, 
        start_date: datetime,
        end_date: datetime,
        user_id: str = "default"
    ):
        """
        Fetch stress data for a date range.
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            user_id: User identifier for caching
            
        Returns:
            List of StressData objects
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching stress data from {start_date.date()} to {end_date.date()}")
            # Convert datetimes to dates if needed
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
                
            stress_data = await self._client.get_stress_data(start_date, end_date)
            return stress_data
        except Exception as e:
            logger.error(f"Failed to fetch stress data range: {e}")
            raise
    
    @rate_limit("body_battery")
    @cached(CacheKey.BODY_BATTERY, ttl=CacheTTL.BODY_BATTERY)
    @with_retry()
    @handle_retry_errors
    @track_metrics("body_battery")
    async def get_body_battery_data(self, *, target_date: datetime, user_id: str = "default"):
        """
        Fetch Body Battery data for a specific date.
        
        Args:
            target_date: The date to fetch Body Battery data for
            user_id: User identifier for caching
            
        Returns:
            BodyBatteryData object containing Body Battery metrics for the specified date
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching Body Battery data for {target_date.date()}")
            # Convert datetime to date if needed
            if isinstance(target_date, datetime):
                target_date = target_date.date()
            
            body_battery_data = await self._client.get_body_battery_data(target_date)
            return body_battery_data
        except Exception as e:
            logger.error(f"Failed to fetch Body Battery data for {target_date}: {e}")
            raise
    
    @rate_limit("body_battery", tokens=2)  # Higher token cost for date range
    @with_retry()
    @handle_retry_errors
    @track_metrics("body_battery_range")
    async def get_body_battery_data_range(
        self, 
        start_date: datetime,
        end_date: datetime,
        user_id: str = "default"
    ):
        """
        Fetch Body Battery data for a date range.
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            user_id: User identifier for caching
            
        Returns:
            List of BodyBatteryData objects
        """
        if not self._initialized:
            await self.init_client()
            
        try:
            logger.info(f"Fetching Body Battery data from {start_date.date()} to {end_date.date()}")
            # Convert datetimes to dates if needed
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
                
            body_battery_data = await self._client.get_body_battery_data(start_date, end_date)
            return body_battery_data
        except Exception as e:
            logger.error(f"Failed to fetch Body Battery data range: {e}")
            raise 