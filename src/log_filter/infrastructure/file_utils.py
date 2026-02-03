"""
Utility functions for file operations.

This module provides helper functions for working with log files,
including filename parsing and sorting.
"""

import logging
import re
from datetime import datetime
from typing import Optional, Tuple

from log_filter.domain.models import FileMetadata

logger = logging.getLogger(__name__)


def extract_date_and_index_from_filename(filename: str) -> Optional[Tuple[datetime, int]]:
    """
    Extract date and sequential index from log filename.

    Supports multiple naming patterns commonly used in log rotation:

    Patterns:
        - DD-MM-YYYY-N: tug-integration-02-02-2026-1.log.gz
        - YYYY-MM-DD-N: application-2026-02-03-2.log
        - YYYYMMDD_N: server_20260203_3.log
        - Simple index: app-5.log (uses epoch date)

    Args:
        filename: Filename to parse (with or without path)

    Returns:
        Tuple of (datetime, index) if pattern matched, None otherwise

    Examples:
        >>> extract_date_and_index_from_filename("tug-integration-02-02-2026-1.log.gz")
        (datetime(2026, 2, 2, 0, 0), 1)
        >>> extract_date_and_index_from_filename("app-5.log")
        (datetime(1970, 1, 1, 0, 0), 5)
        >>> extract_date_and_index_from_filename("unknown.log")
        None

    References:
        - https://docs.python.org/3/library/re.html#re.search
        - https://docs.python.org/3/library/datetime.html#datetime.datetime
    """
    # Pattern 1: DD-MM-YYYY-N (European format)
    # Example: tug-integration-02-02-2026-1.log.gz
    pattern1 = r"(\d{2})-(\d{2})-(\d{4})-(\d+)"
    match = re.search(pattern1, filename)
    if match:
        day, month, year, index = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            logger.debug(
                f"Parsed filename '{filename}' as DD-MM-YYYY-N: date={date.date()}, index={index}"
            )
            return (date, int(index))
        except ValueError as e:
            logger.debug(f"Invalid date in filename '{filename}': {e}")
            # Continue to try other patterns

    # Pattern 2: YYYY-MM-DD-N (ISO format)
    # Example: application-2026-02-03-2.log
    pattern2 = r"(\d{4})-(\d{2})-(\d{2})-(\d+)"
    match = re.search(pattern2, filename)
    if match:
        year, month, day, index = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            logger.debug(
                f"Parsed filename '{filename}' as YYYY-MM-DD-N: date={date.date()}, index={index}"
            )
            return (date, int(index))
        except ValueError as e:
            logger.debug(f"Invalid date in filename '{filename}': {e}")
            # Continue to try other patterns

    # Pattern 3: YYYYMMDD_N (compact format)
    # Example: server_20260203_3.log
    pattern3 = r"(\d{4})(\d{2})(\d{2})[_-](\d+)"
    match = re.search(pattern3, filename)
    if match:
        year, month, day, index = match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            logger.debug(
                f"Parsed filename '{filename}' as YYYYMMDD_N: date={date.date()}, index={index}"
            )
            return (date, int(index))
        except ValueError as e:
            logger.debug(f"Invalid date in filename '{filename}': {e}")
            # Continue to try other patterns

    # Pattern 4: Only index at end (no date)
    # Example: app-5.log, server_10.log.gz
    pattern4 = r"[-_](\d+)\.[^.]+(?:\.gz)?$"
    match = re.search(pattern4, filename)
    if match:
        index = int(match.group(1))
        # Use Unix epoch as placeholder date for files without date
        epoch = datetime(1970, 1, 1)
        logger.debug(
            f"Parsed filename '{filename}' as index-only: index={index} (using epoch date)"
        )
        return (epoch, index)

    # No pattern matched
    logger.debug(f"Could not parse date/index from filename: '{filename}'")
    return None


def sort_files_by_date_and_index(
    files: list[FileMetadata], fallback_sort_key: str = "name"
) -> list[FileMetadata]:
    """
    Sort files by date and index extracted from filename.

    Files are sorted by:
    1. Date (extracted from filename) - ascending (oldest first)
    2. Index (extracted from filename) - ascending
    3. Fallback: filename or modification time

    Files without recognizable date/index pattern are placed at the end
    and sorted by the fallback key.

    Args:
        files: List of FileMetadata to sort
        fallback_sort_key: How to sort files without date/index ("name", "mtime", "size")

    Returns:
        Sorted list of FileMetadata (original list not modified)

    Examples:
        >>> files = [
        ...     FileMetadata(Path("tug-02-03-2026-1.log"), ...),
        ...     FileMetadata(Path("tug-02-02-2026-2.log"), ...),
        ...     FileMetadata(Path("tug-02-02-2026-1.log"), ...),
        ... ]
        >>> sorted_files = sort_files_by_date_and_index(files)
        >>> [f.path.name for f in sorted_files]
        ['tug-02-02-2026-1.log', 'tug-02-02-2026-2.log', 'tug-02-03-2026-1.log']

    References:
        - https://docs.python.org/3/library/functions.html#sorted
        - https://docs.python.org/3/howto/sorting.html
    """
    files_with_date = []
    files_without_date = []

    # Classify files
    for file_meta in files:
        date_index = extract_date_and_index_from_filename(file_meta.path.name)
        if date_index:
            date, index = date_index
            files_with_date.append((date, index, file_meta))
        else:
            files_without_date.append(file_meta)

    # Sort files with date by (date, index)
    # Using tuple comparison: (date1, idx1) < (date2, idx2)
    # Reference: https://docs.python.org/3/tutorial/datastructures.html#comparing-sequences-and-other-types
    files_with_date.sort(key=lambda x: (x[0], x[1]))

    # Sort files without date by fallback key
    if fallback_sort_key == "name":
        files_without_date.sort(key=lambda x: x.path.name)
    elif fallback_sort_key == "mtime":
        files_without_date.sort(key=lambda x: x.path.stat().st_mtime if x.path.exists() else 0)
    elif fallback_sort_key == "size":
        files_without_date.sort(key=lambda x: x.size_bytes)
    else:
        # Default to name
        logger.warning(f"Unknown fallback_sort_key '{fallback_sort_key}', using 'name'")
        files_without_date.sort(key=lambda x: x.path.name)

    # Combine: files with date first (chronologically), then files without
    result = [f[2] for f in files_with_date] + files_without_date

    logger.info(
        f"File sorting complete: {len(files_with_date)} files with date/index, "
        f"{len(files_without_date)} files without pattern"
    )

    if files_with_date:
        first = files_with_date[0]
        last = files_with_date[-1]
        logger.info(
            f"Date range: {first[0].date()} (index {first[1]}) → "
            f"{last[0].date()} (index {last[1]})"
        )

    return result
