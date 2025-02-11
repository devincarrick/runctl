"""Tests for the sleep data service."""

from datetime import datetime, timedelta
from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from zoneinfo import ZoneInfo

from src.models.garmin.sleep import SleepData, SleepStage
from src.services.sleep import SleepDataService


@pytest.fixture
def mock_garth_client() -> AsyncMock:
    """Create a mock GarthClient."""
    client = AsyncMock()
    client.get_sleep_data = AsyncMock()
    return client


@pytest.fixture
def mock_sleep_data() -> Dict:
    """Create mock sleep data response."""
    start_time = int(datetime(2024, 2, 8, 22, 0).timestamp())
    return {
        "dailySleepDTO": {
            "userId": 12345,
            "sleepStartTimeInSeconds": start_time,
            "sleepEndTimeInSeconds": start_time + 28800,  # 8 hours
            "timeOffsetSleepTimeGMT": "America/New_York",
            "sleepScoreDTO": {"value": 85},
        },
        "sleepLevels": [
            {
                "stage": "LIGHT",
                "startTimeInSeconds": start_time,
                "endTimeInSeconds": start_time + 3600,  # 1h light
            },
            {
                "stage": "DEEP",
                "startTimeInSeconds": start_time + 3600,
                "endTimeInSeconds": start_time + 10800,  # 2h deep
            },
            {
                "stage": "REM",
                "startTimeInSeconds": start_time + 10800,
                "endTimeInSeconds": start_time + 14400,  # 1h rem
            },
            {
                "stage": "LIGHT",
                "startTimeInSeconds": start_time + 14400,
                "endTimeInSeconds": start_time + 21600,  # 2h light
            },
            {
                "stage": "AWAKE",
                "startTimeInSeconds": start_time + 21600,
                "endTimeInSeconds": start_time + 28800,  # 2h awake
            },
        ],
    }


@pytest.fixture
def sleep_service(mock_garth_client: AsyncMock) -> SleepDataService:
    """Create a SleepDataService instance."""
    return SleepDataService(client=mock_garth_client)


async def test_get_raw_data(
    sleep_service: SleepDataService,
    mock_garth_client: AsyncMock,
    mock_sleep_data: Dict,
) -> None:
    """Test getting raw sleep data."""
    mock_garth_client.get_sleep_data.return_value = mock_sleep_data
    start_date = datetime(2024, 2, 8)
    end_date = datetime(2024, 2, 9)

    data = await sleep_service.get_raw_data(start_date, end_date)

    assert data == mock_sleep_data
    mock_garth_client.get_sleep_data.assert_called_once_with(start_date, end_date)


def test_parse_raw_data(
    sleep_service: SleepDataService,
    mock_sleep_data: Dict,
) -> None:
    """Test parsing raw sleep data."""
    sleep_data = sleep_service.parse_raw_data(mock_sleep_data)

    assert isinstance(sleep_data, SleepData)
    assert sleep_data.user_id == "12345"
    assert sleep_data.quality_score == 85
    assert sleep_data.timezone == "America/New_York"
    assert len(sleep_data.sleep_stages) == 5

    # Verify stage durations
    assert sleep_data.light_sleep_seconds == 10800  # 3h total
    assert sleep_data.deep_sleep_seconds == 7200  # 2h total
    assert sleep_data.rem_sleep_seconds == 3600  # 1h total
    assert sleep_data.awake_seconds == 7200  # 2h total

    # Verify total duration
    assert sleep_data.duration_seconds == 28800  # 8h total


def test_parse_raw_data_missing_data(sleep_service: SleepDataService) -> None:
    """Test parsing raw data with missing fields."""
    with pytest.raises(ValueError, match="No sleep data available"):
        sleep_service.parse_raw_data({})


def test_parse_raw_data_invalid_stage(
    sleep_service: SleepDataService,
    mock_sleep_data: Dict,
) -> None:
    """Test parsing raw data with invalid sleep stage."""
    # Add an invalid stage
    mock_sleep_data["sleepLevels"].append({
        "stage": "INVALID",
        "startTimeInSeconds": 1234567890,
        "endTimeInSeconds": 1234571490,
    })

    # Should skip invalid stage but process the rest
    sleep_data = sleep_service.parse_raw_data(mock_sleep_data)
    assert len(sleep_data.sleep_stages) == 5  # Original 5 stages, invalid one skipped


async def test_get_data_integration(
    sleep_service: SleepDataService,
    mock_garth_client: AsyncMock,
    mock_sleep_data: Dict,
) -> None:
    """Test complete data retrieval and parsing flow."""
    mock_garth_client.get_sleep_data.return_value = mock_sleep_data
    start_date = datetime(2024, 2, 8)

    sleep_data = await sleep_service.get_data(start_date)

    assert isinstance(sleep_data, SleepData)
    assert sleep_data.user_id == "12345"
    assert sleep_data.quality_score == 85
    mock_garth_client.get_sleep_data.assert_called_once_with(start_date, None)


async def test_get_data_error_handling(
    sleep_service: SleepDataService,
    mock_garth_client: AsyncMock,
) -> None:
    """Test error handling in data retrieval."""
    mock_garth_client.get_sleep_data.side_effect = Exception("API error")
    start_date = datetime(2024, 2, 8)

    with pytest.raises(ValueError, match="Failed to get data: API error"):
        await sleep_service.get_data(start_date) 