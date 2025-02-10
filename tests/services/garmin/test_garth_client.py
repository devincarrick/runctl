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

@pytest.fixture
def mock_stress_data():
    """Mock stress data response from garth."""
    return {
        "startTimeInSeconds": 1707350400,  # 2024-02-07T22:00:00.0
        "endTimeInSeconds": 1707436800,    # 2024-02-08T22:00:00.0
        "averageStressLevel": 35,
        "maxStressLevel": 75,
        "stressDurationSeconds": 86400,
        "restStressDurationSeconds": 28800,
        "activityStressDurationSeconds": 7200,
        "lowStressDurationSeconds": 21600,
        "mediumStressDurationSeconds": 18000,
        "highStressDurationSeconds": 10800,
        "stressLevels": [
            {
                "timestamp": "2024-02-07T22:00:00.0",
                "stressLevel": 35,
                "source": "DEVICE"
            }
        ]
    }

@pytest.fixture
def mock_body_battery_data():
    """Mock Body Battery data response from garth."""
    return {
        "calendarDate": "2024-02-07",
        "charged": 100,
        "drained": 60,
        "highestBattery": 100,
        "lowestBattery": 40,
        "bodyBatteryScores": [
            {
                "timestamp": "2024-02-07T22:00:00.0",
                "bodyBatteryValue": 85,
                "status": "ACTIVE"
            }
        ]
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

@pytest.mark.asyncio
async def test_get_stress_data(mock_settings, mock_stress_data):
    """Test fetching stress data for a single date."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock
        mock_garth.client.get_stress_data.return_value = mock_stress_data
        
        async with GarthClient() as client:
            # Test with datetime
            test_date = datetime(2024, 2, 7)
            result = await client.get_stress_data(test_date)
            
            # Verify the result
            assert result == mock_stress_data
            mock_garth.client.get_stress_data.assert_called_once_with(test_date.date())

@pytest.mark.asyncio
async def test_get_stress_data_range(mock_settings, mock_stress_data):
    """Test fetching stress data for a date range."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to return list of stress data
        mock_garth.client.get_stress_data.return_value = [mock_stress_data, mock_stress_data]
        
        async with GarthClient() as client:
            start_date = datetime(2024, 2, 7)
            end_date = datetime(2024, 2, 8)
            result = await client.get_stress_data_range(start_date, end_date)
            
            # Verify the result
            assert len(result) == 2
            assert all(day == mock_stress_data for day in result)
            mock_garth.client.get_stress_data.assert_called_once_with(
                start_date.date(),
                end_date.date()
            )

@pytest.mark.asyncio
async def test_get_body_battery_data(mock_settings, mock_body_battery_data):
    """Test fetching Body Battery data for a single date."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock
        mock_garth.client.get_body_battery_data.return_value = mock_body_battery_data
        
        async with GarthClient() as client:
            # Test with datetime
            test_date = datetime(2024, 2, 7)
            result = await client.get_body_battery_data(test_date)
            
            # Verify the result
            assert result == mock_body_battery_data
            mock_garth.client.get_body_battery_data.assert_called_once_with(test_date.date())

@pytest.mark.asyncio
async def test_get_body_battery_data_range(mock_settings, mock_body_battery_data):
    """Test fetching Body Battery data for a date range."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to return list of body battery data
        mock_garth.client.get_body_battery_data.return_value = [mock_body_battery_data, mock_body_battery_data]
        
        async with GarthClient() as client:
            start_date = datetime(2024, 2, 7)
            end_date = datetime(2024, 2, 8)
            result = await client.get_body_battery_data_range(start_date, end_date)
            
            # Verify the result
            assert len(result) == 2
            assert all(day == mock_body_battery_data for day in result)
            mock_garth.client.get_body_battery_data.assert_called_once_with(
                start_date.date(),
                end_date.date()
            )

@pytest.mark.asyncio
async def test_authentication_failure(mock_settings):
    """Test handling of authentication failure."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Make login raise an exception
        mock_garth.load.side_effect = FileNotFoundError()
        mock_garth.login.side_effect = Exception("Authentication failed")
        
        with pytest.raises(Exception) as exc_info:
            async with GarthClient() as client:
                pass
        
        assert "Authentication failed" in str(exc_info.value)
        mock_garth.save.assert_not_called()

@pytest.mark.asyncio
async def test_network_error_sleep_data(mock_settings):
    """Test handling of network error when fetching sleep data."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to raise network error
        mock_garth.client.get_sleep_data.side_effect = Exception("Network error")
        
        async with GarthClient() as client:
            with pytest.raises(Exception) as exc_info:
                await client.get_sleep_data(datetime(2024, 2, 7))
            
            assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_network_error_stress_data(mock_settings):
    """Test handling of network error when fetching stress data."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to raise network error
        mock_garth.client.get_stress_data.side_effect = Exception("Network error")
        
        async with GarthClient() as client:
            with pytest.raises(Exception) as exc_info:
                await client.get_stress_data(datetime(2024, 2, 7))
            
            assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_network_error_body_battery_data(mock_settings):
    """Test handling of network error when fetching Body Battery data."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        # Configure mock to raise network error
        mock_garth.client.get_body_battery_data.side_effect = Exception("Network error")
        
        async with GarthClient() as client:
            with pytest.raises(Exception) as exc_info:
                await client.get_body_battery_data(datetime(2024, 2, 7))
            
            assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_invalid_date_handling(mock_settings):
    """Test handling of invalid dates."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        async with GarthClient() as client:
            # Test with future date
            future_date = datetime(2025, 1, 1)
            
            # Test sleep data
            await client.get_sleep_data(future_date)
            mock_garth.client.get_sleep_data.assert_called_once_with(future_date.date())
            
            # Test stress data
            mock_garth.client.get_sleep_data.reset_mock()
            await client.get_stress_data(future_date)
            mock_garth.client.get_stress_data.assert_called_once_with(future_date.date())
            
            # Test body battery data
            mock_garth.client.get_body_battery_data.reset_mock()
            await client.get_body_battery_data(future_date)
            mock_garth.client.get_body_battery_data.assert_called_once_with(future_date.date())

@pytest.mark.asyncio
async def test_date_range_validation(mock_settings):
    """Test validation of date ranges."""
    with patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.garth_client.garth") as mock_garth:
        
        async with GarthClient() as client:
            # Test with end date before start date
            start_date = datetime(2024, 2, 8)
            end_date = datetime(2024, 2, 7)
            
            # The client should still make the call and let garth handle any validation
            await client.get_sleep_data_range(start_date, end_date)
            mock_garth.client.get_sleep_data.assert_called_once_with(
                start_date.date(),
                end_date.date()
            ) 