"""
Progress tracking for log processing operations.

This module provides real-time progress bars and status updates
using tqdm for visual feedback during long-running operations.
"""

from pathlib import Path
from typing import Iterator, Optional, TypeVar

from tqdm import tqdm

from log_filter.domain.models import FileMetadata, LogRecord

T = TypeVar("T")


class ProgressTracker:
    """Progress tracking wrapper using tqdm.

    Provides visual progress bars for file scanning and processing
    with ETA calculation and throughput metrics.

    Example:
        >>> tracker = ProgressTracker(enable=True)
        >>> for file in tracker.track_files(files, total=100):
        ...     process(file)
    """

    def __init__(self, enable: bool = True, desc_width: int = 25):
        """Initialize progress tracker.

        Args:
            enable: Whether to show progress bars
            desc_width: Width of description column
        """
        self.enable = enable
        self.desc_width = desc_width

    def track_files(
        self,
        files: Iterator[FileMetadata],
        total: Optional[int] = None,
        desc: str = "Processing files",
    ) -> Iterator[FileMetadata]:
        """Track file processing progress.

        Args:
            files: Iterator of files to process
            total: Total number of files (for progress percentage)
            desc: Progress bar description

        Yields:
            Files from the input iterator
        """
        if not self.enable:
            yield from files
            return

        with tqdm(
            iterable=files,
            total=total,
            desc=desc.ljust(self.desc_width),
            unit="file",
            unit_scale=False,
            colour="green",
            leave=True,
        ) as pbar:
            for file_meta in pbar:
                # Update status with current file
                pbar.set_postfix_str(f"{Path(file_meta.path).name[:30]}", refresh=False)
                yield file_meta

    def track_records(
        self,
        records: Iterator[LogRecord],
        total: Optional[int] = None,
        desc: str = "Processing records",
    ) -> Iterator[LogRecord]:
        """Track record processing progress.

        Args:
            records: Iterator of records to process
            total: Total number of records (for progress percentage)
            desc: Progress bar description

        Yields:
            Records from the input iterator
        """
        if not self.enable:
            yield from records
            return

        with tqdm(
            iterable=records,
            total=total,
            desc=desc.ljust(self.desc_width),
            unit="rec",
            unit_scale=True,
            colour="blue",
            leave=True,
        ) as pbar:
            yield from pbar

    def track_generic(
        self,
        items: Iterator[T],
        total: Optional[int] = None,
        desc: str = "Processing",
        unit: str = "item",
    ) -> Iterator[T]:
        """Track generic iterator progress.

        Args:
            items: Iterator of items to track
            total: Total number of items
            desc: Progress bar description
            unit: Unit name for items

        Yields:
            Items from the input iterator
        """
        if not self.enable:
            yield from items
            return

        with tqdm(
            iterable=items,
            total=total,
            desc=desc.ljust(self.desc_width),
            unit=unit,
            unit_scale=False,
            leave=True,
        ) as pbar:
            yield from pbar

    def create_counter(
        self, total: Optional[int] = None, desc: str = "Progress", unit: str = "item"
    ) -> "ProgressCounter":
        """Create a manual progress counter.

        Args:
            total: Total number of items
            desc: Progress bar description
            unit: Unit name for items

        Returns:
            Progress counter for manual updates
        """
        return ProgressCounter(
            enable=self.enable, total=total, desc=desc.ljust(self.desc_width), unit=unit
        )


class ProgressCounter:
    """Manual progress counter with context manager support.

    Allows manual updates to a progress bar for cases where
    an iterator wrapper is not appropriate.

    Example:
        >>> with counter.create_counter(total=100) as progress:
        ...     for i in range(100):
        ...         work(i)
        ...         progress.update(1)
    """

    def __init__(self, enable: bool, total: Optional[int], desc: str, unit: str):
        """Initialize progress counter.

        Args:
            enable: Whether to show progress bar
            total: Total number of items
            desc: Progress bar description
            unit: Unit name for items
        """
        self.enable = enable
        self._pbar: Optional[tqdm] = None
        self._total = total
        self._desc = desc
        self._unit = unit

    def __enter__(self) -> "ProgressCounter":
        """Enter context manager."""
        if self.enable:
            self._pbar = tqdm(
                total=self._total, desc=self._desc, unit=self._unit, unit_scale=False, leave=True
            )
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """Exit context manager."""
        if self._pbar is not None:
            self._pbar.close()

    def update(self, n: int = 1) -> None:
        """Update progress by n items.

        Args:
            n: Number of items to increment by
        """
        if self._pbar is not None:
            self._pbar.update(n)

    def set_postfix_str(self, s: str) -> None:
        """Set postfix status string.

        Args:
            s: Status string to display
        """
        if self._pbar is not None:
            self._pbar.set_postfix_str(s, refresh=False)

    def set_description(self, desc: str) -> None:
        """Update progress bar description.

        Args:
            desc: New description
        """
        if self._pbar is not None:
            self._pbar.set_description(desc.ljust(len(self._desc)))
