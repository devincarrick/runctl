from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkoutData(BaseModel):
    """Model representing a running workout."""
    
    id: str
    date: datetime
    distance: float
    duration: int
    average_pace: float
    average_power: Optional[float] = None
    total_elevation_gain: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    cadence: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "w123",
                "date": "2024-01-23T10:30:00",
                "distance": 10.0,
                "duration": 3600,
                "average_pace": 360.0,
                "average_power": 250.0,
                "total_elevation_gain": 100.0,
                "heart_rate": 165.0,
                "temperature": 20.0,
                "humidity": 65.0,
                "cadence": 180.0
            }
        }
    )
