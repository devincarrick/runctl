"""Data models for Garmin Connect API responses."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class SleepLevel(BaseModel):
    """Sleep level data within a sleep period."""
    start_time_in_seconds: int = Field(
        ..., 
        alias="startTimeInSeconds",
        description="Start time of the sleep level in seconds from start of sleep"
    )
    end_time_in_seconds: int = Field(
        ..., 
        alias="endTimeInSeconds",
        description="End time of the sleep level in seconds from start of sleep"
    )
    activity_level: str = Field(
        ..., 
        alias="activityLevel",
        description="Sleep activity level (deep, light, rem, awake)"
    )

    model_config = ConfigDict(populate_by_name=True)

class SleepData(BaseModel):
    """Detailed sleep data for a single night."""
    calendar_date: datetime = Field(
        ..., 
        alias="calendarDate",
        description="The date of the sleep record"
    )
    duration_in_seconds: int = Field(
        ..., 
        alias="totalSleepSeconds",
        description="Total duration of sleep in seconds"
    )
    start_time_local: datetime = Field(
        ..., 
        alias="sleepStartTimeLocal",
        description="Local time when sleep started"
    )
    end_time_local: datetime = Field(
        ..., 
        alias="sleepEndTimeLocal",
        description="Local time when sleep ended"
    )
    sleep_levels: List[SleepLevel] = Field(
        default_factory=list, 
        alias="sleepLevels",
        description="Detailed sleep level data"
    )
    deep_sleep_seconds: int = Field(
        ..., 
        alias="deepSleepSeconds",
        description="Time spent in deep sleep"
    )
    light_sleep_seconds: int = Field(
        ..., 
        alias="lightSleepSeconds",
        description="Time spent in light sleep"
    )
    rem_sleep_seconds: int = Field(
        ..., 
        alias="remSleepSeconds",
        description="Time spent in REM sleep"
    )
    awake_seconds: int = Field(
        ..., 
        alias="awakeSeconds",
        description="Time spent awake"
    )
    validation_type: str = Field(
        ..., 
        alias="validationType",
        description="How the sleep was validated (e.g., 'DEVICE')"
    )
    average_spo2_value: Optional[float] = Field(
        None, 
        alias="averageSpO2Value",
        description="Average SpO2 value during sleep if available"
    )
    average_stress_during_sleep: Optional[float] = Field(
        None, 
        alias="averageStressDuringSleep",
        description="Average stress level during sleep if available"
    )
    overall_sleep_score: Optional[int] = Field(
        None, 
        alias="overallSleepScore",
        description="Overall sleep score if available"
    )

    model_config = ConfigDict(populate_by_name=True)

class StressLevel(BaseModel):
    """Stress level data point."""
    timestamp: datetime = Field(
        ..., 
        description="Timestamp of the stress measurement"
    )
    stress_level: int = Field(
        ..., 
        alias="stressLevel",
        description="Stress level value (0-100)"
    )
    source: str = Field(
        ..., 
        description="Source of the stress data"
    )

    model_config = ConfigDict(populate_by_name=True)

class StressData(BaseModel):
    """Detailed stress data for a time period."""
    start_time_local: datetime = Field(
        ..., 
        alias="startTimeLocal",
        description="Start time of the stress period"
    )
    end_time_local: datetime = Field(
        ..., 
        alias="endTimeLocal",
        description="End time of the stress period"
    )
    average_stress_level: int = Field(
        ..., 
        alias="averageStressLevel",
        description="Average stress level for the period"
    )
    max_stress_level: int = Field(
        ..., 
        alias="maxStressLevel",
        description="Maximum stress level in the period"
    )
    stress_duration_seconds: int = Field(
        ..., 
        alias="stressDurationSeconds",
        description="Duration of the stress period in seconds"
    )
    rest_stress_duration_seconds: int = Field(
        ..., 
        alias="restStressDurationSeconds",
        description="Duration of rest/recovery in seconds"
    )
    activity_stress_duration_seconds: int = Field(
        ..., 
        alias="activityStressDurationSeconds",
        description="Duration of activity stress in seconds"
    )
    low_stress_duration_seconds: int = Field(
        ..., 
        alias="lowStressDurationSeconds",
        description="Duration of low stress in seconds"
    )
    medium_stress_duration_seconds: int = Field(
        ..., 
        alias="mediumStressDurationSeconds",
        description="Duration of medium stress in seconds"
    )
    high_stress_duration_seconds: int = Field(
        ..., 
        alias="highStressDurationSeconds",
        description="Duration of high stress in seconds"
    )
    stress_levels: List[StressLevel] = Field(
        default_factory=list, 
        alias="stressLevels",
        description="Detailed stress level measurements"
    )

    model_config = ConfigDict(populate_by_name=True)

class BodyBattery(BaseModel):
    """Body Battery data point."""
    timestamp: datetime = Field(
        ..., 
        description="Timestamp of the body battery measurement"
    )
    body_battery_value: int = Field(
        ..., 
        alias="bodyBatteryValue",
        description="Body Battery value (0-100)"
    )
    status: str = Field(
        ..., 
        description="Status of the body battery measurement"
    )

    model_config = ConfigDict(populate_by_name=True)

class BodyBatteryData(BaseModel):
    """Detailed Body Battery data for a time period."""
    calendar_date: datetime = Field(
        ..., 
        alias="calendarDate",
        description="The date of the body battery record"
    )
    charged_value: int = Field(
        ..., 
        alias="chargedValue",
        description="Amount of body battery charged"
    )
    drained_value: int = Field(
        ..., 
        alias="drainedValue",
        description="Amount of body battery drained"
    )
    most_charged_value: int = Field(
        ..., 
        alias="mostChargedValue",
        description="Highest body battery value"
    )
    least_charged_value: int = Field(
        ..., 
        alias="leastChargedValue",
        description="Lowest body battery value"
    )
    body_battery_scores: List[BodyBattery] = Field(
        default_factory=list,
        alias="bodyBatteryScores",
        description="Detailed body battery measurements"
    )

    model_config = ConfigDict(populate_by_name=True)

class RecoveryData(BaseModel):
    """Combined recovery metrics including stress and body battery data."""
    date: datetime = Field(
        ...,
        description="The date of the recovery data"
    )
    stress_data: Optional[StressData] = Field(
        None,
        description="Stress metrics for the day"
    )
    body_battery_data: Optional[BodyBatteryData] = Field(
        None,
        description="Body Battery metrics for the day"
    )
    overall_recovery_score: Optional[int] = Field(
        None,
        description="Overall recovery score (0-100) if available"
    )

    model_config = ConfigDict(populate_by_name=True) 