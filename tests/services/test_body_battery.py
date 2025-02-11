"""Tests for the body battery data service."""

from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import AsyncMock

import pytest
from zoneinfo import ZoneInfo

from src.models.garmin.body_battery import BodyBatteryData
from src.services.body_battery import BodyBatteryService


@pytest.fixture
def mock_garth_client() -> AsyncMock:
    """Create a mock GarthClient."""
    client = AsyncMock()
    client.get_body_battery_data = AsyncMock()
    return client


@pytest.fixture
def mock_body_battery_data() -> Dict:
    """Create mock body battery data response."""
    start_time = int(datetime(2024, 2, 8, 8, 0).timestamp())

    def generate_values(
        start_value: int,
        end_value: int,
        base_time: int,
        charge: bool = True,
    ) -> List[List[int]]:
        """Generate values for a period.

        Args:
            start_value: Starting battery level
            end_value: Ending battery level
            base_time: Base timestamp
            charge: Whether this is a charging period
        """
        values = []
        total_change = end_value - start_value
        step = total_change / 59  # Use 59 to ensure last value is exact

        for i in range(60):
            if i == 59:
                current_value = end_value  # Ensure exact end value
            else:
                # Always increase/decrease by a small amount
                current_value = round(start_value + step * i)

            values.append([
                base_time + i * 60,  # timestamp
                current_value,  # battery level
                i if charge else 0,  # charged value
                0 if charge else i,  # drained value
            ])
        return values

    return {
        "dailyBodyBatteryDTO": {
            "userId": 12345,
            "startTimeInSeconds": start_time,
            "endTimeInSeconds": start_time + 14400,  # 4 hours
            "timeOffsetBodyBatteryGMT": "America/New_York",
        },
        "bodyBatteryValuesArray": [
            # First hour: charging from 50 to 80
            *generate_values(50, 80, start_time, charge=True),
            # Second hour: draining from 80 to 50
            *generate_values(80, 50, start_time + 3600, charge=False),
            # Third hour: charging from 50 to 80
            *generate_values(50, 80, start_time + 7200, charge=True),
            # Fourth hour: draining from 80 to 50
            *generate_values(80, 50, start_time + 10800, charge=False),
        ],
    }


@pytest.fixture
def body_battery_service(mock_garth_client: AsyncMock) -> BodyBatteryService:
    """Create a BodyBatteryService instance."""
    return BodyBatteryService(client=mock_garth_client)


@pytest.mark.asyncio
async def test_get_raw_data(
    body_battery_service: BodyBatteryService,
    mock_garth_client: AsyncMock,
    mock_body_battery_data: Dict,
) -> None:
    """Test getting raw body battery data."""
    mock_garth_client.get_body_battery_data.return_value = mock_body_battery_data
    start_date = datetime(2024, 2, 8)
    end_date = datetime(2024, 2, 9)

    data = await body_battery_service.get_raw_data(start_date, end_date)

    assert data == mock_body_battery_data
    mock_garth_client.get_body_battery_data.assert_called_once_with(start_date, end_date)


def test_parse_raw_data(
    body_battery_service: BodyBatteryService,
    mock_body_battery_data: Dict,
) -> None:
    """Test parsing raw body battery data."""
    body_battery_data = body_battery_service.parse_raw_data(mock_body_battery_data)

    assert isinstance(body_battery_data, BodyBatteryData)
    assert body_battery_data.user_id == "12345"
    assert body_battery_data.timezone == "America/New_York"
    assert len(body_battery_data.measurements) == 240  # 4 hours * 60 minutes

    # Verify starting and ending values
    assert body_battery_data.starting_value == 50  # First measurement
    assert body_battery_data.ending_value == 50  # Last measurement

    # Verify min and max values
    assert body_battery_data.min_value == 50  # Lowest value
    assert body_battery_data.max_value == 80  # Highest value

    # Verify charged and drained values
    assert body_battery_data.total_charged == sum(range(60)) * 2  # Two charging periods
    assert body_battery_data.total_drained == sum(range(60)) * 2  # Two draining periods

    # Verify charging and draining times
    # Note: The service calculates charging time based on consecutive measurements
    # where the value increases, and draining time based on consecutive measurements
    # where the value decreases. Since our mock data has some flat periods
    # (where the value stays the same), the actual charging/draining times
    # will be less than the total period duration.
    assert body_battery_data.charging_time_seconds == 3600  # ~1 hour charging
    assert body_battery_data.draining_time_seconds == 3600  # ~1 hour draining


def test_parse_raw_data_missing_data(body_battery_service: BodyBatteryService) -> None:
    """Test parsing raw data with missing fields."""
    with pytest.raises(ValueError, match="No Body Battery data available"):
        body_battery_service.parse_raw_data({})


def test_parse_raw_data_invalid_values(
    body_battery_service: BodyBatteryService,
    mock_body_battery_data: Dict,
) -> None:
    """Test parsing raw data with invalid body battery values."""
    # Add some invalid values
    mock_body_battery_data["bodyBatteryValuesArray"].extend([
        [1234567890],  # Too short
        [1234567890, -1, 0, 0],  # Invalid battery level
        [1234567890, "invalid", 0, 0],  # Wrong type
        None,  # Invalid entry
    ])

    # Should skip invalid values but process the rest
    body_battery_data = body_battery_service.parse_raw_data(mock_body_battery_data)
    assert len(body_battery_data.measurements) == 240  # Original values only


def test_parse_raw_data_no_valid_measurements(
    body_battery_service: BodyBatteryService,
    mock_body_battery_data: Dict,
) -> None:
    """Test parsing raw data with no valid measurements."""
    mock_body_battery_data["bodyBatteryValuesArray"] = [
        [1234567890, -1, 0, 0],  # All invalid values
        [1234567890, -1, 0, 0],
    ]

    with pytest.raises(ValueError, match="No valid Body Battery measurements available"):
        body_battery_service.parse_raw_data(mock_body_battery_data)


@pytest.mark.asyncio
async def test_get_data_integration(
    body_battery_service: BodyBatteryService,
    mock_garth_client: AsyncMock,
    mock_body_battery_data: Dict,
) -> None:
    """Test complete data retrieval and parsing flow."""
    mock_garth_client.get_body_battery_data.return_value = mock_body_battery_data
    start_date = datetime(2024, 2, 8)

    body_battery_data = await body_battery_service.get_data(start_date)

    assert isinstance(body_battery_data, BodyBatteryData)
    assert body_battery_data.user_id == "12345"
    assert len(body_battery_data.measurements) == 240
    mock_garth_client.get_body_battery_data.assert_called_once_with(start_date, None)


@pytest.mark.asyncio
async def test_get_data_error_handling(
    body_battery_service: BodyBatteryService,
    mock_garth_client: AsyncMock,
) -> None:
    """Test error handling in data retrieval."""
    mock_garth_client.get_body_battery_data.side_effect = Exception("API error")
    start_date = datetime(2024, 2, 8)

    with pytest.raises(ValueError, match="Failed to get data: API error"):
        await body_battery_service.get_data(start_date) 