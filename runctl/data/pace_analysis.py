"""Pace analysis and predictions."""
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional

from scipy import stats

from .models import RunningMetrics


@dataclass
class PaceTrend:
    """Trend analysis for running paces."""
    slope: float  # seconds per kilometer per day
    r_value: float  # correlation coefficient
    p_value: float  # statistical significance
    trend_description: str  # human-readable trend description


@dataclass
class RacePrediction:
    """Race time predictions for common distances."""
    distance: float  # meters
    predicted_time: float  # seconds
    predicted_pace: float  # seconds per kilometer
    confidence: float  # prediction confidence (0-1)


@dataclass
class TrainingPaces:
    """Recommended training paces for different workouts."""
    easy_pace: float  # seconds per kilometer
    tempo_pace: float  # seconds per kilometer
    threshold_pace: float  # seconds per kilometer
    interval_pace: float  # seconds per kilometer
    repetition_pace: float  # seconds per kilometer


class PaceAnalyzer:
    """Analyzer for running paces and predictions."""

    # Common race distances in meters
    RACE_DISTANCES = {
        "5K": 5000,
        "10K": 10000,
        "Half Marathon": 21097.5,
        "Marathon": 42195
    }

    def __init__(self, metrics: List[RunningMetrics]):
        """Initialize pace analyzer.
        
        Args:
            metrics: List of running metrics to analyze
        """
        self.metrics = sorted(metrics, key=lambda m: m.timestamp, reverse=True)  # Most recent first

    def analyze_trend(self, window_days: int = 90) -> Optional[PaceTrend]:
        """Analyze pace trends over time.
        
        Args:
            window_days: Number of days to analyze
            
        Returns:
            PaceTrend object or None if insufficient data
        """
        if not self.metrics:
            return None

        # Filter metrics within window
        cutoff = self.metrics[0].timestamp - timedelta(days=window_days)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]
        
        if len(recent_metrics) < 2:
            return None

        # Sort chronologically for regression
        recent_metrics = sorted(
            recent_metrics, 
            key=lambda m: m.timestamp, 
            reverse=True
        )  # Most recent first
        
        # Convert timestamps to days since earliest date
        latest_time = recent_metrics[0].timestamp
        x = [(latest_time - m.timestamp).total_seconds() / 86400 
             for m in recent_metrics]  # Days ago
        y = [m.avg_pace for m in recent_metrics]

        # Calculate linear regression
        slope, intercept, r_value, p_value, _ = stats.linregress(x, y)

        # Generate trend description
        if p_value > 0.05:
            description = "No significant trend detected"
        else:
            change_per_month = slope * 30  # seconds per km per month
            if abs(change_per_month) < 1:
                description = "Pace is stable"
            elif change_per_month > 0:
                description = f"Slowing by {change_per_month:.1f} sec/km per month"
            else:
                description = f"Improving by {abs(change_per_month):.1f} sec/km per month"

        return PaceTrend(slope, r_value, p_value, description)

    def predict_race_times(self) -> Dict[str, RacePrediction]:
        """Predict race times for common distances using recent performances.
        
        Returns:
            Dictionary mapping race names to RacePrediction objects
        """
        if not self.metrics:
            return {}

        # Find best recent performance (within last 90 days)
        cutoff = self.metrics[0].timestamp - timedelta(days=90)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]
        
        if not recent_metrics:
            return {}

        # Find fastest pace for distances > 3km
        best_metric = min(
            (m for m in recent_metrics if m.distance >= 3000),
            key=lambda m: m.avg_pace,
            default=None
        )
        
        if not best_metric:
            return {}

        predictions = {}
        base_distance = best_metric.distance
        base_time = best_metric.duration

        # Use Riegel's formula: T2 = T1 * (D2/D1)^1.06
        for name, distance in self.RACE_DISTANCES.items():
            predicted_time = base_time * (distance / base_distance) ** 1.06
            predicted_pace = predicted_time / (distance / 1000)
            
            # Calculate confidence based on distance difference
            distance_ratio = min(base_distance, distance) / max(base_distance, distance)
            confidence = distance_ratio ** 0.5  # Decreases as distance difference increases
            
            predictions[name] = RacePrediction(
                distance=distance,
                predicted_time=predicted_time,
                predicted_pace=predicted_pace,
                confidence=confidence
            )

        return predictions

    def calculate_training_paces(self) -> Optional[TrainingPaces]:
        """Calculate recommended training paces based on recent performances.
        
        Returns:
            TrainingPaces object or None if insufficient data
        """
        if not self.metrics:
            return None

        # Find recent threshold pace (best 20-30 minute effort)
        cutoff = self.metrics[0].timestamp - timedelta(days=90)
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff and 1200 <= m.duration <= 1800
        ]
        
        if not recent_metrics:
            # Return None if no threshold efforts found
            return None

        # Check if any of the metrics are actually threshold efforts
        # A threshold effort should be sustained for at least 20 minutes
        # and we need at least 2 threshold efforts to establish a reliable pace
        threshold_metrics = [
            m for m in recent_metrics 
            if m.duration >= 1200  # At least 20 minutes
        ]
        
        if len(threshold_metrics) < 2:  # Need at least 2 threshold efforts
            return None

        threshold_pace = min(m.avg_pace for m in threshold_metrics)
        
        # Calculate training paces based on threshold pace
        # Using common training pace calculators' formulas
        return TrainingPaces(
            easy_pace=threshold_pace * 1.3,  # 30% slower than threshold
            tempo_pace=threshold_pace * 1.1,  # 10% slower than threshold
            threshold_pace=threshold_pace,
            interval_pace=threshold_pace * 0.95,  # 5% faster than threshold
            repetition_pace=threshold_pace * 0.9   # 10% faster than threshold
        ) 