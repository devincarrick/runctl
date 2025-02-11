"""Tests for the stress data service."""

from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import AsyncMock

import pytest
from zoneinfo import ZoneInfo

from src.models.garmin.stress import StressData
from src.services.stress import StressDataService


@pytest.fixture
def mock_garth_client() -> AsyncMock:
    """Create a mock GarthClient."""
    client = AsyncMock()
    client.get_stress_data = AsyncMock()
    return client


@pytest.fixture
def mock_stress_data() -> Dict:
    """Create mock stress data response."""
    start_time = int(datetime(2024, 2, 8, 8, 0).timestamp())
    return {
        "dailyStressDTO": {
            "userId": 12345,
            "startTimeInSeconds": start_time,
            "endTimeInSeconds": start_time + 14400,  # 4 hours
            "timeOffsetStressGMT": "America/New_York",
        },
        "stressValuesArray": [
            # Each value is [timestamp, stress_level]
            # First hour: rest stress (0-25)
            *[[start_time + i * 60, 20] for i in range(60)],
            # Second hour: low stress (26-50)
            *[[start_time + 3600 + i * 60, 35] for i in range(60)],
            # Third hour: medium stress (51-75)
            *[[start_time + 7200 + i * 60, 65] for i in range(60)],
            # Fourth hour: high stress (76-100)
            *[[start_time + 10800 + i * 60, 85] for i in range(60)],
        ],
    }


@pytest.fixture
def stress_service(mock_garth_client: AsyncMock) -> StressDataService:
    """Create a StressDataService instance."""
    return StressDataService(client=mock_garth_client)


async def test_get_raw_data(
    stress_service: StressDataService,
    mock_garth_client: AsyncMock,
    mock_stress_data: Dict,
) -> None:
    """Test getting raw stress data."""
    mock_garth_client.get_stress_data.return_value = mock_stress_data
    start_date = datetime(2024, 2, 8)
    end_date = datetime(2024, 2, 9)

    data = await stress_service.get_raw_data(start_date, end_date)

    assert data == mock_stress_data
    mock_garth_client.get_stress_data.assert_called_once_with(start_date, end_date)


def test_parse_raw_data(
    stress_service: StressDataService,
    mock_stress_data: Dict,
) -> None:
    """Test parsing raw stress data."""
    stress_data = stress_service.parse_raw_data(mock_stress_data)

    assert isinstance(stress_data, StressData)
    assert stress_data.user_id == "12345"
    assert stress_data.timezone == "America/New_York"
    assert len(stress_data.stress_levels) == 240  # 4 hours * 60 minutes

    # Verify stress level durations
    assert stress_data.stress_duration_seconds == 14400  # 4h total
    assert stress_data.rest_stress_duration_seconds == 3600  # 1h rest
    assert stress_data.low_stress_duration_seconds == 3600  # 1h low
    assert stress_data.medium_stress_duration_seconds == 3600  # 1h medium
    assert stress_data.high_stress_duration_seconds == 3600  # 1h high

    # Verify average and max stress
    assert stress_data.average_stress_level == 51  # (20 + 35 + 65 + 85) / 4
    assert stress_data.max_stress_level == 85


def test_parse_raw_data_missing_data(stress_service: StressDataService) -> None:
    """Test parsing raw data with missing fields."""
    with pytest.raises(ValueError, match="No stress data available"):
        stress_service.parse_raw_data({})


def test_parse_raw_data_invalid_values(
    stress_service: StressDataService,
    mock_stress_data: Dict,
) -> None:
    """Test parsing raw data with invalid stress values."""
    # Add some invalid values
    mock_stress_data["stressValuesArray"].extend([
        [1234567890],  # Too short
        [1234567890, -1],  # Invalid stress level
        [1234567890, "invalid"],  # Wrong type
        None,  # Invalid entry
    ])

    # Should skip invalid values but process the rest
    stress_data = stress_service.parse_raw_data(mock_stress_data)
    assert len(stress_data.stress_levels) == 240  # Original values only


def test_parse_raw_data_no_valid_measurements(
    stress_service: StressDataService,
    mock_stress_data: Dict,
) -> None:
    """Test parsing raw data with no valid measurements."""
    mock_stress_data["stressValuesArray"] = [
        [1234567890, -1],  # All invalid values
        [1234567890, -1],
    ]

    with pytest.raises(ValueError, match="No valid stress measurements available"):
        stress_service.parse_raw_data(mock_stress_data)


async def test_get_data_integration(
    stress_service: StressDataService,
    mock_garth_client: AsyncMock,
    mock_stress_data: Dict,
) -> None:
    """Test complete data retrieval and parsing flow."""
    mock_garth_client.get_stress_data.return_value = mock_stress_data
    start_date = datetime(2024, 2, 8)

    stress_data = await stress_service.get_data(start_date)

    assert isinstance(stress_data, StressData)
    assert stress_data.user_id == "12345"
    assert len(stress_data.stress_levels) == 240
    mock_garth_client.get_stress_data.assert_called_once_with(start_date, None)


async def test_get_data_error_handling(
    stress_service: StressDataService,
    mock_garth_client: AsyncMock,
) -> None:
    """Test error handling in data retrieval."""
    mock_garth_client.get_stress_data.side_effect = Exception("API error")
    start_date = datetime(2024, 2, 8)

    with pytest.raises(ValueError, match="Failed to get data: API error"):
        await stress_service.get_data(start_date) 