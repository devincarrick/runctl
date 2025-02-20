"""Power zone calculations and analysis."""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .models import RunningMetrics


@dataclass
class PowerZone:
    """Power zone definition."""
    name: str
    lower_bound: float  # in watts/kg
    upper_bound: float  # in watts/kg
    description: str


@dataclass
class PowerZoneStats:
    """Statistics for time spent in power zones."""
    total_time: float  # in seconds
    zone_times: List[float]  # time in each zone in seconds
    zone_percentages: List[float]  # percentage of time in each zone
    transitions: List[Tuple[int, int, float]]  # (from_zone, to_zone, timestamp)


class PowerZones:
    """Power zone calculator and analyzer."""

    # Default power zones based on Stryd's recommendations
    # These are percentage ranges of Critical Power (CP)
    DEFAULT_ZONES = [
        PowerZone("Recovery", 0.0, 0.80, "Very easy, recovery runs"),
        PowerZone("Endurance", 0.80, 0.88, "Easy aerobic runs"),
        PowerZone("Tempo", 0.88, 0.95, "Marathon/half-marathon pace"),
        PowerZone("Threshold", 0.95, 1.05, "Lactate threshold runs"),
        PowerZone("VO2max", 1.05, 1.15, "High-intensity intervals"),
        PowerZone("Anaerobic", 1.15, float('inf'), "Sprint/power development")
    ]

    def __init__(self, critical_power: float, zones: Optional[List[PowerZone]] = None):
        """Initialize power zone calculator.
        
        Args:
            critical_power: Critical Power in watts/kg
            zones: Optional custom power zones, defaults to Stryd zones
        """
        self.critical_power = critical_power
        self.zones = []
        
        # Create a deep copy of zones to avoid modifying the original
        for zone in zones or self.DEFAULT_ZONES:
            self.zones.append(PowerZone(
                name=zone.name,
                lower_bound=zone.lower_bound * critical_power,
                upper_bound=zone.upper_bound * critical_power,
                description=zone.description
            ))

    def detect_zone(self, power: float) -> int:
        """Detect which power zone a power value falls into.
        
        Args:
            power: Power value in watts/kg
            
        Returns:
            Zone index (0-based)
        """
        for i, zone in enumerate(self.zones):
            if zone.lower_bound <= power < zone.upper_bound:
                return i
        return len(self.zones) - 1  # Return highest zone if above all bounds

    def calculate_zone_stats(self, metrics: List[RunningMetrics]) -> PowerZoneStats:
        """Calculate power zone statistics for a list of metrics.
        
        Args:
            metrics: List of running metrics with power data
            
        Returns:
            PowerZoneStats object with zone statistics
        """
        if not metrics:
            return PowerZoneStats(0, [], [], [])

        total_time = 0
        zone_times = [0.0] * len(self.zones)
        transitions = []
        current_zone = None
        
        # Calculate time in each zone and detect transitions
        for i, metric in enumerate(metrics):
            if metric.power is None:
                continue
                
            zone = self.detect_zone(metric.power)
            
            # Record zone transition
            if current_zone is not None and zone != current_zone:
                transitions.append((current_zone, zone, metric.timestamp.timestamp()))
            
            # Calculate time in zone
            if i < len(metrics) - 1:
                time_delta = (metrics[i + 1].timestamp - metric.timestamp).total_seconds()
                zone_times[zone] += time_delta
                total_time += time_delta
            
            current_zone = zone

        # Calculate percentages
        zone_percentages = [
            (time / total_time * 100) if total_time > 0 else 0
            for time in zone_times
        ]

        return PowerZoneStats(total_time, zone_times, zone_percentages, transitions)

    def get_zone_ranges(self) -> List[Tuple[str, float, float, str]]:
        """Get the power zone ranges.
        
        Returns:
            List of tuples (name, lower_bound, upper_bound, description)
        """
        return [(z.name, z.lower_bound, z.upper_bound, z.description) 
                for z in self.zones] 