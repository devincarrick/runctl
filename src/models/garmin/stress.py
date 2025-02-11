"""Stress data model for Garmin Connect data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from zoneinfo import ZoneInfo


class StressLevel(BaseModel):
    """A single stress level measurement."""

    timestamp: datetime = Field(
        ...,
        description="Time of the stress measurement",
    )
    value: int = Field(
        ...,
        description="Stress level value (0-100, where 0 is low stress and 100 is high stress)",
        ge=0,
        le=100,
    )


class StressData(BaseModel):
    """Stress data from Garmin Connect."""

    user_id: str = Field(..., description="User ID from Garmin Connect")
    start_time: datetime = Field(
        ...,
        description="Start time of the stress measurement period",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the stress measurement period",
    )
    timezone: str = Field(
        ...,
        description="Timezone where stress was recorded",
    )
    average_stress_level: Optional[int] = Field(
        None,
        description="Average stress level for the period (0-100)",
        ge=0,
        le=100,
    )
    max_stress_level: Optional[int] = Field(
        None,
        description="Maximum stress level for the period (0-100)",
        ge=0,
        le=100,
    )
    stress_duration_seconds: int = Field(
        0,
        description="Duration of time where stress was measured",
        ge=0,
    )
    rest_stress_duration_seconds: int = Field(
        0,
        description="Duration of time in rest/low stress (0-25)",
        ge=0,
    )
    low_stress_duration_seconds: int = Field(
        0,
        description="Duration of time in low stress (26-50)",
        ge=0,
    )
    medium_stress_duration_seconds: int = Field(
        0,
        description="Duration of time in medium stress (51-75)",
        ge=0,
    )
    high_stress_duration_seconds: int = Field(
        0,
        description="Duration of time in high stress (76-100)",
        ge=0,
    )
    stress_levels: List[StressLevel] = Field(
        ...,
        description="Detailed stress level measurements",
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

    @field_validator("stress_levels")
    @classmethod
    def validate_stress_levels(cls, v: List[StressLevel], info: ValidationInfo) -> List[StressLevel]:
        """Validate stress levels are within the time period and properly ordered."""
        if not v:
            raise ValueError("stress_levels cannot be empty")

        # Sort measurements by timestamp
        v.sort(key=lambda x: x.timestamp)

        # Verify measurements are within the time period
        if "start_time" in info.data and v[0].timestamp < info.data["start_time"]:
            raise ValueError(
                f"First stress measurement ({v[0].timestamp}) "
                f"is before start_time ({info.data['start_time']})"
            )
        if "end_time" in info.data and v[-1].timestamp > info.data["end_time"]:
            raise ValueError(
                f"Last stress measurement ({v[-1].timestamp}) "
                f"is after end_time ({info.data['end_time']})"
            )

        return v

    @field_validator("stress_duration_seconds")
    @classmethod
    def validate_total_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that total duration matches sum of individual durations."""
        required_fields = [
            "rest_stress_duration_seconds",
            "low_stress_duration_seconds",
            "medium_stress_duration_seconds",
            "high_stress_duration_seconds",
        ]
        if all(key in info.data for key in required_fields):
            total_duration = (
                info.data["rest_stress_duration_seconds"]
                + info.data["low_stress_duration_seconds"]
                + info.data["medium_stress_duration_seconds"]
                + info.data["high_stress_duration_seconds"]
            )
            if v != total_duration:
                raise ValueError(
                    f"stress_duration_seconds ({v}) does not match sum of "
                    f"individual stress durations ({total_duration})"
                )
        return v

    @field_validator("average_stress_level")
    @classmethod
    def validate_average_stress(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate that average stress is within bounds of min/max stress."""
        if v is not None and "stress_levels" in info.data:
            stress_values = [level.value for level in info.data["stress_levels"]]
            if not stress_values:
                return v
            min_stress = min(stress_values)
            max_stress = max(stress_values)
            if not (min_stress <= v <= max_stress):
                raise ValueError(
                    f"average_stress_level ({v}) is outside the range of "
                    f"measured stress levels ({min_stress}-{max_stress})"
                )
        return v

    @field_validator("max_stress_level")
    @classmethod
    def validate_max_stress(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate that max stress matches the highest measured stress level."""
        if v is not None and "stress_levels" in info.data:
            max_measured = max(level.value for level in info.data["stress_levels"])
            if v != max_measured:
                raise ValueError(
                    f"max_stress_level ({v}) does not match "
                    f"highest measured stress level ({max_measured})"
                )
        return v 