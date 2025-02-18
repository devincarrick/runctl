# RunCTL Project Structure

## Directory Organization

```
runctl/
├── docs/                      # Documentation
│   ├── adr/                  # Architecture Decision Records
│   ├── api/                  # API documentation
│   └── user/                 # User documentation
├── runctl/                   # Main package directory
│   ├── __init__.py
│   ├── cli/                  # Command-line interface
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── tui/                  # Terminal User Interface
│   │   ├── __init__.py
│   │   ├── app.py           # Main application
│   │   ├── components/      # Reusable UI components
│   │   └── screens/         # Screen definitions
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── analysis.py      # Analysis functions
│   │   ├── models.py        # Data models
│   │   └── utils.py         # Utility functions
│   ├── data/                # Data handling
│   │   ├── __init__.py
│   │   ├── csv.py          # CSV processing
│   │   ├── garmin.py       # Garmin integration
│   │   └── storage.py      # Database operations
│   └── config/              # Configuration
│       ├── __init__.py
│       └── settings.py
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_analysis.py
│   ├── test_data.py
│   └── test_tui.py
├── data/                     # Sample data and resources
│   └── samples/
├── scripts/                  # Development and deployment scripts
├── .env.example             # Environment variables template
├── .gitignore
├── LICENSE
├── MANIFEST.in
├── README.md
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Production dependencies
└── requirements-dev.txt     # Development dependencies
```

## Key Components

### TUI Components

- `app.py`: Main application entry point
- `components/`: Reusable UI elements
- `screens/`: Individual screen implementations

### Core Components

- `analysis.py`: Running metrics analysis
- `models.py`: Data models and schemas
- `utils.py`: Helper functions and utilities

### Data Handling

- `csv.py`: CSV file processing
- `garmin.py`: Garmin API integration
- `storage.py`: Database operations

### Configuration

- `settings.py`: Application settings and constants
- `.env`: Environment-specific configuration

## Development Guidelines

### Code Organization

- Keep modules focused and single-responsibility
- Use clear, descriptive names
- Follow PEP 8 style guide
- Document all public interfaces

### Testing

- Write tests for all new features
- Maintain test coverage > 80%
- Use pytest for testing
- Include both unit and integration tests

### Documentation

- Update docs with code changes
- Include docstrings for all functions
- Maintain ADRs for major decisions
- Keep README current

### Version Control

- Use feature branches
- Write clear commit messages
- Follow conventional commits
- Regular rebasing with main

## Dependencies

### Production

- blessed
- pandas
- numpy
- garth
- sqlalchemy
- pydantic

### Development

- pytest
- black
- isort
- mypy
- pylint
- pytest-cov
