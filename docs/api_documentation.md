# RunCtl API Documentation

## Overview

RunCtl is a powerful running analytics tool that processes workout data from various sources and provides insights into training patterns, zones, and performance metrics.

## Data Models

### WorkoutData

Represents a single running workout with basic metrics:

```python
{
    "id": "w123",
    "date": "2024-01-23T10:30:00",
    "distance": 10.0,
    "duration": 3600,
    "average_pace": 360.0,
    "average_power": 250.0,
    "total_elevation_gain": 100.0,
    "heart_rate": 165.0,
    "temperature": 20.0,
    "humidity": 65.0,
    "cadence": 180.0
}
```

### Training Zones

#### PowerZones

Power-based training zones calculated from Critical Power:

```python
{
    "critical_power": 250,
    "ftp": 238,  # Optional
    "zones": [
        {
            "name": "Recovery",
            "lower_bound": 137.5,
            "upper_bound": 187.5,
            "description": "Very light intensity for recovery",
            "zone_type": "power"
        },
        # ... additional zones
    ]
}
```

#### HeartRateZones

Heart rate-based training zones:

```python
{
    "max_heart_rate": 185,
    "resting_heart_rate": 45,  # Optional
    "zones": [
        {
            "name": "Zone 1",
            "lower_bound": 92.5,
            "upper_bound": 111.0,
            "description": "Very light aerobic activity",
            "zone_type": "heart_rate"
        },
        # ... additional zones
    ]
}
```

### Analytics

#### WorkoutTrend

Represents workout trends over a specified time period:

```python
{
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "time_range": "month",
    "total_workouts": 20,
    "total_distance": 200.5,
    "total_duration": 72000,
    "average_power": 250.0,
    "average_heart_rate": 155.0,
    "power_trend": 2.5,
    "pace_trend": -0.5
}
```

#### WorkoutSummary

Comprehensive workout summary including zone analysis:

```python
{
    "workout": WorkoutData,
    "power_zones": {
        "workout_id": "w123",
        "zone_type": "power",
        "total_duration": 3600,
        "zone_analysis": [
            {
                "zone": TrainingZone,
                "time_in_zone": 1200,
                "percentage_in_zone": 33.3
            }
        ]
    },
    "intensity_score": 85.5,
    "recovery_time": 24
}
```

## Error Handling

The API uses the following exception hierarchy for error handling:

- `RunCtlError`: Base exception class
  - `DataValidationError`: Data validation failures
    - `FileFormatError`: Invalid file formats
  - `StorageError`: Storage operation failures
  - `ConfigurationError`: Configuration issues
  - `DataProcessingError`: Data processing failures
    - `MetricCalculationError`: Metric calculation issues
  - `ZoneCalculationError`: Training zone calculation failures
  - `AnalyticsError`: Analytics calculation failures
  - `APIError`: External API failures
  - `AuthenticationError`: Authentication issues

## CLI Commands

### analyze

Analyze a workout file and display metrics:

```bash
runctl analyze workout.csv --format stryd --weight 70.0
```

### zones

Calculate and display training zones:

```bash
runctl zones --critical-power 250
```

## Data Processing Flow

1. File Upload/Import
2. Data Validation
3. Metric Calculation
4. Zone Analysis
5. Storage
6. Analytics Generation

## Storage

The application uses the following storage structure:

- S3 Buckets:

  - `runctl-raw-data`: Raw workout files
  - `runctl-processed-data`: Processed workout data
  - `runctl-summaries`: Analytics summaries

- DynamoDB Tables:
  - `runctl-workouts`: Workout metadata and metrics
