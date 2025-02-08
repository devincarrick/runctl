# runctl

Command line tool for running analytics and workout tracking, designed for developers who run.

## Installation

1. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install uv:
```bash
pip install uv
```

3. Install dependencies:
```bash
uv pip install -r requirements-dev.txt
```

## Usage

```bash
# Analyze a workout file
runctl analyze workout.csv --format stryd

# Calculate training zones
runctl zones --critical-power 250

# Get help
runctl --help
```

## Development

- Use `uv pip install {package}` to add dependencies
- Update requirements.txt and requirements-dev.txt as needed
- Run `ruff check . --fix` before commits
- Run `mypy src tests` for type checking

## Local Development with LocalStack

1. Start LocalStack:
```bash
docker-compose up -d
```

2. Run tests:
```bash
pytest
```
## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your actual API keys
3. Never commit `.env` to version control
4. For local overrides, use `.env.local`