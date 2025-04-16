# runctl

A Python tool for cleaning and validating heart rate data from running activities, with support for Garmin FIT files and Stryd CSV data.

## Features

- Multi-source heart rate data validation
- Power-based heart rate zone validation
- Statistical anomaly detection
- Data cleaning and interpolation
- Support for Garmin FIT and Stryd CSV formats

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/runctl.git
cd runctl
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python3 clean_heart_rate.py --fit-file activity.fit --output cleaned.fit
```

With Stryd data validation:
```bash
python3 clean_heart_rate.py --fit-file activity.fit --stryd-file activity.csv --output cleaned.fit
```

## Project Structure

```
runctl/
├── README.md
├── requirements.txt
├── clean_heart_rate.py
├── data/
│   ├── sample_fit/
│   │   └── sample.fit
│   └── sample_csv/
│       └── sample.csv
└── tests/
    ├── __init__.py
    ├── test_clean_heart_rate.py
    └── test_data/
        ├── sample.fit
        └── sample.csv
```

## License

MIT License 