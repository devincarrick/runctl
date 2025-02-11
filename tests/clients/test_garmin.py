"""Tests for the Garmin Connect client."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import garth
import pytest
from freezegun import freeze_time

from src.clients.garmin import GarthClient, GarthToken, RateLimiter


@pytest.fixture
def mock_garth_client() -> MagicMock:
    """Create a mock garth client."""
    client = MagicMock(spec=garth.Client)
    client.oauth2_token = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": int(datetime(2024, 2, 8, 12, 0).timestamp()),
    }
    client.headers = {"Authorization": "Bearer test_access_token"}
    return client


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.closed = False
    return session


@pytest.fixture
def mock_response() -> AsyncMock:
    """Create a mock aiohttp response."""
    response = AsyncMock()
    response.status = 200
    response.json.return_value = {"data": "test"}
    return response


@pytest.fixture
async def garth_client(
    tmp_path: Path,
    mock_garth_client: MagicMock,
    mock_session: AsyncMock,
) -> AsyncGenerator[GarthClient, None]:
    """Create a GarthClient instance for testing."""
    token_path = tmp_path / "token.json"
    client = GarthClient(
        email="test@example.com",
        password="test_password",
        token_path=token_path,
    )
    client._client = mock_garth_client
    client._session = mock_session
    yield client
    await client.close()


def test_garth_token_from_garth(mock_garth_client: MagicMock) -> None:
    """Test creating a GarthToken from garth client."""
    token = GarthToken.from_garth(mock_garth_client)
    assert token.access_token == "test_access_token"
    assert token.refresh_token == "test_refresh_token"
    assert token.expires_at == datetime(2024, 2, 8, 12, 0)


def test_garth_token_to_garth(mock_garth_client: MagicMock) -> None:
    """Test updating garth client with token data."""
    token = GarthToken(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        expires_at=datetime(2024, 2, 8, 13, 0),
    )
    token.to_garth(mock_garth_client)
    assert mock_garth_client.oauth2_token == {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_at": int(datetime(2024, 2, 8, 13, 0).timestamp()),
    }


@freeze_time("2024-02-08 12:00:00")
async def test_rate_limiter() -> None:
    """Test rate limiter behavior."""
    limiter = RateLimiter(requests_per_minute=60)
    start_time = datetime.now()

    # First request should not be delayed
    await limiter.acquire()
    elapsed = (datetime.now() - start_time).total_seconds()
    assert elapsed < 0.1

    # Second request should be delayed by 1 second
    await limiter.acquire()
    elapsed = (datetime.now() - start_time).total_seconds()
    assert 0.9 < elapsed < 1.1


async def test_garth_client_connect_with_token(
    garth_client: GarthClient,
    mock_garth_client: MagicMock,
    tmp_path: Path,
) -> None:
    """Test connecting with saved token."""
    token = GarthToken(
        access_token="saved_access_token",
        refresh_token="saved_refresh_token",
        expires_at=datetime(2024, 2, 8, 12, 0),
    )
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(token.model_dump()))
    garth_client.token_path = token_path

    await garth_client.connect()
    mock_garth_client.oauth2_token_refresh.assert_called_once()
    mock_garth_client.login.assert_not_called()


async def test_garth_client_connect_with_credentials(
    garth_client: GarthClient,
    mock_garth_client: MagicMock,
) -> None:
    """Test connecting with credentials."""
    await garth_client.connect()
    mock_garth_client.login.assert_called_once_with("test@example.com", "test_password")


async def test_garth_client_get(
    garth_client: GarthClient,
    mock_session: AsyncMock,
    mock_response: AsyncMock,
) -> None:
    """Test making GET request."""
    mock_session.get.return_value.__aenter__.return_value = mock_response
    response = await garth_client.get("test/endpoint")
    assert response == {"data": "test"}
    mock_session.get.assert_called_once_with(
        "https://connect.garmin.com/modern/test/endpoint",
        headers={"Authorization": "Bearer test_access_token"},
    )


async def test_garth_client_get_rate_limit(
    garth_client: GarthClient,
    mock_session: AsyncMock,
) -> None:
    """Test handling rate limit response."""
    rate_limit_response = AsyncMock()
    rate_limit_response.status = 429
    rate_limit_response.headers = {"Retry-After": "2"}
    success_response = AsyncMock()
    success_response.status = 200
    success_response.json.return_value = {"data": "test"}

    mock_session.get.return_value.__aenter__.side_effect = [
        rate_limit_response,
        success_response,
    ]

    response = await garth_client.get("test/endpoint")
    assert response == {"data": "test"}
    assert mock_session.get.call_count == 2


@pytest.mark.parametrize(
    "method,endpoint",
    [
        (
            "get_sleep_data",
            "proxy/wellness-service/wellness/dailySleepData",
        ),
        (
            "get_stress_data",
            "proxy/wellness-service/wellness/dailyStress",
        ),
        (
            "get_body_battery_data",
            "proxy/wellness-service/wellness/dailyBodyBattery",
        ),
    ],
)
async def test_garth_client_data_methods(
    garth_client: GarthClient,
    mock_session: AsyncMock,
    mock_response: AsyncMock,
    method: str,
    endpoint: str,
) -> None:
    """Test data retrieval methods."""
    mock_session.get.return_value.__aenter__.return_value = mock_response
    start_date = datetime(2024, 2, 8)
    end_date = datetime(2024, 2, 9)

    response = await getattr(garth_client, method)(start_date, end_date)
    assert response == {"data": "test"}
    mock_session.get.assert_called_once_with(
        f"https://connect.garmin.com/modern/{endpoint}",
        headers={"Authorization": "Bearer test_access_token"},
        params={
            "startDate": "2024-02-08",
            "endDate": "2024-02-09",
        },
    ) 