"""Data models for running metrics."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RunningMetrics:
    """Data model for running metrics from a single activity."""
    timestamp: datetime
    distance: float  # in meters
    duration: float  # in seconds
    avg_pace: float  # in seconds per kilometer
    avg_heart_rate: Optional[float] = None  # in bpm
    max_heart_rate: Optional[float] = None  # in bpm
    elevation_gain: Optional[float] = None  # in meters
    calories: Optional[float] = None  # in kcal
    cadence: Optional[float] = None  # steps per minute
    temperature: Optional[float] = None  # in celsius
    weather_condition: Optional[str] = None


@dataclass
class RunningSession:
    """Container for a running session with metrics and metadata."""
    id: str
    metrics: RunningMetrics
    notes: Optional[str] = None
    tags: list[str] = None
    equipment: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass initialization."""
        if self.tags is None:
            self.tags = [] 