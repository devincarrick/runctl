"""Tests for the Garth-based Garmin Connect client."""
import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock

from src.services.garmin.garth_client import GarthClient
from src.services.garmin.config import GarminConnectSettings

@pytest.fixture
def mock_settings():
    """Mock Garmin Connect settings."""
    return GarminConnectSettings(
        email="test@example.com",
        password="test_password",
        api_base_url="https://api.garmin.com"
    )

@pytest.fixture
def mock_sleep_data():
    """Mock sleep data response from garth."""
    return {
        "sleepStartTimestamp": "2024-02-07T22:00:00.0",
        "sleepEndTimestamp": "2024-02-08T06:00:00.0",
        "deepSleepSeconds": 7200,
        "lightSleepSeconds": 14400,
        "remSleepSeconds": 5400,
        "awakeSleepSeconds": 1800,
        "deviceRemCapable": True,
        "calendarDate": "2024-02-07",
        "sleepScores": {
            "overall": {"value": 85},
            "deepSleep": {"value": 90},
            "remSleep": {"value": 85},
            "lightSleep": {"value": 80}
        }
    }

@pytest.mark.asyncio
async def test_garth_client_initialization(mock_settings):
    """Test GarthClient initialization and authentication."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        async with GarthClient() as client:
            # Check that garth was configured
            mock_garth.configure.assert_called_once_with(domain="garmin.com")
            
            # Check that we tried to load existing tokens
            mock_garth.load.assert_called_once()

@pytest.mark.asyncio
async def test_get_sleep_data(mock_settings, mock_sleep_data):
    """Test fetching sleep data for a single date."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock
        mock_garth.client.get_sleep_data.return_value = mock_sleep_data
        
        async with GarthClient() as client:
            # Test with datetime
            test_date = datetime(2024, 2, 7)
            result = await client.get_sleep_data(test_date)
            
            # Verify the result
            assert result == mock_sleep_data
            mock_garth.client.get_sleep_data.assert_called_once_with(test_date.date())

@pytest.mark.asyncio
async def test_get_sleep_data_range(mock_settings, mock_sleep_data):
    """Test fetching sleep data for a date range."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to return list of sleep data
        mock_garth.client.get_sleep_data.return_value = [mock_sleep_data, mock_sleep_data]
        
        async with GarthClient() as client:
            start_date = datetime(2024, 2, 7)
            end_date = datetime(2024, 2, 8)
            result = await client.get_sleep_data_range(start_date, end_date)
            
            # Verify the result
            assert len(result) == 2
            assert all(day == mock_sleep_data for day in result)
            mock_garth.client.get_sleep_data.assert_called_once_with(
                start_date.date(),
                end_date.date()
            )

@pytest.mark.asyncio
async def test_authentication_flow(mock_settings):
    """Test authentication flow when no saved tokens exist."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Make load() raise FileNotFoundError to trigger authentication
        mock_garth.load.side_effect = FileNotFoundError()
        
        async with GarthClient() as client:
            # Verify authentication flow
            mock_garth.configure.assert_called_once()
            mock_garth.load.assert_called_once()
            mock_garth.login.assert_called_once_with(
                mock_settings.email,
                mock_settings.password
            )
            mock_garth.save.assert_called_once() 