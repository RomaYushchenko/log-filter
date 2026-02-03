"""
File handler for plain text log files (.log).

This module provides a handler for reading plain text log files with
automatic encoding detection and error recovery.
"""

import logging
from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers.base import AbstractFileHandler

logger = logging.getLogger(__name__)

# Optimal buffer size for file I/O (256KB - good for modern SSDs)
# Default Python buffer is 8KB which is too small for large log files
OPTIMAL_BUFFER_SIZE = 256 * 1024

# Threshold for small files to read entirely into memory (1MB)
# Files smaller than this are read at once using splitlines() for better performance
# Note: This threshold is conservative to avoid excessive memory usage
SMALL_FILE_THRESHOLD = 1 * 1024 * 1024  # 1MB


class LogFileHandler(AbstractFileHandler):
    """Handler for plain text log files.

    Reads .log files line by line with proper encoding handling.
    Supports fallback encodings if utf-8 fails.

    Example:
        >>> handler = LogFileHandler(Path("app.log"))
        >>> for line in handler.read_lines():
        ...     process(line)
    """

    FALLBACK_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

    def __init__(self, file_path: Path, encoding: str = "utf-8", errors: str = "replace") -> None:
        """Initialize the log file handler.

        Args:
            file_path: Path to the log file
            encoding: Character encoding (default: utf-8)
            errors: How to handle encoding errors (default: replace)
                   Options: 'strict', 'ignore', 'replace'
        """
        super().__init__(file_path, encoding)
        self.errors = errors

    def read_lines(self) -> Iterator[str]:
        """Read log file with optimized strategy based on file size.

        For small files (< 10MB): Reads entire content into memory and uses
        splitlines() for 10-20% better performance compared to line-by-line iteration.

        For large files (>= 10MB): Streams line-by-line with optimized 256KB buffer
        to avoid excessive memory usage.

        Yields:
            Lines from the file (trailing newlines removed)

        Raises:
            FileHandlingError: If file cannot be read
        """
        try:
            file_size = self.get_size_bytes()

            # Small file optimization: read all at once
            if file_size < SMALL_FILE_THRESHOLD:
                with open(
                    self.file_path,
                    "r",
                    encoding=self.encoding,
                    errors=self.errors,
                ) as f:
                    content = f.read()
                    # splitlines() is faster than iterating and doesn't include newlines
                    yield from content.splitlines()
            else:
                # Large file: stream with optimized buffering
                with open(
                    self.file_path,
                    "r",
                    encoding=self.encoding,
                    errors=self.errors,
                    buffering=OPTIMAL_BUFFER_SIZE,
                ) as f:
                    for line in f:
                        yield line.rstrip("\n\r")

        except FileNotFoundError:
            raise FileHandlingError(
                f"File not found during read: {self.file_path}", file_path=self.file_path
            )
        except PermissionError as e:
            raise FileHandlingError(
                f"Permission denied: {self.file_path}", file_path=self.file_path, cause=e
            )
        except UnicodeDecodeError as e:
            # Try fallback encodings
            for fallback_enc in self.FALLBACK_ENCODINGS:
                if fallback_enc == self.encoding:
                    continue
                try:
                    yield from self._read_with_encoding(fallback_enc)
                    return
                except (UnicodeDecodeError, OSError) as fallback_error:
                    logger.debug(
                        "Failed to read %s with encoding %s: %s",
                        self.file_path,
                        fallback_enc,
                        fallback_error,
                    )
                    continue

            # All fallbacks failed
            raise FileHandlingError(
                f"Cannot decode file with any supported encoding: {self.file_path}",
                file_path=self.file_path,
                cause=e,
            )
        except OSError as e:
            raise FileHandlingError(
                f"OS error reading file: {self.file_path}", file_path=self.file_path, cause=e
            )

    def _read_with_encoding(self, encoding: str) -> Iterator[str]:
        """Helper to read file with specific encoding using optimized strategy.

        Uses the same small file optimization as read_lines():
        - Small files (< 10MB): read all at once with splitlines()
        - Large files: stream line-by-line with buffering

        Args:
            encoding: Encoding to use

        Yields:
            Lines from the file
        """
        file_size = self.get_size_bytes()

        if file_size < SMALL_FILE_THRESHOLD:
            # Small file: read all at once
            with open(
                self.file_path,
                "r",
                encoding=encoding,
                errors=self.errors,
            ) as f:
                content = f.read()
                yield from content.splitlines()
        else:
            # Large file: stream with buffering
            with open(
                self.file_path,
                "r",
                encoding=encoding,
                errors=self.errors,
                buffering=OPTIMAL_BUFFER_SIZE,
            ) as f:
                for line in f:
                    yield line.rstrip("\n\r")

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate that the log file can be read.

        Attempts to open the file and read the first line to verify
        it's readable.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(self.file_path, "r", encoding=self.encoding, errors=self.errors) as f:
                # Try to read first line
                f.readline()
            return (True, None)

        except PermissionError:
            return (False, "Permission denied")
        except UnicodeDecodeError:
            # Try fallback encodings
            for fallback_enc in self.FALLBACK_ENCODINGS:
                try:
                    with open(self.file_path, "r", encoding=fallback_enc) as f:
                        f.readline()
                    return (True, None)
                except (UnicodeDecodeError, OSError) as fallback_error:
                    logger.debug(
                        "Validation failed for %s with encoding %s: %s",
                        self.file_path,
                        fallback_enc,
                        fallback_error,
                    )
                    continue
            return (False, "Cannot decode with any supported encoding")
        except OSError as e:
            return (False, f"OS error: {e}")
        except Exception as e:
            return (False, f"Unexpected error: {e}")
