"""Running form metrics analysis."""
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional, Tuple

from scipy import stats

from .models import RunningMetrics


@dataclass
class CadenceTrend:
    """Trend analysis for running cadence."""
    slope: float  # steps per minute per day
    r_value: float  # correlation coefficient
    p_value: float  # statistical significance
    trend_description: str  # human-readable trend description
    optimal_range: Tuple[float, float]  # recommended cadence range


@dataclass
class GroundTimeTrend:
    """Trend analysis for ground contact time."""
    slope: float  # milliseconds per day
    r_value: float  # correlation coefficient
    p_value: float  # statistical significance
    trend_description: str  # human-readable trend description
    optimal_range: Tuple[float, float]  # recommended ground time range
    balance: Optional[float] = None  # left/right balance if available


@dataclass
class VerticalMetrics:
    """Analysis of vertical movement metrics."""
    oscillation: float  # vertical oscillation in cm
    ratio: float  # vertical ratio (oscillation/step length)
    efficiency_score: float  # 0-100 score based on oscillation and ratio
    optimal_oscillation: Tuple[float, float]  # recommended oscillation range
    optimal_ratio: Tuple[float, float]  # recommended ratio range
    balance: Optional[float] = None  # left/right balance if available


@dataclass
class PowerEfficiency:
    """Analysis of running power efficiency."""
    total_power: float  # total power in watts/kg
    form_power: float  # form power in watts/kg
    air_power: float  # air power in watts/kg
    efficiency_ratio: float  # useful power / total power
    efficiency_score: float  # 0-100 score based on power distribution
    optimal_ratio: Tuple[float, float]  # recommended efficiency ratio range


class FormAnalyzer:
    """Analyzer for running form metrics."""

    # Optimal ranges based on research and Stryd recommendations
    CADENCE_RANGE = (170, 180)  # steps per minute
    GROUND_TIME_RANGE = (150, 200)  # milliseconds
    OSCILLATION_RANGE = (6.5, 8.5)  # centimeters
    VERTICAL_RATIO_RANGE = (0.06, 0.08)  # ratio
    POWER_EFFICIENCY_RANGE = (0.92, 0.96)  # ratio

    def __init__(self, metrics: List[RunningMetrics]):
        """Initialize form analyzer.
        
        Args:
            metrics: List of running metrics to analyze
        """
        self.metrics = sorted(metrics, key=lambda m: m.timestamp, reverse=True)  # Most recent first

    def analyze_cadence(self, window_days: int = 90) -> Optional[CadenceTrend]:
        """Analyze cadence trends over time.
        
        Args:
            window_days: Number of days to analyze
            
        Returns:
            CadenceTrend object or None if insufficient data
        """
        if not self.metrics or not any(m.cadence for m in self.metrics):
            return None

        # Filter metrics within window
        cutoff = self.metrics[0].timestamp - timedelta(days=window_days)
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff and m.cadence is not None
        ]
        
        if len(recent_metrics) < 2:
            return None

        # Sort chronologically for regression
        recent_metrics = sorted(recent_metrics, key=lambda m: m.timestamp)
        
        # Convert timestamps to days since earliest date
        earliest_time = recent_metrics[0].timestamp
        x = [(m.timestamp - earliest_time).total_seconds() / 86400 for m in recent_metrics]
        y = [m.cadence for m in recent_metrics]

        # Calculate linear regression
        slope, intercept, r_value, p_value, _ = stats.linregress(x, y)

        # Generate trend description
        if p_value > 0.05:
            description = "No significant trend detected"
        else:
            change_per_month = slope * 30  # steps per minute per month
            if abs(change_per_month) < 1:
                description = "Cadence is stable"
            elif change_per_month > 0:
                description = f"Cadence increasing by {change_per_month:.1f} spm per month"
            else:
                description = f"Cadence decreasing by {abs(change_per_month):.1f} spm per month"

        return CadenceTrend(
            slope=slope,
            r_value=r_value,
            p_value=p_value,
            trend_description=description,
            optimal_range=self.CADENCE_RANGE
        )

    def analyze_ground_time(self, window_days: int = 90) -> Optional[GroundTimeTrend]:
        """Analyze ground contact time trends.
        
        Args:
            window_days: Number of days to analyze
            
        Returns:
            GroundTimeTrend object or None if insufficient data
        """
        if not self.metrics or not any(m.ground_time for m in self.metrics):
            return None

        # Filter metrics within window
        cutoff = self.metrics[0].timestamp - timedelta(days=window_days)
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff and m.ground_time is not None
        ]
        
        if len(recent_metrics) < 2:
            return None

        # Sort chronologically for regression
        recent_metrics = sorted(recent_metrics, key=lambda m: m.timestamp)
        
        # Convert timestamps to days since earliest date
        earliest_time = recent_metrics[0].timestamp
        x = [(m.timestamp - earliest_time).total_seconds() / 86400 for m in recent_metrics]
        y = [m.ground_time for m in recent_metrics]

        # Calculate linear regression
        slope, intercept, r_value, p_value, _ = stats.linregress(x, y)

        # Calculate average balance if available
        balance = None
        balance_metrics = [m for m in recent_metrics if m.ground_time_balance is not None]
        if balance_metrics:
            balance = sum(m.ground_time_balance for m in balance_metrics) / len(balance_metrics)

        # Generate trend description
        if p_value > 0.05:
            description = "No significant trend detected"
        else:
            change_per_month = slope * 30  # milliseconds per month
            if abs(change_per_month) < 1:
                description = "Ground contact time is stable"
            elif change_per_month > 0:
                description = f"Ground time increasing by {change_per_month:.1f} ms per month"
            else:
                description = f"Ground time decreasing by {abs(change_per_month):.1f} ms per month"

        return GroundTimeTrend(
            slope=slope,
            r_value=r_value,
            p_value=p_value,
            trend_description=description,
            optimal_range=self.GROUND_TIME_RANGE,
            balance=balance
        )

    def analyze_vertical_metrics(self) -> Optional[VerticalMetrics]:
        """Analyze vertical oscillation and ratio.
        
        Returns:
            VerticalMetrics object or None if insufficient data
        """
        if not self.metrics:
            return None

        # Get recent metrics with vertical oscillation data
        recent_metrics = sorted(
            [m for m in self.metrics 
             if m.vertical_oscillation is not None and m.vertical_ratio is not None],
            key=lambda m: m.timestamp,
            reverse=True
        )[:10]  # Use last 10 activities

        if not recent_metrics:
            return None

        # Calculate averages
        avg_oscillation = sum(m.vertical_oscillation for m in recent_metrics) / len(recent_metrics)
        avg_ratio = sum(m.vertical_ratio for m in recent_metrics) / len(recent_metrics)

        # Calculate efficiency score (0-100)
        oscillation_score = self._calculate_range_score(
            avg_oscillation, self.OSCILLATION_RANGE[0], self.OSCILLATION_RANGE[1]
        )
        ratio_score = self._calculate_range_score(
            avg_ratio, self.VERTICAL_RATIO_RANGE[0], self.VERTICAL_RATIO_RANGE[1]
        )
        efficiency_score = (oscillation_score + ratio_score) / 2

        # Calculate average balance if available
        balance = None
        balance_metrics = [m for m in recent_metrics if m.vertical_oscillation_balance is not None]
        if balance_metrics:
            balance = (
                sum(m.vertical_oscillation_balance for m in balance_metrics) / 
                len(balance_metrics)
            )

        return VerticalMetrics(
            oscillation=avg_oscillation,
            ratio=avg_ratio,
            efficiency_score=efficiency_score,
            optimal_oscillation=self.OSCILLATION_RANGE,
            optimal_ratio=self.VERTICAL_RATIO_RANGE,
            balance=balance
        )

    def analyze_power_efficiency(self) -> Optional[PowerEfficiency]:
        """Analyze running power efficiency.
        
        Returns:
            PowerEfficiency object or None if insufficient data
        """
        if not self.metrics:
            return None

        # Get recent metrics with power data
        recent_metrics = sorted(
            [m for m in self.metrics 
             if all(x is not None for x in (m.power, m.form_power, m.air_power))],
            key=lambda m: m.timestamp,
            reverse=True
        )[:10]  # Use last 10 activities

        if not recent_metrics:
            return None

        # Calculate averages
        avg_total_power = sum(m.power for m in recent_metrics) / len(recent_metrics)
        avg_form_power = sum(m.form_power for m in recent_metrics) / len(recent_metrics)
        avg_air_power = sum(m.air_power for m in recent_metrics) / len(recent_metrics)

        # Calculate efficiency ratio (useful power / total power)
        # Useful power is total power minus form power and air power
        useful_power = avg_total_power - avg_form_power - avg_air_power
        efficiency_ratio = useful_power / avg_total_power if avg_total_power > 0 else 0

        # Calculate efficiency score (0-100)
        efficiency_score = self._calculate_range_score(
            efficiency_ratio,
            self.POWER_EFFICIENCY_RANGE[0],
            self.POWER_EFFICIENCY_RANGE[1]
        )

        return PowerEfficiency(
            total_power=avg_total_power,
            form_power=avg_form_power,
            air_power=avg_air_power,
            efficiency_ratio=efficiency_ratio,
            efficiency_score=efficiency_score,
            optimal_ratio=self.POWER_EFFICIENCY_RANGE
        )

    def _calculate_range_score(self, value: float, min_optimal: float, max_optimal: float) -> float:
        """Calculate a 0-100 score based on how close a value is to the optimal range.
        
        Args:
            value: Value to score
            min_optimal: Minimum of optimal range
            max_optimal: Maximum of optimal range
            
        Returns:
            Score from 0 to 100
        """
        if min_optimal <= value <= max_optimal:
            return 100.0  # In optimal range
        
        # Calculate how far outside the range
        if value < min_optimal:
            deviation = (min_optimal - value) / min_optimal
        else:
            deviation = (value - max_optimal) / max_optimal
        
        # Convert to score (100 = perfect, 0 = very far from optimal)
        score = 100 * (1 - min(deviation, 1.0))
        return max(0.0, score)  # Ensure non-negative 