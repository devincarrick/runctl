"""Unit tests for analytics models."""

from datetime import datetime, timedelta
import pytest
from pydantic import ValidationError

from src.models.analytics import (
    TimeRange,
    WorkoutTrend,
    ZoneAnalysis,
    WorkoutZonesSummary,
    WorkoutSummary
)
from src.models.workout import WorkoutData
from src.models.training_zones import TrainingZone, ZoneType


@pytest.fixture
def sample_workout():
    """Create a sample workout for testing."""
    return WorkoutData(
        id="test123",
        date=datetime.now(),
        distance=10000.0,  # 10km
        duration=3600,     # 1 hour
        average_pace=360.0,  # 6:00 min/km
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        temperature=20.0,
        humidity=65.0,
        cadence=180.0
    )


@pytest.fixture
def sample_zones():
    """Create sample training zones for testing."""
    return [
        TrainingZone(
            name="Zone 1",
            lower_bound=0,
            upper_bound=200,
            description="Test zone",
            zone_type=ZoneType.POWER
        ),
        TrainingZone(
            name="Zone 2",
            lower_bound=200,
            upper_bound=400,
            description="Test zone",
            zone_type=ZoneType.POWER
        )
    ]


def test_workout_trend_validation():
    """Test WorkoutTrend validation and calculations."""
    # Valid trend
    trend = WorkoutTrend(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        time_range=TimeRange.MONTH,
        total_workouts=20,
        total_distance=200.5,
        total_duration=72000,
        average_power=250.0,
        average_heart_rate=155.0,
        power_trend=2.5,
        pace_trend=-0.5
    )
    assert trend.time_range == TimeRange.MONTH
    assert trend.total_workouts == 20
    
    # Invalid dates (end before start)
    with pytest.raises(ValidationError):
        WorkoutTrend(
            start_date=datetime(2024, 1, 31),
            end_date=datetime(2024, 1, 1),
            time_range=TimeRange.MONTH,
            total_workouts=20,
            total_distance=200.5,
            total_duration=72000
        )


def test_zone_analysis(sample_zones):
    """Test ZoneAnalysis calculations."""
    analysis = ZoneAnalysis(
        zone=sample_zones[0],
        time_in_zone=3600,  # 1 hour
        percentage_in_zone=50.0
    )
    
    assert analysis.time_in_zone_formatted == "1:00:00"
    assert analysis.percentage_in_zone == 50.0


def test_workout_zones_summary(sample_zones):
    """Test WorkoutZonesSummary calculations."""
    summary = WorkoutZonesSummary(
        workout_id="test123",
        zone_type=ZoneType.POWER,
        total_duration=7200,  # 2 hours
        zone_analysis=[
            ZoneAnalysis(
                zone=sample_zones[0],
                time_in_zone=3600,
                percentage_in_zone=0  # Will be calculated
            ),
            ZoneAnalysis(
                zone=sample_zones[1],
                time_in_zone=3600,
                percentage_in_zone=0  # Will be calculated
            )
        ]
    )
    
    summary.calculate_percentages()
    assert all(za.percentage_in_zone == 50.0 for za in summary.zone_analysis)


def test_workout_summary_intensity(sample_workout, sample_zones):
    """Test WorkoutSummary intensity score calculations."""
    # Create power-based summary
    power_summary = WorkoutSummary(
        workout=sample_workout,
        power_zones=WorkoutZonesSummary(
            workout_id=sample_workout.id,
            zone_type=ZoneType.POWER,
            total_duration=3600,
            zone_analysis=[
                ZoneAnalysis(
                    zone=sample_zones[0],
                    time_in_zone=1800,
                    percentage_in_zone=50
                ),
                ZoneAnalysis(
                    zone=sample_zones[1],
                    time_in_zone=1800,
                    percentage_in_zone=50
                )
            ]
        )
    )
    
    power_summary.calculate_intensity_score()
    assert power_summary.intensity_score is not None
    assert 0 <= power_summary.intensity_score <= 100
    assert power_summary.recovery_time in [4, 12, 24, 36, 48]
    
    # Create heart rate-based summary
    hr_summary = WorkoutSummary(
        workout=sample_workout,
        heart_rate_zones=WorkoutZonesSummary(
            workout_id=sample_workout.id,
            zone_type=ZoneType.HEART_RATE,
            total_duration=3600,
            zone_analysis=[
                ZoneAnalysis(
                    zone=TrainingZone(
                        name="Zone 1",
                        lower_bound=60,
                        upper_bound=200,
                        description="Test zone",
                        zone_type=ZoneType.HEART_RATE
                    ),
                    time_in_zone=3600,
                    percentage_in_zone=100
                )
            ]
        )
    )
    
    hr_summary.calculate_intensity_score()
    assert hr_summary.intensity_score is not None
    assert 0 <= hr_summary.intensity_score <= 100
    assert hr_summary.recovery_time in [4, 12, 24, 36, 48] 