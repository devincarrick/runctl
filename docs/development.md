# Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment management tool (venv)
- IDE with Python support (recommended: VS Code, PyCharm)

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/runctl.git
cd runctl
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Development Workflow

### 1. Task Selection
1. Check the [GitHub Issues](https://github.com/devincarrick/runctl/issues) for available tasks
2. Assign yourself to an issue
3. Move the issue to "In Progress" in the project board

### 2. Branch Management
- Create feature branches from `main`
- Use descriptive branch names:
  ```bash
  # Format: feature/issue-number-brief-description
  git checkout -b feature/123-fit-file-parser
  ```

### 3. Code Style
We follow PEP 8 guidelines with these additional requirements:

- Line length: 88 characters (Black default)
- Docstring style: Google format
- Type hints: Required for all functions
- Import order:
  1. Standard library
  2. Third-party packages
  3. Local modules

Example:
```python
from typing import Dict, Optional
import datetime

import pandas as pd
import numpy as np

from runctl.parsers import FITParser
```

### 4. Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=runctl

# Run specific test file
pytest tests/test_fit_parser.py
```

#### Writing Tests
- Place tests in the `tests/` directory
- Match source file structure
- Use descriptive test names
- Include docstrings explaining test purpose

Example:
```python
def test_fit_parser_validates_file_structure():
    """
    Ensure FITParser correctly validates FIT file structure.
    Tests both valid and corrupt file scenarios.
    """
    parser = FITParser("path/to/test/file.fit")
    assert parser.validate_file() is True
```

### 5. Documentation

#### Code Documentation
- All modules, classes, and functions must have docstrings
- Include type hints
- Document exceptions
- Provide usage examples

Example:
```python
def clean_heart_rate(
    fit_file: Path,
    stryd_file: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean heart rate data using multi-source validation.

    Args:
        fit_file: Path to the FIT file containing heart rate data
        stryd_file: Optional path to Stryd CSV file for power data
        config: Optional configuration dictionary

    Returns:
        Tuple containing:
        - DataFrame with cleaned heart rate data
        - Dictionary with cleaning statistics and metrics

    Raises:
        FileNotFoundError: If input files don't exist
        ValidationError: If data validation fails

    Example:
        >>> cleaned_data, stats = clean_heart_rate(
        ...     fit_file="activity.fit",
        ...     stryd_file="activity.csv"
        ... )
    """
```

### 6. Commit Guidelines
- Use clear, descriptive commit messages
- Follow conventional commits format:
  ```
  type(scope): description

  [optional body]
  [optional footer]
  ```
- Types: feat, fix, docs, style, refactor, test, chore
- Reference issue numbers in commits

Example:
```
feat(parser): implement FIT file validation
- Add structure validation
- Implement checksum verification
- Add error handling for corrupt files
Closes #123
```

### 7. Pull Request Process
1. Update documentation if needed
2. Ensure all tests pass
3. Update README if needed
4. Create pull request with:
   - Clear description
   - Issue reference
   - Testing notes
   - Screenshots (if UI changes)

### 8. Code Review
- All code must be reviewed before merging
- Address review comments promptly
- Request re-review after making changes
- Merge only after approval

## Development Tools

### Recommended VS Code Extensions
- Python
- Pylance
- Python Test Explorer
- GitLens
- Python Docstring Generator

### Code Quality Tools
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .
```

## Troubleshooting

### Common Issues

1. Import Errors
```bash
# Ensure you're in the project root
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

2. Virtual Environment
```bash
# If venv is not activating
deactivate  # if already in a venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

3. Test Data
```bash
# Generate test data
python3 scripts/generate_test_data.py
```

## Getting Help

- Check existing [documentation](docs/)
- Search [closed issues](link-to-closed-issues)
- Ask in [discussions](link-to-discussions)
- Contact maintainers

## Additional Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)