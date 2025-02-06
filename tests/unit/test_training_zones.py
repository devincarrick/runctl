"""Unit tests for training zones models."""

import pytest
from pydantic import ValidationError

from src.models.training_zones import (
    TrainingZone,
    PowerZones,
    HeartRateZones,
    PaceZones,
    ZoneType
)


def test_training_zone_validation():
    """Test TrainingZone validation."""
    # Valid zone
    zone = TrainingZone(
        name="Test Zone",
        lower_bound=100,
        upper_bound=200,
        description="Test description",
        zone_type=ZoneType.POWER
    )
    assert zone.name == "Test Zone"
    assert zone.lower_bound == 100
    assert zone.upper_bound == 200
    
    # Invalid zone (upper bound <= lower bound)
    with pytest.raises(ValidationError):
        TrainingZone(
            name="Invalid Zone",
            lower_bound=200,
            upper_bound=100,
            description="Invalid bounds",
            zone_type=ZoneType.POWER
        )


def test_power_zones_calculation():
    """Test power zones calculation."""
    zones = PowerZones(critical_power=250)
    zones.calculate_zones()
    
    assert len(zones.zones) == 6  # Should have 6 power zones
    
    # Test zone bounds
    recovery = zones.zones[0]
    assert recovery.name == "Recovery"
    assert recovery.lower_bound == pytest.approx(137.5)  # 250 * 0.55
    assert recovery.upper_bound == pytest.approx(187.5)  # 250 * 0.75
    
    anaerobic = zones.zones[-1]
    assert anaerobic.name == "Anaerobic"
    assert anaerobic.lower_bound == pytest.approx(300)  # 250 * 1.20
    assert anaerobic.upper_bound == pytest.approx(375)  # 250 * 1.50


def test_heart_rate_zones_calculation():
    """Test heart rate zones calculation."""
    zones = HeartRateZones(max_heart_rate=185)
    zones.calculate_zones()
    
    assert len(zones.zones) == 5  # Should have 5 HR zones
    
    # Test zone bounds
    zone1 = zones.zones[0]
    assert zone1.name == "Zone 1"
    assert zone1.lower_bound == pytest.approx(92.5)  # 185 * 0.50
    assert zone1.upper_bound == pytest.approx(111)  # 185 * 0.60
    
    zone5 = zones.zones[-1]
    assert zone5.name == "Zone 5"
    assert zone5.lower_bound == pytest.approx(166.5)  # 185 * 0.90
    assert zone5.upper_bound == pytest.approx(185)  # 185 * 1.00


def test_pace_zones_calculation():
    """Test pace zones calculation."""
    # Test with 4:00 min/km threshold pace (240 seconds)
    zones = PaceZones(threshold_pace=240)
    zones.calculate_zones()
    
    assert len(zones.zones) == 6  # Should have 6 pace zones
    
    # Test zone bounds
    recovery = zones.zones[0]
    assert recovery.name == "Recovery"
    assert recovery.lower_bound == pytest.approx(300)  # 240 * 1.25
    assert recovery.upper_bound == pytest.approx(336)  # 240 * 1.40
    
    speed = zones.zones[-1]
    assert speed.name == "Speed"
    assert speed.lower_bound == pytest.approx(204)  # 240 * 0.85
    assert speed.upper_bound == pytest.approx(223.2)  # 240 * 0.93
    
    # Test pace formatting
    assert zones.threshold_pace_formatted == "4:00/km"


def test_invalid_inputs():
    """Test validation of invalid inputs."""
    # Test negative critical power
    with pytest.raises(ValidationError):
        PowerZones(critical_power=-250)
    
    # Test zero max heart rate
    with pytest.raises(ValidationError):
        HeartRateZones(max_heart_rate=0)
    
    # Test negative threshold pace
    with pytest.raises(ValidationError):
        PaceZones(threshold_pace=-240) 