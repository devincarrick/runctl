"""Models for training zones and power/heart rate zones calculations."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ZoneType(str, Enum):
    """Type of training zone."""
    
    POWER = "power"
    HEART_RATE = "heart_rate"
    PACE = "pace"


class TrainingZone(BaseModel):
    """Model representing a single training zone."""
    
    name: str
    lower_bound: float
    upper_bound: float
    description: str
    zone_type: ZoneType
    
    @field_validator('upper_bound')
    @classmethod
    def upper_bound_must_be_greater(cls, v: float, values: Dict) -> float:
        """Validate that upper bound is greater than lower bound."""
        if 'lower_bound' in values.data and v <= values.data['lower_bound']:
            raise ValueError('upper_bound must be greater than lower_bound')
        return v


class PowerZones(BaseModel):
    """Model for power-based training zones."""
    
    critical_power: float = Field(..., gt=0)
    ftp: Optional[float] = Field(None, gt=0)
    zones: List[TrainingZone] = Field(default_factory=list)
    
    def calculate_zones(self) -> None:
        """Calculate power zones based on critical power."""
        zone_definitions = [
            ("Recovery", 0.55, 0.75, "Very light intensity for recovery"),
            ("Endurance", 0.75, 0.88, "Aerobic endurance training"),
            ("Tempo", 0.88, 0.95, "Sustained effort at 'comfortably hard' pace"),
            ("Threshold", 0.95, 1.05, "Around critical power/threshold"),
            ("VO2Max", 1.05, 1.20, "High intensity intervals"),
            ("Anaerobic", 1.20, 1.50, "Very high intensity, short duration")
        ]
        
        self.zones = [
            TrainingZone(
                name=name,
                lower_bound=self.critical_power * lower,
                upper_bound=self.critical_power * upper,
                description=desc,
                zone_type=ZoneType.POWER
            )
            for name, lower, upper, desc in zone_definitions
        ]


class HeartRateZones(BaseModel):
    """Model for heart rate-based training zones."""
    
    max_heart_rate: float = Field(..., gt=0)
    resting_heart_rate: Optional[float] = Field(None, gt=0)
    zones: List[TrainingZone] = Field(default_factory=list)
    
    def calculate_zones(self) -> None:
        """Calculate heart rate zones based on max heart rate."""
        zone_definitions = [
            ("Zone 1", 0.50, 0.60, "Very light aerobic activity"),
            ("Zone 2", 0.60, 0.70, "Light aerobic activity"),
            ("Zone 3", 0.70, 0.80, "Moderate aerobic activity"),
            ("Zone 4", 0.80, 0.90, "Hard aerobic activity"),
            ("Zone 5", 0.90, 1.00, "Maximum effort")
        ]
        
        self.zones = [
            TrainingZone(
                name=name,
                lower_bound=self.max_heart_rate * lower,
                upper_bound=self.max_heart_rate * upper,
                description=desc,
                zone_type=ZoneType.HEART_RATE
            )
            for name, lower, upper, desc in zone_definitions
        ]


class PaceZones(BaseModel):
    """Model for pace-based training zones.
    
    Note: Pace is stored in seconds per kilometer for consistency.
    Lower pace numbers indicate faster running (e.g., 240 s/km = 4:00 min/km).
    """
    
    threshold_pace: float = Field(..., gt=0)  # Threshold pace in seconds per kilometer
    zones: List[TrainingZone] = Field(default_factory=list)
    
    def calculate_zones(self) -> None:
        """Calculate pace zones based on threshold pace."""
        zone_definitions = [
            ("Recovery", 1.40, 1.25, "Very easy running"),
            ("Easy", 1.25, 1.15, "Comfortable aerobic running"),
            ("Moderate", 1.15, 1.08, "Steady state running"),
            ("Threshold", 1.08, 1.00, "Comfortably hard/threshold"),
            ("Interval", 1.00, 0.93, "VO2max pace"),
            ("Speed", 0.93, 0.85, "Sprint/anaerobic work")
        ]
        
        self.zones = [
            TrainingZone(
                name=name,
                lower_bound=self.threshold_pace * upper,  # Note: Reversed because lower pace = faster
                upper_bound=self.threshold_pace * lower,
                description=desc,
                zone_type=ZoneType.PACE
            )
            for name, lower, upper, desc in zone_definitions
        ]
        
    @property
    def threshold_pace_formatted(self) -> str:
        """Format threshold pace as MM:SS per kilometer."""
        minutes = int(self.threshold_pace // 60)
        seconds = int(self.threshold_pace % 60)
        return f"{minutes}:{seconds:02d}/km" 