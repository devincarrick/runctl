"""Body Battery data service for Garmin Connect."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from zoneinfo import ZoneInfo

from src.models.garmin.body_battery import BodyBatteryData, BodyBatteryEvent
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class BodyBatteryService(BaseService[BodyBatteryData]):
    """Service for retrieving and parsing Body Battery data."""

    async def get_raw_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get raw Body Battery data from Garmin Connect.

        Args:
            start_date: Start date for Body Battery data.
            end_date: End date for Body Battery data. If None, defaults to start_date + 1 day.

        Returns:
            Raw Body Battery data from Garmin Connect.
        """
        return await self.client.get_body_battery_data(start_date, end_date)

    def parse_raw_data(self, raw_data: Dict[str, Any]) -> BodyBatteryData:
        """Parse raw Body Battery data into BodyBatteryData model.

        Args:
            raw_data: Raw Body Battery data from Garmin Connect.

        Returns:
            Parsed BodyBatteryData instance.

        Raises:
            ValueError: If data is invalid or missing required fields.
        """
        if not raw_data.get("dailyBodyBatteryDTO"):
            raise ValueError("No Body Battery data available")

        battery_data = raw_data["dailyBodyBatteryDTO"]
        battery_values = raw_data.get("bodyBatteryValuesArray", [])

        # Convert battery values to events
        events: List[BodyBatteryEvent] = []
        for value in battery_values:
            try:
                if not isinstance(value, list) or len(value) != 4:
                    continue

                timestamp, battery_level, charged, drained = value
                if battery_level < 0:  # -1 indicates no measurement
                    continue

                event = BodyBatteryEvent(
                    timestamp=datetime.fromtimestamp(
                        timestamp,
                        tz=ZoneInfo(battery_data["timeOffsetBodyBatteryGMT"]),
                    ),
                    value=battery_level,
                    charged_value=charged,
                    drained_value=drained,
                )
                events.append(event)
            except (TypeError, ValueError) as e:
                logger.warning("Failed to parse Body Battery event: %s", e)
                continue

        if not events:
            raise ValueError("No valid Body Battery measurements available")

        # Sort events by timestamp
        events.sort(key=lambda x: x.timestamp)

        # Calculate total charged and drained values
        total_charged = sum(event.charged_value for event in events)
        total_drained = sum(event.drained_value for event in events)

        # Calculate charging and draining times
        charging_time = sum(
            1 for i in range(len(events) - 1)
            if events[i + 1].value > events[i].value
        )
        draining_time = sum(
            1 for i in range(len(events) - 1)
            if events[i + 1].value < events[i].value
        )

        # Get min and max values
        battery_values = [event.value for event in events]
        min_value = min(battery_values)
        max_value = max(battery_values)

        return BodyBatteryData(
            user_id=str(battery_data["userId"]),
            start_time=datetime.fromtimestamp(
                battery_data["startTimeInSeconds"],
                tz=ZoneInfo(battery_data["timeOffsetBodyBatteryGMT"]),
            ),
            end_time=datetime.fromtimestamp(
                battery_data["endTimeInSeconds"],
                tz=ZoneInfo(battery_data["timeOffsetBodyBatteryGMT"]),
            ),
            timezone=battery_data["timeOffsetBodyBatteryGMT"],
            starting_value=events[0].value,
            ending_value=events[-1].value,
            min_value=min_value,
            max_value=max_value,
            total_charged=total_charged,
            total_drained=total_drained,
            charging_time_seconds=charging_time * 60,  # Each measurement is 1 minute
            draining_time_seconds=draining_time * 60,
            measurements=events,
        ) 