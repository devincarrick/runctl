"""Training zone processor for calculating zones from workout data."""

from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from src.models.training_zones import PowerZones, HeartRateZones, PaceZones, TrainingZone, ZoneType
from src.models.workout import WorkoutData
from src.processors import DataProcessor, ProcessingContext

class ZoneProcessor(DataProcessor[WorkoutData, Dict[str, List[TrainingZone]]]):
    """Processor for calculating training zones."""
    
    # Zone boundaries as percentages of threshold values
    POWER_ZONES = [
        ("Recovery", 0.55, 0.75, "Very light intensity for recovery"),
        ("Endurance", 0.75, 0.88, "Aerobic endurance training"),
        ("Tempo", 0.88, 0.95, "Sustained effort at 'comfortably hard' pace"),
        ("Threshold", 0.95, 1.05, "Around critical power/threshold"),
        ("VO2Max", 1.05, 1.20, "High intensity intervals"),
        ("Anaerobic", 1.20, 1.50, "Very high intensity, short duration")
    ]
    
    HEART_RATE_ZONES = [
        ("Zone 1", 0.50, 0.60, "Very light aerobic activity"),
        ("Zone 2", 0.60, 0.70, "Light aerobic activity"),
        ("Zone 3", 0.70, 0.80, "Moderate aerobic activity"),
        ("Zone 4", 0.80, 0.90, "Hard aerobic activity"),
        ("Zone 5", 0.90, 1.00, "Maximum effort")
    ]
    
    PACE_ZONES = [
        ("Recovery", 1.25, 1.40, "Very easy running"),
        ("Easy", 1.15, 1.25, "Comfortable aerobic running"),
        ("Moderate", 1.08, 1.15, "Steady state running"),
        ("Threshold", 1.00, 1.08, "Comfortably hard/threshold"),
        ("Interval", 0.93, 1.00, "VO2max pace"),
        ("Speed", 0.85, 0.93, "Sprint/anaerobic work")
    ]
    
    def __init__(self, context: ProcessingContext) -> None:
        """Initialize zone processor with context."""
        self.context = context
        
    def validate(self, data: WorkoutData) -> bool:
        """Validate workout data for zone calculation."""
        if not isinstance(data, WorkoutData):
            logger.error("Input data must be WorkoutData instance")
            return False
            
        return True
        
    def process(self, workout: WorkoutData) -> Dict[str, List[TrainingZone]]:
        """Calculate training zones based on workout data.
        
        Args:
            workout: Workout data to process
            
        Returns:
            Dictionary mapping zone types to lists of training zones
        """
        zones: Dict[str, List[TrainingZone]] = {}
        
        # Calculate power zones if power data is available
        if workout.average_power is not None and workout.average_power > 0:
            logger.info(f"Calculated power zones based on {workout.average_power} watts")
            zones['power'] = [
                TrainingZone(
                    name=name,
                    lower_bound=workout.average_power * lower,
                    upper_bound=workout.average_power * upper,
                    description=desc,
                    zone_type=ZoneType.POWER
                )
                for name, lower, upper, desc in self.POWER_ZONES
            ]
            
        # Calculate heart rate zones if HR data is available
        if workout.heart_rate is not None and workout.heart_rate > 0:
            logger.info(f"Calculated heart rate zones based on {workout.heart_rate} bpm")
            zones['heart_rate'] = [
                TrainingZone(
                    name=name,
                    lower_bound=workout.heart_rate * lower,
                    upper_bound=workout.heart_rate * upper,
                    description=desc,
                    zone_type=ZoneType.HEART_RATE
                )
                for name, lower, upper, desc in self.HEART_RATE_ZONES
            ]
            
        # Calculate pace zones if pace data is available
        if workout.average_pace is not None and workout.average_pace > 0:
            logger.info(f"Calculated pace zones based on {workout.average_pace} sec/km")
            zones['pace'] = [
                TrainingZone(
                    name=name,
                    lower_bound=workout.average_pace * lower,
                    upper_bound=workout.average_pace * upper,
                    description=desc,
                    zone_type=ZoneType.PACE
                )
                for name, lower, upper, desc in self.PACE_ZONES
            ]
            
        return zones 