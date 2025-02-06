"""Unit tests for training zones models."""

import pytest
from pydantic import ValidationError

from src.models.training_zones import (
    ZoneType,
    TrainingZone,
    PowerZones,
    HeartRateZones,
    PaceZones
)

def test_zone_type_enum():
    """Test ZoneType enum values."""
    assert ZoneType.POWER == "power"
    assert ZoneType.HEART_RATE == "heart_rate"
    assert ZoneType.PACE == "pace"

def test_training_zone_validation():
    """Test TrainingZone validation."""
    # Valid zone
    zone = TrainingZone(
        name="Test Zone",
        lower_bound=100.0,
        upper_bound=200.0,
        description="Test description",
        zone_type=ZoneType.POWER
    )
    assert zone.name == "Test Zone"
    assert zone.lower_bound == 100.0
    assert zone.upper_bound == 200.0
    
    # Invalid zone (upper bound <= lower bound)
    with pytest.raises(ValueError, match="upper_bound must be greater than lower_bound"):
        TrainingZone(
            name="Invalid Zone",
            lower_bound=200.0,
            upper_bound=100.0,
            description="Invalid zone",
            zone_type=ZoneType.POWER
        )

def test_power_zones_calculation():
    """Test power zones calculation."""
    power_zones = PowerZones(critical_power=300.0, ftp=285.0)
    power_zones.calculate_zones()
    
    assert len(power_zones.zones) == 6  # Should have 6 power zones
    
    # Test zone boundaries
    recovery_zone = power_zones.zones[0]
    assert recovery_zone.name == "Recovery"
    assert recovery_zone.lower_bound == pytest.approx(300.0 * 0.55)
    assert recovery_zone.upper_bound == pytest.approx(300.0 * 0.75)
    assert recovery_zone.zone_type == ZoneType.POWER
    
    anaerobic_zone = power_zones.zones[-1]
    assert anaerobic_zone.name == "Anaerobic"
    assert anaerobic_zone.lower_bound == pytest.approx(300.0 * 1.20)
    assert anaerobic_zone.upper_bound == pytest.approx(300.0 * 1.50)

def test_heart_rate_zones_calculation():
    """Test heart rate zones calculation."""
    hr_zones = HeartRateZones(max_heart_rate=185.0, resting_heart_rate=45.0)
    hr_zones.calculate_zones()
    
    assert len(hr_zones.zones) == 5  # Should have 5 HR zones
    
    # Test zone boundaries
    zone1 = hr_zones.zones[0]
    assert zone1.name == "Zone 1"
    assert zone1.lower_bound == pytest.approx(185.0 * 0.50)
    assert zone1.upper_bound == pytest.approx(185.0 * 0.60)
    assert zone1.zone_type == ZoneType.HEART_RATE
    
    zone5 = hr_zones.zones[-1]
    assert zone5.name == "Zone 5"
    assert zone5.lower_bound == pytest.approx(185.0 * 0.90)
    assert zone5.upper_bound == pytest.approx(185.0 * 1.00)

def test_pace_zones_calculation():
    """Test pace zones calculation."""
    pace_zones = PaceZones(threshold_pace=240.0)  # 4:00 min/km
    pace_zones.calculate_zones()
    
    assert len(pace_zones.zones) == 6  # Should have 6 pace zones
    
    # Test zone boundaries (note: pace is reversed - lower is faster)
    recovery_zone = pace_zones.zones[0]
    assert recovery_zone.name == "Recovery"
    assert recovery_zone.lower_bound == pytest.approx(240.0 * 1.25)  # Slower
    assert recovery_zone.upper_bound == pytest.approx(240.0 * 1.40)  # Even slower
    assert recovery_zone.zone_type == ZoneType.PACE
    
    speed_zone = pace_zones.zones[-1]
    assert speed_zone.name == "Speed"
    assert speed_zone.lower_bound == pytest.approx(240.0 * 0.85)  # Faster
    assert speed_zone.upper_bound == pytest.approx(240.0 * 0.93)  # Less fast

def test_pace_zones_formatting():
    """Test pace zone formatting."""
    pace_zones = PaceZones(threshold_pace=240.0)  # 4:00 min/km
    assert pace_zones.threshold_pace_formatted == "4:00/km"
    
    pace_zones = PaceZones(threshold_pace=362.0)  # 6:02 min/km
    assert pace_zones.threshold_pace_formatted == "6:02/km"

def test_power_zones_validation():
    """Test PowerZones validation."""
    # Invalid critical power
    with pytest.raises(ValidationError):
        PowerZones(critical_power=-100.0)
    
    # Invalid FTP
    with pytest.raises(ValidationError):
        PowerZones(critical_power=300.0, ftp=-50.0)

def test_heart_rate_zones_validation():
    """Test HeartRateZones validation."""
    # Invalid max heart rate
    with pytest.raises(ValidationError):
        HeartRateZones(max_heart_rate=-100.0)
    
    # Invalid resting heart rate
    with pytest.raises(ValidationError):
        HeartRateZones(max_heart_rate=185.0, resting_heart_rate=-45.0)

def test_pace_zones_validation():
    """Test PaceZones validation."""
    # Invalid threshold pace
    with pytest.raises(ValidationError):
        PaceZones(threshold_pace=-240.0) 