"""Integration tests for Garmin Connect API client."""
import json
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from aiohttp import web
from unittest.mock import call

from src.services.garmin.garth_client import GarthClient
from src.services.garmin.config import GarminConnectSettings
from src.services.garmin.retry import RetryError, RateLimitError
from src.services.garmin.cache import Cache

# Mock response data
MOCK_SLEEP_DATA = {
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

MOCK_STRESS_DATA = {
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

MOCK_BODY_BATTERY_DATA = {
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

class MockGarminServer:
    """Mock server for Garmin Connect API."""
    
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        self.site = None
        self.url = None
    
    def setup_routes(self):
        """Set up the API routes."""
        self.app.router.add_get('/sleep', self.handle_sleep)
        self.app.router.add_get('/stress', self.handle_stress)
        self.app.router.add_get('/body-battery', self.handle_body_battery)
        self.app.router.add_post('/auth/login', self.handle_login)
        self.app.router.add_post('/auth/token', self.handle_token)
    
    async def start(self):
        """Start the mock server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', 0)
        await self.site.start()
        self.url = f"http://localhost:{self.site._server.sockets[0].getsockname()[1]}"
    
    async def stop(self):
        """Stop the mock server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
    
    async def handle_sleep(self, request):
        """Handle sleep data requests."""
        return web.json_response(MOCK_SLEEP_DATA)
    
    async def handle_stress(self, request):
        """Handle stress data requests."""
        return web.json_response(MOCK_STRESS_DATA)
    
    async def handle_body_battery(self, request):
        """Handle Body Battery data requests."""
        return web.json_response(MOCK_BODY_BATTERY_DATA)
    
    async def handle_login(self, request):
        """Handle login requests."""
        return web.json_response({
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600
        })
    
    async def handle_token(self, request):
        """Handle token refresh requests."""
        return web.json_response({
            "access_token": "mock_refreshed_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600
        })

@pytest_asyncio.fixture
async def mock_server():
    """Fixture to create and manage the mock server."""
    server = MockGarminServer()
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest_asyncio.fixture
async def mock_settings(mock_server):
    """Mock settings using the mock server URL."""
    return GarminConnectSettings(
        email="test@example.com",
        password="test_password",
        api_base_url=mock_server.url
    )

@pytest_asyncio.fixture
async def mock_cache():
    """Mock cache for testing."""
    cache = AsyncMock(spec=Cache)
    cache.get.return_value = None
    cache.set.return_value = True
    return cache

@pytest_asyncio.fixture
async def mock_garth_client():
    """Mock garth.Client instance."""
    client = AsyncMock()
    client.configure = MagicMock()
    client.load = MagicMock()
    client.login = AsyncMock()
    client.save = MagicMock()
    
    # Configure mock methods to return data
    client.get_sleep_data = AsyncMock()
    client.get_sleep_data.return_value = MOCK_SLEEP_DATA
    
    client.get_stress_data = AsyncMock()
    client.get_stress_data.return_value = MOCK_STRESS_DATA
    
    client.get_body_battery_data = AsyncMock()
    client.get_body_battery_data.return_value = MOCK_BODY_BATTERY_DATA
    
    return client

@pytest_asyncio.fixture
async def mock_garth(mock_garth_client):
    """Create a mock garth module."""
    mock_module = MagicMock()
    mock_client = AsyncMock()
    mock_client.login = AsyncMock()
    mock_client.get_sleep_data = AsyncMock(return_value=MOCK_SLEEP_DATA)
    mock_client.get_stress_data = AsyncMock(return_value=MOCK_STRESS_DATA)
    mock_client.get_body_battery_data = AsyncMock(return_value=MOCK_BODY_BATTERY_DATA)
    mock_client.configure = MagicMock()
    mock_client.load = AsyncMock(side_effect=FileNotFoundError())
    mock_client.save = AsyncMock()
    mock_module.Client = MagicMock(return_value=mock_client)
    return mock_module

@pytest.mark.asyncio
async def test_full_authentication_flow(mock_server, mock_settings, mock_garth, mock_cache):
    """Test the complete authentication flow."""
    with patch("src.services.garmin.garth_client.garth", mock_garth), \
         patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.cache.Cache", return_value=mock_cache):
        async with GarthClient() as client:
            mock_client = mock_garth.Client.return_value

            # Verify client initialization
            assert client._initialized
            mock_client.configure.assert_called_once_with(domain="garmin.com")
            assert mock_client.login.await_count == 1
            assert mock_client.login.call_args == call(mock_settings.email, mock_settings.password)
            assert mock_client.save.await_count == 1

@pytest.mark.asyncio
async def test_data_retrieval_workflow(mock_server, mock_settings, mock_garth, mock_cache):
    """Test the complete data retrieval workflow."""
    with patch("src.services.garmin.garth_client.garth", mock_garth), \
         patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.cache.Cache", return_value=mock_cache):
        async with GarthClient() as client:
            test_date = datetime(2024, 2, 7)
            mock_client = mock_garth.Client.return_value

            # Get sleep data
            sleep_data = await client.get_sleep_data(target_date=test_date)
            assert sleep_data == MOCK_SLEEP_DATA
            assert mock_client.get_sleep_data.await_count == 1
            assert mock_client.get_sleep_data.call_args == call(test_date.date())

            # Get stress data
            stress_data = await client.get_stress_data(target_date=test_date)
            assert stress_data == MOCK_STRESS_DATA
            assert mock_client.get_stress_data.await_count == 1
            assert mock_client.get_stress_data.call_args == call(test_date.date())

            # Get body battery data
            body_battery_data = await client.get_body_battery_data(target_date=test_date)
            assert body_battery_data == MOCK_BODY_BATTERY_DATA
            assert mock_client.get_body_battery_data.await_count == 1
            assert mock_client.get_body_battery_data.call_args == call(test_date.date())

@pytest.mark.asyncio
async def test_rate_limiting(mock_server, mock_settings, mock_garth, mock_cache):
    """Test rate limiting behavior."""
    request_count = 0

    # Configure mock client to raise rate limit error after 5 calls
    async def get_sleep_data_with_rate_limit(*args, **kwargs):
        nonlocal request_count
        request_count += 1
        if request_count > 5:
            raise RateLimitError("429: Rate limit exceeded")
        return MOCK_SLEEP_DATA

    mock_client = mock_garth.Client.return_value
    mock_client.get_sleep_data = AsyncMock(side_effect=get_sleep_data_with_rate_limit)

    with patch("src.services.garmin.garth_client.garth", mock_garth), \
         patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.cache.Cache", return_value=mock_cache):
        async with GarthClient() as client:
            test_date = datetime(2024, 2, 7)

            # Make multiple requests to trigger rate limiting
            with pytest.raises(RetryError) as exc_info:
                for _ in range(7):
                    await client.get_sleep_data(target_date=test_date)

            assert request_count > 5
            assert isinstance(exc_info.value.last_attempt.exception(), RateLimitError)

@pytest.mark.asyncio
async def test_network_errors(mock_server, mock_settings, mock_garth, mock_cache):
    """Test handling of network errors."""
    # Configure mock client to raise network error
    async def get_sleep_data_with_error(*args, **kwargs):
        raise Exception("503: Service unavailable")

    mock_client = mock_garth.Client.return_value
    mock_client.get_sleep_data = AsyncMock(side_effect=get_sleep_data_with_error)

    with patch("src.services.garmin.garth_client.garth", mock_garth), \
         patch("src.services.garmin.garth_client.get_settings", return_value=mock_settings), \
         patch("src.services.garmin.cache.Cache", return_value=mock_cache):
        async with GarthClient() as client:
            test_date = datetime(2024, 2, 7)
            with pytest.raises(Exception) as exc_info:
                await client.get_sleep_data(target_date=test_date)

            assert str(exc_info.value) == "503: Service unavailable" 