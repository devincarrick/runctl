# RunCTL

A comprehensive training and recovery management system.

## Features

- Garmin Connect integration for sleep and recovery metrics
- Training load analysis
- Recovery recommendations
- Workout planning and tracking

## Installation

1. Clone the repository:

```bash
git clone https://github.com/devincarrick/runctl.git
cd runctl
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

## Configuration

### Environment Variables

Required environment variables in `.env`:

```ini
# Garmin Connect Configuration
GARMIN_EMAIL=your.email@example.com
GARMIN_PASSWORD=your_password
GARMIN_API_BASE_URL=https://connect.garmin.com/modern

# Application Settings
LOG_LEVEL=INFO
ENABLE_DEBUG=false
```

## Usage

### Garmin Connect Integration

The Garmin Connect integration provides access to sleep, stress, and Body Battery data. Here are some examples:

#### Basic Usage

```python
from datetime import datetime
from src.services.garmin.garth_client import GarthClient

async def get_recovery_data():
    async with GarthClient() as client:
        # Get sleep data for a specific date
        date = datetime(2024, 2, 7)
        sleep_data = await client.get_sleep_data(date)

        # Get stress data for a date range
        start_date = datetime(2024, 2, 1)
        end_date = datetime(2024, 2, 7)
        stress_data = await client.get_stress_data_range(start_date, end_date)

        # Get Body Battery data
        body_battery = await client.get_body_battery_data(date)

        return {
            'sleep': sleep_data,
            'stress': stress_data,
            'body_battery': body_battery
        }
```

#### Error Handling

```python
import logging
from src.services.garmin.garth_client import GarthClient

async def get_data_with_error_handling():
    try:
        async with GarthClient() as client:
            date = datetime(2024, 2, 7)
            return await client.get_sleep_data(date)
    except Exception as e:
        logging.error(f"Failed to get sleep data: {e}")
        raise
```

#### Batch Processing

```python
import asyncio
from src.services.garmin.garth_client import GarthClient

async def get_multiple_days():
    async with GarthClient() as client:
        dates = [
            datetime(2024, 2, 1),
            datetime(2024, 2, 2),
            datetime(2024, 2, 3)
        ]
        tasks = [client.get_sleep_data(date) for date in dates]
        return await asyncio.gather(*tasks)
```

### Data Models

The integration uses Pydantic models for data validation:

```python
from src.services.garmin.models import SleepData, StressData, BodyBatteryData

# Sleep data structure
sleep_data = SleepData(
    calendar_date="2024-02-07",
    duration_in_seconds=28800,
    deep_sleep_seconds=7200,
    light_sleep_seconds=14400,
    rem_sleep_seconds=5400,
    awake_seconds=1800
)

# Access validated data
total_sleep_hours = sleep_data.duration_in_seconds / 3600
deep_sleep_percent = (sleep_data.deep_sleep_seconds / sleep_data.duration_in_seconds) * 100
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/services/garmin/test_garth_client.py

# Run with coverage
pytest --cov=src
```

### Code Style

The project uses Ruff for code formatting and linting:

```bash
# Check code style
ruff check .

# Fix code style issues
ruff check . --fix
```

## Documentation

- [Architecture Decision Records](docs/adr/README.md)
- [Troubleshooting Guide](docs/troubleshooting/garmin_connect.md)
- [API Documentation](docs/api_documentation.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
