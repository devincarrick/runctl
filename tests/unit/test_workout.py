from datetime import datetime

from src.models.workout import WorkoutData


def test_workout_data_creation() -> None:
    """Test WorkoutData model creation and validation."""
    workout = WorkoutData(
        id="w123",
        date=datetime.now(),
        distance=10.0,
        duration=3600,
        average_pace=360.0
    )
    assert workout.id == "w123"
    assert workout.distance == 10.0
