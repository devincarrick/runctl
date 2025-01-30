from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import pandas as pd
import pytest

from src.services.stryd import StrydDataValidator, S3Storage, StrydDataIngestionService
from src.utils.exceptions import DataValidationError

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

def test_stryd_validator_required_columns() -> None:
    """Test validation of required columns."""
    validator = StrydDataValidator()
    df = pd.DataFrame({
        'time': [],
        'distance': [],
        'power': []
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
        'elapsed_time': [600]  # Added missing column
    })
    
    is_valid, messages = validator.validate(df)
    assert not is_valid
    assert "Power values must be between 0 and 1000 watts" in messages

# Add more tests as needed