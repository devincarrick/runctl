"""Unit tests for zone processor."""

import pytest

from src.models.training_zones import TrainingZone, ZoneType
from src.models.workout import WorkoutData
from src.processors import ProcessingContext
from src.processors.zone_processor import ZoneProcessor

@pytest.fixture
def context():
    """Create a processing context."""
    return ProcessingContext()

@pytest.fixture
def workout_data():
    """Create sample workout data."""
    return WorkoutData(
        id="test_workout",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=175.0
    )

def test_zone_processor_initialization(context):
    """Test zone processor initialization."""
    processor = ZoneProcessor(context)
    assert processor.context == context

def test_zone_processor_validation(context, workout_data):
    """Test zone processor validation."""
    processor = ZoneProcessor(context)
    
    # Test valid input
    assert processor.validate(workout_data) is True
    
    # Test invalid input type
    assert processor.validate("not a workout") is False

def test_process_all_metrics(context, workout_data):
    """Test zone calculation with all metrics available."""
    processor = ZoneProcessor(context)
    zones = processor.process(workout_data)
    
    # Check power zones
    assert 'power' in zones
    power_zones = zones['power']
    assert len(power_zones) == 6
    
    # Verify power zone boundaries
    recovery = power_zones[0]
    assert recovery.name == "Recovery"
    assert recovery.lower_bound == pytest.approx(250.0 * 0.55)
    assert recovery.upper_bound == pytest.approx(250.0 * 0.75)
    assert recovery.zone_type == ZoneType.POWER
    
    # Check heart rate zones
    assert 'heart_rate' in zones
    hr_zones = zones['heart_rate']
    assert len(hr_zones) == 5
    
    # Verify heart rate zone boundaries
    zone1 = hr_zones[0]
    assert zone1.name == "Zone 1"
    assert zone1.lower_bound == pytest.approx(165.0 * 0.50)
    assert zone1.upper_bound == pytest.approx(165.0 * 0.60)
    assert zone1.zone_type == ZoneType.HEART_RATE
    
    # Check pace zones
    assert 'pace' in zones
    pace_zones = zones['pace']
    assert len(pace_zones) == 6
    
    # Verify pace zone boundaries (note: pace is reversed)
    recovery_pace = pace_zones[0]
    assert recovery_pace.name == "Recovery"
    assert recovery_pace.lower_bound == pytest.approx(360.0 * 1.25)
    assert recovery_pace.upper_bound == pytest.approx(360.0 * 1.40)
    assert recovery_pace.zone_type == ZoneType.PACE

def test_process_missing_power(context, workout_data):
    """Test zone calculation with missing power data."""
    workout_data.average_power = None
    processor = ZoneProcessor(context)
    zones = processor.process(workout_data)
    
    assert 'power' not in zones
    assert 'heart_rate' in zones
    assert 'pace' in zones

def test_process_missing_heart_rate(context, workout_data):
    """Test zone calculation with missing heart rate data."""
    workout_data.heart_rate = None
    processor = ZoneProcessor(context)
    zones = processor.process(workout_data)
    
    assert 'power' in zones
    assert 'heart_rate' not in zones
    assert 'pace' in zones

def test_process_missing_pace(context, workout_data):
    """Test zone calculation with missing pace data."""
    workout_data.average_pace = 0.0  # Use 0.0 instead of None since it's required
    processor = ZoneProcessor(context)
    zones = processor.process(workout_data)
    
    assert 'power' in zones
    assert 'heart_rate' in zones
    assert 'pace' not in zones

def test_process_all_metrics_missing(context):
    """Test zone calculation with all metrics missing."""
    workout = WorkoutData(
        id="empty_workout",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=0.0,  # Use 0.0 instead of None since it's required
        average_power=None,
        total_elevation_gain=None,
        heart_rate=None,
        cadence=None
    )
    
    processor = ZoneProcessor(context)
    zones = processor.process(workout)
    
    assert not zones  # Should be an empty dictionary

def test_zone_boundaries_validation(context, workout_data):
    """Test that zone boundaries are correctly ordered."""
    processor = ZoneProcessor(context)
    zones = processor.process(workout_data)
    
    for zone_type, zone_list in zones.items():
        for i in range(len(zone_list) - 1):
            current_zone = zone_list[i]
            next_zone = zone_list[i + 1]
            if zone_type == 'pace':
                # For pace zones, lower numbers are faster (boundaries are reversed)
                assert current_zone.upper_bound >= next_zone.lower_bound
            else:
                # For power and heart rate zones, higher numbers are more intense
                assert current_zone.upper_bound <= next_zone.lower_bound 