from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorkoutData(BaseModel):
    """Model representing a running workout."""
    
    id: str
    date: datetime
    distance: float
    duration: int
    average_pace: float
    average_power: Optional[float] = None
    total_elevation_gain: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "w123",
                "date": "2024-01-23T10:30:00",
                "distance": 10.0,
                "duration": 3600,
                "average_pace": 360.0,
                "average_power": 250.0,
                "total_elevation_gain": 100.0
            }
        }
    )
