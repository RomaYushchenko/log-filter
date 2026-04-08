"""
Performance metrics tracking for log processing operations.

This module provides detailed performance metrics collection including
processing rates, throughput, and per-file performance data.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional


@dataclass
class FilePerformance:
    """Performance metrics for a single file.

    Attributes:
        file_path: Path to the file
        file_size_bytes: Size of file in bytes
        records_processed: Number of records processed
        records_matched: Number of records matched
        processing_time_seconds: Time spent processing
        throughput_records_per_sec: Processing throughput
        throughput_mb_per_sec: Data throughput
    """

    file_path: str
    file_size_bytes: int
    records_processed: int
    records_matched: int
    processing_time_seconds: float

    @property
    def throughput_records_per_sec(self) -> float:
        """Calculate records per second throughput."""
        if self.processing_time_seconds > 0:
            return self.records_processed / self.processing_time_seconds
        return 0.0

    @property
    def throughput_mb_per_sec(self) -> float:
        """Calculate megabytes per second throughput."""
        if self.processing_time_seconds > 0:
            mb = self.file_size_bytes / (1024 * 1024)
            return mb / self.processing_time_seconds
        return 0.0

    @property
    def match_rate(self) -> float:
        """Calculate match rate as percentage."""
        if self.records_processed > 0:
            return (self.records_matched / self.records_processed) * 100
        return 0.0


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics.

    Attributes:
        total_files: Total number of files processed
        total_records: Total number of records processed
        total_bytes: Total bytes processed
        total_time_seconds: Total processing time
        file_performances: Per-file performance data
        worker_times: Time spent by each worker thread
    """

    total_files: int = 0
    total_records: int = 0
    total_bytes: int = 0
    total_time_seconds: float = 0.0
    file_performances: List[FilePerformance] = field(default_factory=list)
    worker_times: Dict[str, float] = field(default_factory=dict)

    @property
    def avg_records_per_sec(self) -> float:
        """Calculate average records per second."""
        if self.total_time_seconds > 0:
            return self.total_records / self.total_time_seconds
        return 0.0

    @property
    def avg_mb_per_sec(self) -> float:
        """Calculate average megabytes per second."""
        if self.total_time_seconds > 0:
            mb = self.total_bytes / (1024 * 1024)
            return mb / self.total_time_seconds
        return 0.0

    @property
    def avg_file_time_seconds(self) -> float:
        """Calculate average time per file."""
        if self.total_files > 0:
            return self.total_time_seconds / self.total_files
        return 0.0

    @property
    def total_megabytes(self) -> float:
        """Calculate total megabytes processed."""
        return self.total_bytes / (1024 * 1024)

    def get_slowest_files(self, n: int = 10) -> List[FilePerformance]:
        """Get the n slowest files by processing time.

        Args:
            n: Number of files to return

        Returns:
            List of slowest file performances
        """
        return sorted(
            self.file_performances, key=lambda x: x.processing_time_seconds, reverse=True
        )[:n]

    def get_largest_files(self, n: int = 10) -> List[FilePerformance]:
        """Get the n largest files by size.

        Args:
            n: Number of files to return

        Returns:
            List of largest file performances
        """
        return sorted(self.file_performances, key=lambda x: x.file_size_bytes, reverse=True)[:n]


class PerformanceTracker:
    """Thread-safe performance metrics tracker.

    Tracks detailed performance metrics for file processing operations
    including per-file metrics and aggregated statistics.

    Example:
        >>> tracker = PerformanceTracker()
        >>> with tracker.track_file(path, size) as timer:
        ...     records = process_file(path)
        ...     timer.set_records(records, matches)
        >>> metrics = tracker.get_metrics()
    """

    def __init__(self) -> None:
        """Initialize performance tracker."""
        self._lock = Lock()
        self._file_performances: List[FilePerformance] = []
        self._worker_times: Dict[str, float] = defaultdict(float)
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def start(self) -> None:
        """Mark the start of processing."""
        with self._lock:
            self._start_time = time.time()

    def stop(self) -> None:
        """Mark the end of processing."""
        with self._lock:
            self._end_time = time.time()

    def track_file(
        self, file_path: Path, file_size: int, worker_id: Optional[str] = None
    ) -> "FileTimer":
        """Create a timer for tracking file processing.

        Args:
            file_path: Path to file being processed
            file_size: Size of file in bytes
            worker_id: Optional worker thread identifier

        Returns:
            Context manager for timing file processing
        """
        return FileTimer(
            tracker=self, file_path=str(file_path), file_size=file_size, worker_id=worker_id
        )

    def _record_file_performance(
        self,
        file_path: str,
        file_size: int,
        records_processed: int,
        records_matched: int,
        processing_time: float,
        worker_id: Optional[str],
    ) -> None:
        """Record performance metrics for a completed file.

        Args:
            file_path: Path to processed file
            file_size: Size of file
            records_processed: Number of records processed
            records_matched: Number of records matched
            processing_time: Time spent processing
            worker_id: Worker thread identifier
        """
        perf = FilePerformance(
            file_path=file_path,
            file_size_bytes=file_size,
            records_processed=records_processed,
            records_matched=records_matched,
            processing_time_seconds=processing_time,
        )

        with self._lock:
            self._file_performances.append(perf)
            if worker_id is not None:
                self._worker_times[worker_id] += processing_time

    def get_metrics(self) -> PerformanceMetrics:
        """Get aggregated performance metrics.

        Returns:
            Performance metrics snapshot
        """
        with self._lock:
            total_files = len(self._file_performances)
            total_records = sum(p.records_processed for p in self._file_performances)
            total_bytes = sum(p.file_size_bytes for p in self._file_performances)

            # Calculate total time
            if self._start_time and self._end_time:
                total_time = self._end_time - self._start_time
            else:
                total_time = sum(p.processing_time_seconds for p in self._file_performances)

            return PerformanceMetrics(
                total_files=total_files,
                total_records=total_records,
                total_bytes=total_bytes,
                total_time_seconds=total_time,
                file_performances=list(self._file_performances),
                worker_times=dict(self._worker_times),
            )


class FileTimer:
    """Context manager for timing file processing.

    Example:
        >>> with tracker.track_file(path, size) as timer:
        ...     records = process_file(path)
        ...     timer.set_records(100, 25)
    """

    def __init__(
        self, tracker: PerformanceTracker, file_path: str, file_size: int, worker_id: Optional[str]
    ):
        """Initialize file timer.

        Args:
            tracker: Parent performance tracker
            file_path: Path to file being processed
            file_size: Size of file in bytes
            worker_id: Optional worker thread identifier
        """
        self._tracker = tracker
        self._file_path = file_path
        self._file_size = file_size
        self._worker_id = worker_id
        self._start_time: float = 0.0
        self._records_processed: int = 0
        self._records_matched: int = 0

    def __enter__(self) -> "FileTimer":
        """Enter context manager and start timing."""
        self._start_time = time.time()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """Exit context manager and record metrics."""
        processing_time = time.time() - self._start_time

        # Only record if processing completed successfully
        if exc_type is None:
            self._tracker._record_file_performance(
                file_path=self._file_path,
                file_size=self._file_size,
                records_processed=self._records_processed,
                records_matched=self._records_matched,
                processing_time=processing_time,
                worker_id=self._worker_id,
            )

    def set_records(self, processed: int, matched: int) -> None:
        """Set record counts for the file.

        Args:
            processed: Number of records processed
            matched: Number of records matched
        """
        self._records_processed = processed
        self._records_matched = matched
