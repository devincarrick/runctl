"""Tests for running statistics calculations."""
from datetime import datetime, timezone

import pytest

from runctl.data.models import RunningMetrics, RunningSession
from runctl.data.stats import calculate_stats


@pytest.fixture
def sample_sessions():
    """Create sample running sessions for testing."""
    sessions = []
    
    # Morning run
    sessions.append(RunningSession(
        id="RUN_1",
        metrics=RunningMetrics(
            timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
            distance=5000,  # 5km
            duration=1500,  # 25min
            avg_pace=300,   # 5:00/km
        )
    ))
    
    # Afternoon run
    sessions.append(RunningSession(
        id="RUN_2",
        metrics=RunningMetrics(
            timestamp=datetime(2024, 2, 19, 14, 30, tzinfo=timezone.utc),
            distance=10000,  # 10km
            duration=2700,   # 45min
            avg_pace=270,    # 4:30/km
        )
    ))
    
    # Evening run
    sessions.append(RunningSession(
        id="RUN_3",
        metrics=RunningMetrics(
            timestamp=datetime(2024, 2, 19, 19, 30, tzinfo=timezone.utc),
            distance=3000,   # 3km
            duration=900,    # 15min
            avg_pace=300,    # 5:00/km
        )
    ))
    
    return sessions


def test_calculate_stats_empty():
    """Test statistics calculation with empty session list."""
    assert calculate_stats([]) is None


def test_calculate_stats(sample_sessions):
    """Test statistics calculation with sample sessions."""
    stats = calculate_stats(sample_sessions)
    assert stats is not None
    
    # Test totals
    assert stats.total_distance == 18000  # 5km + 10km + 3km = 18km
    assert stats.total_duration == 5100   # 25min + 45min + 15min = 85min
    
    # Test paces
    assert stats.avg_pace == pytest.approx(283.33, rel=0.01)  # ~4:43/km
    assert stats.fastest_pace == 270  # 4:30/km
    assert stats.slowest_pace == 300  # 5:00/km
    
    # Test time distribution
    assert stats.morning_runs == 1
    assert stats.afternoon_runs == 1
    assert stats.evening_runs == 1


def test_calculate_stats_single_session():
    """Test statistics calculation with a single session."""
    session = RunningSession(
        id="RUN_1",
        metrics=RunningMetrics(
            timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
            distance=5000,
            duration=1500,
            avg_pace=300,
        )
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
    session = RunningSession(
        id="RUN_1",
        metrics=RunningMetrics(
            timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
            distance=0,
            duration=0,
            avg_pace=0,
        )
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