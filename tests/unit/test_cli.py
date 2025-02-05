from typing import TYPE_CHECKING
from pathlib import Path
from typer.testing import CliRunner
import pytest
from pytest_mock import MockerFixture
from datetime import datetime

from src.cli import app

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