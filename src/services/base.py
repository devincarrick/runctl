"""Base service class for data services."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel

from src.clients.garmin import GarthClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseService(ABC, Generic[T]):
    """Base service class for data services."""

    def __init__(self, client: GarthClient):
        """Initialize service.

        Args:
            client: GarthClient instance for API access.
        """
        self.client = client

    @abstractmethod
    async def get_raw_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get raw data from Garmin Connect.

        Args:
            start_date: Start date for data retrieval.
            end_date: End date for data retrieval. If None, defaults to start_date + 1 day.

        Returns:
            Raw data from Garmin Connect.
        """
        pass

    @abstractmethod
    def parse_raw_data(self, raw_data: Dict[str, Any]) -> T:
        """Parse raw data into model instance.

        Args:
            raw_data: Raw data from Garmin Connect.

        Returns:
            Parsed data model instance.
        """
        pass

    async def get_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> T:
        """Get and parse data from Garmin Connect.

        Args:
            start_date: Start date for data retrieval.
            end_date: End date for data retrieval. If None, defaults to start_date + 1 day.

        Returns:
            Parsed data model instance.

        Raises:
            ValueError: If data retrieval or parsing fails.
        """
        try:
            raw_data = await self.get_raw_data(start_date, end_date)
            return self.parse_raw_data(raw_data)
        except Exception as e:
            logger.error("Failed to get data: %s", e)
            raise ValueError(f"Failed to get data: {e}") from e 