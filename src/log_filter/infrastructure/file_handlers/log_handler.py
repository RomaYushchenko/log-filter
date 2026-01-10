"""
File handler for plain text log files (.log).

This module provides a handler for reading plain text log files with
automatic encoding detection and error recovery.
"""

from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers.base import AbstractFileHandler


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
        """Read log file line by line.

        Yields:
            Lines from the file (trailing newlines removed)

        Raises:
            FileHandlingError: If file cannot be read
        """
        try:
            with open(self.file_path, "r", encoding=self.encoding, errors=self.errors) as f:
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
                except (UnicodeDecodeError, Exception):
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
        """Helper to read file with specific encoding.

        Args:
            encoding: Encoding to use

        Yields:
            Lines from the file
        """
        with open(self.file_path, "r", encoding=encoding, errors=self.errors) as f:
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
                except Exception:
                    continue
            return (False, "Cannot decode with any supported encoding")
        except OSError as e:
            return (False, f"OS error: {e}")
        except Exception as e:
            return (False, f"Unexpected error: {e}")
