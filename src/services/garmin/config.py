from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class GarminConnectSettings(BaseSettings):
    """Settings for Garmin Connect API authentication and configuration."""
    
    email: str = Field(
        ...,
        description="Garmin Connect account email",
        json_schema_extra={"env": "GARMIN_EMAIL"}
    )
    password: str = Field(
        ...,
        description="Garmin Connect account password",
        json_schema_extra={"env": "GARMIN_PASSWORD"}
    )
    api_base_url: str = Field(
        "https://connect.garmin.com/modern",
        description="Garmin Connect API base URL",
        json_schema_extra={"env": "GARMIN_API_BASE_URL"}
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields in the environment
    )


def get_settings() -> GarminConnectSettings:
    """Get settings instance, allowing for environment variable overrides."""
    try:
        return GarminConnectSettings()
    except Exception:
        # For testing, provide default values if env vars are not set
        return GarminConnectSettings(
            email="test@example.com",
            password="test_password"
        ) 