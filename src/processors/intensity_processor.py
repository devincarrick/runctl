"""Processor for calculating workout intensity scores based on training zones."""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from src.models.training_zones import TrainingZone
from src.models.workout import WorkoutData
from src.processors import DataProcessor, ProcessingContext

class IntensityScore:
    """Model for workout intensity scores."""
    
    def __init__(
        self,
        overall_score: float,
        zone_distribution: Dict[str, float],
        primary_zone: str,
        training_load: float
    ) -> None:
        """Initialize intensity score.
        
        Args:
            overall_score: Overall intensity score (0-100)
            zone_distribution: Percentage of time spent in each zone
            primary_zone: The zone where most time was spent
            training_load: Estimated training load/stress score
        """
        self.overall_score = overall_score
        self.zone_distribution = zone_distribution
        self.primary_zone = primary_zone
        self.training_load = training_load

class IntensityProcessor(DataProcessor[WorkoutData, IntensityScore]):
    """Processor for calculating workout intensity scores."""
    
    # Zone weights for intensity calculation (higher zones = higher intensity)
    ZONE_WEIGHTS = {
        "Recovery": 1.0,
        "Endurance": 1.2,
        "Tempo": 1.5,
        "Threshold": 2.0,
        "VO2Max": 2.5,
        "Anaerobic": 3.0,
        "Zone 1": 1.0,  # HR zones
        "Zone 2": 1.2,
        "Zone 3": 1.5,
        "Zone 4": 2.0,
        "Zone 5": 2.5
    }
    
    def __init__(self, context: ProcessingContext) -> None:
        """Initialize the intensity processor.
        
        Args:
            context: Processing context containing training zones
        """
        self.context = context
        
    def validate(self, data: WorkoutData) -> bool:
        """Validate workout data and context for intensity calculation."""
        if not isinstance(data, WorkoutData):
            logger.error("Input data must be WorkoutData instance")
            return False
            
        zones = self.context.get('zone_output')
        if not zones:
            logger.error("No zone output found in context")
            return False
            
        return True
        
    def _calculate_zone_distribution(
        self,
        workout: WorkoutData,
        zones: List[TrainingZone]
    ) -> Dict[str, float]:
        """Calculate time distribution across zones.
        
        Args:
            workout: Workout data
            zones: List of training zones
            
        Returns:
            Dictionary mapping zone names to percentage of time spent in each
        """
        if not zones:
            return {}
            
        total_time = workout.duration
        zone_times: Dict[str, float] = {}
        
        # For now, use average values since we don't have time series data
        # This will be enhanced when we add time series processing
        value = (
            workout.average_power if zones[0].zone_type == "power"
            else workout.heart_rate if zones[0].zone_type == "heart_rate"
            else None
        )
        
        if value is None:
            return {}
            
        # Find which zone the average value falls into
        for zone in zones:
            if zone.lower_bound <= value <= zone.upper_bound:
                # For now, assume all time was spent in this zone
                zone_times[zone.name] = 100.0
                break
                
        return zone_times
        
    def process(self, workout: WorkoutData) -> IntensityScore:
        """Calculate intensity score for the workout.
        
        Args:
            workout: Workout data to analyze
            
        Returns:
            IntensityScore with overall score and zone distribution
            
        Raises:
            ValueError: If no distributions can be calculated
        """
        zones = self.context.get('zone_output')
        
        # Try power zones first, then heart rate zones
        power_zones = zones.get('power', [])
        hr_zones = zones.get('heart_rate', [])
        
        # Calculate distributions
        power_dist = self._calculate_zone_distribution(workout, power_zones)
        hr_dist = self._calculate_zone_distribution(workout, hr_zones)
        
        # Use power distribution if available, otherwise heart rate
        zone_dist = power_dist if power_dist else hr_dist
        if not zone_dist:
            raise ValueError("No zone distributions could be calculated")
            
        # Calculate overall intensity score
        primary_zone = max(zone_dist.items(), key=lambda x: x[1])[0]
        zone_weight = self.ZONE_WEIGHTS.get(primary_zone, 1.0)
        
        # Base score on zone weight (higher zones = higher intensity)
        base_score = (zone_weight / max(self.ZONE_WEIGHTS.values())) * 100
        
        # Adjust for duration (longer workouts = higher training load)
        duration_factor = min(workout.duration / 3600, 2.0)  # Cap at 2 hours
        training_load = base_score * duration_factor
        
        return IntensityScore(
            overall_score=base_score,
            zone_distribution=zone_dist,
            primary_zone=primary_zone,
            training_load=training_load
        ) 