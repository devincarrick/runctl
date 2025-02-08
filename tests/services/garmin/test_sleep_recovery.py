"""Tests for Garmin Connect sleep and recovery data retrieval."""
import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, patch

from src.services.garmin.client import GarminConnectClient
from src.services.garmin.models import SleepData, StressData, BodyBatteryData, RecoveryData

@pytest.fixture
def mock_aioresponse():
    """Mock aiohttp responses."""
    from aioresponses import aioresponses
    with aioresponses() as m:
        yield m

@pytest.fixture
def mock_response_context():
    """Mock response context for async operations."""
    with patch('aiohttp.ClientResponse._wait_released', new_callable=AsyncMock) as mock_wait_released:
        yield mock_wait_released

@pytest.fixture
def mock_signin_response():
    """Mock response for SSO signin page."""
    return """
    <html>
        <form>
            <input type="hidden" name="_csrf" value="test-csrf-token"/>
        </form>
    </html>
    """

@pytest.fixture
def mock_ticket_response():
    """Mock response for ticket exchange."""
    return """
    <html>
        <body>Success</body>
    </html>
    """

@pytest.fixture
def mock_oauth_response():
    """Mock response for OAuth token."""
    return {
        "access_token": "test-access-token",
        "token_type": "Bearer",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
        "scope": "read write"
    }

@pytest.fixture
def mock_sleep_response():
    """Mock response for sleep data."""
    return {
        "calendarDate": "2024-02-07",
        "totalSleepSeconds": 28800,
        "sleepStartTimeLocal": "2024-02-07T00:00:00",
        "sleepEndTimeLocal": "2024-02-07T08:00:00",
        "deepSleepSeconds": 7200,
        "lightSleepSeconds": 14400,
        "remSleepSeconds": 5400,
        "awakeSeconds": 1800,
        "validationType": "DEVICE",
        "averageSpO2Value": 97.0,
        "averageStressDuringSleep": 25.0,
        "overallSleepScore": 85,
        "sleepLevels": [
            {
                "startTimeInSeconds": 0,
                "endTimeInSeconds": 7200,
                "activityLevel": "deep"
            },
            {
                "startTimeInSeconds": 7200,
                "endTimeInSeconds": 21600,
                "activityLevel": "light"
            },
            {
                "startTimeInSeconds": 21600,
                "endTimeInSeconds": 27000,
                "activityLevel": "rem"
            },
            {
                "startTimeInSeconds": 27000,
                "endTimeInSeconds": 28800,
                "activityLevel": "awake"
            }
        ]
    }

@pytest.fixture
def mock_stress_response():
    """Mock response for stress data."""
    return {
        "startTimeLocal": "2024-02-07T00:00:00",
        "endTimeLocal": "2024-02-07T23:59:59",
        "averageStressLevel": 35,
        "maxStressLevel": 75,
        "stressDurationSeconds": 86400,
        "restStressDurationSeconds": 21600,
        "activityStressDurationSeconds": 7200,
        "lowStressDurationSeconds": 28800,
        "mediumStressDurationSeconds": 14400,
        "highStressDurationSeconds": 7200,
        "stressLevels": [
            {
                "timestamp": "2024-02-07T00:00:00",
                "stressLevel": 25,
                "source": "DEVICE"
            },
            {
                "timestamp": "2024-02-07T12:00:00",
                "stressLevel": 45,
                "source": "DEVICE"
            }
        ]
    }

@pytest.fixture
def mock_body_battery_response():
    """Mock response for Body Battery data."""
    return {
        "calendarDate": "2024-02-07",
        "chargedValue": 70,
        "drainedValue": 30,
        "mostChargedValue": 100,
        "leastChargedValue": 20,
        "bodyBatteryScores": [
            {
                "timestamp": "2024-02-07T00:00:00",
                "bodyBatteryValue": 85,
                "status": "CHARGED"
            },
            {
                "timestamp": "2024-02-07T12:00:00",
                "bodyBatteryValue": 65,
                "status": "ACTIVE"
            }
        ]
    }

@pytest.mark.asyncio
async def test_get_sleep_data(mock_response_context, mock_aioresponse, mock_sleep_response, mock_signin_response, mock_ticket_response, mock_oauth_response):
    """Test fetching sleep data for a specific date."""
    date = datetime(2024, 2, 7)
    endpoint = f"wellness-api/wellness/dailySleepData/2024-02-07"

    # Mock SSO signin page
    mock_aioresponse.get(
        "https://sso.garmin.com/sso/signin",
        status=200,
        body=mock_signin_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock login response with ticket URL
    mock_aioresponse.post(
        "https://sso.garmin.com/sso/signin",
        status=302,
        headers={
            "Location": "https://connect.garmin.com/modern?ticket=test-ticket",
            "Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"
        }
    )

    # Mock ticket exchange
    mock_aioresponse.get(
        "https://connect.garmin.com/modern?ticket=test-ticket",
        status=200,
        body=mock_ticket_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock OAuth token request
    mock_aioresponse.post(
        "https://connect.garmin.com/oauth-token",
        status=200,
        body=json.dumps(mock_oauth_response),
        content_type="application/json"
    )

    # Mock sleep data request
    mock_aioresponse.get(
        f"https://connect.garmin.com/modern/{endpoint}",
        status=200,
        body=json.dumps(mock_sleep_response),
        content_type="application/json"
    )

    async with GarminConnectClient() as client:
        sleep_data = await client.get_sleep_data(date)
        assert isinstance(sleep_data, SleepData)
        assert sleep_data.duration_in_seconds == 28800
        assert sleep_data.deep_sleep_seconds == 7200
        assert sleep_data.light_sleep_seconds == 14400
        assert sleep_data.rem_sleep_seconds == 5400
        assert sleep_data.awake_seconds == 1800
        assert len(sleep_data.sleep_levels) == 4

@pytest.mark.asyncio
async def test_get_sleep_data_range(mock_response_context, mock_aioresponse, mock_sleep_response, mock_signin_response, mock_ticket_response, mock_oauth_response):
    """Test fetching sleep data for a date range."""
    start_date = datetime(2024, 2, 7)
    end_date = datetime(2024, 2, 8)

    # Mock SSO signin page
    mock_aioresponse.get(
        "https://sso.garmin.com/sso/signin",
        status=200,
        body=mock_signin_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock login response with ticket URL
    mock_aioresponse.post(
        "https://sso.garmin.com/sso/signin",
        status=302,
        headers={
            "Location": "https://connect.garmin.com/modern?ticket=test-ticket",
            "Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"
        }
    )

    # Mock ticket exchange
    mock_aioresponse.get(
        "https://connect.garmin.com/modern?ticket=test-ticket",
        status=200,
        body=mock_ticket_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock OAuth token request
    mock_aioresponse.post(
        "https://connect.garmin.com/oauth-token",
        status=200,
        body=json.dumps(mock_oauth_response),
        content_type="application/json"
    )

    for date in (start_date, end_date):
        endpoint = f"wellness-api/wellness/dailySleepData/{date.strftime('%Y-%m-%d')}"
        mock_aioresponse.get(
            f"https://connect.garmin.com/modern/{endpoint}",
            status=200,
            body=json.dumps(mock_sleep_response),
            content_type="application/json"
        )

    async with GarminConnectClient() as client:
        sleep_data_list = await client.get_sleep_data_range(start_date, end_date)
        assert len(sleep_data_list) == 2
        for sleep_data in sleep_data_list:
            assert isinstance(sleep_data, SleepData)
            assert sleep_data.duration_in_seconds == 28800
            assert sleep_data.deep_sleep_seconds == 7200
            assert sleep_data.light_sleep_seconds == 14400
            assert sleep_data.rem_sleep_seconds == 5400
            assert sleep_data.awake_seconds == 1800
            assert len(sleep_data.sleep_levels) == 4

@pytest.mark.asyncio
async def test_get_stress_data(mock_response_context, mock_aioresponse, mock_stress_response, mock_signin_response, mock_ticket_response, mock_oauth_response):
    """Test fetching stress data for a specific date."""
    date = datetime(2024, 2, 7)
    endpoint = f"wellness-api/wellness/dailyStress/2024-02-07"

    # Mock SSO signin page
    mock_aioresponse.get(
        "https://sso.garmin.com/sso/signin",
        status=200,
        body=mock_signin_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock login response with ticket URL
    mock_aioresponse.post(
        "https://sso.garmin.com/sso/signin",
        status=302,
        headers={
            "Location": "https://connect.garmin.com/modern?ticket=test-ticket",
            "Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"
        }
    )

    # Mock ticket exchange
    mock_aioresponse.get(
        "https://connect.garmin.com/modern?ticket=test-ticket",
        status=200,
        body=mock_ticket_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock OAuth token request
    mock_aioresponse.post(
        "https://connect.garmin.com/oauth-token",
        status=200,
        body=json.dumps(mock_oauth_response),
        content_type="application/json"
    )

    # Mock stress data request
    mock_aioresponse.get(
        f"https://connect.garmin.com/modern/{endpoint}",
        status=200,
        body=json.dumps(mock_stress_response),
        content_type="application/json"
    )

    async with GarminConnectClient() as client:
        stress_data = await client.get_stress_data(date)
        assert isinstance(stress_data, StressData)
        assert stress_data.average_stress_level == 35
        assert stress_data.max_stress_level == 75
        assert stress_data.activity_stress_duration_seconds == 7200
        assert stress_data.rest_stress_duration_seconds == 21600
        assert len(stress_data.stress_levels) == 2

@pytest.mark.asyncio
async def test_get_body_battery_data(mock_response_context, mock_aioresponse, mock_body_battery_response, mock_signin_response, mock_ticket_response, mock_oauth_response):
    """Test fetching Body Battery data for a specific date."""
    date = datetime(2024, 2, 7)
    endpoint = f"wellness-api/wellness/dailyBodyBattery/2024-02-07"

    # Mock SSO signin page
    mock_aioresponse.get(
        "https://sso.garmin.com/sso/signin",
        status=200,
        body=mock_signin_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock login response with ticket URL
    mock_aioresponse.post(
        "https://sso.garmin.com/sso/signin",
        status=302,
        headers={
            "Location": "https://connect.garmin.com/modern?ticket=test-ticket",
            "Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"
        }
    )

    # Mock ticket exchange
    mock_aioresponse.get(
        "https://connect.garmin.com/modern?ticket=test-ticket",
        status=200,
        body=mock_ticket_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock OAuth token request
    mock_aioresponse.post(
        "https://connect.garmin.com/oauth-token",
        status=200,
        body=json.dumps(mock_oauth_response),
        content_type="application/json"
    )

    # Mock body battery data request
    mock_aioresponse.get(
        f"https://connect.garmin.com/modern/{endpoint}",
        status=200,
        body=json.dumps(mock_body_battery_response),
        content_type="application/json"
    )

    async with GarminConnectClient() as client:
        body_battery_data = await client.get_body_battery_data(date)
        assert isinstance(body_battery_data, BodyBatteryData)
        assert body_battery_data.charged_value == 70
        assert body_battery_data.drained_value == 30
        assert body_battery_data.most_charged_value == 100
        assert body_battery_data.least_charged_value == 20
        assert len(body_battery_data.body_battery_scores) == 2

@pytest.mark.asyncio
async def test_get_recovery_data(mock_response_context, mock_aioresponse, mock_stress_response, mock_body_battery_response, mock_signin_response, mock_ticket_response, mock_oauth_response):
    """Test fetching combined recovery data for a specific date."""
    date = datetime(2024, 2, 7)

    # Mock both endpoints
    stress_endpoint = f"wellness-api/wellness/dailyStress/2024-02-07"
    body_battery_endpoint = f"wellness-api/wellness/dailyBodyBattery/2024-02-07"

    # Mock SSO signin page
    mock_aioresponse.get(
        "https://sso.garmin.com/sso/signin",
        status=200,
        body=mock_signin_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock login response with ticket URL
    mock_aioresponse.post(
        "https://sso.garmin.com/sso/signin",
        status=302,
        headers={
            "Location": "https://connect.garmin.com/modern?ticket=test-ticket",
            "Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"
        }
    )

    # Mock ticket exchange
    mock_aioresponse.get(
        "https://connect.garmin.com/modern?ticket=test-ticket",
        status=200,
        body=mock_ticket_response,
        content_type="text/html; charset=utf-8",
        headers={"Set-Cookie": "GARMIN-SSO-GUID=test-sso-guid"}
    )

    # Mock OAuth token request
    mock_aioresponse.post(
        "https://connect.garmin.com/oauth-token",
        status=200,
        body=json.dumps(mock_oauth_response),
        content_type="application/json"
    )

    # Mock stress data request
    mock_aioresponse.get(
        f"https://connect.garmin.com/modern/{stress_endpoint}",
        status=200,
        body=json.dumps(mock_stress_response),
        content_type="application/json"
    )

    # Mock body battery data request
    mock_aioresponse.get(
        f"https://connect.garmin.com/modern/{body_battery_endpoint}",
        status=200,
        body=json.dumps(mock_body_battery_response),
        content_type="application/json"
    )

    async with GarminConnectClient() as client:
        recovery_data = await client.get_recovery_data(date)
        assert isinstance(recovery_data, RecoveryData)
        assert recovery_data.stress_data.average_stress_level == 35
        assert recovery_data.stress_data.max_stress_level == 75
        assert recovery_data.body_battery_data.charged_value == 70
        assert recovery_data.body_battery_data.drained_value == 30