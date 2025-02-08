import pytest
from src.services.garmin.config import GarminConnectSettings


def test_garmin_connect_settings_required_fields():
    """Test that required fields raise ValidationError when missing."""
    with pytest.raises(ValueError, match="Field required"):
        GarminConnectSettings()


def test_garmin_connect_settings_with_env_vars():
    """Test settings initialization with environment variables."""
    test_email = "test@example.com"
    test_password = "test_password"
    test_base_url = "https://test.garmin.com"
    
    settings = GarminConnectSettings(
        email=test_email,
        password=test_password,
        api_base_url=test_base_url
    )
    
    assert settings.email == test_email
    assert settings.password == test_password
    assert settings.api_base_url == test_base_url


def test_garmin_connect_settings_default_base_url():
    """Test that api_base_url has the correct default value."""
    test_email = "test@example.com"
    test_password = "test_password"
    
    settings = GarminConnectSettings(
        email=test_email,
        password=test_password
    )
    
    assert settings.api_base_url == "https://connect.garmin.com/modern" 