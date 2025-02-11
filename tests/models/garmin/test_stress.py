"""Tests for the stress data model."""

from datetime import datetime, timedelta
from typing import List

import pytest
from pydantic import ValidationError
from zoneinfo import ZoneInfo

from src.models.garmin.stress import StressData, StressLevel


def create_stress_levels(
    start_time: datetime,
    values: List[int],
    interval_seconds: int = 60,
) -> List[StressLevel]:
    """Helper function to create a list of stress levels."""
    result = []
    current_time = start_time

    for value in values:
        result.append(
            StressLevel(
                timestamp=current_time,
                value=value,
            )
        )
        current_time += timedelta(seconds=interval_seconds)

    return result


def test_valid_stress_data():
    """Test creating a valid stress data instance."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time,
        values=[20, 30, 60, 80],  # rest, low, medium, high
        interval_seconds=3600,
    )

    stress_data = StressData(
        user_id="test_user",
        start_time=start_time,
        end_time=start_time + timedelta(hours=4),
        timezone="America/New_York",
        average_stress_level=47,  # (20 + 30 + 60 + 80) / 4
        max_stress_level=80,
        stress_duration_seconds=14400,  # 4 hours
        rest_stress_duration_seconds=3600,  # 1h in rest
        low_stress_duration_seconds=3600,  # 1h in low
        medium_stress_duration_seconds=3600,  # 1h in medium
        high_stress_duration_seconds=3600,  # 1h in high
        stress_levels=stress_levels,
    )

    assert stress_data.user_id == "test_user"
    assert stress_data.start_time == start_time
    assert stress_data.stress_duration_seconds == 14400
    assert len(stress_data.stress_levels) == 4


def test_invalid_timezone():
    """Test that invalid timezone raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time,
        values=[20],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="Invalid timezone"):
        StressData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            timezone="Invalid/Timezone",
            stress_duration_seconds=3600,
            rest_stress_duration_seconds=3600,
            stress_levels=stress_levels,
        )


def test_invalid_stress_level():
    """Test that invalid stress level value raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))

    with pytest.raises(ValidationError, match="Input should be less than or equal to 100"):
        create_stress_levels(
            start_time=start_time,
            values=[101],  # Invalid stress level
            interval_seconds=3600,
        )


def test_stress_levels_outside_period():
    """Test that stress levels outside the period raise validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time - timedelta(hours=1),  # Start before period
        values=[20, 30],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="First stress measurement .* is before start_time"):
        StressData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            timezone="America/New_York",
            stress_duration_seconds=3600,
            rest_stress_duration_seconds=3600,
            stress_levels=stress_levels,
        )


def test_mismatched_duration():
    """Test that mismatched durations raise validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time,
        values=[20, 30],  # Two rest/low measurements
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="stress_duration_seconds .* does not match sum of"):
        StressData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            stress_duration_seconds=7200,  # 2h total
            rest_stress_duration_seconds=3600,  # 1h rest
            low_stress_duration_seconds=0,  # Should be 3600
            medium_stress_duration_seconds=0,
            high_stress_duration_seconds=0,
            stress_levels=stress_levels,
        )


def test_invalid_average_stress():
    """Test that invalid average stress level raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time,
        values=[20, 30],  # Max stress is 30
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="average_stress_level .* is outside the range"):
        StressData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            average_stress_level=40,  # Higher than max measured stress
            stress_duration_seconds=7200,
            rest_stress_duration_seconds=3600,
            low_stress_duration_seconds=3600,
            stress_levels=stress_levels,
        )


def test_invalid_max_stress():
    """Test that invalid max stress level raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    stress_levels = create_stress_levels(
        start_time=start_time,
        values=[20, 30],  # Max stress is 30
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="max_stress_level .* does not match highest measured"):
        StressData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            max_stress_level=40,  # Higher than max measured stress
            stress_duration_seconds=7200,
            rest_stress_duration_seconds=3600,
            low_stress_duration_seconds=3600,
            stress_levels=stress_levels,
        ) 