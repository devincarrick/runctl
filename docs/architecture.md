# Technical Architecture

## Phase 1 Architecture

### Data Processing Pipeline
```
Input Files → Data Loading → Validation → Cleaning → Output
   (FIT)        (FIT + CSV)   (Power + HR)  (Stats)   (FIT)
```

### Key Components

#### 1. Data Loading
- FIT file parsing using fitparse
- CSV parsing using pandas
- Timestamp alignment between sources
- Unified DataFrame creation

#### 2. Validation
- Heart rate range validation (30-220 bpm)
- Power zone correlation:
  * Z1: <123 bpm should match power <247W
  * Z2: 123-153 bpm should match 247-278W
  * Z3: 153-169 bpm should match 278-309W
  * Z4: 169-184 bpm should match 309-355W
  * Z5: >184 bpm should match >355W

#### 3. Cleaning
- Statistical outlier detection
- Rolling window analysis
- Interpolation for missing values
- Smoothing of sudden spikes

#### 4. Output
- Cleaned FIT file generation
- Data quality report
- Validation summary

## Technical Decisions

### Data Processing
- Use pandas for data manipulation
- Implement custom validation logic
- Use scipy for statistical analysis

### File Handling
- Primary format: FIT
- Secondary format: CSV (Stryd)
- Output format: FIT

### Validation Approach
- Multi-source validation
- Statistical methods
- Power zone correlation
- Physiological limits

## Future Architecture Considerations
- Stream processing capabilities
- Data warehouse integration
- Real-time processing
- Advanced analytics pipeline 