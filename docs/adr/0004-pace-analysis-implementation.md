# 4. Pace Analysis Implementation

Date: 2024-03-19

## Status

Accepted

## Context

We needed to implement comprehensive pace analysis features to help runners understand their performance trends, predict race times, and determine appropriate training paces. The implementation needed to be statistically sound, efficient, and provide meaningful insights.

## Decision

We implemented the pace analysis module with three main components:

1. **Pace Trend Analysis**

   - Uses linear regression to analyze pace trends over time
   - Calculates statistical significance (p-value) and correlation strength (r-value)
   - Provides human-readable trend descriptions
   - Filters data to recent window (default 90 days)

2. **Race Time Predictions**

   - Uses Riegel's formula: T2 = T1 \* (D2/D1)^1.06
   - Predicts times for common race distances (5K to Marathon)
   - Includes confidence scores based on distance differences
   - Uses recent best performances as baseline

3. **Training Pace Calculations**
   - Based on threshold pace from recent efforts
   - Requires multiple threshold efforts for reliability
   - Uses standard training pace formulas
   - Provides paces for easy, tempo, threshold, interval, and repetition runs

## Consequences

### Positive

- Statistically sound trend analysis with significance testing
- Accurate race predictions based on proven formula
- Reliable training paces based on actual performance
- Comprehensive test coverage with edge cases
- Clean, maintainable code following project standards

### Negative

- Requires sufficient recent data for meaningful analysis
- Race predictions may be less accurate for large distance differences
- Training paces require multiple threshold efforts

## Technical Details

- Used scipy.stats for statistical calculations
- Implemented data filtering to focus on recent performances
- Added comprehensive test suite with >90% coverage
- Followed project code style and documentation standards

## Alternatives Considered

1. **Moving Average for Trends**

   - Simpler but less statistically rigorous
   - Wouldn't provide significance testing
   - Rejected in favor of linear regression

2. **Different Race Prediction Formulas**

   - Considered Cameron's formula
   - Riegel's formula chosen for simplicity and proven accuracy

3. **Single Threshold Effort for Paces**
   - Would provide faster results
   - Rejected for reliability concerns
   - Chose to require multiple efforts

## References

- Riegel's Formula: [Running Calculator](https://www.runnersworld.com/uk/training/a761676/rws-race-time-predictor/)
- Training Paces: [Jack Daniels' Running Formula](https://www.amazon.com/Daniels-Running-Formula-Jack/dp/1450431836)
