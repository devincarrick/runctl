"""Tests for pace analysis."""
from datetime import datetime, timedelta, timezone

import pytest

from runctl.data.models import RunningMetrics
from runctl.data.pace_analysis import PaceAnalyzer


@pytest.fixture
def sample_metrics():
    """Create a list of sample metrics with varying paces."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics = []
    
    # Create 10 sessions over 90 days with improving pace
    for i in range(10):
        metrics.append(RunningMetrics(
            timestamp=base_time - timedelta(days=i * 9),  # Every 9 days
            distance=5000,  # 5 km
            duration=1500 - i * 30,  # Starting at 25:00, improving by 30s each time
            avg_pace=300 - i * 6  # Starting at 5:00/km, improving by 6s/km each time
        ))
    
    return metrics


@pytest.fixture
def race_metrics():
    """Create metrics with a recent good performance for race predictions."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    
    return [
        RunningMetrics(
            timestamp=base_time - timedelta(days=30),
            distance=5000,  # 5K
            duration=1200,  # 20:00
            avg_pace=240  # 4:00/km
        ),
        RunningMetrics(
            timestamp=base_time - timedelta(days=7),
            distance=10000,  # 10K
            duration=2520,  # 42:00
            avg_pace=252  # 4:12/km
        )
    ]


@pytest.fixture
def threshold_metrics():
    """Create metrics with recent threshold efforts."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    
    return [
        # 25-minute threshold run
        RunningMetrics(
            timestamp=base_time - timedelta(days=7),
            distance=7000,
            duration=1500,  # 25:00
            avg_pace=214.3  # ~3:34/km
        ),
        # 20-minute threshold run
        RunningMetrics(
            timestamp=base_time - timedelta(days=14),
            distance=5600,
            duration=1200,  # 20:00
            avg_pace=214.3  # ~3:34/km
        )
    ]


def test_pace_trend_analysis(sample_metrics):
    """Test pace trend analysis."""
    analyzer = PaceAnalyzer(sample_metrics)
    trend = analyzer.analyze_trend()
    
    assert trend is not None
    assert trend.slope < 0  # Negative slope (improving)
    assert abs(trend.r_value) > 0.9  # Strong correlation
    assert trend.p_value < 0.05  # Statistically significant
    assert "Improving" in trend.trend_description


def test_race_predictions(race_metrics):
    """Test race time predictions."""
    analyzer = PaceAnalyzer(race_metrics)
    predictions = analyzer.predict_race_times()
    
    assert len(predictions) == 4  # 5K, 10K, Half, Marathon
    
    # Check 5K prediction
    assert "5K" in predictions
    p5k = predictions["5K"]
    assert p5k.distance == 5000
    assert 1150 < p5k.predicted_time < 1250  # ~20:00
    assert p5k.confidence > 0.9  # High confidence (recent 5K)
    
    # Check marathon prediction
    assert "Marathon" in predictions
    marathon = predictions["Marathon"]
    assert marathon.distance == 42195
    assert marathon.confidence < 0.5  # Lower confidence (much longer)


def test_training_paces(threshold_metrics):
    """Test training pace calculations."""
    analyzer = PaceAnalyzer(threshold_metrics)
    paces = analyzer.calculate_training_paces()
    
    assert paces is not None
    assert paces.threshold_pace == pytest.approx(214.3)  # From test data
    assert paces.easy_pace > paces.threshold_pace  # Easy is slower
    assert paces.repetition_pace < paces.threshold_pace  # Reps are faster


def test_empty_metrics():
    """Test handling of empty metrics list."""
    analyzer = PaceAnalyzer([])
    
    assert analyzer.analyze_trend() is None
    assert analyzer.predict_race_times() == {}
    assert analyzer.calculate_training_paces() is None


def test_insufficient_data():
    """Test handling of insufficient data."""
    # Single data point
    metrics = [RunningMetrics(
        timestamp=datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc),
        distance=5000,
        duration=1500,
        avg_pace=300
    )]
    
    analyzer = PaceAnalyzer(metrics)
    
    assert analyzer.analyze_trend() is None  # Need at least 2 points
    assert analyzer.predict_race_times() != {}  # Can still predict
    assert analyzer.calculate_training_paces() is None  # No threshold efforts


def test_old_data_filtering():
    """Test filtering of old data."""
    base_time = datetime(2024, 2, 19, 8, 30, tzinfo=timezone.utc)
    metrics = [
        # Recent run
        RunningMetrics(
            timestamp=base_time,
            distance=5000,
            duration=1500,
            avg_pace=300
        ),
        # Old run (120 days ago)
        RunningMetrics(
            timestamp=base_time - timedelta(days=120),
            distance=5000,
            duration=1400,
            avg_pace=280
        )
    ]
    
    analyzer = PaceAnalyzer(metrics)
    trend = analyzer.analyze_trend()
    
    assert trend is None  # Only one recent data point 