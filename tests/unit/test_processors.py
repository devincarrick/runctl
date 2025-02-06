"""Unit tests for base processor components."""

import pytest

from src.processors import DataProcessor, ProcessingContext

class SimpleProcessor(DataProcessor[str, int]):
    """Simple processor for testing."""
    
    def process(self, input_data: str) -> int:
        """Convert string length to int."""
        return len(input_data)
        
    def validate(self, data: str) -> bool:
        """Validate input is a non-empty string."""
        return isinstance(data, str) and len(data) > 0

def test_processing_context():
    """Test ProcessingContext functionality."""
    context = ProcessingContext()
    
    # Test setting and getting values
    context.set("test_key", "test_value")
    assert context.get("test_key") == "test_value"
    
    # Test getting non-existent key
    assert context.get("non_existent") is None
    
    # Test clearing context
    context.clear()
    assert context.get("test_key") is None

def test_data_processor():
    """Test DataProcessor base class with simple implementation."""
    processor = SimpleProcessor()
    
    # Test valid input
    assert processor.validate("test") is True
    assert processor.process("test") == 4
    
    # Test invalid input
    assert processor.validate("") is False
    assert processor.validate(123) is False
    
    # Test processing invalid input raises error
    with pytest.raises(TypeError):
        processor.process(123)  # type: ignore

def test_processor_type_hints():
    """Test processor type hints are correct."""
    processor = SimpleProcessor()
    
    # These should type check correctly
    result: int = processor.process("test")
    valid: bool = processor.validate("test")
    
    assert isinstance(result, int)
    assert isinstance(valid, bool)

def test_abstract_processor():
    """Test that abstract processor cannot be instantiated."""
    with pytest.raises(TypeError):
        DataProcessor()  # type: ignore

def test_abstract_methods():
    """Test that abstract methods must be implemented."""
    class IncompleteProcessor(DataProcessor[str, int]):
        pass
        
    with pytest.raises(TypeError):
        IncompleteProcessor()  # type: ignore 