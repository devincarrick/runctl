"""Base processor interfaces for data processing pipeline."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')

class DataProcessor(Generic[InputType, OutputType], ABC):
    """Base interface for all data processors in the pipeline."""
    
    @abstractmethod
    def process(self, input_data: InputType) -> OutputType:
        """Process the input data and return processed output.
        
        Args:
            input_data: Data to be processed
            
        Returns:
            Processed output data
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate input or output data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass

class ProcessingContext:
    """Context object for sharing state between processors."""
    
    def __init__(self) -> None:
        """Initialize an empty context."""
        self._data: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self._data[key] = value
    
    def get(self, key: str) -> Any:
        """Get a value from the context."""
        return self._data.get(key)
    
    def clear(self) -> None:
        """Clear all data from the context."""
        self._data.clear() 