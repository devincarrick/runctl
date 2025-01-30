from typing import TYPE_CHECKING
from pathlib import Path
from typer.testing import CliRunner
import pytest
from pytest_mock import MockerFixture

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
    
    # Run command with the test file
    result = runner.invoke(app, ["analyze", str(test_file)])
    
    assert result.exit_code == 0
    assert "Successfully processed" in result.stdout

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