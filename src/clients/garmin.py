"""Garmin Connect client implementation using garth."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
import garth
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GarthToken(BaseModel):
    """Token data for Garmin Connect authentication."""

    access_token: str = Field(..., description="OAuth access token")
    refresh_token: str = Field(..., description="OAuth refresh token")
    expires_at: datetime = Field(..., description="Token expiration timestamp")

    @classmethod
    def from_garth(cls, client: garth.Client) -> "GarthToken":
        """Create a token from garth client session."""
        if not client.oauth2_token:
            raise ValueError("Garth client is not authenticated")

        return cls(
            access_token=client.oauth2_token["access_token"],
            refresh_token=client.oauth2_token["refresh_token"],
            expires_at=datetime.fromtimestamp(client.oauth2_token["expires_at"]),
        )

    def to_garth(self, client: garth.Client) -> None:
        """Update garth client with token data."""
        client.oauth2_token = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": int(self.expires_at.timestamp()),
        }


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute  # Time between requests
        self.last_request: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a rate limit token."""
        async with self._lock:
            if self.last_request is not None:
                elapsed = (datetime.now() - self.last_request).total_seconds()
                if elapsed < self.interval:
                    await asyncio.sleep(self.interval - elapsed)
            self.last_request = datetime.now()


class GarthClient:
    """Garmin Connect client using garth library."""

    def __init__(
        self,
        email: str,
        password: str,
        token_path: Optional[Path] = None,
        requests_per_minute: int = 60,
    ):
        """Initialize Garth client.

        Args:
            email: Garmin Connect account email.
            password: Garmin Connect account password.
            token_path: Path to store authentication token. If None, token is not persisted.
            requests_per_minute: Maximum number of requests allowed per minute.
        """
        self.email = email
        self.password = password
        self.token_path = token_path
        self.rate_limiter = RateLimiter(requests_per_minute)
        self._client: Optional[garth.Client] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GarthClient":
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    def _load_token(self) -> Optional[GarthToken]:
        """Load authentication token from file."""
        if not self.token_path or not self.token_path.exists():
            return None

        try:
            token_data = json.loads(self.token_path.read_text())
            return GarthToken.model_validate(token_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to load token: %s", e)
            return None

    def _save_token(self, token: GarthToken) -> None:
        """Save authentication token to file."""
        if not self.token_path:
            return

        try:
            token_data = token.model_dump()
            self.token_path.write_text(json.dumps(token_data))
        except (OSError, ValueError) as e:
            logger.warning("Failed to save token: %s", e)

    async def _create_session(self) -> None:
        """Create a new aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def connect(self) -> None:
        """Connect to Garmin Connect and authenticate."""
        await self._create_session()
        if not self._session:
            raise RuntimeError("Failed to create session")

        self._client = garth.Client(session=self._session)

        # Try to load existing token
        token = self._load_token()
        if token:
            try:
                token.to_garth(self._client)
                await self._client.oauth2_token_refresh()
                logger.info("Authenticated using saved token")
                return
            except Exception as e:
                logger.warning("Failed to refresh token: %s", e)

        # Authenticate with credentials
        try:
            await self._client.login(self.email, self.password)
            logger.info("Authenticated using credentials")
            token = GarthToken.from_garth(self._client)
            self._save_token(token)
        except Exception as e:
            logger.error("Authentication failed: %s", e)
            raise

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a GET request to Garmin Connect API.

        Args:
            endpoint: API endpoint to request.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            JSON response from the API.

        Raises:
            ValueError: If client is not connected.
            aiohttp.ClientError: If request fails.
        """
        if not self._client or not self._session:
            raise ValueError("Client is not connected")

        await self.rate_limiter.acquire()

        try:
            async with self._session.get(
                f"https://connect.garmin.com/modern/{endpoint}",
                headers=self._client.headers,
                **kwargs,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            if response.status == 429:  # Too Many Requests
                retry_after = int(response.headers.get("Retry-After", "60"))
                logger.warning("Rate limit exceeded, waiting %d seconds", retry_after)
                await asyncio.sleep(retry_after)
                return await self.get(endpoint, **kwargs)
            logger.error("Request failed: %s", e)
            raise

    async def get_sleep_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get sleep data from Garmin Connect.

        Args:
            start_date: Start date for sleep data.
            end_date: End date for sleep data. If None, defaults to start_date + 1 day.

        Returns:
            Sleep data from Garmin Connect.
        """
        if end_date is None:
            end_date = start_date + timedelta(days=1)

        return await self.get(
            "proxy/wellness-service/wellness/dailySleepData",
            params={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            },
        )

    async def get_stress_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get stress data from Garmin Connect.

        Args:
            start_date: Start date for stress data.
            end_date: End date for stress data. If None, defaults to start_date + 1 day.

        Returns:
            Stress data from Garmin Connect.
        """
        if end_date is None:
            end_date = start_date + timedelta(days=1)

        return await self.get(
            "proxy/wellness-service/wellness/dailyStress",
            params={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            },
        )

    async def get_body_battery_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get Body Battery data from Garmin Connect.

        Args:
            start_date: Start date for Body Battery data.
            end_date: End date for Body Battery data. If None, defaults to start_date + 1 day.

        Returns:
            Body Battery data from Garmin Connect.
        """
        if end_date is None:
            end_date = start_date + timedelta(days=1)

        return await self.get(
            "proxy/wellness-service/wellness/dailyBodyBattery",
            params={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            },
        ) 