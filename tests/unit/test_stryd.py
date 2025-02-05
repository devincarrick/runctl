from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import pandas as pd
import pytest
from pytest_mock import MockerFixture
from botocore.exceptions import ClientError

from src.services.stryd import StrydDataValidator, S3Storage, StrydDataIngestionService
from src.utils.exceptions import DataValidationError, StorageError
from src.models.workout import WorkoutData

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

def test_stryd_validator_required_columns() -> None:
    """Test validation of required columns."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [100],
        'power': [200]
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "Missing required columns" in messages[0]

def test_stryd_validator_power_range() -> None:
    """Test validation of power values."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [1000],
        'power': [1500],  # Invalid power value
        'heartrate': [150],
        'cadence': [180],
        'elevation': [100],
        'pace': [360],
        'elapsed_time': [600]
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "Power values must be between 0 and 1000 watts" in messages

def test_stryd_validator_heart_rate_range() -> None:
    """Test validation of heart rate values."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [1000],
        'power': [200],
        'heartrate': [300],  # Invalid heart rate
        'cadence': [180],
        'elevation': [100],
        'pace': [360],
        'elapsed_time': [600]
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "Heart rate values must be between 0 and 250 bpm" in messages

def test_stryd_validator_distance_range() -> None:
    """Test validation of distance values."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [-100],  # Invalid distance
        'power': [200],
        'heartrate': [150],
        'cadence': [180],
        'elevation': [100],
        'pace': [360],
        'elapsed_time': [600]
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "Distance values must be non-negative" in messages

def test_stryd_validator_valid_data() -> None:
    """Test validation of valid data."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [1000],
        'power': [200],
        'heartrate': [150],
        'cadence': [180],
        'elevation': [100],
        'pace': [360],
        'elapsed_time': [600]
    })
    
    is_valid, messages = validator.validate(df)
    assert is_valid
    assert len(messages) == 0

def test_stryd_validator_empty_file() -> None:
    """Test validation of an empty DataFrame."""
    validator = StrydDataValidator()
    df = pd.DataFrame()
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "DataFrame is empty" in messages[0]

def test_stryd_validator_malformed_data_types() -> None:
    """Test validation with incorrect data types."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': ['invalid_time'],  # Invalid datetime
        'distance': ['not_a_number'],  # Invalid number
        'power': [200],
        'heartrate': [150],
        'cadence': [180],
        'elevation': [100],
        'pace': [360],
        'elapsed_time': [600]
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert any("Invalid data type" in msg for msg in messages)

def test_stryd_validator_extreme_valid_values() -> None:
    """Test validation with extreme but valid values."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [datetime.now()],
        'distance': [42195],  # Marathon distance
        'power': [999],  # Just under max
        'heartrate': [220],  # Maximum theoretical heart rate
        'cadence': [250],  # Very high but possible
        'elevation': [8848],  # Height of Mount Everest
        'pace': [1000],  # Very slow pace
        'elapsed_time': [86400]  # 24 hours
    })
    
    is_valid, messages = validator.validate(df)
    assert is_valid
    assert len(messages) == 0

def test_s3_storage_upload_success(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test successful file upload to S3."""
    mock_s3 = mocker.Mock()
    storage = S3Storage("test-bucket", endpoint_url="http://localhost:4566")
    storage.s3 = mock_s3
    
    # Create a temporary test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")
    
    storage.upload_file(test_file, "test/key.csv")
    
    mock_s3.upload_file.assert_called_once_with(
        str(test_file),
        "test-bucket",
        "test/key.csv"
    )

def test_s3_storage_upload_failure(mocker: MockerFixture) -> None:
    """Test file upload failure handling."""
    mock_s3 = mocker.Mock()
    mock_s3.upload_file.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Test error'}},
        'upload_file'
    )
    
    storage = S3Storage("test-bucket", endpoint_url="http://localhost:4566")
    storage.s3 = mock_s3
    
    with pytest.raises(StorageError) as exc_info:
        storage.upload_file(Path("test.csv"), "test/key.csv")
    assert "Failed to upload file" in str(exc_info.value)

def test_s3_storage_upload_connection_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test handling of connection errors during upload."""
    mock_s3 = mocker.patch('boto3.client')
    mock_s3.return_value.upload_file.side_effect = ConnectionError("Network error")
    
    storage = S3Storage("test-bucket", "http://localhost:4566")
    
    # Create a temporary test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")
    
    with pytest.raises(StorageError) as exc_info:
        storage.upload_file(test_file, "destination.csv")
    assert "Failed to upload file" in str(exc_info.value)
    assert "Network error" in str(exc_info.value)

def test_s3_storage_upload_permission_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test handling of permission errors during upload."""
    mock_s3 = mocker.patch('boto3.client')
    mock_s3.return_value.upload_file.side_effect = ClientError(
        {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'Access Denied'
            }
        },
        'PutObject'
    )
    
    storage = S3Storage("test-bucket", "http://localhost:4566")
    
    # Create a temporary test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")
    
    with pytest.raises(StorageError) as exc_info:
        storage.upload_file(test_file, "destination.csv")
    assert "Failed to upload file" in str(exc_info.value)
    assert "Access Denied" in str(exc_info.value)

def test_s3_storage_upload_nonexistent_file() -> None:
    """Test handling of non-existent source file."""
    storage = S3Storage("test-bucket", "http://localhost:4566")
    with pytest.raises(StorageError) as exc_info:
        storage.upload_file("nonexistent.csv", "destination.csv")
    assert "Failed to upload file" in str(exc_info.value)
    assert "No such file" in str(exc_info.value)

def test_stryd_service_transform_data() -> None:
    """Test data transformation in the Stryd service."""
    service = StrydDataIngestionService(
        storage=S3Storage("test-bucket"),
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create test data with Stryd format
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [1000],
        'Power (w/kg)': [3.0],
        'Heart Rate (bpm)': [150],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [2.8]
    })
    
    transformed = service._transform_data(df)
    
    assert 'time' in transformed.columns
    assert 'distance' in transformed.columns
    assert 'power' in transformed.columns
    assert transformed['power'].iloc[0] == 210.0  # 3.0 * 70.0
    assert transformed['distance'].iloc[0] == 1000
    assert transformed['heartrate'].iloc[0] == 150

def test_stryd_service_transform_data_missing_heart_rate() -> None:
    """Test data transformation when heart rate column is missing."""
    service = StrydDataIngestionService(
        storage=S3Storage("test-bucket"),
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create test data without heart rate
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [1000],
        'Power (w/kg)': [3.0],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [2.8]
    })
    
    transformed = service._transform_data(df)
    
    assert 'heartrate' in transformed.columns
    assert pd.isna(transformed['heartrate'].iloc[0])

def test_stryd_service_transform_data_nan_values() -> None:
    """Test data transformation with NaN values in numeric columns."""
    service = StrydDataIngestionService(
        storage=S3Storage("test-bucket"),
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create test data with NaN values
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [float('nan')],
        'Power (w/kg)': [float('nan')],
        'Heart Rate (bpm)': [150],
        'Cadence (spm)': [float('nan')],
        'Stryd Elevation (m)': [float('nan')],
        'Watch Speed (m/s)': [float('nan')]
    })
    
    transformed = service._transform_data(df)
    
    # Check that numeric columns have no NaN values
    numeric_columns = ['power', 'distance', 'cadence', 'elevation', 'pace']
    for col in numeric_columns:
        assert not transformed[col].isna().any()
        assert transformed[col].iloc[0] == 0

def test_stryd_service_process_file_validation_error(tmp_path: Path) -> None:
    """Test file processing with validation error."""
    service = StrydDataIngestionService(
        storage=S3Storage("test-bucket"),
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create invalid test file
    test_file = tmp_path / "invalid.csv"
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [-1000],  # Invalid distance
        'Power (w/kg)': [3.0],
        'Heart Rate (bpm)': [150],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [3.0]
    })
    df.to_csv(test_file, index=False)
    
    with pytest.raises(DataValidationError):
        service.process_file(test_file)

def test_stryd_service_process_file_success(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test successful file processing."""
    mock_storage = mocker.Mock()
    service = StrydDataIngestionService(
        storage=mock_storage,
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create valid test file
    test_file = tmp_path / "valid.csv"
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [1000],
        'Power (w/kg)': [3.0],
        'Heart Rate (bpm)': [150],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [2.8]
    })
    df.to_csv(test_file, index=False)
    
    workouts = service.process_file(test_file)
    
    assert len(workouts) == 1
    assert isinstance(workouts[0], WorkoutData)
    assert workouts[0].average_power == pytest.approx(210.0)  # 3.0 * 70.0
    assert workouts[0].distance == 1000
    assert workouts[0].heart_rate == 150

def test_stryd_service_process_file_with_nan_heart_rate(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test file processing with NaN heart rate values."""
    mock_storage = mocker.Mock()
    service = StrydDataIngestionService(
        storage=mock_storage,
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create test file with NaN heart rate
    test_file = tmp_path / "valid.csv"
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [1000],
        'Power (w/kg)': [3.0],
        'Heart Rate (bpm)': [float('nan')],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [2.8]
    })
    df.to_csv(test_file, index=False)
    
    workouts = service.process_file(test_file)
    
    assert len(workouts) == 1
    assert workouts[0].heart_rate is None

def test_stryd_service_process_file_zero_speed(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test file processing with zero speed values."""
    mock_storage = mocker.Mock()
    service = StrydDataIngestionService(
        storage=mock_storage,
        validator=StrydDataValidator(),
        athlete_weight=70.0
    )
    
    # Create test file with zero speed
    test_file = tmp_path / "valid.csv"
    df = pd.DataFrame({
        'Timestamp': [datetime.now()],
        'Stryd Distance (meters)': [1000],
        'Power (w/kg)': [3.0],
        'Heart Rate (bpm)': [150],
        'Cadence (spm)': [180],
        'Stryd Elevation (m)': [100],
        'Watch Speed (m/s)': [0.0]  # Zero speed
    })
    df.to_csv(test_file, index=False)
    
    workouts = service.process_file(test_file)
    
    assert len(workouts) == 1
    assert workouts[0].average_pace == 0  # Pace should be 0 when speed is 0