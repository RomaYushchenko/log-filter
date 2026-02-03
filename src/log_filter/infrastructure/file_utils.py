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

# Pre-compiled regex patterns for filename parsing (performance optimization)
# These patterns are compiled once at module load time instead of on every function call
_PATTERN_DD_MM_YYYY = re.compile(r"(\d{2})-(\d{2})-(\d{4})-(\d+)")
_PATTERN_YYYY_MM_DD = re.compile(r"(\d{4})-(\d{2})-(\d{2})-(\d+)")
_PATTERN_YYYYMMDD = re.compile(r"(\d{4})(\d{2})(\d{2})[_-](\d+)")
_PATTERN_INDEX_ONLY = re.compile(r"[-_](\d+)\.[^.]+(?:\.gz)?$")


def extract_date_and_index_from_filename(filename: str) -> Optional[Tuple[datetime, int]]:
    """
    Extract date and sequential index from log filename.

    Supports multiple naming patterns commonly used in log rotation:

    Patterns:
        - DD-MM-YYYY-N: tug-integration-02-02-2026-1.log.gz
        - MM-DD-YYYY-N: tug-integration-12-15-2025-32.log.gz (American format)
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
    # Pattern 1: DD-MM-YYYY-N or MM-DD-YYYY-N (European or American format)
    # Example: tug-integration-02-02-2026-1.log.gz or tug-integration-12-15-2025-32.log.gz
    match = _PATTERN_DD_MM_YYYY.search(filename)
    if match:
        first, second, year, index = match.groups()
        # Try DD-MM-YYYY first (European format)
        try:
            date = datetime(int(year), int(second), int(first))
            logger.debug(
                "Parsed '%s' as MM-DD-YYYY-N: date=%s, index=%s",
                filename,
                date.date(),
                index,
            )
            return (date, int(index))
        except ValueError:
            # If DD-MM-YYYY fails, try MM-DD-YYYY (American format)
            try:
                date = datetime(int(year), int(first), int(second))
                logger.debug(
                    f"Parsed filename '{filename}' as MM-DD-YYYY-N: date={date.date()}, index={index}"
                )
                return (date, int(index))
            except ValueError as e:
                logger.debug(f"Invalid date in filename '{filename}': {e}")
                # Continue to try other patterns

    # Pattern 2: YYYY-MM-DD-N (ISO format)
    # Example: application-2026-02-03-2.log
    match = _PATTERN_YYYY_MM_DD.search(filename)
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
    match = _PATTERN_YYYYMMDD.search(filename)
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
    match = _PATTERN_INDEX_ONLY.search(filename)
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
    Sort files by directory, then by date and index within each directory.

    Sorting strategy:
    1. Group files by parent directory
    2. Within each directory:
       - Files WITHOUT date/index patterns come FIRST (sorted by fallback_sort_key)
       - Files WITH date/index patterns come AFTER (sorted chronologically)
    3. Sort directories by their earliest dated file
    4. Directories with only undated files are processed first

    This ensures:
    - Configuration or main log files (without rotation numbers) are processed first
    - Rotated logs are then processed in chronological order
    - Files from the same directory stay together

    Args:
        files: List of FileMetadata to sort
        fallback_sort_key: How to sort files without date/index ("name", "mtime", "size")

    Returns:
        Sorted list of FileMetadata (original list not modified)

    Examples:
        >>> files = [
        ...     FileMetadata(Path("/logs/app-02-03-2026-1.log"), ...),
        ...     FileMetadata(Path("/logs/current.log"), ...),  # No date/index
        ...     FileMetadata(Path("/logs/app-02-02-2026-1.log"), ...),
        ... ]
        >>> sorted_files = sort_files_by_date_and_index(files)
        >>> [f.path.name for f in sorted_files]
        ['current.log', 'app-02-02-2026-1.log', 'app-02-03-2026-1.log']

    References:
        - https://docs.python.org/3/library/functions.html#sorted
        - https://docs.python.org/3/howto/sorting.html
        - https://docs.python.org/3/library/collections.html#collections.defaultdict
    """
    from collections import defaultdict

    # Group files by parent directory
    files_by_dir = defaultdict(list)
    for file_meta in files:
        parent_dir = file_meta.path.parent
        files_by_dir[parent_dir].append(file_meta)

    # Sort files within each directory
    sorted_directories = []

    for directory, dir_files in files_by_dir.items():
        files_with_date = []
        files_without_date = []

        # Classify files in this directory
        for file_meta in dir_files:
            date_index = extract_date_and_index_from_filename(file_meta.path.name)
            if date_index:
                date, index = date_index
                files_with_date.append((date, index, file_meta))
            else:
                files_without_date.append(file_meta)

        # Sort files with date by (date, index)
        files_with_date.sort(key=lambda x: (x[0], x[1]))

        # Sort files without date by fallback key
        if fallback_sort_key == "name":
            files_without_date.sort(key=lambda x: x.path.name)
        elif fallback_sort_key == "mtime":
            # Use cached mtime from FileMetadata (performance optimization)
            # Avoids calling stat() again - already collected during file scan
            files_without_date.sort(key=lambda x: x.mtime)
        elif fallback_sort_key == "size":
            files_without_date.sort(key=lambda x: x.size_bytes)
        else:
            logger.warning(f"Unknown fallback_sort_key '{fallback_sort_key}', using 'name'")
            files_without_date.sort(key=lambda x: x.path.name)

        # Combine files: non-dated FIRST, then dated (chronological)
        # This ensures files without patterns (like config files) are processed before log rotations
        sorted_files_in_dir = files_without_date + [f[2] for f in files_with_date]

        # Determine directory's earliest date for sorting directories
        # Use earliest dated file, or datetime.min for directories with only undated files
        earliest_date = files_with_date[0][0] if files_with_date else datetime.min

        sorted_directories.append((earliest_date, directory, sorted_files_in_dir))

    # Sort directories by earliest date
    sorted_directories.sort(key=lambda x: x[0])

    # Flatten to single list
    result = []
    total_with_date = 0
    total_without_date = 0

    for earliest_date, directory, sorted_files_in_dir in sorted_directories:
        result.extend(sorted_files_in_dir)

        # Count files for logging
        dir_files_with_date = sum(
            1
            for f in sorted_files_in_dir
            if extract_date_and_index_from_filename(f.path.name) is not None
        )
        total_with_date += dir_files_with_date
        total_without_date += len(sorted_files_in_dir) - dir_files_with_date

    # Log sorting summary
    logger.info(
        f"File sorting complete: {len(sorted_directories)} directories, "
        f"{total_with_date} files with date/index, {total_without_date} files without pattern"
    )

    if sorted_directories:
        first_dir = sorted_directories[0]
        last_dir = sorted_directories[-1]
        if first_dir[0] != datetime.min and last_dir[0] != datetime.min:
            logger.info(f"Directory date range: {first_dir[0].date()} → {last_dir[0].date()}")
        logger.debug(f"Processing order: {len(sorted_directories)} directories")
        for idx, (earliest_date, directory, dir_files) in enumerate(sorted_directories[:3], 1):
            logger.debug(
                f"  {idx}. {directory} ({len(dir_files)} files, "
                f"earliest: {earliest_date.date() if earliest_date != datetime.max else 'N/A'})"
            )

    return result
