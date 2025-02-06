### Testing Strategy

- ✓ LocalStack-based testing
- ✓ Unit test coverage (98% coverage achieved)
  - ✓ CLI functionality
  - ✓ Data models
  - ✓ Processors
  - ✓ Services
- ✓ Integration testing
  - ✓ Pipeline integration
  - ✓ LocalStack integration
  - ✓ CLI integration
- Data quality testing
- Pipeline testing
- Performance testing

### Code Quality

- ✓ Type hints throughout
- ✓ Comprehensive documentation
- ✓ Code formatting (Ruff)
- Regular security reviews

### Phase 2: Data Processing Pipeline

#### Data Ingestion Layer

- Core Pipeline Components

  - [ ] Data ingestion processors
    - ✓ Stryd data normalization
    - [ ] Weather data integration
    - [ ] Multi-format support for enrichment data
    - [ ] Batch processing capability
  - ✓ Zone calculation engine
    - ✓ Integration with PaceZones model
    - ✓ Dynamic zone boundary calculations
    - ✓ Zone distribution analysis
  - ✓ Intensity score processor
    - ✓ Power-based calculations
    - ✓ Heart rate-based calculations
    - ✓ Combined metrics

- [ ] Data validation and cleaning
  - ✓ Schema enforcement using Pydantic V2
  - [ ] Data quality monitoring (enriched data)
  - Error handling and reporting

#### Data Processing Layer

- ETL job implementation

  - [ ] Python-based transformations
  - [ ] Data enrichment workflows

    # Priority 1: Core Health & Recovery Data

    - Garmin Connect API Integration
      - [ ] Sleep metrics
        - Total sleep time
        - Sleep stages
        - Sleep score
        - Sleep schedule consistency
      - [ ] Recovery data
        - Body battery
        - Stress score
        - HRV status
        - Recovery time advisor
      - [ ] Daily metrics
        - Resting heart rate
        - Steps/activity
        - Stress tracking

    # Priority 2: Environmental Impact

    - Weather & Environment
      - [ ] Weather data (OpenWeatherMap/WeatherAPI)
        - Temperature
        - Humidity
        - Wind speed/direction
        - Precipitation
      - [ ] Air quality (OpenAQ/AirNow)
        - AQI
        - Pollutant levels
      - [ ] UV index

    # Priority 3: Training Context

    - Equipment & Location
      - [ ] Shoe tracking
        - Current mileage
        - Shoe type/model
        - Retirement tracking
      - [ ] Route classification
        - Surface type
        - Elevation profile
        - Common routes

    # Priority 4: Extended Analysis

    - Training Load

      - [ ] Fatigue metrics
      - [ ] Season periodization
      - [ ] Race preparation periods

    - Personal Context
      - [ ] RPE logging
      - [ ] Training notes/tags
      - [ ] Weight tracking

  - [ ] Transformation logic separation
  - [ ] dbt-compatible naming conventions

#### Integration Requirements

1. Garmin Connect API

   - [ ] Authentication setup
   - [ ] Rate limiting handling
   - [ ] Data sync scheduling
   - [ ] Error handling & retries
   - [ ] Data storage strategy

2. Weather API Integration

   - [ ] API selection & setup
   - [ ] Historical data handling
   - [ ] Location-based lookups
   - [ ] Cache management

3. Data Storage & Updates
   - [ ] Incremental updates
   - [ ] Historical backfill
   - [ ] Data versioning
   - [ ] Cache invalidation

#### Schema Updates

- [ ] Extend WorkoutData model

  ```python
  class WorkoutData(BaseModel):
      # Existing fields...

      # New fields
      sleep_score: Optional[int]
      body_battery: Optional[int]
      recovery_time: Optional[int]
      resting_hr: Optional[int]
      hrv_status: Optional[str]
      weather_conditions: Optional[WeatherData]
      equipment: Optional[EquipmentData]
  ```

## Next Steps (Current Priority)

1. Begin Phase 2a: Core Pipeline Components & Data Enrichment

   - [ ] Garmin Connect Integration
     - [ ] API authentication and setup
     - [ ] Sleep metrics integration
     - [ ] Recovery data processing
     - [ ] Daily metrics collection
   - [ ] Weather Data Integration
     - [ ] API selection and setup
     - [ ] Basic weather metrics
     - [ ] Air quality data
   - [ ] Data Quality & Processing
     - [ ] Enrichment data validation
     - [ ] Data storage strategy
     - [ ] Cache management

2. Plan Phase 2b: Analysis Pipeline

   - [ ] Combined metrics analysis
   - [ ] Training load calculations
   - [ ] Recovery recommendations

3. Design Phase 2c: Storage Integration

   - [ ] Schema updates for enriched data
   - [ ] Incremental update strategy
   - [ ] Historical data management

4. Update testing framework

   - ✓ Unit test coverage (98% achieved)
   - ✓ Integration tests
   - [ ] Data quality tests
   - [ ] API integration tests

5. Document pipeline architecture and data flow
