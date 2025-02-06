"""Models for workout analytics and trend analysis."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import math

from .workout import WorkoutData
from .training_zones import TrainingZone, ZoneType


class TimeRange(str, Enum):
    """Time range for analytics calculations."""
    
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class WorkoutTrend(BaseModel):
    """Model for workout trend analysis."""
    
    start_date: datetime
    end_date: datetime
    time_range: TimeRange
    total_workouts: int = Field(gt=0)
    total_distance: float = Field(gt=0)
    total_duration: int = Field(gt=0)
    average_power: Optional[float] = Field(None, gt=0)
    average_heart_rate: Optional[float] = Field(None, gt=0)
    power_trend: Optional[float] = None  # Positive indicates improvement
    pace_trend: Optional[float] = None
    
    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start(cls, v: datetime, values: Dict) -> datetime:
        """Validate that end_date is after start_date."""
        if 'start_date' in values.data and v <= values.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-31T23:59:59",
                "time_range": "month",
                "total_workouts": 20,
                "total_distance": 200.5,
                "total_duration": 72000,
                "average_power": 250.0,
                "average_heart_rate": 155.0,
                "power_trend": 2.5,
                "pace_trend": -0.5
            }
        }
    }


class ZoneAnalysis(BaseModel):
    """Model for analyzing time spent in different training zones."""
    
    zone: TrainingZone
    time_in_zone: int  # seconds
    percentage_in_zone: float
    
    @property
    def time_in_zone_formatted(self) -> str:
        """Format time in zone as HH:MM:SS."""
        return str(timedelta(seconds=self.time_in_zone))


class WorkoutZonesSummary(BaseModel):
    """Summary of time spent in different training zones for a workout."""
    
    workout_id: str
    zone_type: ZoneType
    total_duration: int
    zone_analysis: List[ZoneAnalysis]
    
    def calculate_percentages(self) -> None:
        """Calculate percentage of time spent in each zone."""
        total_time = sum(za.time_in_zone for za in self.zone_analysis)
        for za in self.zone_analysis:
            za.percentage_in_zone = (za.time_in_zone / total_time * 100) if total_time > 0 else 0


class WorkoutSummary(BaseModel):
    """Comprehensive summary of a workout including zones and metrics."""
    
    workout: WorkoutData
    power_zones: Optional[WorkoutZonesSummary] = None
    heart_rate_zones: Optional[WorkoutZonesSummary] = None
    intensity_score: Optional[float] = None  # Training load score
    recovery_time: Optional[int] = None  # Recommended recovery time in hours
    
    def calculate_intensity_score(self) -> None:
        """Calculate training intensity score based on zones and duration.
        
        The intensity score is calculated using either power or heart rate data:
        - For power data: Uses time in zones weighted by intensity factors
        - For heart rate data: Uses TRIMP (Training Impulse) calculation
        
        The score is normalized to a 0-100 scale where:
        - 0-20: Very light training
        - 20-40: Light training
        - 40-60: Moderate training
        - 60-80: Hard training
        - 80-100: Very hard training
        """
        if self.power_zones:
            # Power-based intensity calculation
            zone_factors = {
                "Recovery": 1,
                "Endurance": 2,
                "Tempo": 3,
                "Threshold": 4,
                "VO2Max": 5,
                "Anaerobic": 6
            }
            
            weighted_sum = sum(
                analysis.time_in_zone * zone_factors.get(analysis.zone.name, 1)
                for analysis in self.power_zones.zone_analysis
            )
            
            # Normalize to 0-100 scale (assuming max 2-hour workout at highest intensity)
            max_possible_score = 6 * 7200  # 2 hours in seconds * max factor
            self.intensity_score = min(100, (weighted_sum / max_possible_score) * 100)
            
        elif self.heart_rate_zones:
            # Heart rate-based intensity calculation using TRIMP
            # TRIMP = duration * avg_hr_ratio * 0.64 * e^(1.92 * avg_hr_ratio)
            # where avg_hr_ratio = (avg_hr - rest_hr)/(max_hr - rest_hr)
            
            if self.workout.heart_rate:
                max_hr = max(
                    analysis.zone.upper_bound
                    for analysis in self.heart_rate_zones.zone_analysis
                )
                rest_hr = min(
                    analysis.zone.lower_bound
                    for analysis in self.heart_rate_zones.zone_analysis
                )
                
                hr_ratio = (self.workout.heart_rate - rest_hr) / (max_hr - rest_hr)
                trimp = (
                    self.workout.duration 
                    * hr_ratio 
                    * 0.64 
                    * math.exp(1.92 * hr_ratio)
                )
                
                # Normalize TRIMP to 0-100 scale (assuming max TRIMP of 400)
                self.intensity_score = min(100, (trimp / 400) * 100)
        
        # Calculate recovery time based on intensity score
        if self.intensity_score is not None:
            if self.intensity_score < 20:
                self.recovery_time = 4
            elif self.intensity_score < 40:
                self.recovery_time = 12
            elif self.intensity_score < 60:
                self.recovery_time = 24
            elif self.intensity_score < 80:
                self.recovery_time = 36
            else:
                self.recovery_time = 48 