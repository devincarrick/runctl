"""Unit tests for analytics models."""

import pytest
from datetime import datetime, timedelta

from src.models.analytics import (
    TimeRange,
    WorkoutTrend,
    ZoneAnalysis,
    WorkoutZonesSummary,
    WorkoutSummary
)
from src.models.training_zones import TrainingZone, ZoneType
from src.models.workout import WorkoutData

@pytest.fixture
def workout_data():
    """Create sample workout data."""
    return WorkoutData(
        id="test_workout",
        date=datetime(2024, 2, 1, 12, 0),
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=175.0
    )

@pytest.fixture
def training_zone():
    """Create sample training zone."""
    return TrainingZone(
        name="Threshold",
        lower_bound=225.0,
        upper_bound=275.0,
        description="Threshold zone",
        zone_type=ZoneType.POWER
    )

def test_time_range_enum():
    """Test TimeRange enum values."""
    assert TimeRange.WEEK == "week"
    assert TimeRange.MONTH == "month"
    assert TimeRange.YEAR == "year"
    assert TimeRange.ALL == "all"

def test_workout_trend_validation():
    """Test WorkoutTrend validation."""
    # Valid trend
    trend = WorkoutTrend(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        time_range=TimeRange.MONTH,
        total_workouts=10,
        total_distance=100.0,
        total_duration=36000,
        average_power=250.0,
        average_heart_rate=160.0,
        power_trend=2.5,
        pace_trend=-0.5
    )
    assert trend.total_workouts == 10
    
    # Test end_date validation
    with pytest.raises(ValueError, match="end_date must be after start_date"):
        WorkoutTrend(
            start_date=datetime(2024, 1, 31),
            end_date=datetime(2024, 1, 1),
            time_range=TimeRange.MONTH,
            total_workouts=10,
            total_distance=100.0,
            total_duration=36000
        )

def test_zone_analysis():
    """Test ZoneAnalysis model."""
    zone = TrainingZone(
        name="Threshold",
        lower_bound=225.0,
        upper_bound=275.0,
        description="Threshold zone",
        zone_type=ZoneType.POWER
    )
    
    analysis = ZoneAnalysis(
        zone=zone,
        time_in_zone=3600,  # 1 hour
        percentage_in_zone=50.0
    )
    
    assert analysis.time_in_zone_formatted == "1:00:00"
    assert analysis.percentage_in_zone == 50.0

def test_workout_zones_summary():
    """Test WorkoutZonesSummary model."""
    zone1 = TrainingZone(
        name="Easy",
        lower_bound=150.0,
        upper_bound=200.0,
        description="Easy zone",
        zone_type=ZoneType.POWER
    )
    zone2 = TrainingZone(
        name="Threshold",
        lower_bound=225.0,
        upper_bound=275.0,
        description="Threshold zone",
        zone_type=ZoneType.POWER
    )
    
    analysis1 = ZoneAnalysis(
        zone=zone1,
        time_in_zone=2700,  # 45 minutes
        percentage_in_zone=0.0  # Will be calculated
    )
    analysis2 = ZoneAnalysis(
        zone=zone2,
        time_in_zone=900,  # 15 minutes
        percentage_in_zone=0.0  # Will be calculated
    )
    
    summary = WorkoutZonesSummary(
        workout_id="test_workout",
        zone_type=ZoneType.POWER,
        total_duration=3600,
        zone_analysis=[analysis1, analysis2]
    )
    
    summary.calculate_percentages()
    assert analysis1.percentage_in_zone == 75.0
    assert analysis2.percentage_in_zone == 25.0

def test_workout_summary(workout_data, training_zone):
    """Test WorkoutSummary model."""
    zone_analysis = ZoneAnalysis(
        zone=training_zone,
        time_in_zone=3600,
        percentage_in_zone=100.0
    )
    
    power_zones = WorkoutZonesSummary(
        workout_id=workout_data.id,
        zone_type=ZoneType.POWER,
        total_duration=workout_data.duration,
        zone_analysis=[zone_analysis]
    )
    
    summary = WorkoutSummary(
        workout=workout_data,
        power_zones=power_zones
    )
    
    # Test intensity score calculation with power data
    summary.calculate_intensity_score()
    assert summary.intensity_score is not None
    assert 0 <= summary.intensity_score <= 100
    assert summary.recovery_time in [4, 12, 24, 36, 48]

def test_workout_summary_heart_rate(workout_data):
    """Test WorkoutSummary with heart rate data."""
    hr_zone = TrainingZone(
        name="Zone 4",
        lower_bound=150.0,
        upper_bound=170.0,
        description="Hard aerobic activity",
        zone_type=ZoneType.HEART_RATE
    )
    
    zone_analysis = ZoneAnalysis(
        zone=hr_zone,
        time_in_zone=3600,
        percentage_in_zone=100.0
    )
    
    hr_zones = WorkoutZonesSummary(
        workout_id=workout_data.id,
        zone_type=ZoneType.HEART_RATE,
        total_duration=workout_data.duration,
        zone_analysis=[zone_analysis]
    )
    
    summary = WorkoutSummary(
        workout=workout_data,
        heart_rate_zones=hr_zones
    )
    
    # Test intensity score calculation with heart rate data
    summary.calculate_intensity_score()
    assert summary.intensity_score is not None
    assert 0 <= summary.intensity_score <= 100
    assert summary.recovery_time in [4, 12, 24, 36, 48]

def test_workout_summary_no_zones(workout_data):
    """Test WorkoutSummary with no zone data."""
    summary = WorkoutSummary(workout=workout_data)
    summary.calculate_intensity_score()
    assert summary.intensity_score is None
    assert summary.recovery_time is None 