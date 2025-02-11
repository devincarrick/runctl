"""Interface definitions for Garmin Connect client."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, Optional


class GarminClientInterface(ABC):
    """Interface for Garmin Connect client."""

    @abstractmethod
    async def check_auth(self) -> None:
        """Check authentication status.
        
        Raises:
            ValueError: If authentication fails.
        """
        pass

    @abstractmethod
    async def get_sleep_data(
        self,
        target_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get sleep data from Garmin Connect.

        Args:
            target_date: Target date for sleep data.
            end_date: Optional end date for sleep data range.

        Returns:
            Sleep data from Garmin Connect.

        Raises:
            ValueError: If data retrieval fails.
        """
        pass

    @abstractmethod
    async def get_stress_data(
        self,
        target_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get stress data from Garmin Connect.

        Args:
            target_date: Target date for stress data.
            end_date: Optional end date for stress data range.

        Returns:
            Stress data from Garmin Connect.

        Raises:
            ValueError: If data retrieval fails.
        """
        pass

    @abstractmethod
    async def get_body_battery_data(
        self,
        target_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get Body Battery data from Garmin Connect.

        Args:
            target_date: Target date for Body Battery data.
            end_date: Optional end date for Body Battery data range.

        Returns:
            Body Battery data from Garmin Connect.

        Raises:
            ValueError: If data retrieval fails.
        """
        pass 