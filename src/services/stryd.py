"""Stryd data ingestion service for processing running data files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple
from uuid import uuid4

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from loguru import logger

from src.models.workout import WorkoutData
from src.utils.exceptions import DataValidationError, StorageError
from src.infra.localstack.config import LocalStackConfig

class DataValidator(Protocol):
    """Protocol for data validation implementations."""
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate the input DataFrame."""
        ...

@dataclass
class StrydValidationRule:
    """Validation rule for Stryd data."""
    
    column: str
    validation_fn: callable
    error_message: str

class StrydDataValidator:
    """Validates Stryd CSV data format and contents."""
    
    REQUIRED_COLUMNS = [
        "time", "distance", "power", "heartrate",
        "cadence", "elevation", "pace", "elapsed_time"
    ]
    
    def __init__(self) -> None:
        """Initialize validator with standard validation rules."""
        self.rules: List[StrydValidationRule] = [
            StrydValidationRule(
                column="power",
                validation_fn=lambda x: x.between(0, 1000).all(),
                error_message="Power values must be between 0 and 1000 watts"
            ),
            StrydValidationRule(
                column="heartrate",
                validation_fn=lambda x: x[x.notna()].between(0, 250).all(),
                error_message="Heart rate values must be between 0 and 250 bpm"
            ),
            StrydValidationRule(
                column="distance",
                validation_fn=lambda x: (x >= 0).all(),
                error_message="Distance values must be non-negative"
            )
        ]

    def validate(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate Stryd data format and contents."""
        messages: List[str] = []
        
        missing_cols = set(self.REQUIRED_COLUMNS) - set(data.columns)
        if missing_cols:
            messages.append(f"Missing required columns: {missing_cols}")
            return False, messages
            
        for rule in self.rules:
            try:
                if not rule.validation_fn(data[rule.column]):
                    messages.append(rule.error_message)
            except Exception as e:
                messages.append(f"Error validating {rule.column}: {str(e)}")
                
        is_valid = len(messages) == 0
        return is_valid, messages

class S3Storage:
    """Handles S3 storage operations for workout data."""
    
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None
    ) -> None:
        """Initialize S3 storage handler."""
        self.bucket = bucket_name
        self.s3 = boto3.client('s3', endpoint_url=endpoint_url)
        
    def upload_file(self, file_path: Path, key: str) -> None:
        """Upload file to S3 bucket."""
        try:
            self.s3.upload_file(str(file_path), self.bucket, key)
        except ClientError as e:
            raise StorageError(f"Failed to upload file: {str(e)}") from e

class StrydDataIngestionService:
    """Service for ingesting Stryd workout data."""
    
    def __init__(self, storage: 'S3Storage', validator: 'StrydDataValidator') -> None:
        self.storage = storage
        self.validator = validator
        
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw Stryd data to expected format."""
        logger.debug(f"Columns before transform: {df.columns.tolist()}")
        
        # Create a new DataFrame with just the columns we need
        transformed_df = pd.DataFrame()
        
        # Transform each column individually
        transformed_df['time'] = pd.to_datetime(df['Timestamp'])
        transformed_df['power'] = df['Power (w/kg)'] * 70  # Convert to watts
        transformed_df['distance'] = df['Stryd Distance (meters)']
        transformed_df['cadence'] = df['Cadence (spm)']
        transformed_df['elevation'] = df['Stryd Elevation (m)']
        transformed_df['pace'] = df['Watch Speed (m/s)'].apply(lambda x: 1/x * 1000 if x > 0 else 0)
        transformed_df['elapsed_time'] = range(0, len(df) * 1000, 1000)
        
        # Handle heart rate - use actual value if present, otherwise None
        transformed_df['heartrate'] = (
            df['Heart Rate (bpm)'] if 'Heart Rate (bpm)' in df.columns 
            else pd.Series([None] * len(df))
        )
        
        # Ensure no NaN values in numeric columns
        numeric_columns = ['power', 'distance', 'cadence', 'elevation', 'pace']
        for col in numeric_columns:
            transformed_df[col] = transformed_df[col].fillna(0)
        
        logger.debug(f"Columns after transform: {transformed_df.columns.tolist()}")
        logger.debug(f"Power stats after transform:\n{transformed_df['power'].describe()}")
        
        return transformed_df
    
    def process_file(self, file_path: Path) -> List[WorkoutData]:
        """Process a Stryd CSV file."""
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Transform data
            df = self._transform_data(df)
            
            # Validate transformed data
            is_valid, messages = self.validator.validate(df)
            if not is_valid:
                raise DataValidationError("\n".join(messages))
            
            # Upload raw file to S3
            file_key = f"raw/{datetime.now().strftime('%Y/%m/%d')}/{file_path.name}"
            self.storage.upload_file(file_path, file_key)
            
            # Calculate workout-level metrics
            workout_metrics = {
                'average_power': df['power'].mean(),
                'distance': df['distance'].max(),  # Total distance
                'duration': df['elapsed_time'].max(),  # Total duration
                'average_pace': df['pace'].mean(),
                'total_elevation_gain': df['elevation'].max() - df['elevation'].min(),
                'average_heart_rate': df['heartrate'].mean() if 'heartrate' in df else None,
                'average_cadence': df['cadence'].mean()
            }
            
            logger.debug(f"Calculated workout metrics: {workout_metrics}")
            
            # Create single workout object with aggregated metrics
            workout = WorkoutData(
                id=str(uuid4()),
                date=df['time'].iloc[0],  # Use first timestamp
                distance=float(workout_metrics['distance']),
                duration=int(workout_metrics['duration']),
                average_pace=float(workout_metrics['average_pace']),
                average_power=float(workout_metrics['average_power']),
                total_elevation_gain=float(workout_metrics['total_elevation_gain']),
                heart_rate=float(workout_metrics['average_heart_rate']) if pd.notna(workout_metrics['average_heart_rate']) else None,
                cadence=float(workout_metrics['average_cadence'])
            )
            
            logger.info(f"Successfully processed workout with power: {workout.average_power:.2f} watts")
            return [workout]
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise