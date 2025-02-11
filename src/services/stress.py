"""Stress data service for Garmin Connect."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from zoneinfo import ZoneInfo

from src.models.garmin.stress import StressData, StressLevel
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class StressDataService(BaseService[StressData]):
    """Service for retrieving and parsing stress data."""

    async def get_raw_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get raw stress data from Garmin Connect.

        Args:
            start_date: Start date for stress data.
            end_date: End date for stress data. If None, defaults to start_date + 1 day.

        Returns:
            Raw stress data from Garmin Connect.
        """
        return await self.client.get_stress_data(start_date, end_date)

    def parse_raw_data(self, raw_data: Dict[str, Any]) -> StressData:
        """Parse raw stress data into StressData model.

        Args:
            raw_data: Raw stress data from Garmin Connect.

        Returns:
            Parsed StressData instance.

        Raises:
            ValueError: If data is invalid or missing required fields.
        """
        if not raw_data.get("dailyStressDTO"):
            raise ValueError("No stress data available")

        stress_data = raw_data["dailyStressDTO"]
        stress_values = raw_data.get("stressValuesArray", [])

        # Convert stress values to stress levels
        levels: List[StressLevel] = []
        for value in stress_values:
            try:
                if not isinstance(value, list) or len(value) != 2:
                    continue

                timestamp, stress_level = value
                if stress_level < 0:  # -1 indicates no measurement
                    continue

                level = StressLevel(
                    timestamp=datetime.fromtimestamp(
                        timestamp,
                        tz=ZoneInfo(stress_data["timeOffsetStressGMT"]),
                    ),
                    value=stress_level,
                )
                levels.append(level)
            except (TypeError, ValueError) as e:
                logger.warning("Failed to parse stress level: %s", e)
                continue

        if not levels:
            raise ValueError("No valid stress measurements available")

        # Sort levels by timestamp
        levels.sort(key=lambda x: x.timestamp)

        # Calculate stress level durations
        total_duration = sum(
            1 for level in levels
            if 0 <= level.value <= 100
        )
        rest_duration = sum(
            1 for level in levels
            if 0 <= level.value <= 25
        )
        low_duration = sum(
            1 for level in levels
            if 26 <= level.value <= 50
        )
        medium_duration = sum(
            1 for level in levels
            if 51 <= level.value <= 75
        )
        high_duration = sum(
            1 for level in levels
            if 76 <= level.value <= 100
        )

        # Calculate average and max stress levels
        valid_levels = [level.value for level in levels]
        average_stress = int(sum(valid_levels) / len(valid_levels))
        max_stress = max(valid_levels)

        return StressData(
            user_id=str(stress_data["userId"]),
            start_time=datetime.fromtimestamp(
                stress_data["startTimeInSeconds"],
                tz=ZoneInfo(stress_data["timeOffsetStressGMT"]),
            ),
            end_time=datetime.fromtimestamp(
                stress_data["endTimeInSeconds"],
                tz=ZoneInfo(stress_data["timeOffsetStressGMT"]),
            ),
            timezone=stress_data["timeOffsetStressGMT"],
            average_stress_level=average_stress,
            max_stress_level=max_stress,
            stress_duration_seconds=total_duration * 60,  # Each measurement is 1 minute
            rest_stress_duration_seconds=rest_duration * 60,
            low_stress_duration_seconds=low_duration * 60,
            medium_stress_duration_seconds=medium_duration * 60,
            high_stress_duration_seconds=high_duration * 60,
            stress_levels=levels,
        ) 