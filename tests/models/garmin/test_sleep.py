"""Tests for the sleep data model."""

from datetime import datetime, timedelta
from typing import List

import pytest
from pydantic import ValidationError
from zoneinfo import ZoneInfo

from src.models.garmin.sleep import SleepData, SleepStage, SleepStageInterval


def create_sleep_stages(
    start_time: datetime,
    durations: List[int],
    stages: List[SleepStage],
) -> List[SleepStageInterval]:
    """Helper function to create a list of sleep stages."""
    if len(durations) != len(stages):
        raise ValueError("durations and stages must have the same length")

    result = []
    current_time = start_time

    for duration, stage in zip(durations, stages):
        end_time = current_time + timedelta(seconds=duration)
        result.append(
            SleepStageInterval(
                stage=stage,
                start_time=current_time,
                end_time=end_time,
                duration_seconds=duration,
            )
        )
        current_time = end_time

    return result


def test_valid_sleep_data():
    """Test creating a valid sleep data instance."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    sleep_stages = create_sleep_stages(
        start_time=start_time,
        durations=[3600, 7200, 3600],  # 1h light, 2h deep, 1h rem
        stages=[SleepStage.LIGHT, SleepStage.DEEP, SleepStage.REM],
    )

    sleep_data = SleepData(
        user_id="test_user",
        start_time=start_time,
        end_time=start_time + timedelta(hours=4),
        duration_seconds=14400,  # 4 hours
        timezone="America/New_York",
        quality_score=85,
        deep_sleep_seconds=7200,  # 2h
        light_sleep_seconds=3600,  # 1h
        rem_sleep_seconds=3600,  # 1h
        awake_seconds=0,
        sleep_stages=sleep_stages,
    )

    assert sleep_data.user_id == "test_user"
    assert sleep_data.start_time == start_time
    assert sleep_data.duration_seconds == 14400
    assert len(sleep_data.sleep_stages) == 3


def test_invalid_timezone():
    """Test that invalid timezone raises validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    sleep_stages = create_sleep_stages(
        start_time=start_time,
        durations=[3600],
        stages=[SleepStage.LIGHT],
    )

    with pytest.raises(ValidationError, match="Invalid timezone"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            duration_seconds=3600,
            timezone="Invalid/Timezone",
            sleep_stages=sleep_stages,
        )


def test_invalid_quality_score():
    """Test that invalid quality score raises validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    sleep_stages = create_sleep_stages(
        start_time=start_time,
        durations=[3600],
        stages=[SleepStage.LIGHT],
    )

    with pytest.raises(ValidationError, match="Input should be less than or equal to 100"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            duration_seconds=3600,
            timezone="America/New_York",
            quality_score=101,
            sleep_stages=sleep_stages,
        )


def test_invalid_duration():
    """Test that duration mismatch raises validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    sleep_stages = create_sleep_stages(
        start_time=start_time,
        durations=[3600],
        stages=[SleepStage.LIGHT],
    )

    with pytest.raises(ValidationError, match="duration_seconds .* does not match time difference"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            duration_seconds=7200,  # Incorrect duration
            timezone="America/New_York",
            sleep_stages=sleep_stages,
        )


def test_sleep_stages_with_gap():
    """Test that sleep stages with gaps raise validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    stage1 = SleepStageInterval(
        stage=SleepStage.LIGHT,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        duration_seconds=3600,
    )
    # Gap of 1 hour
    stage2 = SleepStageInterval(
        stage=SleepStage.DEEP,
        start_time=start_time + timedelta(hours=2),
        end_time=start_time + timedelta(hours=3),
        duration_seconds=3600,
    )

    with pytest.raises(ValidationError, match="Gap or overlap detected between sleep stages"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=3),
            duration_seconds=10800,
            timezone="America/New_York",
            sleep_stages=[stage1, stage2],
        )


def test_sleep_stages_with_overlap():
    """Test that sleep stages with overlaps raise validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    stage1 = SleepStageInterval(
        stage=SleepStage.LIGHT,
        start_time=start_time,
        end_time=start_time + timedelta(hours=2),
        duration_seconds=7200,
    )
    # Overlaps with stage1
    stage2 = SleepStageInterval(
        stage=SleepStage.DEEP,
        start_time=start_time + timedelta(hours=1),
        end_time=start_time + timedelta(hours=3),
        duration_seconds=7200,
    )

    with pytest.raises(ValidationError, match="Gap or overlap detected between sleep stages"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=3),
            duration_seconds=10800,
            timezone="America/New_York",
            sleep_stages=[stage1, stage2],
        )


def test_mismatched_stage_durations():
    """Test that mismatched stage durations raise validation error."""
    start_time = datetime(2024, 2, 8, 22, 0, tzinfo=ZoneInfo("America/New_York"))
    sleep_stages = create_sleep_stages(
        start_time=start_time,
        durations=[3600, 3600],  # 1h light, 1h deep
        stages=[SleepStage.LIGHT, SleepStage.DEEP],
    )

    with pytest.raises(ValidationError, match="does not match sum of LIGHT stage durations"):
        SleepData(
            user_id="test_user",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            duration_seconds=7200,
            timezone="America/New_York",
            light_sleep_seconds=7200,  # Should be 3600
            deep_sleep_seconds=3600,
            sleep_stages=sleep_stages,
        ) 