from typing import TYPE_CHECKING
from typer.testing import CliRunner
import pytest

from src.cli import app

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

runner = CliRunner()

def test_analyze_command() -> None:
    """Test the analyze command with valid arguments."""
    result = runner.invoke(app, ["analyze", "workout.csv"])
    assert result.exit_code == 0
    assert "Analyzing workout.csv in stryd format" in result.stdout

def test_analyze_command_with_format() -> None:
    """Test the analyze command with custom format."""
    result = runner.invoke(app, ["analyze", "workout.csv", "--format", "garmin"])
    assert result.exit_code == 0
    assert "Analyzing workout.csv in garmin format" in result.stdout

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