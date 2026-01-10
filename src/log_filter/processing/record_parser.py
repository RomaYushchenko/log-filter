"""
Streaming log record parser with memory-bounded operation.

This module parses log records from a stream of lines without accumulating
the entire record in memory. It uses a generator-based approach for
efficient processing of large log files.
"""

import re
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import RecordSizeExceededError
from log_filter.domain.models import LogRecord


class StreamingRecordParser:
    """Memory-bounded parser for multiline log records.

    Parses log records from a stream of lines. A record begins with a line
    matching the timestamp pattern:

        YYYY-MM-DD HH:MM:SS.mmm±ZZZZ <LEVEL>

    The parser yields complete records without accumulating them in memory,
    making it suitable for processing very large log files.

    Attributes:
        record_start_pattern: Regex pattern for record start line
        max_record_size_bytes: Maximum allowed record size (None = unlimited)

    Example:
        >>> parser = StreamingRecordParser(max_record_size_bytes=1024 * 100)
        >>> for record in parser.parse_lines(lines):
        ...     if record.level == "ERROR":
        ...         print(record.content)
    """

    # Pattern for log record start line
    DEFAULT_RECORD_START_PATTERN = re.compile(
        r"^(\d{4}-\d{2}-\d{2}) "  # date: YYYY-MM-DD
        r"(\d{2}:\d{2}:\d{2})"  # time: HH:MM:SS
        r"\.\d{3}[+-]\d{4}\s+"  # milliseconds and timezone
        r"([A-Z]+)"  # level: ERROR, WARN, INFO, etc.
    )

    def __init__(
        self,
        record_start_pattern: Optional[re.Pattern] = None,
        max_record_size_bytes: Optional[int] = None,
    ) -> None:
        """Initialize the streaming record parser.

        Args:
            record_start_pattern: Regex pattern for record start.
                                 If None, uses DEFAULT_RECORD_START_PATTERN
            max_record_size_bytes: Maximum record size in bytes.
                                  Records exceeding this will raise an error.
                                  None means unlimited.
        """
        self.record_start_pattern = record_start_pattern or self.DEFAULT_RECORD_START_PATTERN
        self.max_record_size_bytes = max_record_size_bytes

    def parse_lines(
        self, lines: Iterator[str], file_path: Optional[str] = None
    ) -> Iterator[LogRecord]:
        """Parse lines into log records.

        Yields complete log records as they are assembled from the stream.
        Memory usage is bounded - only the current record is kept in memory.

        Args:
            lines: Iterator of lines from a log file
            file_path: Optional file path for error messages

        Yields:
            LogRecord objects

        Raises:
            RecordSizeExceededError: If a record exceeds max_record_size_bytes
        """
        from pathlib import Path

        current_lines: list[str] = []
        current_size_bytes = 0
        first_line_info: Optional[tuple[str, str, str]] = None  # (date, time, level)
        start_line = 1
        line_number = 0
        source_path = Path(file_path) if file_path else Path("unknown")

        for line in lines:
            line_number += 1
            match = self.record_start_pattern.match(line)

            if match:
                # New record starts - yield previous record if exists
                if current_lines:
                    end_line = line_number - 1
                    yield self._create_record(
                        current_lines,
                        current_size_bytes,
                        first_line_info,
                        source_path,
                        start_line,
                        end_line,
                    )

                # Start new record
                current_lines = [line]
                current_size_bytes = len(line.encode("utf-8"))
                first_line_info = (match.group(1), match.group(2), match.group(3))
                start_line = line_number

                # Check size limit
                if self.max_record_size_bytes and current_size_bytes > self.max_record_size_bytes:
                    raise RecordSizeExceededError(
                        size_kb=current_size_bytes / 1024,
                        max_size_kb=self.max_record_size_bytes // 1024,
                    )
            else:
                # Continuation of current record
                if current_lines:
                    current_lines.append(line)
                    current_size_bytes += len(line.encode("utf-8"))

                    # Check size limit
                    if (
                        self.max_record_size_bytes
                        and current_size_bytes > self.max_record_size_bytes
                    ):
                        raise RecordSizeExceededError(
                            size_kb=current_size_bytes / 1024,
                            max_size_kb=self.max_record_size_bytes // 1024,
                        )

        # Yield final record if exists
        if current_lines:
            end_line = line_number
            yield self._create_record(
                current_lines,
                current_size_bytes,
                first_line_info,
                source_path,
                start_line,
                end_line,
            )

    def _create_record(
        self,
        lines: list[str],
        size_bytes: int,
        first_line_info: Optional[tuple[str, str, str]],
        source_file: Path,
        start_line: int,
        end_line: int,
    ) -> LogRecord:
        """Create a LogRecord from accumulated lines.

        Args:
            lines: List of lines in the record
            size_bytes: Total size in bytes
            first_line_info: Tuple of (date_str, time_str, level) from first line
            source_file: Path to the source file
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)

        Returns:
            LogRecord object
        """
        from datetime import datetime

        content = "\n".join(lines)
        first_line = lines[0] if lines else ""

        # Extract metadata from first line if available
        timestamp = None
        level = None

        if first_line_info:
            date_str, time_str, level = first_line_info
            # Try to parse the timestamp
            try:
                timestamp_str = f"{date_str} {time_str}"
                # Handle various timestamp formats
                for fmt in [
                    "%Y-%m-%d %H:%M:%S.%f%z",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                ]:
                    try:
                        timestamp = datetime.strptime(timestamp_str.strip(), fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        return LogRecord(
            content=content,
            first_line=first_line,
            source_file=source_file,
            start_line=start_line,
            end_line=end_line,
            timestamp=timestamp,
            level=level,
            size_bytes=size_bytes,
        )

    def is_record_start(self, line: str) -> bool:
        """Check if a line is the start of a new record.

        Args:
            line: Line to check

        Returns:
            True if line matches record start pattern
        """
        return bool(self.record_start_pattern.match(line))

    def extract_record_metadata(self, line: str) -> Optional[tuple[str, str, str]]:
        """Extract date, time, and level from a record start line.

        Args:
            line: Record start line

        Returns:
            Tuple of (date, time, level) if line matches pattern,
            None otherwise
        """
        match = self.record_start_pattern.match(line)
        if match:
            return (match.group(1), match.group(2), match.group(3))
        return None

    def parse_date(self, date_str: str) -> Optional[dt_date]:
        """Parse date string to datetime.date.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            datetime.date object or None if parsing fails
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def parse_time(self, time_str: str) -> Optional[dt_time]:
        """Parse time string to datetime.time.

        Args:
            time_str: Time string in HH:MM:SS format

        Returns:
            datetime.time object or None if parsing fails
        """
        try:
            return datetime.strptime(time_str, "%H:%M:%S").time()
        except (ValueError, TypeError):
            return None
