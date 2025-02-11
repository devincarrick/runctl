"""Tests for the body battery data model."""

from datetime import datetime, timedelta
from typing import List, Tuple

import pytest
from pydantic import ValidationError
from zoneinfo import ZoneInfo

from src.models.garmin.body_battery import BodyBatteryData, BodyBatteryEvent


def create_body_battery_events(
    start_time: datetime,
    values: List[int],
    charge_drain_pairs: List[Tuple[int, int]],
    interval_seconds: int = 60,
) -> List[BodyBatteryEvent]:
    """Helper function to create a list of body battery events."""
    if len(values) != len(charge_drain_pairs):
        raise ValueError("values and charge_drain_pairs must have the same length")

    result = []
    current_time = start_time

    for value, (charged, drained) in zip(values, charge_drain_pairs):
        result.append(
            BodyBatteryEvent(
                timestamp=current_time,
                value=value,
                charged_value=charged,
                drained_value=drained,
            )
        )
        current_time += timedelta(seconds=interval_seconds)

    return result


def test_valid_body_battery_data():
    """Test creating a valid body battery data instance."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time,
        values=[50, 60, 40, 30],  # Battery levels
        charge_drain_pairs=[
            (10, 0),  # Charged 10
            (0, 20),  # Drained 20
            (0, 10),  # Drained 10
            (5, 0),  # Charged 5
        ],
        interval_seconds=3600,
    )

    body_battery_data = BodyBatteryData(
        user_id="test_user",
        start_time=start_time,
        end_time=start_time + timedelta(hours=4),
        timezone="America/New_York",
        starting_value=50,
        ending_value=30,
        max_value=60,
        min_value=30,
        total_charged=15,  # 10 + 5
        total_drained=30,  # 20 + 10
        charging_time_seconds=7200,  # 2h charging
        draining_time_seconds=7200,  # 2h draining
        measurements=events,
    )

    assert body_battery_data.user_id == "test_user"
    assert body_battery_data.start_time == start_time
    assert body_battery_data.total_charged == 15
    assert body_battery_data.total_drained == 30
    assert len(body_battery_data.measurements) == 4


def test_invalid_timezone():
    """Test that invalid timezone raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time,
        values=[50],
        charge_drain_pairs=[(0, 0)],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="Invalid timezone"):
        BodyBatteryData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            timezone="Invalid/Timezone",
            starting_value=50,
            ending_value=50,
            measurements=events,
        )


def test_invalid_battery_value():
    """Test that invalid battery value raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))

    with pytest.raises(ValidationError, match="Input should be less than or equal to 100"):
        create_body_battery_events(
            start_time=start_time,
            values=[101],  # Invalid battery value
            charge_drain_pairs=[(0, 0)],
            interval_seconds=3600,
        )


def test_measurements_outside_period():
    """Test that measurements outside the period raise validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time - timedelta(hours=1),  # Start before period
        values=[50, 60],
        charge_drain_pairs=[(10, 0), (0, 10)],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="First measurement .* is before start_time"):
        BodyBatteryData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            timezone="America/New_York",
            starting_value=50,
            ending_value=60,
            measurements=events,
        )


def test_mismatched_starting_value():
    """Test that mismatched starting value raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time,
        values=[50, 60],
        charge_drain_pairs=[(10, 0), (0, 10)],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="starting_value .* does not match first measurement"):
        BodyBatteryData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            starting_value=40,  # Should be 50
            ending_value=60,
            measurements=events,
        )


def test_mismatched_total_charged():
    """Test that mismatched total charged value raises validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time,
        values=[50, 60],
        charge_drain_pairs=[(10, 0), (5, 0)],  # Total charged = 15
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="total_charged .* does not match sum of charged values"):
        BodyBatteryData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            starting_value=50,
            ending_value=60,
            total_charged=20,  # Should be 15
            total_drained=0,
            charging_time_seconds=7200,
            measurements=events,
        )


def test_mismatched_time_values():
    """Test that mismatched time values raise validation error."""
    start_time = datetime(2024, 2, 8, 8, 0, tzinfo=ZoneInfo("America/New_York"))
    events = create_body_battery_events(
        start_time=start_time,
        values=[50, 60],
        charge_drain_pairs=[(10, 0), (5, 0)],
        interval_seconds=3600,
    )

    with pytest.raises(ValidationError, match="Sum of charging_time_seconds and draining_time_seconds"):
        BodyBatteryData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            timezone="America/New_York",
            starting_value=50,
            ending_value=60,
            total_charged=15,
            total_drained=0,
            charging_time_seconds=3600,  # Should sum to 7200
            draining_time_seconds=2400,
            measurements=events,
        ) 