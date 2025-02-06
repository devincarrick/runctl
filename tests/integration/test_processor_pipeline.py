"""Integration tests for the full data processing pipeline."""

import pytest

from src.models.workout import WorkoutData
from src.processors import ProcessingContext
from src.processors.pipeline import ProcessingPipeline
from src.processors.zone_processor import ZoneProcessor
from src.processors.intensity_processor import IntensityProcessor, IntensityScore

@pytest.fixture
def workout_data():
    """Create a real workout data instance."""
    return WorkoutData(
        id="test_integration",
        date="2024-02-06T12:00:00",
        distance=10000.0,  # 10km
        duration=3600,     # 1 hour
        average_pace=360.0,  # 6:00 min/km
        average_power=250.0,  # 250 watts (threshold power)
        total_elevation_gain=100.0,
        heart_rate=165.0,  # High aerobic
        cadence=175.0
    )

@pytest.fixture
def pipeline():
    """Create a pipeline with all processors."""
    pipeline = ProcessingPipeline()
    context = pipeline.context
    
    # Add processors in sequence
    zone_processor = ZoneProcessor(context=context)
    intensity_processor = IntensityProcessor(context)
    
    pipeline.add_processor(zone_processor)
    pipeline.add_processor(intensity_processor)
    
    return pipeline

def test_full_pipeline_processing(pipeline, workout_data):
    """Test the full pipeline from workout data to intensity score."""
    # Process workout through pipeline
    result = pipeline.process(workout_data)
    
    # Verify result type
    assert isinstance(result, IntensityScore)
    
    # Verify zone calculations
    zones = pipeline.context.get('zone_output')
    assert 'power' in zones
    assert 'heart_rate' in zones
    assert 'pace' in zones
    
    # Verify intensity score components
    assert result.overall_score > 0
    assert result.zone_distribution
    assert result.primary_zone
    assert result.training_load > 0

def test_pipeline_with_missing_data(pipeline):
    """Test pipeline with partially missing workout data."""
    partial_workout = WorkoutData(
        id="partial_test",
        date="2024-02-06T12:00:00",
        distance=5000.0,
        duration=1800,
        average_pace=360.0,
        average_power=None,  # Missing power
        total_elevation_gain=50.0,
        heart_rate=150.0,
        cadence=170.0
    )
    
    result = pipeline.process(partial_workout)
    
    # Should still get valid results using HR data
    assert isinstance(result, IntensityScore)
    zones = pipeline.context.get('zone_output')
    assert 'heart_rate' in zones
    assert 'power' not in zones  # No power data

def test_pipeline_data_flow(pipeline, workout_data):
    """Test data flow and context sharing between processors."""
    # Add a spy to track processor execution
    class ProcessorSpy:
        def __init__(self):
            self.zone_processor_called = False
            self.intensity_processor_called = False
    spy = ProcessorSpy()
    
    # Wrap processors to track calls
    original_zone_process = pipeline.processors[0].process
    original_intensity_process = pipeline.processors[1].process
    
    def zone_spy(workout):
        spy.zone_processor_called = True
        return original_zone_process(workout)
    
    def intensity_spy(workout):
        spy.intensity_processor_called = True
        assert pipeline.context.get('zone_output') is not None  # Verify context sharing
        return original_intensity_process(workout)
    
    pipeline.processors[0].process = zone_spy
    pipeline.processors[1].process = intensity_spy
    
    # Process workout
    result = pipeline.process(workout_data)
    
    # Verify processor execution order and context sharing
    assert spy.zone_processor_called
    assert spy.intensity_processor_called
    
def test_pipeline_error_handling(pipeline):
    """Test pipeline error handling with invalid data."""
    invalid_workout = "not a workout"  # Invalid input
    
    result = pipeline.process(invalid_workout)
    assert result is None  # Pipeline should fail gracefully
    
def test_pipeline_reset(pipeline, workout_data):
    """Test pipeline reset functionality."""
    # Process a workout
    pipeline.process(workout_data)
    assert pipeline.context.get('zone_output') is not None
    
    # Reset pipeline
    pipeline.reset()
    assert len(pipeline.processors) == 0
    assert pipeline.context.get('zone_output') is None 