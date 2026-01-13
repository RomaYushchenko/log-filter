"""Configuration models with validation."""

import sys
from dataclasses import dataclass, field
from datetime import date, time
from pathlib import Path
from typing import Optional

# Maximum worker counts per platform
MAX_WORKERS_LINUX = 32  # Conservative for CI/CD and production
MAX_WORKERS_WINDOWS = 61  # Windows ProcessPoolExecutor limit
MAX_WORKERS_MACOS = 32  # Similar to Linux
MAX_WORKERS_DEFAULT = 32  # Fallback for unknown platforms


@dataclass
class SearchConfig:
    """Configuration for search operations.

    Attributes:
        expression: Boolean search expression
        ignore_case: Whether to perform case-insensitive search
        use_regex: Whether to interpret search terms as regular expressions
        word_boundary: Whether to match whole words only (not substrings)
        strip_quotes: Whether to strip quote characters before matching
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
        time_from: Start time for filtering (inclusive)
        time_to: End time for filtering (inclusive)
    """

    expression: str
    ignore_case: bool = False
    use_regex: bool = False
    word_boundary: bool = False
    strip_quotes: bool = False
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    time_from: Optional[time] = None
    time_to: Optional[time] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.expression or not self.expression.strip():
            raise ValueError("Search expression cannot be empty")

        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError(f"date_from ({self.date_from}) must be <= date_to ({self.date_to})")

        if self.time_from and self.time_to and self.time_from > self.time_to:
            raise ValueError(f"time_from ({self.time_from}) must be <= time_to ({self.time_to})")


@dataclass
class FileConfig:
    """Configuration for file operations.

    Attributes:
        path: Path to search for log files
        file_masks: List of filename patterns to include (empty = all files)
        include_patterns: Glob patterns for files to include (empty = all files)
        exclude_patterns: Glob patterns for files to exclude
        max_file_size_mb: Maximum file size in MB (None = unlimited)
        max_record_size_kb: Maximum record size in KB (None = unlimited)
        extensions: Allowed file extensions
    """

    path: Path = Path(".")
    file_masks: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    max_file_size_mb: Optional[int] = None
    max_record_size_kb: Optional[int] = None
    extensions: tuple[str, ...] = (".log", ".gz")

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.path.exists():
            raise ValueError(f"Path does not exist: {self.path}")

        if not self.path.is_dir():
            raise ValueError(f"Path is not a directory: {self.path}")

        if self.max_file_size_mb is not None and self.max_file_size_mb <= 0:
            raise ValueError(f"max_file_size_mb must be positive, got {self.max_file_size_mb}")

        if self.max_record_size_kb is not None and self.max_record_size_kb <= 0:
            raise ValueError(f"max_record_size_kb must be positive, got {self.max_record_size_kb}")

    def matches_file_mask(self, filename: str) -> bool:
        """Check if filename matches any of the configured masks.

        Args:
            filename: Name of the file to check

        Returns:
            True if file matches any mask or no masks configured, False otherwise
        """
        if not self.file_masks:
            return True
        return any(mask in filename for mask in self.file_masks)

    def has_allowed_extension(self, filename: str) -> bool:
        """Check if filename has an allowed extension.

        Args:
            filename: Name of the file to check

        Returns:
            True if file has allowed extension, False otherwise
        """
        return any(filename.endswith(ext) for ext in self.extensions)


@dataclass
class OutputConfig:
    """Configuration for output operations.

    Attributes:
        output_file: Path to the output file
        include_file_path: Whether to include source file path in output
        highlight_matches: Whether to highlight matches with <<< >>>
        show_progress: Whether to show progress messages
        show_stats: Whether to show final statistics
        dry_run: Whether to perform a dry run (no actual processing)
        dry_run_details: Whether to show detailed dry run statistics
    """

    output_file: Path = Path("filter-result.log")
    include_file_path: bool = True
    highlight_matches: bool = False
    show_progress: bool = False
    show_stats: bool = False
    dry_run: bool = False
    dry_run_details: bool = False


@dataclass
class ProcessingConfig:
    """Configuration for processing operations.

    Attributes:
        worker_count: Number of worker threads (None = auto-detect)
        debug: Whether to enable debug logging
        normalize_log_levels: Whether to normalize abbreviated log levels (E, W, I, D)
                             to full names (ERROR, WARN, INFO, DEBUG).
                             Default: True (user-friendly)
    """

    worker_count: Optional[int] = None
    debug: bool = False
    normalize_log_levels: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.worker_count is not None:
            if self.worker_count <= 0:
                raise ValueError(f"worker_count must be positive, got {self.worker_count}")

            # Determine platform-specific maximum
            max_workers = self._get_max_workers_for_platform()

            if self.worker_count > max_workers:
                raise ValueError(
                    f"worker_count ({self.worker_count}) exceeds platform maximum ({max_workers}). "
                    f"This limit prevents resource exhaustion and system instability."
                )

    @staticmethod
    def _get_max_workers_for_platform() -> int:
        """Get maximum worker count for current platform."""
        if sys.platform == "win32":
            return MAX_WORKERS_WINDOWS

        if sys.platform == "darwin":
            return MAX_WORKERS_MACOS

        if sys.platform.startswith("linux"):
            return MAX_WORKERS_LINUX

        return MAX_WORKERS_DEFAULT


@dataclass
class ApplicationConfig:
    """Complete application configuration.

    Attributes:
        search: Search configuration
        files: File handling configuration
        output: Output configuration
        processing: Processing configuration
    """

    search: SearchConfig
    files: FileConfig = field(default_factory=FileConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
