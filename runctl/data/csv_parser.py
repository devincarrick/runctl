"""CSV parser for running metrics data."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd

from .models import RunningMetrics, RunningSession
from .validation import DataValidationError, validate_metrics


class CSVParser:
    """Parser for CSV files containing running metrics."""

    # Column indices for the raw workout format
    RAW_WORKOUT_COLUMNS = {
        'timestamp': 0,
        'distance': 1,  # normalized, needs scaling
        'duration': 2,  # normalized, needs scaling
        'elevation': 3,  # normalized, needs scaling
        'speed': 4,     # current speed
        'avg_speed': 5, # average speed
        'total_distance': 6,
        'total_time': 7,
        'heart_rate': 8,
        'cadence': 9,   # normalized, needs scaling
        'power': 10,
        'avg_power': 11,
        'temperature': 12,
        'grade': 13,
        'resistance': 14
    }

    # Column names for Stryd format
    STRYD_COLUMNS = {
        'timestamp': 'Timestamp',
        'power': 'Power (w/kg)',
        'form_power': 'Form Power (w/kg)',
        'air_power': 'Air Power (w/kg)',
        'watch_speed': 'Watch Speed (m/s)',
        'stryd_speed': 'Stryd Speed (m/s)',
        'watch_distance': 'Watch Distance (meters)',
        'stryd_distance': 'Stryd Distance (meters)',
        'stiffness': 'Stiffness',
        'stiffness_kg': 'Stiffness/kg',
        'ground_time': 'Ground Time (ms)',
        'cadence': 'Cadence (spm)',
        'vertical_oscillation': 'Vertical Oscillation (cm)',
        'watch_elevation': 'Watch Elevation (m)',
        'stryd_elevation': 'Stryd Elevation (m)',
        'ground_time_balance': 'Ground Time Balance',
        'vertical_oscillation_balance': 'Vertical Oscillation Balance',
        'leg_spring_stiffness_balance': 'Leg Spring Stiffness Balance',
        'impact_loading_rate_balance': 'Impact Loading Rate Balance',
        'vertical_ratio': 'Vertical Ratio'
    }

    REQUIRED_COLUMNS = {
        'timestamp',
        'distance',
        'duration',
        'avg_pace'
    }

    OPTIONAL_COLUMNS = {
        'avg_heart_rate',
        'max_heart_rate',
        'elevation_gain',
        'calories',
        'cadence',
        'temperature',
        'weather_condition',
        'notes',
        'tags',
        'equipment'
    }

    def __init__(self, csv_path: Path, format_type: str = 'standard', check_exists: bool = True):
        """Initialize the CSV parser.
        
        Args:
            csv_path: Path to the CSV file
            format_type: Type of CSV format ('standard' or 'raw_workout' or 'stryd')
            check_exists: Whether to check if the file exists
            
        Raises:
            FileNotFoundError: If check_exists is True and the CSV file doesn't exist
        """
        self.csv_path = Path(csv_path)
        self.format_type = format_type
        if check_exists and not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            datetime: Parsed datetime object
            
        Raises:
            ValueError: If timestamp format is invalid
        """
        try:
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d"
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")
        except Exception as e:
            raise ValueError(f"Error parsing timestamp: {e}")

    def _convert_to_float(self, value: str, field: str) -> Optional[float]:
        """Convert string value to float, handling empty values.
        
        Args:
            value: String value to convert
            field: Field name for error messages
            
        Returns:
            Optional[float]: Converted float value or None if empty
            
        Raises:
            ValueError: If value cannot be converted to float
        """
        if not value or value.lower() in ('na', 'n/a', ''):
            return None
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid {field} value: {value}")

    def _parse_tags(self, tags_str: str) -> list[str]:
        """Parse tags string into list of tags.
        
        Args:
            tags_str: Comma-separated tags string
            
        Returns:
            list[str]: List of parsed tags
        """
        if not tags_str or tags_str.lower() in ('na', 'n/a', ''):
            return []
        return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

    def _parse_raw_workout_timestamp(self, value: str) -> datetime:
        """Parse timestamp from raw workout format.
        
        Args:
            value: Raw timestamp value
            
        Returns:
            datetime: Parsed datetime
        """
        try:
            # The timestamp appears to be Unix timestamp in seconds
            timestamp = float(value)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp value: {value}") from e

    def _scale_raw_workout_value(self, value: str, field: str) -> float:
        """Scale normalized values from raw workout format.
        
        Args:
            value: Raw value to scale
            field: Field name for scaling rules
            
        Returns:
            float: Scaled value
        """
        try:
            raw_value = float(value)
            if field == 'distance':
                return raw_value * 1000  # Convert to meters
            elif field == 'duration':
                return raw_value * 3600  # Convert to seconds
            elif field == 'cadence':
                return raw_value * 60    # Convert to steps per minute
            return raw_value
        except ValueError as e:
            raise ValueError(f"Invalid {field} value: {value}") from e

    def parse(self) -> Iterator[RunningSession]:
        """Parse the CSV file and yield RunningSession objects.
        
        Yields:
            RunningSession: Parsed running session data
            
        Raises:
            DataValidationError: If data validation fails
            ValueError: If required fields are missing or invalid
        """
        if self.format_type == 'raw_workout':
            yield from self._parse_raw_workout()
        elif self.format_type == 'stryd':
            yield from self._parse_stryd()
        else:
            yield from self._parse_standard()

    def _parse_raw_workout(self) -> Iterator[RunningSession]:
        """Parse raw workout format CSV file.
        
        Yields:
            RunningSession: Parsed running session data
        """
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.reader(f)
                for idx, row in enumerate(reader, 1):
                    try:
                        # Extract and convert values
                        timestamp = self._parse_raw_workout_timestamp(row[self.RAW_WORKOUT_COLUMNS['timestamp']])
                        distance = self._scale_raw_workout_value(row[self.RAW_WORKOUT_COLUMNS['distance']], 'distance')
                        duration = self._scale_raw_workout_value(row[self.RAW_WORKOUT_COLUMNS['duration']], 'duration')
                        
                        # Calculate pace from speed
                        speed = float(row[self.RAW_WORKOUT_COLUMNS['speed']])
                        if speed > 0:
                            pace = 1000 / speed  # Convert to seconds per kilometer
                        else:
                            pace = 0
                        
                        metrics = RunningMetrics(
                            timestamp=timestamp,
                            distance=distance,
                            duration=duration,
                            avg_pace=pace,
                            avg_heart_rate=float(row[self.RAW_WORKOUT_COLUMNS['heart_rate']]),
                            cadence=self._scale_raw_workout_value(row[self.RAW_WORKOUT_COLUMNS['cadence']], 'cadence'),
                            temperature=float(row[self.RAW_WORKOUT_COLUMNS['temperature']])
                        )
                        
                        # Validate metrics with raw workout mode
                        validate_metrics(metrics, is_raw_workout=True)
                        
                        session = RunningSession(
                            id=f"RUN_{idx}_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}",
                            metrics=metrics
                        )
                        
                        yield session
                        
                    except (ValueError, DataValidationError) as e:
                        # Log error but continue processing other rows
                        print(f"Error processing row {idx}: {e}")
                        continue
                    
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {e}")

    def _parse_standard(self) -> Iterator[RunningSession]:
        """Parse standard format CSV file.
        
        Yields:
            RunningSession: Parsed running session data
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Validate required columns
            required_columns = {'timestamp', 'distance', 'duration', 'avg_pace'}
            missing_cols = required_columns - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Process each row
            for idx, row in df.iterrows():
                try:
                    metrics = RunningMetrics(
                        timestamp=self._parse_timestamp(row['timestamp']),
                        distance=self._convert_to_float(str(row['distance']), 'distance'),
                        duration=self._convert_to_float(str(row['duration']), 'duration'),
                        avg_pace=self._convert_to_float(str(row['avg_pace']), 'avg_pace'),
                        avg_heart_rate=self._convert_to_float(str(row.get('avg_heart_rate', '')), 'avg_heart_rate'),
                        max_heart_rate=self._convert_to_float(str(row.get('max_heart_rate', '')), 'max_heart_rate'),
                        elevation_gain=self._convert_to_float(str(row.get('elevation_gain', '')), 'elevation_gain'),
                        calories=self._convert_to_float(str(row.get('calories', '')), 'calories'),
                        cadence=self._convert_to_float(str(row.get('cadence', '')), 'cadence'),
                        temperature=self._convert_to_float(str(row.get('temperature', '')), 'temperature'),
                        weather_condition=row.get('weather_condition')
                    )
                    
                    # Validate metrics
                    validate_metrics(metrics)
                    
                    session = RunningSession(
                        id=f"RUN_{idx}_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}",
                        metrics=metrics,
                        notes=row.get('notes'),
                        tags=self._parse_tags(str(row.get('tags', ''))),
                        equipment=row.get('equipment')
                    )
                    
                    yield session
                    
                except (ValueError, DataValidationError) as e:
                    # Log error but continue processing other rows
                    print(f"Error processing row {idx}: {e}")
                    continue
                
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {e}")

    def _parse_stryd_timestamp(self, value: str) -> datetime:
        """Parse timestamp from Stryd format.
        
        Args:
            value: Stryd timestamp value (Unix timestamp in seconds)
            
        Returns:
            datetime: Parsed datetime
        """
        try:
            # Stryd uses Unix timestamp (seconds since epoch)
            timestamp = float(value)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid Stryd timestamp value: {value}") from e

    def _parse_stryd(self) -> Iterator[RunningSession]:
        """Parse Stryd format CSV file.
        
        Yields:
            RunningSession: Parsed running session data
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Validate required Stryd columns
            missing_cols = set(self.STRYD_COLUMNS.values()) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required Stryd columns: {missing_cols}")
            
            # Group data points into sessions (when there's a gap > 5 minutes)
            df['datetime'] = df[self.STRYD_COLUMNS['timestamp']].apply(self._parse_stryd_timestamp)
            df['time_diff'] = df['datetime'].diff()
            session_breaks = df['time_diff'] > pd.Timedelta(minutes=5)
            df['session_id'] = session_breaks.cumsum()
            
            # Process each session
            for session_id, session_data in df.groupby('session_id'):
                if len(session_data) < 2:  # Skip single-point sessions
                    continue
                
                # Calculate session metrics
                start_time = session_data['datetime'].iloc[0]
                duration = (session_data['datetime'].iloc[-1] - start_time).total_seconds()
                
                # Use Stryd distance if available, fall back to watch distance
                total_distance = session_data[self.STRYD_COLUMNS['stryd_distance']].iloc[-1]
                if pd.isna(total_distance) or total_distance == 0:
                    total_distance = session_data[self.STRYD_COLUMNS['watch_distance']].iloc[-1]
                
                # Calculate average pace (s/km)
                avg_speed = total_distance / duration if duration > 0 else 0
                avg_pace = 1000 / avg_speed if avg_speed > 0 else 0
                
                # Create metrics object
                metrics = RunningMetrics(
                    timestamp=start_time,
                    distance=total_distance,
                    duration=duration,
                    avg_pace=avg_pace,
                    cadence=session_data[self.STRYD_COLUMNS['cadence']].mean(),
                    power=session_data[self.STRYD_COLUMNS['power']].mean(),
                    ground_time=session_data[self.STRYD_COLUMNS['ground_time']].mean(),
                    vertical_oscillation=session_data[self.STRYD_COLUMNS['vertical_oscillation']].mean(),
                    elevation=session_data[self.STRYD_COLUMNS['stryd_elevation']].mean()
                )
                
                # Create session
                session = RunningSession(
                    id=f"STRYD_{start_time.strftime('%Y%m%d_%H%M%S')}",
                    metrics=metrics
                )
                
                yield session
                
        except Exception as e:
            raise ValueError(f"Error parsing Stryd CSV file: {e}") 