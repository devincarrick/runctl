# Contributing to RunCtl

Thank you for your interest in contributing to RunCtl! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Make (optional, but recommended)
- Git

### Initial Setup

1. Clone the repository:

```bash
git clone https://github.com/devincarrick/runctl.git
cd runctl
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. Start LocalStack (for AWS services emulation):

```bash
docker-compose up -d
```

5. Initialize development environment:

```bash
make init  # Sets up LocalStack resources
```

### Running Tests

The project uses pytest for testing. To run tests:

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run with coverage
make coverage
```

### Code Style

The project follows PEP 8 style guide and uses several tools to maintain code quality:

- Black for code formatting
- isort for import sorting
- flake8 for style guide enforcement
- mypy for type checking

To check code style:

```bash
make lint
```

To automatically fix formatting:

```bash
make format
```

## Project Structure

```
runctl/
├── src/
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   ├── utils/           # Utilities and helpers
│   ├── infra/          # Infrastructure code
│   └── cli.py          # CLI implementation
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── docs/               # Documentation
└── docker-compose.yml  # Docker services configuration
```

## Making Changes

1. Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, following these guidelines:

   - Write tests for new functionality
   - Update documentation as needed
   - Follow the existing code style
   - Add type hints to new code
   - Handle errors appropriately using custom exceptions

3. Commit your changes:

```bash
git add .
git commit -m "feat: description of your changes"
```

4. Push your changes and create a pull request:

```bash
git push origin feature/your-feature-name
```

## Pull Request Guidelines

1. Ensure all tests pass
2. Include tests for new functionality
3. Update documentation as needed
4. Follow the commit message convention:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - style: Code style changes
   - refactor: Code refactoring
   - test: Test changes
   - chore: Build process or auxiliary tool changes

## Getting Help

If you need help or have questions:

1. Check existing documentation
2. Search for similar issues
3. Create a new issue with a clear description
4. Tag appropriate maintainers

## Code of Conduct

Please note that this project follows a Code of Conduct. By participating in this project, you agree to abide by its terms.
