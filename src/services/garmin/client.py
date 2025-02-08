import logging
from typing import Dict, Optional, List
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin

from .config import get_settings
from .models import SleepData, StressData, BodyBatteryData, RecoveryData

logger = logging.getLogger(__name__)

class GarminConnectClient:
    """Async client for interacting with Garmin Connect API."""
    
    def __init__(self):
        self._settings = get_settings()
        self.base_url = self._settings.api_base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._auth_expires: Optional[datetime] = None
        self._headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (compatible; runctl/1.0;)",
            "Accept": "application/json",
            "Origin": "https://sso.garmin.com"
        }
        self._csrf_token: Optional[str] = None

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def init_session(self):
        """Initialize the aiohttp session and authenticate."""
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
        
        if not self.is_authenticated:
            await self.authenticate()

    async def close(self):
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated and the token is still valid."""
        if not self._auth_token or not self._auth_expires:
            return False
        return datetime.now() < self._auth_expires

    def _extract_cookies_from_headers(self, response: aiohttp.ClientResponse) -> None:
        """Extract cookies from response headers and add them to the session cookie jar."""
        if 'Set-Cookie' in response.headers:
            cookies = response.headers.getall('Set-Cookie', [])
            for cookie in cookies:
                if 'GARMIN-SSO-GUID' in cookie:
                    # Parse the cookie value
                    cookie_parts = cookie.split(';')[0].split('=')
                    if len(cookie_parts) == 2:
                        self._session.cookie_jar.update_cookies({
                            cookie_parts[0]: cookie_parts[1]
                        }, response.url)

    async def authenticate(self):
        """Authenticate with Garmin Connect using email and password."""
        if not self._session:
            await self.init_session()

        try:
            # Step 1: Get the login page and CSRF token
            logger.info("Starting Garmin Connect authentication flow...")
            response = await self._session.get("https://sso.garmin.com/sso/signin")
            response.raise_for_status()
            text = await response.text()
            csrf_match = re.search(r'name="_csrf" value="([^"]+)"', text)
            if not csrf_match:
                raise ValueError("Could not find CSRF token")
            self._csrf_token = csrf_match.group(1)

            # Step 2: Submit login credentials
            login_data = {
                "username": self._settings.email,
                "password": self._settings.password,
                "_csrf": self._csrf_token,
                "embed": "false"
            }
            login_url = "https://sso.garmin.com/sso/signin"
            response = await self._session.post(login_url, data=login_data, allow_redirects=False)
            response.raise_for_status()
            if response.status != 302:
                raise ValueError("Login failed - expected redirect")
            ticket_url = response.headers.get("Location")
            if not ticket_url:
                raise ValueError("No ticket URL in response")
            self._extract_cookies_from_headers(response)

            # Step 3: Exchange ticket for session token
            response = await self._session.get(ticket_url, allow_redirects=True)
            response.raise_for_status()
            self._extract_cookies_from_headers(response)
            if not any(cookie.key == "GARMIN-SSO-GUID" for cookie in self._session.cookie_jar):
                raise ValueError("Authentication failed - no SSO cookie")

            # Step 4: Get the OAuth token
            token_url = urljoin(self.base_url, "/oauth-token")
            response = await self._session.post(token_url)
            response.raise_for_status()
            token_data = await response.json()
            self._auth_token = token_data.get("access_token")
            if not self._auth_token:
                raise ValueError("Failed to get access token")
            
            # Set token expiration (default 1 hour if not specified)
            expires_in = token_data.get("expires_in", 3600)
            self._auth_expires = datetime.now() + timedelta(seconds=expires_in)
            
            # Update session headers with the token
            self._headers["Authorization"] = f"Bearer {self._auth_token}"
            
            logger.info("Successfully authenticated with Garmin Connect")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Garmin Connect: {e}")
            raise

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an authenticated request to the Garmin Connect API."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if not self._session:
            await self.init_session()
        
        try:
            response = await self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise

    async def get_sleep_data(self, date: datetime) -> SleepData:
        """
        Fetch sleep data for a specific date.
        
        Args:
            date: The date to fetch sleep data for
            
        Returns:
            SleepData object containing sleep information
        """
        formatted_date = date.strftime("%Y-%m-%d")
        endpoint = f"wellness-api/wellness/dailySleepData/{formatted_date}"
        
        try:
            data = await self._request("GET", endpoint)
            return SleepData.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to fetch sleep data for {formatted_date}: {e}")
            raise

    async def get_sleep_data_range(self, start_date: datetime, end_date: datetime) -> List[SleepData]:
        """
        Fetch sleep data for a date range.
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range (inclusive)
            
        Returns:
            List of SleepData objects
        """
        sleep_data = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                data = await self.get_sleep_data(current_date)
                sleep_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to fetch sleep data for {current_date}: {e}")
            current_date += timedelta(days=1)
            
        return sleep_data

    async def get_stress_data(self, date: datetime) -> StressData:
        """
        Fetch stress data for a specific date.
        
        Args:
            date: The date to fetch stress data for
            
        Returns:
            StressData object containing stress information
        """
        formatted_date = date.strftime("%Y-%m-%d")
        endpoint = f"wellness-api/wellness/dailyStress/{formatted_date}"
        
        try:
            data = await self._request("GET", endpoint)
            return StressData.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to fetch stress data for {formatted_date}: {e}")
            raise

    async def get_body_battery_data(self, date: datetime) -> BodyBatteryData:
        """
        Fetch Body Battery data for a specific date.
        
        Args:
            date: The date to fetch Body Battery data for
            
        Returns:
            BodyBatteryData object containing Body Battery information
        """
        formatted_date = date.strftime("%Y-%m-%d")
        endpoint = f"wellness-api/wellness/dailyBodyBattery/{formatted_date}"
        
        try:
            data = await self._request("GET", endpoint)
            return BodyBatteryData.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to fetch Body Battery data for {formatted_date}: {e}")
            raise

    async def get_recovery_data(self, date: datetime) -> RecoveryData:
        """
        Fetch combined recovery metrics (stress and Body Battery) for a specific date.
        
        Args:
            date: The date to fetch recovery data for
            
        Returns:
            RecoveryData object containing combined recovery metrics
        """
        formatted_date = date.strftime("%Y-%m-%d")
        
        try:
            # Fetch both stress and body battery data
            stress_data = await self.get_stress_data(date)
            body_battery_data = await self.get_body_battery_data(date)
            
            # Combine into recovery data
            recovery_data = RecoveryData(
                date=date,
                stress_data=stress_data,
                body_battery_data=body_battery_data
            )
            
            return recovery_data
        except Exception as e:
            logger.error(f"Failed to fetch recovery data for {formatted_date}: {e}")
            raise 