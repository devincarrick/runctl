"""Integration tests for Stryd data ingestion."""

import os
from pathlib import Path
from typing import Generator

import pytest
import pandas as pd
from _pytest.fixtures import FixtureRequest

from src.services.stryd import (
    StrydDataIngestionService,
    StrydDataValidator,
    S3Storage
)
from src.infra.localstack.config import LocalStackConfig


@pytest.fixture
def localstack_config() -> LocalStackConfig:
    """Create LocalStack configuration."""
    return LocalStackConfig()


@pytest.fixture
def sample_workout(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a sample workout file."""
    content = """Timestamp,Power (w/kg),Stryd Distance (meters),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)
2024-01-30 07:00:00,2.85,1000,150,180,100,2.77
2024-01-30 07:01:00,3.57,2000,155,182,102,2.82
"""
    file_path = tmp_path / "workout.csv"
    file_path.write_text(content)
    yield file_path


@pytest.fixture
def real_workout_data() -> Path:
    """Get path to real workout test data."""
    return Path("tests/data/real_workout_test.csv")


@pytest.fixture
def service(localstack_config: LocalStackConfig) -> StrydDataIngestionService:
    """Create a test service instance."""
    storage = S3Storage("runctl-raw-data", localstack_config.endpoint_url)
    validator = StrydDataValidator()
    return StrydDataIngestionService(storage, validator, athlete_weight=65.0)  # Test with 65kg


def test_stryd_ingestion_with_localstack(
    localstack_config: LocalStackConfig,
    sample_workout: Path
) -> None:
    """Test complete Stryd ingestion workflow with LocalStack."""
    # Setup
    storage = S3Storage("runctl-raw-data", localstack_config.endpoint_url)
    validator = StrydDataValidator()
    service = StrydDataIngestionService(storage, validator)
    
    # Process file
    workouts = service.process_file(sample_workout)
    
    # Verify results
    assert len(workouts) == 1, "Should create one workout from the file"
    workout = workouts[0]
    
    # Verify workout metrics
    assert workout.average_power == 224.7, f"Expected power 224.7W, got {workout.average_power}W"
    assert workout.distance == 2000.0, f"Expected distance 2000m, got {workout.distance}m"
    assert workout.heart_rate == 152.5, f"Expected HR 152.5, got {workout.heart_rate}"
    assert workout.cadence == 181.0, f"Expected cadence 181, got {workout.cadence}"
    
    # Verify S3 upload
    s3_client = localstack_config.get_client('s3')
    objects = s3_client.list_objects_v2(Bucket="runctl-raw-data")
    assert 'Contents' in objects
    assert any(obj['Key'].endswith('workout.csv') for obj in objects['Contents'])


def test_stryd_ingestion_with_real_data(
    real_workout_data: Path,
    service: StrydDataIngestionService
) -> None:
    """Test Stryd ingestion with real workout data."""
    # Read the source file to compare
    df = pd.read_csv(real_workout_data)
    print(f"\nInput file power stats:\n{df['Power (w/kg)'].describe()}")
    
    # Process file
    workouts = service.process_file(real_workout_data)
    
    # Debug output
    print(f"\nProcessed {len(workouts)} workouts")
    print(f"First workout power: {workouts[0].average_power:.2f} watts")
    print(f"Power per kg: {workouts[0].average_power/service.athlete_weight:.2f} w/kg")
    
    # Verify results
    assert len(workouts) == 1, "Should create one workout from the file"
    
    # Test specific metrics from the workout
    workout = workouts[0]
    assert workout.average_power > 200, f"Power should be ~250W, got {workout.average_power}"
    assert workout.distance > 0, f"Distance should be positive, got {workout.distance}"
    assert workout.cadence is not None, f"Cadence should not be None, got {workout.cadence}"
    assert 100 <= workout.cadence <= 200, f"Cadence out of range: {workout.cadence}"


def test_stryd_data_validation(real_workout_data: Path) -> None:
    """Test validation rules with real workout data."""
    validator = StrydDataValidator()
    service = StrydDataIngestionService(S3Storage("test-bucket"), validator)
    
    # Read and transform data first
    df = pd.read_csv(real_workout_data)
    df = service._transform_data(df)  # Access the transformed data
    
    # Validate transformed data
    is_valid, messages = validator.validate(df)
    assert is_valid, f"Validation failed with messages: {messages}"
    
    # Test with corrupted data
    df_corrupt = df.copy()
    df_corrupt.loc[0, 'power'] = 9999  # Invalid power value
    is_valid, messages = validator.validate(df_corrupt)
    assert not is_valid
    assert any("Power values must be between" in msg for msg in messages)