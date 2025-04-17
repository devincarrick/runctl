# runctl

A Python tool for cleaning and validating heart rate data from running activities, with support for Garmin FIT files and Stryd CSV data.

> **Note**: This project is currently in active initial development. Features and APIs are subject to change.

## Project Status

This project is in Phase 1 (Foundation) of development, focusing on:
- Multi-source heart rate data cleaning implementation
- Power-based heart rate validation
- Command-line interface development
- Testing framework establishment

## Planned Features

- [x] Project structure and development environment
- [ ] Multi-source heart rate data validation
  - [ ] FIT file parsing
  - [ ] Stryd CSV integration
  - [ ] Data alignment
- [ ] Heart rate anomaly detection
- [ ] Power-based validation
- [ ] Data cleaning and interpolation
- [ ] Comprehensive test suite
- [ ] API documentation

## Installation

> **Note**: These instructions are for development setup.

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
## Documentation

- [Project Overview](docs/overview.md)
- [Technical Architecture](docs/architecture.md)
- [Development Guide](docs/development.md)
- [API Documentation](docs/api.md) (coming soon)

## License

MIT License 