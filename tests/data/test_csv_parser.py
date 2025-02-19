"""Tests for CSV parsing and validation."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pandas as pd
import pytest
import time_machine

from runctl.data.csv_parser import CSVParser
from runctl.data.models import RunningMetrics, RunningSession
from runctl.data.validation import DataValidationError, validate_metrics


@pytest.fixture
def valid_csv_path():
    """Create a temporary CSV file with valid running data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'distance', 'duration', 'avg_pace',
            'avg_heart_rate', 'max_heart_rate', 'elevation_gain',
            'calories', 'cadence', 'temperature', 'weather_condition',
            'notes', 'tags', 'equipment'
        ])
        writer.writerow([
            '2024-02-19 08:30:00',  # timestamp
            '5000',                  # distance (meters)
            '1500',                  # duration (seconds)
            '300',                   # avg_pace (seconds per km)
            '145',                   # avg_heart_rate
            '165',                   # max_heart_rate
            '50',                    # elevation_gain
            '450',                   # calories
            '175',                   # cadence
            '20',                    # temperature
            'Sunny',                 # weather_condition
            'Morning run',           # notes
            'easy,morning',          # tags
            'Nike Pegasus'           # equipment
        ])
    yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def raw_workout_csv_path():
    """Create a temporary CSV file with raw workout data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        # Sample row from real workout data
        writer.writerow([
            '1736694777',  # timestamp (days since 1900-01-01)
            '3.1830',      # distance (normalized)
            '0.9436',      # duration (normalized)
            '0.0704',      # elevation
            '2.976',       # speed
            '2.8984',      # avg_speed
            '10418.57',    # total_distance
            '9887.16',     # total_time
            '9.75',        # heart_rate
            '0.1373',      # cadence (normalized)
            '270',         # power
            '170',         # avg_power
            '6.625',       # temperature
            '19.8',        # grade
            '29'           # resistance
        ])
    yield Path(f.name)
    Path(f.name).unlink()


def test_csv_parser_initialization(valid_csv_path):
    """Test CSV parser initialization."""
    parser = CSVParser(valid_csv_path)
    assert parser.csv_path == valid_csv_path
    assert parser.format_type == 'standard'

    parser = CSVParser(valid_csv_path, format_type='raw_workout')
    assert parser.format_type == 'raw_workout'

    with pytest.raises(FileNotFoundError):
        CSVParser(Path('nonexistent.csv'))


def test_parse_valid_csv(valid_csv_path):
    """Test parsing a valid CSV file."""
    parser = CSVParser(valid_csv_path)
    sessions = list(parser.parse())
    
    assert len(sessions) == 1
    session = sessions[0]
    
    assert isinstance(session, RunningSession)
    assert isinstance(session.metrics, RunningMetrics)
    
    # Check parsed values
    metrics = session.metrics
    assert metrics.timestamp == datetime(2024, 2, 19, 8, 30).replace(tzinfo=timezone.utc)
    assert metrics.distance == 5000
    assert metrics.duration == 1500
    assert metrics.avg_pace == 300
    assert metrics.avg_heart_rate == 145
    assert metrics.max_heart_rate == 165
    assert metrics.elevation_gain == 50
    assert metrics.calories == 450
    assert metrics.cadence == 175
    assert metrics.temperature == 20
    assert metrics.weather_condition == 'Sunny'
    
    assert session.notes == 'Morning run'
    assert session.tags == ['easy', 'morning']
    assert session.equipment == 'Nike Pegasus'


def test_parse_raw_workout(raw_workout_csv_path):
    """Test parsing raw workout format CSV file."""
    parser = CSVParser(raw_workout_csv_path, format_type='raw_workout')
    sessions = list(parser.parse())
    
    assert len(sessions) == 1
    session = sessions[0]
    
    assert isinstance(session, RunningSession)
    assert isinstance(session.metrics, RunningMetrics)
    
    # Check parsed values
    metrics = session.metrics
    
    # Timestamp should be Unix timestamp
    assert isinstance(metrics.timestamp, datetime)
    
    # Check scaled values
    assert abs(metrics.distance - 3.1830 * 1000) < 0.01  # ~3183 meters
    assert abs(metrics.duration - 0.9436 * 3600) < 0.01  # ~3397 seconds
    assert metrics.avg_pace > 0  # Calculated from speed
    assert metrics.avg_heart_rate == 9.75
    assert abs(metrics.cadence - 0.1373 * 60) < 0.01  # ~8.24 steps/min
    assert metrics.temperature == 6.625


def test_parse_missing_required_columns():
    """Test parsing CSV with missing required columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'distance'])  # Missing duration and avg_pace
        writer.writerow(['2024-02-19 08:30:00', '5000'])
    
    parser = CSVParser(Path(f.name))
    with pytest.raises(ValueError) as exc:
        list(parser.parse())
    assert "Missing required columns" in str(exc.value)
    
    Path(f.name).unlink()


def test_parse_invalid_values():
    """Test parsing CSV with invalid values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'distance', 'duration', 'avg_pace'])
        writer.writerow(['invalid_date', '-100', '1500', '300'])
    
    parser = CSVParser(Path(f.name))
    sessions = list(parser.parse())  # Should skip invalid row
    assert len(sessions) == 0
    
    Path(f.name).unlink()


@time_machine.travel("2024-02-19 12:00:00+00:00")
def test_validation():
    """Test metrics validation."""
    # Test future timestamp (1 year ahead)
    current_time = datetime.now(timezone.utc)
    future_time = current_time + timedelta(days=365)
    
    future_metrics = RunningMetrics(
        timestamp=future_time,
        distance=5000,
        duration=1500,
        avg_pace=300
    )
    with pytest.raises(DataValidationError) as exc:
        validate_metrics(future_metrics)
    assert "future" in str(exc.value)
    
    # Test negative distance
    invalid_distance = RunningMetrics(
        timestamp=current_time,
        distance=-100,
        duration=1500,
        avg_pace=300
    )
    with pytest.raises(DataValidationError) as exc:
        validate_metrics(invalid_distance)
    assert "Distance" in str(exc.value)
    
    # Test invalid heart rate relationship
    invalid_hr = RunningMetrics(
        timestamp=current_time,
        distance=5000,
        duration=1500,
        avg_pace=300,
        avg_heart_rate=160,
        max_heart_rate=150
    )
    with pytest.raises(DataValidationError) as exc:
        validate_metrics(invalid_hr)
    assert "heart rate" in str(exc.value)

    # Test raw workout validation
    raw_workout_metrics = RunningMetrics(
        timestamp=current_time,
        distance=5000,
        duration=1500,
        avg_pace=300,
        avg_heart_rate=15,  # Normalized value
        cadence=0.2,        # Normalized value
        temperature=25
    )
    # This should not raise an exception
    validate_metrics(raw_workout_metrics, is_raw_workout=True)

    # Test invalid raw workout values
    invalid_raw_hr = RunningMetrics(
        timestamp=current_time,
        distance=5000,
        duration=1500,
        avg_pace=300,
        avg_heart_rate=50  # Too high for normalized value
    )
    with pytest.raises(DataValidationError) as exc:
        validate_metrics(invalid_raw_hr, is_raw_workout=True)
    assert "between 0 and 30 (normalized)" in str(exc.value)


def test_parse_tags():
    """Test tag parsing."""
    # Create parser without checking file existence
    parser = CSVParser(Path('dummy.csv'), check_exists=False)
    assert parser._parse_tags('') == []
    assert parser._parse_tags('N/A') == []
    assert parser._parse_tags('tag1,tag2') == ['tag1', 'tag2']
    assert parser._parse_tags(' tag1 , tag2 ') == ['tag1', 'tag2']
    assert parser._parse_tags('tag1,,tag2') == ['tag1', 'tag2'] 