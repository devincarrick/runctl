"""Unit tests for CLI commands."""

from typing import TYPE_CHECKING
from pathlib import Path
from typer.testing import CliRunner
import pytest
from pytest_mock import MockerFixture
from datetime import datetime
from unittest.mock import Mock, patch
import typer

from src.cli import app, validate_weight, validate_critical_power, main
from src.models.workout import WorkoutData

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

runner = CliRunner()

def test_analyze_command(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with valid arguments."""
    # Create a test file
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power,heartrate,cadence,elevation,pace,elapsed_time\n"
                        "2024-01-30 07:00:00,1000,200,150,180,100,360,600")
    
    # Mock LocalStack config and S3 storage
    mocker.patch('src.cli.LocalStackConfig')
    mock_storage = mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    mock_service.return_value.process_file.return_value = []
    
    # Run command with the test file and provide weight
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed" in result.stdout

def test_analyze_command_with_format() -> None:
    """Test the analyze command with custom format."""
    result = runner.invoke(app, ["analyze", "workout.csv", "--format", "garmin"])
    assert result.exit_code == 0
    assert "Format garmin not supported yet" in result.stdout

def test_analyze_command_missing_file() -> None:
    """Test the analyze command with missing file argument."""
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 2  # Typer returns 2 for CLI usage errors
    assert "Missing argument" in result.stdout

def test_zones_command() -> None:
    """Test the zones command with optional critical power."""
    result = runner.invoke(app, ["zones", "--critical-power", "250"])
    assert result.exit_code == 0
    assert "Calculating training zones" in result.stdout

def test_zones_command_no_power() -> None:
    """Test the zones command without critical power argument."""
    result = runner.invoke(app, ["zones"])
    assert result.exit_code == 0
    assert "Calculating training zones" in result.stdout

def test_analyze_command_with_weight_prompt(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with weight prompt."""
    # Create a test file
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power,heartrate,cadence,elevation,pace,elapsed_time\n"
                        "2024-01-30 07:00:00,1000,200,150,180,100,360,600")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mock_storage = mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    mock_service.return_value.process_file.return_value = []
    
    # Run command and simulate weight prompt input
    result = runner.invoke(app, ["analyze", str(test_file)], input="65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Processed" in result.stdout

def test_analyze_command_service_error(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command when service raises an error."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    mock_service.return_value.process_file.side_effect = ValueError("Invalid data format")
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file: Invalid data format" in result.stdout

def test_analyze_command_invalid_file(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with a non-existent file."""
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    
    result = runner.invoke(app, ["analyze", "nonexistent.csv", "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout

def test_analyze_command_with_workouts(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with multiple workouts."""
    from src.models.workout import WorkoutData
    
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    
    # Create mock workouts
    mock_workouts = [
        WorkoutData(
            id="w1",
            date=datetime.now(),
            distance=10.0,
            duration=3600,
            average_pace=360.0,
            average_power=200.0
        ),
        WorkoutData(
            id="w2",
            date=datetime.now(),
            distance=10.0,
            duration=3600,
            average_pace=360.0,
            average_power=250.0
        )
    ]
    mock_service.return_value.process_file.return_value = mock_workouts
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed 2 workouts" in result.stdout
    assert "3.1 W/kg" in result.stdout  # 200/65
    assert "3.8 W/kg" in result.stdout  # 250/65

def test_zones_command_with_critical_power() -> None:
    """Test the zones command with critical power calculation."""
    result = runner.invoke(app, ["zones", "--critical-power", "300"])
    
    assert result.exit_code == 0
    assert "Calculating training zones" in result.stdout

def test_analyze_command_invalid_weight(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with invalid weight value."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "-5.0"])
    
    assert result.exit_code == 2  # Typer validation error
    assert "Invalid value for '--weight'" in result.stdout

def test_analyze_command_invalid_weight_prompt(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with invalid weight input in prompt."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    
    # First try invalid input, then valid input
    result = runner.invoke(app, ["analyze", str(test_file)], input="-5.0\n65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Processed" in result.stdout

def test_zones_command_invalid_power() -> None:
    """Test the zones command with invalid critical power value."""
    result = runner.invoke(app, ["zones", "--critical-power", "-100"])
    
    assert result.exit_code == 2  # Typer validation error
    assert "Invalid value for '--critical-power'" in result.stdout

def test_zones_command_power_ranges() -> None:
    """Test the zones command with different power ranges."""
    # Test with low CP
    result_low = runner.invoke(app, ["zones", "--critical-power", "100"])
    assert result_low.exit_code == 0
    assert "Calculating training zones" in result_low.stdout
    
    # Test with high CP
    result_high = runner.invoke(app, ["zones", "--critical-power", "500"])
    assert result_high.exit_code == 0
    assert "Calculating training zones" in result_high.stdout

def test_main_function(mocker: MockerFixture) -> None:
    """Test the main entry point of the CLI."""
    mock_app = mocker.patch('src.cli.app')
    
    from src.cli import main
    main()
    
    mock_app.assert_called_once()

def test_analyze_command_empty_file(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with an empty file."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("")  # Empty file
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    mock_service.return_value.process_file.return_value = []
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed 0 workouts" in result.stdout

def test_analyze_command_invalid_weight_prompt_multiple_retries(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with multiple invalid weight inputs in prompt."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    
    # Try multiple invalid inputs before a valid one
    result = runner.invoke(app, ["analyze", str(test_file)], input="-5.0\n0\n-1.0\n65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Weight must be greater than 0" in result.stdout
    assert "Processed" in result.stdout

def test_analyze_command_unsupported_format_with_weight(tmp_path: Path) -> None:
    """Test the analyze command with unsupported format and weight."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    result = runner.invoke(app, ["analyze", str(test_file), "--format", "garmin", "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Format garmin not supported yet" in result.stdout

def test_analyze_command_file_not_found_with_weight() -> None:
    """Test the analyze command with non-existent file and weight."""
    result = runner.invoke(app, ["analyze", "nonexistent.csv", "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file: File nonexistent.csv does not exist" in result.stdout

def test_zones_command_with_zero_power() -> None:
    """Test the zones command with zero critical power."""
    result = runner.invoke(app, ["zones", "--critical-power", "0"])
    
    assert result.exit_code == 2  # Typer validation error
    assert "Invalid value for '--critical-power'" in result.stdout

def test_zones_command_with_negative_power() -> None:
    """Test the zones command with negative critical power."""
    result = runner.invoke(app, ["zones", "--critical-power", "-100"])
    
    assert result.exit_code == 2  # Typer validation error
    assert "Invalid value for '--critical-power'" in result.stdout

def test_analyze_command_with_multiple_workouts_and_weight_prompt(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test the analyze command with multiple workouts and weight prompt."""
    from src.models.workout import WorkoutData
    
    test_file = tmp_path / "workout.csv"
    test_file.write_text("time,distance,power\n2024-01-30,1000,200")
    
    # Mock dependencies
    mocker.patch('src.cli.LocalStackConfig')
    mocker.patch('src.cli.S3Storage')
    mock_service = mocker.patch('src.cli.StrydDataIngestionService')
    
    # Create mock workouts
    mock_workouts = [
        WorkoutData(
            id="w1",
            date=datetime.now(),
            distance=10.0,
            duration=3600,
            average_pace=360.0,
            average_power=200.0
        ),
        WorkoutData(
            id="w2",
            date=datetime.now(),
            distance=10.0,
            duration=3600,
            average_pace=360.0,
            average_power=250.0
        )
    ]
    mock_service.return_value.process_file.return_value = mock_workouts
    
    # Run command with weight prompt
    result = runner.invoke(app, ["analyze", str(test_file)], input="65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Processed 2 workouts" in result.stdout
    assert "3.1 W/kg" in result.stdout  # 200/65
    assert "3.8 W/kg" in result.stdout  # 250/65

def test_validate_weight():
    """Test weight validation."""
    # Test valid weight
    assert validate_weight(70.0) == 70.0
    
    # Test None weight
    assert validate_weight(None) is None
    
    # Test invalid weight
    with pytest.raises(typer.BadParameter, match="Weight must be greater than 0"):
        validate_weight(0.0)
    with pytest.raises(typer.BadParameter, match="Weight must be greater than 0"):
        validate_weight(-1.0)

def test_validate_critical_power():
    """Test critical power validation."""
    # Test valid critical power
    assert validate_critical_power(250) == 250
    
    # Test None critical power
    assert validate_critical_power(None) is None
    
    # Test invalid critical power
    with pytest.raises(typer.BadParameter, match="Critical power must be greater than 0"):
        validate_critical_power(0)
    with pytest.raises(typer.BadParameter, match="Critical power must be greater than 0"):
        validate_critical_power(-100)

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_success(mock_validator, mock_storage, mock_service, tmp_path):
    """Test successful workout file analysis."""
    # Create a test file
    test_file = tmp_path / "test_workout.csv"
    test_file.write_text("test data")
    
    # Mock service response
    mock_workout = WorkoutData(
        id="test123",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=170.0
    )
    mock_service_instance = Mock()
    mock_service_instance.process_file.return_value = [mock_workout]
    mock_service.return_value = mock_service_instance
    
    # Run command
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "70.0"])
    
    assert result.exit_code == 0
    assert "Processed 1 workouts" in result.stdout
    assert "Average Power: 250.0W (3.6 W/kg)" in result.stdout

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_file_not_found(mock_validator, mock_storage, mock_service):
    """Test analyze command with non-existent file."""
    result = runner.invoke(app, ["analyze", "nonexistent.csv", "--weight", "70.0"])
    
    assert result.exit_code == 1
    assert "File nonexistent.csv does not exist" in result.stdout

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_unsupported_format(mock_validator, mock_storage, mock_service, tmp_path):
    """Test analyze command with unsupported format."""
    # Create a test file
    test_file = tmp_path / "test_workout.fit"
    test_file.write_text("test data")
    
    result = runner.invoke(app, [
        "analyze",
        str(test_file),
        "--format", "fit",
        "--weight", "70.0"
    ])
    
    assert "Format fit not supported yet" in result.stdout

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_processing_error(mock_validator, mock_storage, mock_service, tmp_path):
    """Test analyze command with processing error."""
    # Create a test file
    test_file = tmp_path / "test_workout.csv"
    test_file.write_text("test data")
    
    # Mock service to raise an error
    mock_service_instance = Mock()
    mock_service_instance.process_file.side_effect = Exception("Processing error")
    mock_service.return_value = mock_service_instance
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "70.0"])
    
    assert result.exit_code == 1
    assert "Error processing file: Processing error" in result.stdout

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_weight_prompt(mock_validator, mock_storage, mock_service, tmp_path):
    """Test analyze command with weight prompt."""
    # Create a test file
    test_file = tmp_path / "test_workout.csv"
    test_file.write_text("test data")
    
    # Mock service response
    mock_workout = WorkoutData(
        id="test123",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=170.0
    )
    mock_service_instance = Mock()
    mock_service_instance.process_file.return_value = [mock_workout]
    mock_service.return_value = mock_service_instance
    
    # Run command without weight parameter (should prompt)
    result = runner.invoke(app, ["analyze", str(test_file)], input="70.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Processed 1 workouts" in result.stdout

def test_zones_command():
    """Test zones command."""
    result = runner.invoke(app, ["zones", "--critical-power", "250"])
    
    assert result.exit_code == 0
    assert "Calculating training zones..." in result.stdout

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_weight_prompt_invalid_input(mock_validator, mock_storage, mock_service, tmp_path):
    """Test analyze command with invalid weight prompt input."""
    # Create a test file
    test_file = tmp_path / "test_workout.csv"
    test_file.write_text("test data")
    
    # Mock service response
    mock_workout = WorkoutData(
        id="test123",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=170.0
    )
    mock_service_instance = Mock()
    mock_service_instance.process_file.return_value = [mock_workout]
    mock_service.return_value = mock_service_instance
    
    # Run command without weight parameter and provide invalid input first
    result = runner.invoke(app, ["analyze", str(test_file)], input="-1.0\n70.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Weight must be greater than 0" in result.stdout
    assert "Processed 1 workouts" in result.stdout

def test_main():
    """Test main entry point."""
    with patch('sys.argv', ['runctl', '--help']):
        with pytest.raises(SystemExit) as excinfo:
            app()
        assert excinfo.value.code == 0

@patch('src.cli.StrydDataIngestionService')
@patch('src.cli.S3Storage')
@patch('src.cli.StrydDataValidator')
def test_analyze_command_weight_prompt_none_input(mock_validator, mock_storage, mock_service, tmp_path):
    """Test analyze command with None weight prompt input."""
    # Create a test file
    test_file = tmp_path / "test_workout.csv"
    test_file.write_text("test data")
    
    # Mock service response
    mock_workout = WorkoutData(
        id="test123",
        date="2024-02-06T12:00:00",
        distance=10000.0,
        duration=3600,
        average_pace=360.0,
        average_power=250.0,
        total_elevation_gain=100.0,
        heart_rate=165.0,
        cadence=170.0
    )
    mock_service_instance = Mock()
    mock_service_instance.process_file.return_value = [mock_workout]
    mock_service.return_value = mock_service_instance
    
    # Mock validate_weight to return None once
    original_validate = validate_weight
    validation_count = 0
    def mock_validate(value):
        nonlocal validation_count
        if validation_count == 0:
            validation_count += 1
            return None
        return original_validate(value)
    
    with patch('src.cli.validate_weight', side_effect=mock_validate):
        result = runner.invoke(app, ["analyze", str(test_file)], input="0.0\n70.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Weight must be greater than 0" in result.stdout
    assert "Processed 1 workouts" in result.stdout

def test_main_entry():
    """Test main entry point when run as script."""
    with patch('src.cli.app') as mock_app:
        with patch('src.cli.__name__', '__main__'):
            main()
            mock_app.assert_called_once()