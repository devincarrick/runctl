"""Pipeline for orchestrating data processors."""

from typing import List, Optional, TypeVar

from loguru import logger

from src.processors import DataProcessor, ProcessingContext

T = TypeVar('T')
U = TypeVar('U')

class ProcessingPipeline:
    """Pipeline for executing data processors in sequence."""
    
    def __init__(self) -> None:
        """Initialize an empty pipeline."""
        self.processors: List[DataProcessor] = []
        self.context = ProcessingContext()
        
    def add_processor(self, processor: DataProcessor[T, U]) -> None:
        """Add a processor to the pipeline.
        
        Args:
            processor: DataProcessor instance to add
        """
        self.processors.append(processor)
        logger.info(f"Added processor: {processor.__class__.__name__}")
        
    def process(self, input_data: T) -> Optional[U]:
        """Execute all processors in sequence.
        
        Args:
            input_data: Initial input data for the pipeline
            
        Returns:
            Result from the final processor, or input_data if no processors,
            or None if pipeline fails
        """
        if not self.processors:
            logger.info("No processors in pipeline, returning input data")
            return input_data  # type: ignore
            
        current_data = input_data
        final_result = None
        
        try:
            for processor in self.processors:
                logger.info(f"Executing processor: {processor.__class__.__name__}")
                
                if not processor.validate(current_data):
                    logger.error(
                        f"Validation failed for {processor.__class__.__name__}"
                    )
                    return None
                    
                result = processor.process(current_data)
                logger.debug(f"Processor output: {result}")
                
                # Store result in context if it's not the final processor
                if processor != self.processors[-1]:
                    processor_name = processor.__class__.__name__.lower().replace('processor', '')
                    self.context.set(f"{processor_name}_output", result)
                    # Keep original input data for next processor
                    current_data = input_data
                else:
                    # For the final processor, return its result
                    final_result = result
                
            return final_result
            
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            return None
            
    def reset(self) -> None:
        """Reset the pipeline, clearing all processors and context."""
        self.processors.clear()
        self.context = ProcessingContext()
        logger.info("Pipeline reset") 