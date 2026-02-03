"""
File handler for gzip-compressed log files (.gz).

This module provides a handler for reading gzip-compressed log files
with automatic decompression and encoding handling. Supports parallel
decompression using pigz if available for improved performance.
"""

import gzip
import logging
import shutil
import subprocess  # nosec B404 - Required for pigz parallel decompression
from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers.base import AbstractFileHandler

logger = logging.getLogger(__name__)

# Optimal buffer size for file I/O (256KB - good for modern SSDs)
# Default Python buffer is 8KB which is too small for large log files
OPTIMAL_BUFFER_SIZE = 256 * 1024

# Threshold for using pigz parallel decompression (5MB compressed)
# For files larger than this, pigz can provide 2-4x faster decompression
# Note: We check compressed size, but benefit comes from large decompressed data
# Typical 5-10MB .gz files decompress to 50-100MB, perfect for parallelization
PIGZ_THRESHOLD = 5 * 1024 * 1024

# Check if pigz is available (cached for performance)
_PIGZ_AVAILABLE: Optional[bool] = None


def _is_pigz_available() -> bool:
    """Check if pigz (parallel gzip) is available on the system.

    This function checks once and caches the result for performance.
    pigz is a parallel implementation of gzip that can provide 2-4x
    faster decompression for large compressed files.

    Returns:
        True if pigz is available, False otherwise
    """
    global _PIGZ_AVAILABLE

    if _PIGZ_AVAILABLE is not None:
        return _PIGZ_AVAILABLE

    try:
        # Check if pigz command exists
        _PIGZ_AVAILABLE = shutil.which("pigz") is not None
        if _PIGZ_AVAILABLE:
            logger.debug("pigz found - parallel decompression available")
        else:
            logger.debug("pigz not found - using standard gzip decompression")
    except Exception as e:
        logger.debug("Error checking for pigz: %s", e)
        _PIGZ_AVAILABLE = False

    return _PIGZ_AVAILABLE


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

    def _read_with_pigz(self) -> Iterator[str]:
        """Read gzip file using pigz for parallel decompression.

        pigz (parallel gzip) can decompress files 2-4x faster than standard
        gzip by utilizing multiple CPU cores. This method is used automatically
        for large compressed files when pigz is available.

        Yields:
            Lines from the decompressed file (trailing newlines removed)

        Raises:
            FileHandlingError: If decompression fails
        """
        try:
            # Use pigz with -dc flags: -d (decompress), -c (to stdout)
            # Safe use: pigz command with validated file path, no shell injection
            with subprocess.Popen(  # nosec B603 B607
                ["pigz", "-dc", str(self.file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=OPTIMAL_BUFFER_SIZE,
            ) as proc:
                # Read from process stdout with proper encoding
                for line in proc.stdout:
                    try:
                        decoded_line = line.decode(self.encoding, errors=self.errors)
                        yield decoded_line.rstrip("\n\r")
                    except UnicodeDecodeError as e:
                        logger.debug("Unicode decode error with %s: %s", self.encoding, e)
                        # Try fallback encodings
                        for fallback_enc in self.FALLBACK_ENCODINGS:
                            if fallback_enc == self.encoding:
                                continue
                            try:
                                decoded_line = line.decode(fallback_enc, errors=self.errors)
                                yield decoded_line.rstrip("\n\r")
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # All encodings failed - use replacement
                            decoded_line = line.decode(self.encoding, errors="replace")
                            yield decoded_line.rstrip("\n\r")

                # Wait for process to complete and check return code
                return_code = proc.wait()
                if return_code != 0:
                    stderr = proc.stderr.read().decode("utf-8", errors="replace")
                    raise FileHandlingError(
                        f"pigz decompression failed for {self.file_path}: {stderr}",
                        file_path=self.file_path,
                    )

        except FileNotFoundError:
            # pigz command not found - should not happen if _is_pigz_available() was checked
            logger.warning("pigz command not found, falling back to standard gzip")
            raise
        except Exception as e:
            raise FileHandlingError(
                f"Error during pigz decompression: {self.file_path}",
                file_path=self.file_path,
                cause=e,
            ) from e

    def read_lines(self) -> Iterator[str]:
        """Read gzip file with intelligent decompression strategy.

        Strategy selection based on file size and system capabilities:
        - Large files (>= 20MB compressed) + pigz available: Parallel decompression (2-4x faster)
        - All other files: Standard gzip streaming with optimized buffering

        Yields:
            Lines from the decompressed file (trailing newlines removed)

        Raises:
            FileHandlingError: If file cannot be read or decompressed
        """
        try:
            file_size = self.get_size_bytes()  # Compressed size

            # Strategy 1: Large file with pigz - use parallel decompression
            if file_size >= PIGZ_THRESHOLD and _is_pigz_available():
                logger.debug(
                    "Using pigz parallel decompression for %s (%.2f MB)",
                    self.file_path.name,
                    file_size / (1024 * 1024),
                )
                try:
                    yield from self._read_with_pigz()
                    return  # Success - exit early
                except (FileNotFoundError, FileHandlingError) as e:
                    # pigz failed - fall back to standard gzip
                    logger.warning(
                        "pigz decompression failed, falling back to standard gzip: %s", e
                    )

            # Strategy 2: Standard gzip streaming with buffering (default path)
            # Note: We always stream line-by-line to avoid loading huge decompressed
            # data into memory. A 10MB .gz file can decompress to 100MB+!
            with gzip.open(
                self.file_path,
                "rt",
                encoding=self.encoding,
                errors=self.errors,
                # Python's gzip.open doesn't expose buffering parameter directly,
                # but we can wrap the underlying file object
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
                        "Failed to read %s with encoding %s: %s",
                        self.file_path,
                        fallback_enc,
                        fallback_error,
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
        """Helper to read gzip file with specific encoding using optimized strategy.

        Uses the same small file optimization as read_lines():
        - Small compressed files (< 10MB): read and decompress all at once
        - Large compressed files: stream line-by-line

        Args:
            encoding: Encoding to use

        Yields:
            Lines from the decompressed file
        """
        # Always stream line-by-line for gzip files to avoid loading
        # huge decompressed data into memory (compressed size != decompressed size!)
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
                        "Validation failed for %s with encoding %s: %s",
                        self.file_path,
                        fallback_enc,
                        fallback_error,
                    )
                    continue
            return (False, "Cannot decode with any supported encoding")
        except EOFError:
            return (False, "Unexpected end of file")
        except OSError as e:
            return (False, f"OS error: {e}")
        except Exception as e:
            return (False, f"Unexpected error: {e}")
