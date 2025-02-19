"""Tests for the statistics module."""
from datetime import datetime, timezone

from runctl.data.models import RunningMetrics
from runctl.data.stats import calculate_stats


def test_calculate_stats_empty():
    """Test statistics calculation with empty list."""
    assert calculate_stats([]) is None


def test_calculate_stats():
    """Test statistics calculation with sample sessions."""
    sessions = [
        RunningMetrics(
            timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
            distance=5000,  # 5 km
            duration=1500,  # 25 minutes
            avg_pace=300,  # 5:00 min/km
            avg_heart_rate=150,
            max_heart_rate=170,
            elevation_gain=100,
            calories=500,
            cadence=180,
            temperature=20
        ),
        RunningMetrics(
            timestamp=datetime(2024, 2, 19, 14, 30, tzinfo=timezone.utc),
            distance=10000,  # 10 km
            duration=3000,  # 50 minutes
            avg_pace=300,  # 5:00 min/km
            avg_heart_rate=155,
            max_heart_rate=175,
            elevation_gain=200,
            calories=1000,
            cadence=185,
            temperature=22
        ),
        RunningMetrics(
            timestamp=datetime(2024, 2, 19, 18, 30, tzinfo=timezone.utc),
            distance=3000,  # 3 km
            duration=900,  # 15 minutes
            avg_pace=300,  # 5:00 min/km
            avg_heart_rate=145,
            max_heart_rate=165,
            elevation_gain=50,
            calories=300,
            cadence=175,
            temperature=18
        )
    ]
    
    stats = calculate_stats(sessions)
    
    assert stats is not None
    assert stats.total_distance == 18000  # 18 km
    assert stats.total_duration == 5400  # 90 minutes
    assert stats.avg_pace == 300  # 5:00 min/km
    assert stats.fastest_pace == 300
    assert stats.slowest_pace == 300
    assert stats.morning_runs == 1
    assert stats.afternoon_runs == 1
    assert stats.evening_runs == 1


def test_calculate_stats_single_session():
    """Test statistics calculation with a single session."""
    session = RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=5000,  # 5 km
        duration=1500,  # 25 minutes
        avg_pace=300,  # 5:00 min/km
        avg_heart_rate=150,
        max_heart_rate=170,
        elevation_gain=100,
        calories=500,
        cadence=180,
        temperature=20
    )
    
    stats = calculate_stats([session])
    
    assert stats is not None
    assert stats.total_distance == 5000
    assert stats.total_duration == 1500
    assert stats.avg_pace == 300
    assert stats.fastest_pace == 300
    assert stats.slowest_pace == 300
    assert stats.morning_runs == 1
    assert stats.afternoon_runs == 0
    assert stats.evening_runs == 0


def test_calculate_stats_zero_values():
    """Test statistics calculation with zero values."""
    session = RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=0,
        duration=0,
        avg_pace=0,
        avg_heart_rate=None,
        max_heart_rate=None,
        elevation_gain=None,
        calories=None,
        cadence=None,
        temperature=None
    )
    
    stats = calculate_stats([session])
    
    assert stats is not None
    assert stats.total_distance == 0
    assert stats.total_duration == 0
    assert stats.avg_pace == 0
    assert stats.fastest_pace == 0
    assert stats.slowest_pace == 0
    assert stats.morning_runs == 1
    assert stats.afternoon_runs == 0
    assert stats.evening_runs == 0 