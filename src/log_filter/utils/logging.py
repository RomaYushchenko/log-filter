"""
Structured logging configuration for the log filter application.

This module provides centralized logging configuration with support
for multiple handlers, log levels, and structured output formats.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default log format with timestamp, level, component, and message
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    file_level: Optional[str] = None,
    console_level: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    log_to_console: bool = True,
) -> None:
    """Configure application logging with console and file handlers.

    Args:
        level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        file_level: Log level for file handler (defaults to level)
        console_level: Log level for console handler (defaults to level)
        format_string: Custom log format string
        date_format: Custom date format string
        log_to_console: Whether to log to console

    Example:
        >>> configure_logging(
        ...     level="INFO",
        ...     log_file=Path("app.log"),
        ...     file_level="DEBUG"
        ... )
    """
    # Parse log levels
    default_level = _parse_level(level)
    file_log_level = _parse_level(file_level or level)
    console_log_level = _parse_level(console_level or level)

    # Use custom format or default
    fmt = format_string or DEFAULT_FORMAT
    date_fmt = date_format or DEFAULT_DATE_FORMAT
    formatter = logging.Formatter(fmt, date_fmt)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to allow handlers to filter

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set default level for log_filter package
    logging.getLogger("log_filter").setLevel(default_level)


def configure_component_logging(component: str, level: str, propagate: bool = True) -> None:
    """Configure logging for a specific component.

    Args:
        component: Component name (e.g., "log_filter.processing")
        level: Log level for this component
        propagate: Whether to propagate to parent loggers

    Example:
        >>> configure_component_logging("log_filter.processing", "DEBUG")
    """
    logger = logging.getLogger(component)
    logger.setLevel(_parse_level(level))
    logger.propagate = propagate


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def _parse_level(level: str) -> int:
    """Parse string log level to logging constant.

    Args:
        level: Log level string (case-insensitive)

    Returns:
        logging level constant

    Raises:
        ValueError: If level is invalid
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level_upper = level.upper()
    if level_upper not in level_map:
        raise ValueError(
            f"Invalid log level: {level}. " f"Must be one of: {', '.join(level_map.keys())}"
        )

    return level_map[level_upper]


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter for adding contextual information to log messages.

    Example:
        >>> logger = get_logger(__name__)
        >>> adapter = LoggerAdapter(logger, {"file": "data.log"})
        >>> adapter.info("Processing started")
        # Outputs: ... | INFO | ... | Processing started | file=data.log
    """

    def process(self, msg: str, kwargs: dict) -> tuple:
        """Process log message with extra context.

        Args:
            msg: Log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of (message, kwargs)
        """
        # Add context from extra dict to message
        if self.extra:
            context_parts = [f"{k}={v}" for k, v in self.extra.items()]
            msg = f"{msg} | {' | '.join(context_parts)}"

        return msg, kwargs


def create_file_logger(file_path: Path) -> logging.Logger:
    """Create a logger specifically for a file being processed.

    Args:
        file_path: Path to file being processed

    Returns:
        Logger with file context

    Example:
        >>> logger = create_file_logger(Path("data.log"))
        >>> logger.info("Started processing")
    """
    base_logger = get_logger("log_filter.processing")
    return LoggerAdapter(base_logger, {"file": str(file_path)})
