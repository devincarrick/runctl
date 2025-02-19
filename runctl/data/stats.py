"""Statistics module for analyzing running data."""
from dataclasses import dataclass
from typing import List, Optional

from .models import RunningMetrics


@dataclass
class SessionStats:
    """Statistics for a collection of running sessions."""
    total_distance: float  # meters
    total_duration: float  # seconds
    avg_pace: float  # seconds per kilometer
    fastest_pace: float  # seconds per kilometer
    slowest_pace: float  # seconds per kilometer
    morning_runs: int  # before 12:00
    afternoon_runs: int  # 12:00-17:00
    evening_runs: int  # after 17:00


def calculate_stats(sessions: List[RunningMetrics]) -> Optional[SessionStats]:
    """Calculate statistics for a list of running sessions.
    
    Args:
        sessions: List of running sessions to analyze
        
    Returns:
        SessionStats object or None if no sessions provided
    """
    if not sessions:
        return None
    
    total_distance = sum(session.distance for session in sessions)
    total_duration = sum(session.duration for session in sessions)
    avg_pace = total_duration / (total_distance / 1000) if total_distance > 0 else 0
    
    paces = [session.avg_pace for session in sessions]
    fastest_pace = min(paces) if paces else 0
    slowest_pace = max(paces) if paces else 0
    
    morning_runs = sum(1 for s in sessions if s.timestamp.hour < 12)
    afternoon_runs = sum(1 for s in sessions if 12 <= s.timestamp.hour < 17)
    evening_runs = sum(1 for s in sessions if s.timestamp.hour >= 17)
    
    return SessionStats(
        total_distance=total_distance,
        total_duration=total_duration,
        avg_pace=avg_pace,
        fastest_pace=fastest_pace,
        slowest_pace=slowest_pace,
        morning_runs=morning_runs,
        afternoon_runs=afternoon_runs,
        evening_runs=evening_runs
    ) 