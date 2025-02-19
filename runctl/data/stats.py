"""Basic statistical analysis for running data."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from .models import RunningSession


@dataclass
class SessionStats:
    """Basic statistics for a collection of running sessions."""
    total_distance: float  # meters
    total_duration: float  # seconds
    avg_pace: float  # seconds per km
    fastest_pace: float  # seconds per km
    slowest_pace: float  # seconds per km
    morning_runs: int  # before 12:00
    afternoon_runs: int  # 12:00-17:00
    evening_runs: int  # after 17:00


def calculate_stats(sessions: List[RunningSession]) -> Optional[SessionStats]:
    """Calculate basic statistics for a list of running sessions.
    
    Args:
        sessions: List of running sessions to analyze
        
    Returns:
        SessionStats: Calculated statistics, or None if no valid sessions
    """
    if not sessions:
        return None

    # Initialize accumulators
    total_distance = 0.0
    total_duration = 0.0
    paces = []
    morning = 0
    afternoon = 0
    evening = 0

    # Process each session
    for session in sessions:
        metrics = session.metrics
        total_distance += metrics.distance
        total_duration += metrics.duration
        if metrics.avg_pace > 0:  # Exclude zero paces
            paces.append(metrics.avg_pace)
        
        # Time of day classification
        hour = metrics.timestamp.hour
        if hour < 12:
            morning += 1
        elif hour < 17:
            afternoon += 1
        else:
            evening += 1

    # Calculate averages and ranges
    avg_pace = total_duration / (total_distance / 1000) if total_distance > 0 else 0
    fastest_pace = min(paces) if paces else 0
    slowest_pace = max(paces) if paces else 0

    return SessionStats(
        total_distance=total_distance,
        total_duration=total_duration,
        avg_pace=avg_pace,
        fastest_pace=fastest_pace,
        slowest_pace=slowest_pace,
        morning_runs=morning,
        afternoon_runs=afternoon,
        evening_runs=evening
    ) 