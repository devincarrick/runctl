# 5. Form Metrics Implementation

Date: 2024-03-19

## Status

Accepted

## Context

We needed to implement comprehensive form metrics analysis to help runners understand and improve their running technique. This includes analyzing cadence, ground contact time, vertical oscillation, and power efficiency. The implementation needed to be statistically sound and provide actionable insights.

## Decision

We implemented the form metrics analysis module with four main components:

1. **Cadence Analysis**

   - Trend analysis using linear regression
   - Statistical significance testing
   - Optimal range recommendations (170-180 spm)
   - Human-readable trend descriptions

2. **Ground Contact Time Analysis**

   - Trend analysis for ground time changes
   - Left/right balance monitoring
   - Optimal range recommendations (150-200 ms)
   - Statistical significance testing

3. **Vertical Metrics**

   - Vertical oscillation monitoring (6.5-8.5 cm)
   - Vertical ratio analysis (0.06-0.08)
   - Efficiency scoring system
   - Balance monitoring

4. **Power Efficiency**
   - Total power analysis
   - Form power and air power breakdown
   - Efficiency ratio calculation
   - Optimal range recommendations (0.92-0.96)

## Consequences

### Positive

- Comprehensive form analysis with multiple metrics
- Statistical validation of trends
- Clear, actionable insights
- Efficient data processing
- High test coverage
- Robust error handling

### Negative

- Requires Stryd data for full functionality
- Some metrics need multiple sessions for analysis
- Optimal ranges may need adjustment for different runners

## Technical Details

- Used scipy.stats for statistical calculations
- Implemented trend analysis with linear regression
- Added comprehensive test suite with >90% coverage
- Included data validation and error handling
- Followed project code style and documentation standards

## Alternatives Considered

1. **Moving Average for Trends**

   - Simpler but less statistically rigorous
   - Wouldn't provide significance testing
   - Rejected in favor of linear regression

2. **Fixed Time Windows**

   - Could use fixed 4-week windows
   - Less flexible than rolling windows
   - Rejected for reduced data utilization

3. **Individual Session Analysis**
   - Could analyze each session separately
   - Would miss long-term trends
   - Rejected for lack of trend detection

## References

- Stryd Running Power Metrics: [Stryd Documentation](https://www.stryd.com/guide)
- Running Form Analysis: [Running Research](https://www.scienceofultra.com/blog/runningform)
- Optimal Running Cadence: [Research Paper](https://pubmed.ncbi.nlm.nih.gov/26816209/)
