"""Sleep data model for Garmin Connect data."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from zoneinfo import ZoneInfo


class SleepStage(str, Enum):
    """Sleep stage classifications."""

    DEEP = "deep"
    LIGHT = "light"
    REM = "rem"
    AWAKE = "awake"
    UNKNOWN = "unknown"


class SleepStageInterval(BaseModel):
    """A single interval of sleep with its stage classification."""

    stage: SleepStage = Field(
        ...,
        description="The sleep stage classification for this interval",
    )
    start_time: datetime = Field(
        ...,
        description="Start time of the sleep stage interval",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the sleep stage interval",
    )
    duration_seconds: int = Field(
        ...,
        description="Duration of the sleep stage in seconds",
        gt=0,
    )

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Validate that end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that duration matches start and end times."""
        if "start_time" in info.data and "end_time" in info.data:
            expected_duration = int((info.data["end_time"] - info.data["start_time"]).total_seconds())
            if v != expected_duration:
                raise ValueError(
                    f"duration_seconds ({v}) does not match time difference "
                    f"between start and end times ({expected_duration})"
                )
        return v


class SleepData(BaseModel):
    """Sleep data from Garmin Connect."""

    user_id: str = Field(..., description="User ID from Garmin Connect")
    start_time: datetime = Field(
        ...,
        description="Start time of the sleep session",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the sleep session",
    )
    duration_seconds: int = Field(
        ...,
        description="Total duration of sleep in seconds",
        gt=0,
    )
    timezone: str = Field(
        ...,
        description="Timezone where sleep was recorded",
    )
    quality_score: Optional[int] = Field(
        None,
        description="Sleep quality score (0-100)",
        ge=0,
        le=100,
    )
    deep_sleep_seconds: int = Field(
        0,
        description="Time spent in deep sleep",
        ge=0,
    )
    light_sleep_seconds: int = Field(
        0,
        description="Time spent in light sleep",
        ge=0,
    )
    rem_sleep_seconds: int = Field(
        0,
        description="Time spent in REM sleep",
        ge=0,
    )
    awake_seconds: int = Field(
        0,
        description="Time spent awake during sleep session",
        ge=0,
    )
    sleep_stages: List[SleepStageInterval] = Field(
        ...,
        description="Detailed sleep stage intervals",
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate that timezone is valid."""
        try:
            ZoneInfo(v)
            return v
        except KeyError:
            raise ValueError(f"Invalid timezone: {v}")

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Validate that end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that duration matches start and end times."""
        if "start_time" in info.data and "end_time" in info.data:
            expected_duration = int((info.data["end_time"] - info.data["start_time"]).total_seconds())
            if v != expected_duration:
                raise ValueError(
                    f"duration_seconds ({v}) does not match time difference "
                    f"between start and end times ({expected_duration})"
                )
        return v

    @field_validator("sleep_stages")
    @classmethod
    def validate_sleep_stages(cls, v: List[SleepStageInterval], info: ValidationInfo) -> List[SleepStageInterval]:
        """Validate sleep stages cover the entire sleep period with no gaps or overlaps."""
        if not v:
            raise ValueError("sleep_stages cannot be empty")

        # Sort intervals by start time
        v.sort(key=lambda x: x.start_time)

        # Check for gaps and overlaps
        for i in range(len(v) - 1):
            if v[i].end_time != v[i + 1].start_time:
                raise ValueError(
                    f"Gap or overlap detected between sleep stages at index {i}: "
                    f"stage {i} ends at {v[i].end_time}, "
                    f"stage {i + 1} starts at {v[i + 1].start_time}"
                )

        # Verify total duration matches sum of stage durations
        total_stage_duration = sum(stage.duration_seconds for stage in v)
        if "duration_seconds" in info.data and total_stage_duration != info.data["duration_seconds"]:
            raise ValueError(
                f"Sum of sleep stage durations ({total_stage_duration}) "
                f"does not match total duration ({info.data['duration_seconds']})"
            )

        # Verify first and last stages match overall start and end times
        if "start_time" in info.data and v[0].start_time != info.data["start_time"]:
            raise ValueError(
                f"First sleep stage start time ({v[0].start_time}) "
                f"does not match overall start time ({info.data['start_time']})"
            )
        if "end_time" in info.data and v[-1].end_time != info.data["end_time"]:
            raise ValueError(
                f"Last sleep stage end time ({v[-1].end_time}) "
                f"does not match overall end time ({info.data['end_time']})"
            )

        return v

    @field_validator("deep_sleep_seconds", "light_sleep_seconds", "rem_sleep_seconds", "awake_seconds")
    @classmethod
    def validate_stage_durations(cls, v: int, info: ValidationInfo) -> int:
        """Validate that individual stage durations match sleep_stages data."""
        if "sleep_stages" in info.data:
            stage_type = info.field_name.split("_")[0].upper()
            if stage_type == "AWAKE":
                stage_type = "AWAKE"  # Special case since we split on underscore
            expected_duration = sum(
                stage.duration_seconds
                for stage in info.data["sleep_stages"]
                if stage.stage == SleepStage(stage_type)
            )
            if v != expected_duration:
                raise ValueError(
                    f"{info.field_name} ({v}) does not match sum of {stage_type} "
                    f"stage durations ({expected_duration})"
                )
        return v 