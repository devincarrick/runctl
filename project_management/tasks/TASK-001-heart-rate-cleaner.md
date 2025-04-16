# TASK-001: Heart Rate Data Cleaning Script - Multi-Source Validation

## Overview
Create a Python script that processes running activity data from multiple sources (Garmin FIT and Stryd CSV) to clean and validate heart rate data. This represents the origin story of the runctl project, starting from solving a specific problem: inaccurate heart rate readings during runs.

## Objectives
- Create a command-line script that processes heart rate data with power data validation
- Implement basic statistical methods for anomaly detection
- Establish a foundation for future development
- Demonstrate data integration from multiple sources

## Technical Requirements

### Environment
- Python 3.11+
- requirements.txt for dependency management
- pytest for testing

### Project Structure

runctl/
├── README.md
├── requirements.txt
├── clean_heart_rate.py
├── data/
│   ├── sample_fit/
│   │   └── sample.fit
│   └── sample_csv/
│       └── sample.csv
└── tests/
    ├── __init__.py
    ├── test_clean_heart_rate.py
    └── test_data/
        ├── sample.fit
        └── sample.csv


### Input Data Format
1. Garmin FIT file containing:
   - Timestamp
   - Heart rate
   - Speed/pace
   - GPS data

2. Stryd CSV containing:
   - Timestamp
   - Power (w/kg)
   - Form Power
   - Speed
   - Cadence
   - Ground contact time

### Implementation Requirements

1. Command Line Interface
   ```bash
   python3 clean_heart_rate.py --fit-file activity.fit --stryd-file activity.csv --output cleaned.fit
   ```
   - Accept FIT file path argument
   - Accept optional Stryd CSV file path
   - Accept output file path argument
   - Optional arguments for customizing cleaning parameters

2. Data Processing Pipeline
   a. Data Loading
      - Parse FIT file using fitparse
      - Parse Stryd CSV using pandas
      - Align timestamps between sources
      - Create unified DataFrame

   b. Heart Rate Validation
      - Flag heart rates outside physiological range (30-220 bpm)
      - Detect sudden spikes/drops (>25% change between consecutive readings)
      - Validate against power zones:
        * Z1: <123 bpm should match power <247W
        * Z2: 123-153 bpm should match 247-278W
        * Z3: 153-169 bpm should match 278-309W
        * Z4: 169-184 bpm should match 309-355W
        * Z5: >184 bpm should match >355W

   c. Anomaly Detection
      - Statistical outliers using rolling windows
      - Power-HR correlation analysis
      - Pace correlation validation
      - Cadence pattern validation

   d. Data Cleaning
      - Remove physiologically impossible values
      - Interpolate missing/removed values
      - Smooth sudden spikes
      - Apply corrections based on power/pace correlation

3. Error Handling
   - Validate input file formats
   - Handle missing or corrupted data
   - Provide clear error messages
   - Handle timestamp misalignment between sources

4. Testing
   - Unit tests for each component
   - Integration tests for full pipeline
   - Test cases with known anomalies
   - Validation tests using power zones
   - Multi-source data alignment tests
   - Power-HR correlation tests
   - Edge case handling tests
   - Data quality metric tests

5. Documentation
   - README with setup and usage instructions
   - Code comments explaining algorithms
   - Example input/output files
   - Explanation of cleaning methodology

## Acceptance Criteria

1. Script successfully processes both FIT and CSV files
2. Heart rate anomalies are correctly identified using:
   - Basic statistical methods
   - Power zone correlation
   - Pace correlation
   - Cadence patterns
3. All tests pass with good coverage
4. README provides clear setup and usage instructions
5. Code follows PEP 8 style guidelines
6. Error handling covers common failure cases

## Sample Usage

```bash
# Basic usage
python3 clean_heart_rate.py --fit-file activity.fit --output cleaned.fit

# With Stryd data validation
python3 clean_heart_rate.py --fit-file activity.fit --stryd-file activity.csv --output cleaned.fit

# With custom parameters
python3 clean_heart_rate.py --fit-file activity.fit --stryd-file activity.csv --output cleaned.fit --max-hr 190 --min-hr 40
```

## Deliverables

1. Working Python script
2. Test suite with sample data
3. Documentation
4. Requirements file

## Future Considerations

1. Additional Data Sources
   - Support for other device formats (GPX, TCX)
   - Integration with other power meters
   - Strava API integration for data sync
   - Garmin Connect compatibility

2. Enhanced Analytics
   - Heart rate variability analysis
   - Advanced power metrics
   - Machine learning-based anomaly detection
   - Training load calculation and tracking
   - Performance trend analysis
   - Race time predictions

3. Data Export
   - Multiple output formats
   - Summary reports
   - Visualization options
   - Webhook support for real-time updates

4. Platform Integration
   - Terminal User Interface (TUI)
   - Data pipeline management
   - Automated ETL/ELT workflows
   - Real-time and batch processing capabilities

## Resources

- [FIT SDK Documentation](https://developer.garmin.com/fit/overview/)
- [Python fitparse Documentation](https://github.com/dtcooper/python-fitparse)
- [Heart Rate Zones Reference](https://www.polar.com/blog/running-heart-rate-zones-basics/)
- [Power Zones in Running](https://www.stryd.com/blog/power-zones-running)

## Task Completion Checklist

- [x] Project structure created
- [ ] FIT file parsing implemented
- [ ] Stryd CSV parsing implemented
- [ ] Data alignment implemented
- [ ] Basic cleaning algorithms implemented
- [ ] Power-based validation implemented
- [ ] Tests written and passing
- [ ] Documentation completed
- [ ] Code review passed