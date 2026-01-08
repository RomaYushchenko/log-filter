"""
Thread-safe statistics collector for processing metrics.

This module provides thread-safe collection of processing statistics
including file counts, record counts, and performance metrics.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProcessingStats:
    """Statistics for log processing.
    
    Tracks various metrics during processing including file counts,
    record counts, match counts, and skip reasons.
    
    All fields are updated atomically through the StatisticsCollector.
    """
    
    # File statistics
    files_scanned: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    skip_reasons: Dict[str, int] = field(default_factory=dict)
    
    # Record statistics
    records_total: int = 0
    records_matched: int = 0
    records_skipped: int = 0
    
    # Data volume
    total_bytes_processed: int = 0
    total_lines_processed: int = 0
    
    # Performance metrics
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate processing duration in seconds.
        
        Returns:
            Duration in seconds, or 0 if not started/ended
        """
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    @property
    def records_per_second(self) -> float:
        """Calculate records processed per second.
        
        Returns:
            Records per second, or 0 if duration is 0
        """
        duration = self.duration_seconds
        return self.records_total / duration if duration > 0 else 0.0
    
    @property
    def megabytes_processed(self) -> float:
        """Calculate total megabytes processed.
        
        Returns:
            Total MB processed (rounded to 2 decimals)
        """
        return round(self.total_bytes_processed / (1024 * 1024), 2)


class StatisticsCollector:
    """Thread-safe collector for processing statistics.
    
    Provides atomic operations for updating statistics from multiple
    worker threads. Uses a lock to ensure consistency.
    
    Attributes:
        stats: Current processing statistics
        
    Example:
        >>> collector = StatisticsCollector()
        >>> collector.start()
        >>> collector.increment_files_processed()
        >>> collector.increment_records_total(100)
        >>> collector.stop()
        >>> print(f"Processed {collector.stats.records_total} records")
    """
    
    def __init__(self) -> None:
        """Initialize the statistics collector."""
        self.stats = ProcessingStats()
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Mark processing start time."""
        with self._lock:
            self.stats.start_time = time.time()
    
    def stop(self) -> None:
        """Mark processing end time."""
        with self._lock:
            self.stats.end_time = time.time()
    
    def increment_files_scanned(self, count: int = 1) -> None:
        """Increment scanned files count.
        
        Args:
            count: Number of files to add (default: 1)
        """
        with self._lock:
            self.stats.files_scanned += count
    
    def increment_files_processed(self, count: int = 1) -> None:
        """Increment processed files count.
        
        Args:
            count: Number of files to add (default: 1)
        """
        with self._lock:
            self.stats.files_processed += count
    
    def increment_files_skipped(self, reason: str, count: int = 1) -> None:
        """Increment skipped files count with reason.
        
        Args:
            reason: Skip reason (e.g., 'size-limit', 'name-filter')
            count: Number of files to add (default: 1)
        """
        with self._lock:
            self.stats.files_skipped += count
            self.stats.skip_reasons[reason] = (
                self.stats.skip_reasons.get(reason, 0) + count
            )
    
    def increment_records_total(self, count: int = 1) -> None:
        """Increment total records count.
        
        Args:
            count: Number of records to add (default: 1)
        """
        with self._lock:
            self.stats.records_total += count
    
    def increment_records_matched(self, count: int = 1) -> None:
        """Increment matched records count.
        
        Args:
            count: Number of records to add (default: 1)
        """
        with self._lock:
            self.stats.records_matched += count
    
    def increment_records_skipped(self, count: int = 1) -> None:
        """Increment skipped records count.
        
        Args:
            count: Number of records to add (default: 1)
        """
        with self._lock:
            self.stats.records_skipped += count
    
    def add_bytes_processed(self, bytes_count: int) -> None:
        """Add to total bytes processed.
        
        Args:
            bytes_count: Number of bytes to add
        """
        with self._lock:
            self.stats.total_bytes_processed += bytes_count
    
    def add_lines_processed(self, lines_count: int) -> None:
        """Add to total lines processed.
        
        Args:
            lines_count: Number of lines to add
        """
        with self._lock:
            self.stats.total_lines_processed += lines_count
    
    def get_snapshot(self) -> ProcessingStats:
        """Get a snapshot of current statistics.
        
        Returns:
            Copy of current statistics
        """
        with self._lock:
            # Create a copy to avoid external modification
            return ProcessingStats(
                files_scanned=self.stats.files_scanned,
                files_processed=self.stats.files_processed,
                files_skipped=self.stats.files_skipped,
                skip_reasons=self.stats.skip_reasons.copy(),
                records_total=self.stats.records_total,
                records_matched=self.stats.records_matched,
                records_skipped=self.stats.records_skipped,
                total_bytes_processed=self.stats.total_bytes_processed,
                total_lines_processed=self.stats.total_lines_processed,
                start_time=self.stats.start_time,
                end_time=self.stats.end_time
            )
    
    def reset(self) -> None:
        """Reset all statistics to initial state."""
        with self._lock:
            self.stats = ProcessingStats()
    
    def __repr__(self) -> str:
        """String representation of the collector."""
        snapshot = self.get_snapshot()
        return (
            f"StatisticsCollector(files={snapshot.files_processed}, "
            f"records={snapshot.records_total}, "
            f"matches={snapshot.records_matched})"
        )
