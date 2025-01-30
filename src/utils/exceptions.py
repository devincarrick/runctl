"""Custom exceptions for the application."""

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class StorageError(Exception):
    """Raised when storage operations fail."""
    pass