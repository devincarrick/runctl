"""Tests for power zone calculations."""
from datetime import datetime, timedelta, timezone

import pytest

from runctl.data.models import RunningMetrics
from runctl.data.power_zones import PowerZone, PowerZones


@pytest.fixture
def power_zones():
    """Create a PowerZones instance with test critical power."""
    return PowerZones(critical_power=3.5)  # 3.5 W/kg critical power


@pytest.fixture
def sample_metrics():
    """Create a list of sample metrics with power data."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics = []
    
    # Create metrics at 1-second intervals with varying power
    for i in range(60):  # 1 minute of data
        power = 3.5  # Critical power
        
        # Vary power to test different zones
        if 10 <= i < 20:  # Recovery (0-80% CP)
            power = 2.5  # ~71% CP
        elif 20 <= i < 30:  # Endurance (80-88% CP)
            power = 3.0  # ~86% CP
        elif 30 <= i < 40:  # Tempo (88-95% CP)
            power = 3.2  # ~91% CP
        elif 40 <= i < 50:  # Threshold (95-105% CP)
            power = 3.5  # 100% CP
        elif 50 <= i < 55:  # VO2max (105-115% CP)
            power = 3.8  # ~109% CP
        else:  # Anaerobic (>115% CP)
            power = 4.2  # ~120% CP
        
        metrics.append(RunningMetrics(
            timestamp=base_time + timedelta(seconds=i),
            distance=i * 3,  # 3 m/s pace
            duration=float(i),
            avg_pace=333.33,  # ~5:33 min/km
            power=power
        ))
    
    return metrics


def test_power_zone_initialization(power_zones):
    """Test power zone initialization and scaling."""
    # Check that zones were created and scaled correctly
    zones = power_zones.get_zone_ranges()
    assert len(zones) == 6  # Should have 6 default zones
    
    # Check scaling of first zone (Recovery: 0-80% CP)
    name, lower, upper, desc = zones[0]
    assert name == "Recovery"
    assert lower == 0.0
    assert upper == pytest.approx(2.8)  # 80% of 3.5
    assert "recovery" in desc.lower()
    
    # Check scaling of threshold zone (95-105% CP)
    name, lower, upper, desc = zones[3]
    assert name == "Threshold"
    assert lower == pytest.approx(3.325)  # 95% of 3.5
    assert upper == pytest.approx(3.675)  # 105% of 3.5
    assert "threshold" in desc.lower()


def test_zone_detection(power_zones):
    """Test power zone detection."""
    assert power_zones.detect_zone(2.0) == 0  # Recovery
    assert power_zones.detect_zone(3.0) == 1  # Endurance
    assert power_zones.detect_zone(3.2) == 2  # Tempo
    assert power_zones.detect_zone(3.5) == 3  # Threshold
    assert power_zones.detect_zone(3.8) == 4  # VO2max
    assert power_zones.detect_zone(4.2) == 5  # Anaerobic


def test_zone_stats_calculation(power_zones, sample_metrics):
    """Test power zone statistics calculation."""
    stats = power_zones.calculate_zone_stats(sample_metrics)
    
    assert stats.total_time == 59  # 60 data points = 59 seconds of intervals
    assert len(stats.zone_times) == 6
    assert len(stats.zone_percentages) == 6
    
    # Check that percentages sum to approximately 100%
    assert sum(stats.zone_percentages) == pytest.approx(100.0)
    
    # Check zone transitions
    assert len(stats.transitions) > 0
    for from_zone, to_zone, timestamp in stats.transitions:
        assert 0 <= from_zone < 6
        assert 0 <= to_zone < 6
        assert from_zone != to_zone
        assert isinstance(timestamp, float)


def test_custom_zones():
    """Test using custom power zones."""
    custom_zones = [
        PowerZone("Easy", 0.0, 0.7, "Easy running"),
        PowerZone("Moderate", 0.7, 0.9, "Moderate effort"),
        PowerZone("Hard", 0.9, float('inf'), "Hard effort")
    ]
    
    power_zones = PowerZones(critical_power=3.5, zones=custom_zones)
    assert len(power_zones.zones) == 3
    
    # Test zone detection with custom zones
    assert power_zones.detect_zone(2.0) == 0  # Easy
    assert power_zones.detect_zone(2.8) == 1  # Moderate
    assert power_zones.detect_zone(3.5) == 2  # Hard


def test_empty_metrics(power_zones):
    """Test handling of empty metrics list."""
    stats = power_zones.calculate_zone_stats([])
    assert stats.total_time == 0
    assert stats.zone_times == []
    assert stats.zone_percentages == []
    assert stats.transitions == []


def test_metrics_without_power(power_zones):
    """Test handling of metrics without power data."""
    metrics = [
        RunningMetrics(
            timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
            distance=1000,
            duration=300,
            avg_pace=300,
            power=None
        )
    ]
    
    stats = power_zones.calculate_zone_stats(metrics)
    assert stats.total_time == 0
    assert all(time == 0 for time in stats.zone_times)
    assert all(pct == 0 for pct in stats.zone_percentages)
    assert stats.transitions == [] 