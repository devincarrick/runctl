"""
Garmin Connect data models.

This package contains Pydantic models for Garmin Connect data types including:
- Sleep data
- Stress data
- Body Battery data
"""

from src.models.garmin.sleep import SleepData
from src.models.garmin.stress import StressData
from src.models.garmin.body_battery import BodyBatteryData

__all__ = ["SleepData", "StressData", "BodyBatteryData"] 