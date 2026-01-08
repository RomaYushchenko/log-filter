"""Custom exceptions for the log filter application."""


class LogFilterException(Exception):
    """Base exception for all log filter errors."""

    pass


class ParseError(LogFilterException):
    """Exception raised during expression parsing."""

    def __init__(self, message: str, position: int | None = None, expression: str = "") -> None:
        """Initialize parse error with context.

        Args:
            message: Error description
            position: Character position where error occurred
            expression: The expression being parsed
        """
        self.message = message
        self.position = position
        self.expression = expression

        if position is not None and expression:
            pointer = " " * position + "^"
            full_message = f"{message}\n  {expression}\n  {pointer}"
        else:
            full_message = message

        super().__init__(full_message)


class TokenizationError(ParseError):
    """Exception raised during tokenization."""

    pass


class EvaluationError(LogFilterException):
    """Exception raised during expression evaluation."""

    pass


class ConfigurationError(LogFilterException):
    """Exception raised for configuration validation errors."""

    pass


class FileHandlingError(LogFilterException):
    """Exception raised for file operation errors."""

    def __init__(self, message: str, file_path: str = "", cause: Exception | None = None) -> None:
        """Initialize file handling error with context.

        Args:
            message: Error description
            file_path: Path to the file that caused the error
            cause: Original exception that caused this error
        """
        self.file_path = file_path
        self.cause = cause

        if file_path:
            full_message = f"{message}: {file_path}"
        else:
            full_message = message

        if cause:
            full_message += f" (caused by: {cause})"

        super().__init__(full_message)


class RecordSizeExceededError(LogFilterException):
    """Exception raised when a log record exceeds size limits."""

    def __init__(self, size_kb: float, max_size_kb: int) -> None:
        """Initialize record size error.

        Args:
            size_kb: Actual size in KB
            max_size_kb: Maximum allowed size in KB
        """
        self.size_kb = size_kb
        self.max_size_kb = max_size_kb
        super().__init__(f"Record size {size_kb:.2f}KB exceeds limit of {max_size_kb}KB")
