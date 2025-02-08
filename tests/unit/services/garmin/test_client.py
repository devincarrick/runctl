import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
import re

from src.services.garmin.client import GarminConnectClient


@pytest.fixture
async def client():
    """Create a GarminConnectClient instance for testing."""
    client = GarminConnectClient()
    with patch.object(client, 'authenticate', AsyncMock()):
        await client.init_session()
        yield client
        await client.close()


def test_client_initialization():
    """Test client initialization and default values."""
    client = GarminConnectClient()
    
    assert client.base_url == "https://connect.garmin.com/modern"
    assert client._session is None
    assert client._auth_token is None
    assert client._auth_expires is None
    assert client._csrf_token is None
    assert "User-Agent" in client._headers
    assert "Accept" in client._headers
    assert "Origin" in client._headers
    assert client._headers["Origin"] == "https://sso.garmin.com"


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client works correctly as an async context manager."""
    with patch('src.services.garmin.client.GarminConnectClient.authenticate', AsyncMock()):
        async with GarminConnectClient() as client:
            assert client._session is not None
            assert isinstance(client, GarminConnectClient)
        
        assert client._session is None


@pytest.mark.asyncio
async def test_is_authenticated_property():
    """Test is_authenticated property behavior."""
    client = GarminConnectClient()
    
    # Not authenticated initially
    assert not client.is_authenticated
    
    # Set mock authentication
    client._auth_token = "test_token"
    client._auth_expires = datetime.now() + timedelta(hours=1)
    assert client.is_authenticated
    
    # Test expired token
    client._auth_expires = datetime.now() - timedelta(minutes=1)
    assert not client.is_authenticated


@pytest.mark.asyncio
async def test_authenticate_flow():
    """Test the complete authentication flow."""
    client = GarminConnectClient()
    
    # Create mock responses
    mock_login_page = AsyncMock()
    mock_login_page.text = AsyncMock(return_value='<input name="_csrf" value="test_csrf_token">')
    mock_login_page.raise_for_status = MagicMock()
    
    mock_login_response = AsyncMock()
    mock_login_response.status = 302
    mock_login_response.headers = {"Location": "https://connect.garmin.com/ticket?ticket=test_ticket"}
    mock_login_response.raise_for_status = MagicMock()
    
    mock_ticket_response = AsyncMock()
    mock_ticket_response.raise_for_status = MagicMock()
    
    mock_token_response = AsyncMock()
    mock_token_response.raise_for_status = MagicMock()
    mock_token_response.json = AsyncMock(return_value={
        "access_token": "test_access_token",
        "expires_in": 3600
    })
    
    # Create mock session
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(side_effect=[mock_login_page, mock_ticket_response])
    mock_session.post = AsyncMock(side_effect=[mock_login_response, mock_token_response])
    mock_session.cookie_jar = [MagicMock(key="GARMIN-SSO-GUID")]
    
    # Set up the client with our mock session
    client._session = mock_session
    
    # Perform authentication
    await client.authenticate()
    
    # Verify the flow
    assert client._csrf_token == "test_csrf_token"
    assert client._auth_token == "test_access_token"
    assert client.is_authenticated
    assert "Bearer test_access_token" in client._headers["Authorization"]


@pytest.mark.asyncio
async def test_authenticate_creates_session():
    """Test authenticate creates a session if none exists."""
    client = GarminConnectClient()
    with patch.object(client, 'authenticate', AsyncMock()) as mock_auth:
        await client.init_session()
        assert client._session is not None
        mock_auth.assert_called_once()


@pytest.mark.asyncio
async def test_request_with_authentication():
    """Test _request method handles authentication and makes requests."""
    client = GarminConnectClient()
    
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"test": "data"})
    
    # Create a mock session
    mock_session = AsyncMock()
    mock_session.request = AsyncMock(return_value=mock_response)
    
    # Set up the client with our mock session
    client._session = mock_session
    client._auth_token = "test_token"
    client._auth_expires = datetime.now() + timedelta(hours=1)
    
    # Make a request
    result = await client._request("GET", "/test/endpoint")
    
    assert result == {"test": "data"}
    assert client.is_authenticated
    mock_session.request.assert_called_once_with(
        "GET",
        "https://connect.garmin.com/modern/test/endpoint"
    )


@pytest.mark.asyncio
async def test_request_handles_errors():
    """Test _request method handles errors appropriately."""
    client = GarminConnectClient()
    
    # Create a mock session that raises an error
    mock_session = AsyncMock()
    mock_session.request = AsyncMock(side_effect=aiohttp.ClientError())
    
    # Set up the client with our mock session
    client._session = mock_session
    client._auth_token = "test_token"
    client._auth_expires = datetime.now() + timedelta(hours=1)
    
    with pytest.raises(aiohttp.ClientError):
        await client._request("GET", "/test/endpoint") 