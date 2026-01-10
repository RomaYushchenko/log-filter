"""
File handler for gzip-compressed log files (.gz).

This module provides a handler for reading gzip-compressed log files
with automatic decompression and encoding handling.
"""

import gzip
import logging
from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers.base import AbstractFileHandler

logger = logging.getLogger(__name__)


class GzipFileHandler(AbstractFileHandler):
    """Handler for gzip-compressed log files.

    Reads .gz files line by line with automatic decompression.
    Supports the same encoding features as LogFileHandler.

    Example:
        >>> handler = GzipFileHandler(Path("app.log.gz"))
        >>> for line in handler.read_lines():
        ...     process(line)
    """

    FALLBACK_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

    def __init__(self, file_path: Path, encoding: str = "utf-8", errors: str = "replace") -> None:
        """Initialize the gzip file handler.

        Args:
            file_path: Path to the .gz file
            encoding: Character encoding (default: utf-8)
            errors: How to handle encoding errors (default: replace)
                   Options: 'strict', 'ignore', 'replace'
        """
        super().__init__(file_path, encoding)
        self.errors = errors

    def read_lines(self) -> Iterator[str]:
        """Read gzip file line by line with decompression.

        Yields:
            Lines from the decompressed file (trailing newlines removed)

        Raises:
            FileHandlingError: If file cannot be read or decompressed
        """
        try:
            with gzip.open(self.file_path, "rt", encoding=self.encoding, errors=self.errors) as f:
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
        except gzip.BadGzipFile as e:
            raise FileHandlingError(
                f"Invalid or corrupted gzip file: {self.file_path}",
                file_path=self.file_path,
                cause=e,
            )
        except UnicodeDecodeError as e:
            # Try fallback encodings
            for fallback_enc in self.FALLBACK_ENCODINGS:
                if fallback_enc == self.encoding:
                    continue
                try:
                    yield from self._read_with_encoding(fallback_enc)
                    return
                except (UnicodeDecodeError, OSError, EOFError) as fallback_error:
                    logger.debug(
                        f"Failed to read {self.file_path} with encoding {fallback_enc}: {fallback_error}"
                    )
                    continue

            # All fallbacks failed
            raise FileHandlingError(
                f"Cannot decode gzip file with any supported encoding: {self.file_path}",
                file_path=self.file_path,
                cause=e,
            )
        except OSError as e:
            raise FileHandlingError(
                f"OS error reading gzip file: {self.file_path}", file_path=self.file_path, cause=e
            )
        except EOFError as e:
            raise FileHandlingError(
                f"Unexpected end of gzip file: {self.file_path}", file_path=self.file_path, cause=e
            )

    def _read_with_encoding(self, encoding: str) -> Iterator[str]:
        """Helper to read gzip file with specific encoding.

        Args:
            encoding: Encoding to use

        Yields:
            Lines from the decompressed file
        """
        with gzip.open(self.file_path, "rt", encoding=encoding, errors=self.errors) as f:
            for line in f:
                yield line.rstrip("\n\r")

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate that the gzip file can be read.

        Attempts to open the file and read the first line to verify
        it's a valid gzip file and is readable.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with gzip.open(self.file_path, "rt", encoding=self.encoding, errors=self.errors) as f:
                # Try to read first line
                f.readline()
            return (True, None)

        except PermissionError:
            return (False, "Permission denied")
        except gzip.BadGzipFile:
            return (False, "Invalid or corrupted gzip file")
        except UnicodeDecodeError:
            # Try fallback encodings
            for fallback_enc in self.FALLBACK_ENCODINGS:
                try:
                    with gzip.open(self.file_path, "rt", encoding=fallback_enc) as f:
                        f.readline()
                    return (True, None)
                except (UnicodeDecodeError, OSError, EOFError) as fallback_error:
                    logger.debug(
                        f"Validation failed for {self.file_path} with encoding {fallback_enc}: {fallback_error}"
                    )
                    continue
            return (False, "Cannot decode with any supported encoding")
        except EOFError:
            return (False, "Unexpected end of file")
        except OSError as e:
            return (False, f"OS error: {e}")
        except Exception as e:
            return (False, f"Unexpected error: {e}")
