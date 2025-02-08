"""Garth-based client for Garmin Connect API."""
import logging
from datetime import datetime, date
from typing import Optional, List

import garth

from .config import get_settings

logger = logging.getLogger(__name__)

class GarthClient:
    """Client for Garmin Connect API using garth library."""
    
    def __init__(self):
        self._settings = get_settings()
        self._initialized = False
    
    async def __aenter__(self):
        await self.init_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # garth handles session cleanup internally
        pass
    
    async def init_client(self):
        """Initialize the garth client and authenticate."""
        if not self._initialized:
            try:
                logger.info("Initializing Garth client...")
                garth.configure(domain="garmin.com")
                
                # Try to load saved tokens first
                try:
                    garth.load()
                except FileNotFoundError:
                    # If no saved tokens, authenticate with credentials
                    await self._authenticate()
                
                self._initialized = True
                logger.info("Garth client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Garth client: {e}")
                raise
    
    async def _authenticate(self):
        """Authenticate with Garmin Connect using email and password."""
        try:
            logger.info("Authenticating with Garmin Connect...")
            garth.login(self._settings.email, self._settings.password)
            # Save tokens for future use
            garth.save()
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def get_sleep_data(self, target_date: datetime):
        """
        Fetch sleep data for a specific date.
        
        Args:
            target_date: The date to fetch sleep data for
            
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
            
            sleep_data = garth.client.get_sleep_data(target_date)
            return sleep_data
        except Exception as e:
            logger.error(f"Failed to fetch sleep data for {target_date}: {e}")
            raise
    
    async def get_sleep_data_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ):
        """
        Fetch sleep data for a date range.
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            
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
                
            sleep_data = garth.client.get_sleep_data(start_date, end_date)
            return sleep_data
        except Exception as e:
            logger.error(f"Failed to fetch sleep data range: {e}")
            raise 