"""Validation module for running metrics data."""
from datetime import datetime, timezone
from typing import Optional

from .models import RunningMetrics


class DataValidationError(Exception):
    """Exception raised when data validation fails."""
    pass


def validate_metrics(metrics: RunningMetrics, is_raw_workout: bool = False) -> None:
    """Validate running metrics data.
    
    Args:
        metrics: RunningMetrics object to validate
        is_raw_workout: Whether the data is from raw workout format
        
    Raises:
        DataValidationError: If validation fails
    """
    # Validate timestamp
    now = datetime.now(timezone.utc)
    metrics_ts = metrics.timestamp
    if metrics_ts.tzinfo is None:
        metrics_ts = metrics_ts.replace(tzinfo=timezone.utc)
    
    print(f"Debug: now={now}, metrics_ts={metrics_ts}")  # Debug log
    
    if metrics_ts > now:
        raise DataValidationError("Timestamp cannot be in the future")

    # Validate distance (must be positive)
    if metrics.distance <= 0:
        raise DataValidationError("Distance must be positive")

    # Validate duration (must be positive)
    if metrics.duration <= 0:
        raise DataValidationError("Duration must be positive")

    # Validate avg_pace (must be positive)
    if metrics.avg_pace <= 0:
        raise DataValidationError("Average pace must be positive")

    # Different validation rules for raw workout data
    if is_raw_workout:
        # Raw workout data has different ranges
        if metrics.avg_heart_rate is not None and not 0 <= metrics.avg_heart_rate <= 30:
            raise DataValidationError("Heart rate must be between 0 and 30 (normalized)")
            
        if metrics.cadence is not None and not 0 <= metrics.cadence <= 30:
            raise DataValidationError("Cadence must be between 0 and 30 (normalized)")
            
        if metrics.temperature is not None and not -20 <= metrics.temperature <= 50:
            raise DataValidationError("Temperature must be between -20 and 50")
    else:
        # Standard validation rules
        if metrics.avg_heart_rate is not None:
            if not 30 <= metrics.avg_heart_rate <= 250:
                raise DataValidationError("Average heart rate must be between 30 and 250 bpm")

        if metrics.max_heart_rate is not None:
            if not 30 <= metrics.max_heart_rate <= 250:
                raise DataValidationError("Maximum heart rate must be between 30 and 250 bpm")

            # Max heart rate should be greater than or equal to average
            if metrics.avg_heart_rate is not None and metrics.max_heart_rate < metrics.avg_heart_rate:
                raise DataValidationError("Maximum heart rate cannot be less than average heart rate")

        # Validate elevation gain if present (must be non-negative)
        if metrics.elevation_gain is not None and metrics.elevation_gain < 0:
            raise DataValidationError("Elevation gain cannot be negative")

        # Validate calories if present (must be positive)
        if metrics.calories is not None and metrics.calories <= 0:
            raise DataValidationError("Calories must be positive")

        # Validate cadence if present (typical range 140-200 spm)
        if metrics.cadence is not None and not 100 <= metrics.cadence <= 250:
            raise DataValidationError("Cadence must be between 100 and 250 steps per minute")

        # Validate temperature if present (reasonable range -50 to 50 celsius)
        if metrics.temperature is not None and not -50 <= metrics.temperature <= 50:
            raise DataValidationError("Temperature must be between -50 and 50 celsius")

        # Validate calculated pace matches distance and duration
        calculated_pace = metrics.duration / (metrics.distance / 1000)  # seconds per kilometer
        if abs(calculated_pace - metrics.avg_pace) > 1:  # Allow 1 second tolerance
            raise DataValidationError("Average pace does not match distance and duration") 