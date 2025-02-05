import pytest
from pathlib import Path
from typer.testing import CliRunner
import boto3
import shutil
from datetime import datetime

from src.cli import app
from src.infra.localstack.config import LocalStackConfig, setup_localstack_resources

runner = CliRunner()

@pytest.fixture(scope="module")
def localstack_setup():
    """Set up LocalStack resources for testing."""
    config = LocalStackConfig()
    setup_localstack_resources()
    return config

@pytest.fixture(scope="function")
def sample_workout_file(tmp_path):
    """Create a sample workout file for testing."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8\n"
        "2024-01-30 07:01:00,2000,3.5,155,182,102,2.9\n"
        "2024-01-30 07:02:00,3000,3.2,153,181,103,2.85"
    )
    return test_file

@pytest.fixture(scope="function")
def real_workout_file(tmp_path):
    """Copy a real workout file from test data for testing."""
    source_file = Path("tests/data/real_workout_test.csv")
    if not source_file.exists():
        pytest.skip("Real workout test file not found")
    
    dest_file = tmp_path / "real_workout.csv"
    shutil.copy(source_file, dest_file)
    return dest_file

def test_analyze_command_with_real_file(real_workout_file, localstack_setup):
    """Test analyzing a real workout file with LocalStack integration."""
    # Run command with the test file
    result = runner.invoke(app, ["analyze", str(real_workout_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed" in result.stdout
    assert "Average Power" in result.stdout
    assert "W/kg" in result.stdout

def test_analyze_command_data_persistence(sample_workout_file, localstack_setup):
    """Test that workout data is properly stored in S3 and DynamoDB."""
    # Run analyze command
    result = runner.invoke(app, ["analyze", str(sample_workout_file), "--weight", "70.0"])
    assert result.exit_code == 0
    
    # Verify data in S3
    s3 = boto3.client(
        's3',
        endpoint_url=localstack_setup.endpoint_url,
        aws_access_key_id=localstack_setup.aws_access_key_id,
        aws_secret_access_key=localstack_setup.aws_secret_access_key,
        region_name=localstack_setup.region_name
    )
    
    # List objects in the raw data bucket
    response = s3.list_objects_v2(Bucket="runctl-raw-data")
    assert 'Contents' in response
    assert len(response['Contents']) > 0

def test_analyze_command_with_weight_prompt_integration(sample_workout_file, localstack_setup):
    """Test the weight prompt in an integration scenario."""
    result = runner.invoke(app, ["analyze", str(sample_workout_file)], input="65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Processed" in result.stdout
    assert "Average Power" in result.stdout

def test_analyze_command_multiple_files(tmp_path, localstack_setup):
    """Test analyzing multiple workout files in sequence."""
    # Create two test files
    file1 = tmp_path / "workout1.csv"
    file2 = tmp_path / "workout2.csv"
    
    file1.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8"
    )
    file2.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-31 07:00:00,1000,3.2,155,182,102,2.9"
    )
    
    # Process both files
    result1 = runner.invoke(app, ["analyze", str(file1), "--weight", "65.0"])
    result2 = runner.invoke(app, ["analyze", str(file2), "--weight", "65.0"])
    
    assert result1.exit_code == 0 and result2.exit_code == 0
    assert "Processed" in result1.stdout and "Processed" in result2.stdout

def test_analyze_command_invalid_csv_format(tmp_path, localstack_setup):
    """Test handling of invalid CSV format."""
    invalid_file = tmp_path / "invalid.csv"
    invalid_file.write_text("invalid,csv,format\n1,2,3")
    
    result = runner.invoke(app, ["analyze", str(invalid_file), "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout

def test_analyze_command_large_file(tmp_path, localstack_setup):
    """Test processing a larger workout file."""
    large_file = tmp_path / "large_workout.csv"
    
    # Create a file with 1000 rows
    header = "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
    rows = []
    for i in range(1000):
        time = datetime.now().replace(minute=i % 60, second=0).strftime("%Y-%m-%d %H:%M:%S")
        rows.append(f"{time},{1000+i},3.0,150,180,100,2.8")
    
    large_file.write_text(header + "\n".join(rows))
    
    result = runner.invoke(app, ["analyze", str(large_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed" in result.stdout

def test_analyze_command_with_weight_prompt_invalid_inputs(tmp_path, localstack_setup):
    """Test the analyze command with invalid weight inputs in an integration scenario."""
    # Create test file
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8"
    )
    
    # Try multiple invalid inputs before a valid one
    result = runner.invoke(app, ["analyze", str(test_file)], input="-5.0\n0\n-1.0\n65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Weight must be greater than 0" in result.stdout
    assert "Processed" in result.stdout

def test_analyze_command_with_empty_file(tmp_path, localstack_setup):
    """Test analyzing an empty file."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    
    result = runner.invoke(app, ["analyze", str(empty_file), "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout

def test_analyze_command_with_missing_columns(tmp_path, localstack_setup):
    """Test analyzing a file with missing required columns."""
    invalid_file = tmp_path / "invalid.csv"
    invalid_file.write_text(
        "Timestamp,Power (w/kg)\n"  # Missing required columns
        "2024-01-30 07:00:00,3.0"
    )
    
    result = runner.invoke(app, ["analyze", str(invalid_file), "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout

def test_analyze_command_with_invalid_data(tmp_path, localstack_setup):
    """Test analyzing a file with invalid data values."""
    invalid_file = tmp_path / "invalid.csv"
    invalid_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,-1000,3.0,150,180,100,2.8"  # Invalid negative distance
    )
    
    result = runner.invoke(app, ["analyze", str(invalid_file), "--weight", "65.0"])
    
    assert result.exit_code == 1
    assert "Error processing file" in result.stdout

def test_analyze_command_with_unsupported_format(tmp_path, localstack_setup):
    """Test analyzing a file with unsupported format."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8"
    )
    
    result = runner.invoke(app, ["analyze", str(test_file), "--format", "garmin", "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Format garmin not supported yet" in result.stdout

def test_analyze_command_with_nan_values(tmp_path, localstack_setup):
    """Test analyzing a file with NaN values."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,,180,100,2.8\n"  # Missing heart rate
        "2024-01-30 07:01:00,2000,3.5,155,182,102,2.9"
    )
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed" in result.stdout

def test_analyze_command_with_zero_speed(tmp_path, localstack_setup):
    """Test analyzing a file with zero speed values."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,0.0"  # Zero speed
    )
    
    result = runner.invoke(app, ["analyze", str(test_file), "--weight", "65.0"])
    
    assert result.exit_code == 0
    assert "Processed" in result.stdout

def test_zones_command_with_invalid_power(localstack_setup):
    """Test zones command with invalid critical power values."""
    # Test with negative power
    result_negative = runner.invoke(app, ["zones", "--critical-power", "-100"])
    assert result_negative.exit_code == 2
    assert "Invalid value for '--critical-power'" in result_negative.stdout
    
    # Test with zero power
    result_zero = runner.invoke(app, ["zones", "--critical-power", "0"])
    assert result_zero.exit_code == 2
    assert "Invalid value for '--critical-power'" in result_zero.stdout

def test_main_function_integration():
    """Test the main entry point of the CLI in an integration scenario."""
    from src.cli import main
    import sys
    from io import StringIO
    
    # Capture stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    try:
        # Call main with no arguments (should show error)
        sys.argv = ["runctl"]
        main()
    except SystemExit as e:
        assert e.code == 2  # Typer returns 2 for missing command
    finally:
        stderr = sys.stderr.getvalue()
        stdout = sys.stdout.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    assert "Usage: runctl" in stderr
    assert "Missing command" in stderr

def test_analyze_command_weight_prompt_multiple_errors(tmp_path, localstack_setup):
    """Test the analyze command with multiple weight prompt errors."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8"
    )
    
    # Try multiple invalid inputs including non-numeric values
    result = runner.invoke(app, ["analyze", str(test_file)], input="abc\n-5.0\n0\n-1.0\n65.0\n")
    
    assert result.exit_code == 0
    assert "Enter athlete weight in kg" in result.stdout
    assert "Weight must be greater than 0" in result.stdout
    assert "Processed" in result.stdout

def test_zones_command_with_default_values(localstack_setup):
    """Test the zones command with default values."""
    result = runner.invoke(app, ["zones"])
    
    assert result.exit_code == 0
    assert "Calculating training zones" in result.stdout

def test_zones_command_with_valid_power(localstack_setup):
    """Test the zones command with valid critical power."""
    result = runner.invoke(app, ["zones", "--critical-power", "300"])
    
    assert result.exit_code == 0
    assert "Calculating training zones" in result.stdout

def test_cli_help_command():
    """Test the CLI help command."""
    result = runner.invoke(app, ["--help"])
    
    assert result.exit_code == 0
    assert "Usage: runctl" in result.stdout
    assert "analyze" in result.stdout.lower()
    assert "zones" in result.stdout.lower()

def test_analyze_command_help():
    """Test the analyze command help."""
    result = runner.invoke(app, ["analyze", "--help"])
    
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "--format" in result.stdout
    assert "--weight" in result.stdout

def test_zones_command_help():
    """Test the zones command help."""
    result = runner.invoke(app, ["zones", "--help"])
    
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "--critical-power" in result.stdout

def test_analyze_command_with_invalid_format_and_weight_prompt(tmp_path, localstack_setup):
    """Test analyze command with invalid format and weight prompt."""
    test_file = tmp_path / "workout.csv"
    test_file.write_text(
        "Timestamp,Stryd Distance (meters),Power (w/kg),Heart Rate (bpm),Cadence (spm),Stryd Elevation (m),Watch Speed (m/s)\n"
        "2024-01-30 07:00:00,1000,3.0,150,180,100,2.8"
    )
    
    result = runner.invoke(app, ["analyze", str(test_file), "--format", "invalid"], input="65.0\n")
    
    assert result.exit_code == 0
    assert "Format invalid not supported yet" in result.stdout 