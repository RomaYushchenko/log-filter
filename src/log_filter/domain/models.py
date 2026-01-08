"""Domain models for log filtering."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class LogRecord:
    """Represents a single multiline log record.

    Attributes:
        content: Complete log record text (all lines)
        first_line: First line of the record (contains timestamp and level)
        source_file: Path to the source log file
        start_line: Line number where this record starts (1-based)
        end_line: Line number where this record ends (1-based)
        timestamp: Parsed timestamp from the first line
        level: Log level (ERROR, WARN, INFO, etc.)
        size_bytes: Total size of the record in bytes
    """

    content: str
    first_line: str
    source_file: Path
    start_line: int
    end_line: int
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    size_bytes: int = 0

    @property
    def line_count(self) -> int:
        """Return the number of lines in this record."""
        return self.end_line - self.start_line + 1

    @property
    def date(self) -> Optional[date]:
        """Extract date from timestamp."""
        return self.timestamp.date() if self.timestamp else None

    @property
    def time(self) -> Optional[time]:
        """Extract time from timestamp."""
        return self.timestamp.time() if self.timestamp else None


@dataclass
class SearchResult:
    """Result of evaluating a search expression against a log record.

    Attributes:
        record: The log record that was evaluated
        matched: Whether the record matched the search expression
        match_positions: List of (start, end) tuples for match positions
        highlighted_content: Content with matches highlighted (if applicable)
    """

    record: LogRecord
    matched: bool
    match_positions: list[tuple[int, int]] = field(default_factory=list)
    highlighted_content: Optional[str] = None


@dataclass
class FileMetadata:
    """Metadata about a log file.

    Attributes:
        path: Full path to the file
        size_bytes: File size in bytes
        extension: File extension (.log, .gz, etc.)
        is_compressed: Whether the file is compressed
        is_readable: Whether the file can be read
        skip_reason: Reason for skipping this file (if applicable)
    """

    path: Path
    size_bytes: int
    extension: str
    is_compressed: bool
    is_readable: bool = True
    skip_reason: Optional[str] = None

    @property
    def size_mb(self) -> float:
        """Return file size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def should_skip(self) -> bool:
        """Return whether this file should be skipped."""
        return self.skip_reason is not None or not self.is_readable


# Type aliases for AST nodes
ASTNode = tuple[str, ...]  # ('WORD', 'value') or ('AND', left, right), etc.
