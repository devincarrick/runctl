"""Validation module for running metrics data."""
from datetime import datetime, timezone

from .models import RunningMetrics


class DataValidationError(Exception):
    """Exception raised for validation errors in running metrics data."""
    pass


def validate_metrics(metrics: RunningMetrics, is_raw_workout: bool = False) -> None:
    """Validate running metrics data.
    
    Args:
        metrics: The metrics to validate
        is_raw_workout: Whether the metrics are from a raw workout format
        
    Raises:
        DataValidationError: If validation fails
    """
    try:
        # Validate timestamp (must be in the past)
        current_time = datetime.now(timezone.utc)
        if metrics.timestamp > current_time:
            raise DataValidationError("Timestamp cannot be in the future")
        
        # Validate distance (must be non-negative)
        if metrics.distance < 0:
            raise DataValidationError("Distance cannot be negative")
        
        # Validate duration (must be non-negative)
        if metrics.duration < 0:
            raise DataValidationError("Duration cannot be negative")
        
        # Validate pace (must be non-negative)
        if metrics.avg_pace < 0:
            raise DataValidationError("Pace cannot be negative")
        
        if not is_raw_workout:
            # Validate heart rate (must be in reasonable range)
            if metrics.avg_heart_rate is not None:
                if not 30 <= metrics.avg_heart_rate <= 250:
                    raise DataValidationError(
                        "Average heart rate must be between 30 and 250 bpm"
                    )
            
            if metrics.max_heart_rate is not None:
                if not 30 <= metrics.max_heart_rate <= 250:
                    raise DataValidationError(
                        "Maximum heart rate must be between 30 and 250 bpm"
                    )
                
                # Max heart rate should be greater than or equal to average
                if (metrics.avg_heart_rate is not None and 
                    metrics.max_heart_rate < metrics.avg_heart_rate):
                    raise DataValidationError(
                        "Maximum heart rate cannot be less than average heart rate"
                    )
        
        # Validate elevation gain if present (must be non-negative)
        if metrics.elevation_gain is not None and metrics.elevation_gain < 0:
            raise DataValidationError("Elevation gain cannot be negative")
        
        # Validate calories if present (must be non-negative)
        if metrics.calories is not None and metrics.calories < 0:
            raise DataValidationError("Calories cannot be negative")
        
        # Validate cadence if present (must be non-negative)
        if metrics.cadence is not None and metrics.cadence < 0:
            raise DataValidationError("Cadence cannot be negative")
        
        # Validate raw workout values
        if is_raw_workout:
            if metrics.avg_heart_rate is not None and not 0 <= metrics.avg_heart_rate <= 30:
                raise DataValidationError(
                    "Heart rate must be between 0 and 30 (normalized)"
                )
            if metrics.cadence is not None and not 0 <= metrics.cadence <= 1:
                raise DataValidationError(
                    "Cadence must be between 0 and 1 (normalized)"
                )
    
    except DataValidationError:
        raise
    except Exception as e:
        raise DataValidationError(f"Validation error: {e}") from e 