"""Unit tests for processing pipeline."""

from typing import List, Optional

import pytest

from src.models.workout import WorkoutData
from src.processors import DataProcessor, ProcessingContext
from src.processors.pipeline import ProcessingPipeline

class MockProcessor(DataProcessor[WorkoutData, WorkoutData]):
    """Mock processor for testing."""
    
    def __init__(
        self,
        context: ProcessingContext,
        should_fail: bool = False,
        should_validate: bool = True,
        store_result: bool = True
    ) -> None:
        """Initialize mock processor.
        
        Args:
            context: Processing context
            should_fail: Whether process() should raise an exception
            should_validate: Whether validate() should return True
            store_result: Whether to store result in context
        """
        self.context = context
        self.should_fail = should_fail
        self.should_validate = should_validate
        self.store_result = store_result
        self.process_called = False
        self.validate_called = False
        
    def process(self, input_data: WorkoutData) -> WorkoutData:
        """Mock process method."""
        self.process_called = True
        if self.should_fail:
            raise ValueError("Mock processor failure")
            
        if self.store_result:
            self.context.set('mock_output', input_data)
            
        return input_data
        
    def validate(self, data: WorkoutData) -> bool:
        """Mock validate method."""
        self.validate_called = True
        return self.should_validate

@pytest.fixture
def workout_data():
    """Create sample workout data."""
    return WorkoutData(
        id="test_workout",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=200.0,
        total_elevation_gain=100.0,
        heart_rate=150.0,
        cadence=170.0
    )

def test_pipeline_initialization():
    """Test pipeline initialization."""
    pipeline = ProcessingPipeline()
    assert len(pipeline.processors) == 0
    assert isinstance(pipeline.context, ProcessingContext)

def test_add_processor():
    """Test adding processor to pipeline."""
    pipeline = ProcessingPipeline()
    processor = MockProcessor(pipeline.context)
    
    pipeline.add_processor(processor)
    assert len(pipeline.processors) == 1
    assert pipeline.processors[0] == processor

def test_pipeline_processing_success(workout_data):
    """Test successful pipeline processing."""
    pipeline = ProcessingPipeline()
    
    # Add multiple processors
    processors = [
        MockProcessor(pipeline.context),
        MockProcessor(pipeline.context),
        MockProcessor(pipeline.context)
    ]
    
    for processor in processors:
        pipeline.add_processor(processor)
        
    result = pipeline.process(workout_data)
    
    assert result == workout_data  # Mock processors return input unchanged
    for processor in processors:
        assert processor.process_called
        assert processor.validate_called
        
    # Verify context sharing
    assert pipeline.context.get('mock_output') == workout_data

def test_pipeline_validation_failure(workout_data):
    """Test pipeline stops on validation failure."""
    pipeline = ProcessingPipeline()
    
    # Add processors with second one failing validation
    processor1 = MockProcessor(pipeline.context)
    processor2 = MockProcessor(pipeline.context, should_validate=False)
    processor3 = MockProcessor(pipeline.context)
    
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)
    pipeline.add_processor(processor3)
    
    result = pipeline.process(workout_data)
    
    assert result is None
    assert processor1.validate_called
    assert processor2.validate_called
    assert not processor3.validate_called
    assert processor1.process_called
    assert not processor2.process_called
    assert not processor3.process_called

def test_pipeline_processing_failure(workout_data):
    """Test pipeline handles processing failure."""
    pipeline = ProcessingPipeline()
    
    # Add processors with second one raising an exception
    processor1 = MockProcessor(pipeline.context)
    processor2 = MockProcessor(pipeline.context, should_fail=True)
    processor3 = MockProcessor(pipeline.context)
    
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)
    pipeline.add_processor(processor3)
    
    result = pipeline.process(workout_data)
    
    assert result is None
    assert processor1.process_called
    assert processor2.process_called
    assert not processor3.process_called

def test_pipeline_context_sharing(workout_data):
    """Test context sharing between processors."""
    pipeline = ProcessingPipeline()
    
    # First processor stores data in context
    processor1 = MockProcessor(pipeline.context, store_result=True)
    # Second processor verifies data is available
    processor2 = MockProcessor(pipeline.context, store_result=False)
    
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)
    
    result = pipeline.process(workout_data)
    
    assert result == workout_data
    assert pipeline.context.get('mock_output') == workout_data

def test_pipeline_empty_processors(workout_data):
    """Test processing with no processors."""
    pipeline = ProcessingPipeline()
    result = pipeline.process(workout_data)
    
    # Should return input unchanged if no processors
    assert result == workout_data

def test_pipeline_reset():
    """Test pipeline reset functionality."""
    pipeline = ProcessingPipeline()
    processor = MockProcessor(pipeline.context)
    
    pipeline.add_processor(processor)
    pipeline.context.set("test_key", "test_value")
    
    pipeline.reset()
    
    assert len(pipeline.processors) == 0
    assert pipeline.context.get("test_key") is None 