"""
Garmin Connect API integration for runctl.

This package provides authentication and API client functionality for
interacting with the Garmin Connect API to retrieve sleep and recovery metrics.
"""

from .client import GarminConnectClient
from .config import GarminConnectSettings, get_settings

__all__ = ['GarminConnectClient', 'GarminConnectSettings', 'get_settings'] 