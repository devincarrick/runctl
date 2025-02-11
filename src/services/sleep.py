"""Sleep data service for Garmin Connect."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from zoneinfo import ZoneInfo

from src.models.garmin.sleep import SleepData, SleepStage, SleepStageInterval
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class SleepDataService(BaseService[SleepData]):
    """Service for retrieving and parsing sleep data."""

    async def get_raw_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get raw sleep data from Garmin Connect.

        Args:
            start_date: Start date for sleep data.
            end_date: End date for sleep data. If None, defaults to start_date + 1 day.

        Returns:
            Raw sleep data from Garmin Connect.
        """
        return await self.client.get_sleep_data(start_date, end_date)

    def parse_raw_data(self, raw_data: Dict[str, Any]) -> SleepData:
        """Parse raw sleep data into SleepData model.

        Args:
            raw_data: Raw sleep data from Garmin Connect.

        Returns:
            Parsed SleepData instance.

        Raises:
            ValueError: If data is invalid or missing required fields.
        """
        if not raw_data.get("dailySleepDTO"):
            raise ValueError("No sleep data available")

        sleep_data = raw_data["dailySleepDTO"]
        sleep_levels = raw_data.get("sleepLevels", [])

        # Convert sleep levels to stage intervals
        stages: List[SleepStageInterval] = []
        for level in sleep_levels:
            try:
                stage = SleepStageInterval(
                    stage=SleepStage(level["stage"].lower()),
                    start_time=datetime.fromtimestamp(
                        level["startTimeInSeconds"],
                        tz=ZoneInfo(sleep_data["timeOffsetSleepTimeGMT"]),
                    ),
                    end_time=datetime.fromtimestamp(
                        level["endTimeInSeconds"],
                        tz=ZoneInfo(sleep_data["timeOffsetSleepTimeGMT"]),
                    ),
                    duration_seconds=level["endTimeInSeconds"] - level["startTimeInSeconds"],
                )
                stages.append(stage)
            except (KeyError, ValueError) as e:
                logger.warning("Failed to parse sleep stage: %s", e)
                continue

        # Calculate stage durations
        deep_sleep_seconds = sum(
            stage.duration_seconds
            for stage in stages
            if stage.stage == SleepStage.DEEP
        )
        light_sleep_seconds = sum(
            stage.duration_seconds
            for stage in stages
            if stage.stage == SleepStage.LIGHT
        )
        rem_sleep_seconds = sum(
            stage.duration_seconds
            for stage in stages
            if stage.stage == SleepStage.REM
        )
        awake_seconds = sum(
            stage.duration_seconds
            for stage in stages
            if stage.stage == SleepStage.AWAKE
        )

        return SleepData(
            user_id=str(sleep_data["userId"]),
            start_time=datetime.fromtimestamp(
                sleep_data["sleepStartTimeInSeconds"],
                tz=ZoneInfo(sleep_data["timeOffsetSleepTimeGMT"]),
            ),
            end_time=datetime.fromtimestamp(
                sleep_data["sleepEndTimeInSeconds"],
                tz=ZoneInfo(sleep_data["timeOffsetSleepTimeGMT"]),
            ),
            duration_seconds=sleep_data["sleepEndTimeInSeconds"]
            - sleep_data["sleepStartTimeInSeconds"],
            timezone=sleep_data["timeOffsetSleepTimeGMT"],
            quality_score=sleep_data.get("sleepScoreDTO", {}).get("value"),
            deep_sleep_seconds=deep_sleep_seconds,
            light_sleep_seconds=light_sleep_seconds,
            rem_sleep_seconds=rem_sleep_seconds,
            awake_seconds=awake_seconds,
            sleep_stages=stages,
        ) 