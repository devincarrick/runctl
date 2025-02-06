"""Unit tests for intensity processor."""

import pytest
from typing import Dict, List

from src.models.training_zones import TrainingZone, ZoneType
from src.models.workout import WorkoutData
from src.processors import ProcessingContext
from src.processors.intensity_processor import IntensityProcessor, IntensityScore

@pytest.fixture
def context():
    """Create a processing context with zone data."""
    context = ProcessingContext()
    
    # Create sample power zones
    power_zones = {
        'power': [
            TrainingZone(
                name="Recovery",
                lower_bound=100.0,
                upper_bound=150.0,
                description="Recovery zone",
                zone_type=ZoneType.POWER
            ),
            TrainingZone(
                name="Threshold",
                lower_bound=225.0,
                upper_bound=275.0,
                description="Threshold zone",
                zone_type=ZoneType.POWER
            ),
            TrainingZone(
                name="VO2Max",
                lower_bound=275.0,
                upper_bound=325.0,
                description="VO2Max zone",
                zone_type=ZoneType.POWER
            )
        ]
    }
    
    context.set('zone_output', power_zones)
    return context

@pytest.fixture
def workout_data():
    """Create sample workout data."""
    return WorkoutData(
        id="test_workout",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,  # In threshold zone
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=175.0
    )

def test_intensity_processor_initialization(context):
    """Test intensity processor initialization."""
    processor = IntensityProcessor(context)
    assert processor.context == context

def test_intensity_processor_validation(context, workout_data):
    """Test intensity processor validation."""
    processor = IntensityProcessor(context)
    
    # Test valid input
    assert processor.validate(workout_data) is True
    
    # Test invalid input type
    assert processor.validate("not a workout") is False
    
    # Test missing zones in context
    empty_context = ProcessingContext()
    processor_empty = IntensityProcessor(empty_context)
    assert processor_empty.validate(workout_data) is False

def test_zone_distribution_calculation(context, workout_data):
    """Test zone distribution calculation."""
    processor = IntensityProcessor(context)
    zones = context.get('zone_output')['power']
    
    distribution = processor._calculate_zone_distribution(workout_data, zones)
    
    assert isinstance(distribution, dict)
    assert sum(distribution.values()) == pytest.approx(100.0)
    assert "Threshold" in distribution  # Should be in threshold zone
    assert distribution["Threshold"] == 100.0  # Should be 100% in threshold zone

def test_zone_distribution_no_matching_zone(context, workout_data):
    """Test zone distribution when power doesn't fall into any zone."""
    processor = IntensityProcessor(context)
    zones = context.get('zone_output')['power']
    
    # Modify workout to have power outside any zone
    workout_data.average_power = 1000.0
    distribution = processor._calculate_zone_distribution(workout_data, zones)
    
    assert distribution == {}

def test_zone_distribution_no_power_data(context, workout_data):
    """Test zone distribution with no power data."""
    processor = IntensityProcessor(context)
    zones = context.get('zone_output')['power']
    
    workout_data.average_power = None
    distribution = processor._calculate_zone_distribution(workout_data, zones)
    
    assert distribution == {}

def test_intensity_score_calculation_power(context, workout_data):
    """Test intensity score calculation using power data."""
    processor = IntensityProcessor(context)
    score = processor.process(workout_data)
    
    assert isinstance(score, IntensityScore)
    assert 0 <= score.overall_score <= 100
    assert score.zone_distribution
    assert score.primary_zone == "Threshold"
    assert score.training_load > 0

def test_intensity_score_calculation_heart_rate(context, workout_data):
    """Test intensity score calculation using heart rate data."""
    processor = IntensityProcessor(context)
    
    # Remove power zones and add heart rate zones
    hr_zones = {
        'heart_rate': [
            TrainingZone(
                name="Zone 3",
                lower_bound=150.0,
                upper_bound=170.0,
                description="Moderate aerobic",
                zone_type=ZoneType.HEART_RATE
            ),
            TrainingZone(
                name="Zone 4",
                lower_bound=170.0,
                upper_bound=180.0,
                description="Hard aerobic",
                zone_type=ZoneType.HEART_RATE
            )
        ]
    }
    context.set('zone_output', hr_zones)
    
    # Remove power data
    workout_data.average_power = None
    
    score = processor.process(workout_data)
    
    assert isinstance(score, IntensityScore)
    assert 0 <= score.overall_score <= 100
    assert score.zone_distribution
    assert score.primary_zone == "Zone 3"
    assert score.training_load > 0

def test_intensity_score_no_matching_zones(context, workout_data):
    """Test intensity score calculation with no matching zones."""
    processor = IntensityProcessor(context)
    
    # Set power outside any zone
    workout_data.average_power = 1000.0
    
    with pytest.raises(ValueError, match="No zone distributions could be calculated"):
        processor.process(workout_data)

def test_intensity_score_model():
    """Test IntensityScore model."""
    score = IntensityScore(
        overall_score=75.5,
        zone_distribution={"Threshold": 0.8, "VO2Max": 0.2},
        primary_zone="Threshold",
        training_load=85.0
    )
    
    assert score.overall_score == 75.5
    assert score.zone_distribution == {"Threshold": 0.8, "VO2Max": 0.2}
    assert score.primary_zone == "Threshold"
    assert score.training_load == 85.0 