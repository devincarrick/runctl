"""Tests for running form analysis."""
from datetime import datetime, timedelta, timezone

import pytest

from runctl.data.form_analysis import FormAnalyzer
from runctl.data.models import RunningMetrics


@pytest.fixture
def sample_metrics():
    """Create a list of sample metrics with form data."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics = []
    
    # Create 10 sessions over 90 days with improving form
    for i in range(10):
        metrics.append(RunningMetrics(
            timestamp=base_time - timedelta(days=(9 - i) * 9),  # Every 9 days, forward in time
            distance=5000,  # 5 km
            duration=1500,  # 25:00
            avg_pace=300,  # 5:00/km
            cadence=170 + i * 0.5,  # Starting at 170, increasing by 0.5 spm
            ground_time=200 - i * 2,  # Starting at 200ms, decreasing by 2ms
            vertical_oscillation=8.0 - i * 0.1,  # Starting at 8.0cm, decreasing
            vertical_ratio=0.08 - i * 0.001,  # Starting at 0.08, decreasing
            power=3.5,  # watts/kg
            form_power=0.2,  # watts/kg (reduced for better efficiency)
            air_power=0.05,  # watts/kg (reduced for better efficiency)
            ground_time_balance=50.0,  # perfect balance
            vertical_oscillation_balance=50.0,  # perfect balance
            leg_spring_stiffness_balance=50.0  # perfect balance
        ))
    
    return metrics  # Already in chronological order


@pytest.fixture
def imbalanced_metrics():
    """Create metrics with form imbalances."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics = []
    
    # Create 5 sessions with imbalances
    for i in range(5):
        metrics.append(RunningMetrics(
            timestamp=base_time - timedelta(days=(4 - i) * 2),  # Forward in time
            distance=5000,
            duration=1500,
            avg_pace=300,
            cadence=175,
            ground_time=180,
            vertical_oscillation=7.5,
            vertical_ratio=0.07,
            power=3.5,
            form_power=0.2,
            air_power=0.05,
            ground_time_balance=45.0,  # Left side dominant
            vertical_oscillation_balance=48.0,  # Slight left bias
            leg_spring_stiffness_balance=52.0  # Slight right bias
        ))
    
    return metrics


def test_cadence_trend_analysis(sample_metrics):
    """Test cadence trend analysis."""
    analyzer = FormAnalyzer(sample_metrics)
    trend = analyzer.analyze_cadence()
    
    assert trend is not None
    assert trend.slope > 0  # Increasing trend
    assert abs(trend.r_value) > 0.9  # Strong correlation
    assert trend.p_value < 0.05  # Statistically significant
    assert "increasing" in trend.trend_description.lower()
    assert trend.optimal_range == (170, 180)


def test_ground_time_trend(sample_metrics):
    """Test ground contact time trend analysis."""
    analyzer = FormAnalyzer(sample_metrics)
    trend = analyzer.analyze_ground_time()
    
    assert trend is not None
    assert trend.slope < 0  # Decreasing trend
    assert abs(trend.r_value) > 0.9  # Strong correlation
    assert trend.p_value < 0.05  # Statistically significant
    assert "decreasing" in trend.trend_description.lower()
    assert trend.optimal_range == (150, 200)
    assert trend.balance == 50.0  # Perfect balance


def test_vertical_metrics(sample_metrics):
    """Test vertical oscillation and ratio analysis."""
    analyzer = FormAnalyzer(sample_metrics)
    metrics = analyzer.analyze_vertical_metrics()
    
    assert metrics is not None
    assert 6.5 <= metrics.oscillation <= 8.5  # Within optimal range
    assert 0.06 <= metrics.ratio <= 0.08  # Within optimal range
    assert metrics.efficiency_score > 90  # High efficiency
    assert metrics.optimal_oscillation == (6.5, 8.5)
    assert metrics.optimal_ratio == (0.06, 0.08)
    assert metrics.balance == 50.0  # Perfect balance


def test_power_efficiency(sample_metrics):
    """Test power efficiency analysis."""
    analyzer = FormAnalyzer(sample_metrics)
    efficiency = analyzer.analyze_power_efficiency()
    
    assert efficiency is not None
    assert efficiency.total_power == 3.5
    assert efficiency.form_power == 0.2
    assert efficiency.air_power == 0.05
    assert 0.92 <= efficiency.efficiency_ratio <= 0.96  # Within optimal range
    assert efficiency.efficiency_score > 90  # High efficiency
    assert efficiency.optimal_ratio == (0.92, 0.96)


def test_form_imbalances(imbalanced_metrics):
    """Test detection of form imbalances."""
    analyzer = FormAnalyzer(imbalanced_metrics)
    
    # Check ground time balance
    ground_trend = analyzer.analyze_ground_time()
    assert ground_trend is not None
    assert ground_trend.balance < 50.0  # Left side dominant
    
    # Check vertical metrics balance
    vertical = analyzer.analyze_vertical_metrics()
    assert vertical is not None
    assert vertical.balance < 50.0  # Left side bias


def test_empty_metrics():
    """Test handling of empty metrics list."""
    analyzer = FormAnalyzer([])
    
    assert analyzer.analyze_cadence() is None
    assert analyzer.analyze_ground_time() is None
    assert analyzer.analyze_vertical_metrics() is None
    assert analyzer.analyze_power_efficiency() is None


def test_insufficient_data():
    """Test handling of insufficient data."""
    # Single data point
    metrics = [RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=5000,
        duration=1500,
        avg_pace=300,
        cadence=175,
        ground_time=180,
        vertical_oscillation=7.5,
        vertical_ratio=0.07
    )]
    
    analyzer = FormAnalyzer(metrics)
    
    assert analyzer.analyze_cadence() is None  # Need at least 2 points
    assert analyzer.analyze_ground_time() is None  # Need at least 2 points
    assert analyzer.analyze_vertical_metrics() is not None  # Can analyze single point
    assert analyzer.analyze_power_efficiency() is None  # Missing power data


def test_range_score_calculation():
    """Test the range score calculation."""
    analyzer = FormAnalyzer([])  # Empty list is fine for this test
    
    # Test value within range
    assert analyzer._calculate_range_score(175, 170, 180) == 100.0
    
    # Test value below range
    score = analyzer._calculate_range_score(160, 170, 180)
    assert 0 < score < 100
    
    # Test value above range
    score = analyzer._calculate_range_score(190, 170, 180)
    assert 0 < score < 100
    
    # Test extreme values
    assert analyzer._calculate_range_score(0, 170, 180) == 0.0
    assert analyzer._calculate_range_score(1000, 170, 180) == 0.0 