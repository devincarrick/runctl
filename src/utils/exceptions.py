"""Custom exceptions for the application."""

class RunCtlError(Exception):
    """Base exception class for all application errors."""
    pass


class DataValidationError(RunCtlError):
    """Raised when data validation fails."""
    pass


class StorageError(RunCtlError):
    """Raised when storage operations fail."""
    pass


class ConfigurationError(RunCtlError):
    """Raised when there are configuration-related errors."""
    pass


class DataProcessingError(RunCtlError):
    """Raised when data processing operations fail."""
    pass


class ZoneCalculationError(RunCtlError):
    """Raised when training zone calculations fail."""
    pass


class AnalyticsError(RunCtlError):
    """Raised when analytics calculations fail."""
    pass


class APIError(RunCtlError):
    """Raised when external API calls fail."""
    
    def __init__(self, message: str, status_code: int = None, response: str = None):
        """Initialize API error with optional status code and response."""
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(RunCtlError):
    """Raised when authentication fails."""
    pass


class FileFormatError(DataValidationError):
    """Raised when file format is invalid or unsupported."""
    pass


class MetricCalculationError(DataProcessingError):
    """Raised when metric calculations fail."""
    pass