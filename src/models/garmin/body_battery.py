"""Body Battery data model for Garmin Connect data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from zoneinfo import ZoneInfo


class BodyBatteryEvent(BaseModel):
    """A single Body Battery measurement event."""

    timestamp: datetime = Field(
        ...,
        description="Time of the Body Battery measurement",
    )
    value: int = Field(
        ...,
        description="Body Battery value (0-100, where 0 is depleted and 100 is fully charged)",
        ge=0,
        le=100,
    )
    charged_value: int = Field(
        ...,
        description="Amount of battery charged since last measurement",
        ge=0,
    )
    drained_value: int = Field(
        ...,
        description="Amount of battery drained since last measurement",
        ge=0,
    )


class BodyBatteryData(BaseModel):
    """Body Battery data from Garmin Connect."""

    user_id: str = Field(..., description="User ID from Garmin Connect")
    start_time: datetime = Field(
        ...,
        description="Start time of the Body Battery measurement period",
    )
    end_time: datetime = Field(
        ...,
        description="End time of the Body Battery measurement period",
    )
    timezone: str = Field(
        ...,
        description="Timezone where Body Battery was recorded",
    )
    starting_value: int = Field(
        ...,
        description="Body Battery value at start of period (0-100)",
        ge=0,
        le=100,
    )
    ending_value: int = Field(
        ...,
        description="Body Battery value at end of period (0-100)",
        ge=0,
        le=100,
    )
    max_value: Optional[int] = Field(
        None,
        description="Maximum Body Battery value during period (0-100)",
        ge=0,
        le=100,
    )
    min_value: Optional[int] = Field(
        None,
        description="Minimum Body Battery value during period (0-100)",
        ge=0,
        le=100,
    )
    total_charged: int = Field(
        0,
        description="Total amount of Body Battery charged during period",
        ge=0,
    )
    total_drained: int = Field(
        0,
        description="Total amount of Body Battery drained during period",
        ge=0,
    )
    charging_time_seconds: int = Field(
        0,
        description="Total time spent charging Body Battery",
        ge=0,
    )
    draining_time_seconds: int = Field(
        0,
        description="Total time spent draining Body Battery",
        ge=0,
    )
    measurements: List[BodyBatteryEvent] = Field(
        ...,
        description="Detailed Body Battery measurements",
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

    @field_validator("measurements")
    @classmethod
    def validate_measurements(cls, v: List[BodyBatteryEvent], info: ValidationInfo) -> List[BodyBatteryEvent]:
        """Validate measurements are within the time period and properly ordered."""
        if not v:
            raise ValueError("measurements cannot be empty")

        # Sort measurements by timestamp
        v.sort(key=lambda x: x.timestamp)

        # Verify measurements are within the time period
        if "start_time" in info.data and v[0].timestamp < info.data["start_time"]:
            raise ValueError(
                f"First measurement ({v[0].timestamp}) "
                f"is before start_time ({info.data['start_time']})"
            )
        if "end_time" in info.data and v[-1].timestamp > info.data["end_time"]:
            raise ValueError(
                f"Last measurement ({v[-1].timestamp}) "
                f"is after end_time ({info.data['end_time']})"
            )

        # Verify starting and ending values match measurements
        if "starting_value" in info.data and v[0].value != info.data["starting_value"]:
            raise ValueError(
                f"starting_value ({info.data['starting_value']}) does not match "
                f"first measurement value ({v[0].value})"
            )
        if "ending_value" in info.data and v[-1].value != info.data["ending_value"]:
            raise ValueError(
                f"ending_value ({info.data['ending_value']}) does not match "
                f"last measurement value ({v[-1].value})"
            )

        return v

    @field_validator("max_value", "min_value")
    @classmethod
    def validate_min_max_values(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate that min/max values match measurements."""
        if v is not None and "measurements" in info.data:
            measured_values = [event.value for event in info.data["measurements"]]
            if info.field_name == "max_value":
                expected = max(measured_values)
            else:  # min_value
                expected = min(measured_values)
            if v != expected:
                raise ValueError(
                    f"{info.field_name} ({v}) does not match "
                    f"{'maximum' if info.field_name == 'max_value' else 'minimum'} "
                    f"measured value ({expected})"
                )
        return v

    @field_validator("total_charged", "total_drained")
    @classmethod
    def validate_total_values(cls, v: int, info: ValidationInfo) -> int:
        """Validate that total charged/drained values match measurements."""
        if "measurements" in info.data:
            if info.field_name == "total_charged":
                expected = sum(event.charged_value for event in info.data["measurements"])
            else:  # total_drained
                expected = sum(event.drained_value for event in info.data["measurements"])
            if v != expected:
                raise ValueError(
                    f"{info.field_name} ({v}) does not match sum of "
                    f"{'charged' if info.field_name == 'total_charged' else 'drained'} "
                    f"values ({expected})"
                )
        return v

    @field_validator("charging_time_seconds", "draining_time_seconds")
    @classmethod
    def validate_time_values(cls, v: int, info: ValidationInfo) -> int:
        """Validate that charging and draining times sum to total duration."""
        required_fields = ["charging_time_seconds", "draining_time_seconds", "start_time", "end_time"]
        if all(key in info.data for key in required_fields):
            total_duration = int((info.data["end_time"] - info.data["start_time"]).total_seconds())
            total_time = info.data["charging_time_seconds"] + info.data["draining_time_seconds"]
            if total_time != total_duration:
                raise ValueError(
                    f"Sum of charging_time_seconds and draining_time_seconds ({total_time}) "
                    f"does not match total duration ({total_duration})"
                )
        return v 