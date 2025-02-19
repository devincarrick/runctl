# RunCTL

A Terminal User Interface (TUI) application for analyzing running metrics, managing training data, and tracking fitness progress.

> **Note**: This project is currently in active development. Features are being implemented according to the [development plan](docs/development_plan.md).

## Features

- CSV running data analysis
- Garmin Connect integration (planned)
- Training metrics visualization (in progress)
- Equipment tracking (planned)
- Health metrics monitoring (planned)
- Performance analytics (in progress)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/runctl.git
cd runctl

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python -m runctl
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
ruff check runctl
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
