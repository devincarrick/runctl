# ADR 0001: CSV Parser Implementation

## Status

Accepted

## Context

The application needs to support importing running data from various CSV file formats, including standard running data, raw workout data, and Stryd device data. Each format has its own structure and requirements:

1. Standard format: Simple CSV with basic running metrics
2. Raw workout format: Normalized values that need scaling
3. Stryd format: High-frequency data with device-specific metrics

## Decision

We implemented a flexible CSV parser with the following key features:

1. Format-specific parsing strategies:

   - Standard CSV parsing using pandas
   - Raw workout parsing with value scaling
   - Stryd format parsing with session grouping

2. Comprehensive data models:

   - `RunningMetrics` class for core metrics
   - Extended support for Stryd-specific fields
   - `RunningSession` class for metadata

3. Validation system:

   - Basic metric validation
   - Format-specific validation rules
   - Error handling with continuation

4. Implementation details:
   - Used pandas for efficient data processing
   - Implemented timestamp parsing for various formats
   - Added session detection for high-frequency data

## Consequences

### Positive

1. Flexible support for multiple data formats
2. Strong type safety through dataclasses
3. Efficient data processing with pandas
4. Good test coverage
5. Easy to extend for new formats

### Negative

1. Increased complexity in parser logic
2. Memory usage with pandas for large files
3. Need to maintain format-specific parsing rules

## Notes

- Consider implementing streaming parser for very large files
- May need to optimize memory usage for high-frequency data
- Should add more validation rules for Stryd-specific metrics
