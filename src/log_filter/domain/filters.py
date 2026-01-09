"""
Filter strategies for log record filtering.

This module provides filter strategies for date and time filtering
of log records. Follows the Strategy pattern for extensibility.
"""

from abc import ABC, abstractmethod
from datetime import date, time
from typing import TYPE_CHECKING, Optional

from log_filter.domain.models import LogRecord

if TYPE_CHECKING:
    from log_filter.processing.record_parser import StreamingRecordParser


class RecordFilter(ABC):
    """Abstract base class for record filters.
    
    Filters determine whether a log record should be included
    based on specific criteria (date, time, content, etc.).
    """
    
    @abstractmethod
    def matches(self, record: LogRecord) -> bool:
        """Check if record matches filter criteria.
        
        Args:
            record: LogRecord to check
            
        Returns:
            True if record passes the filter
        """
        pass


class DateRangeFilter(RecordFilter):
    """Filter records by date range.
    
    Includes records with dates within the specified range (inclusive).
    Records without date information are excluded.
    
    Attributes:
        date_from: Start date (inclusive), None means no lower bound
        date_to: End date (inclusive), None means no upper bound
        parser: Record parser for date extraction
    """
    
    def __init__(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        parser: Optional["StreamingRecordParser"] = None
    ) -> None:
        """Initialize date range filter.
        
        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            parser: Record parser for date extraction (creates default if None)
        """
        self.date_from = date_from
        self.date_to = date_to
        if parser is None:
            from log_filter.processing.record_parser import StreamingRecordParser
            self.parser = StreamingRecordParser()
        else:
            self.parser = parser
        
        # Validate range
        if date_from and date_to and date_from > date_to:
            raise ValueError(
                f"Invalid date range: from={date_from} > to={date_to}"
            )
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record's date is within range.
        
        Args:
            record: LogRecord to check
            
        Returns:
            True if record's date is within range, False otherwise
        """
        # If no date filter, accept all
        if self.date_from is None and self.date_to is None:
            return True
        
        # Extract date from record (it's already a date object)
        record_date = record.date
        if record_date is None:
            return False
        
        # Check lower bound
        if self.date_from and record_date < self.date_from:
            return False
        
        # Check upper bound
        if self.date_to and record_date > self.date_to:
            return False
        
        return True


class TimeRangeFilter(RecordFilter):
    """Filter records by time range.
    
    Includes records with times within the specified range (inclusive).
    Records without time information are excluded.
    
    Attributes:
        time_from: Start time (inclusive), None means no lower bound
        time_to: End time (inclusive), None means no upper bound
        parser: Record parser for time extraction
    """
    
    def __init__(
        self,
        time_from: Optional[time] = None,
        time_to: Optional[time] = None,
        parser: Optional["StreamingRecordParser"] = None
    ) -> None:
        """Initialize time range filter.
        
        Args:
            time_from: Start time (inclusive)
            time_to: End time (inclusive)
            parser: Record parser for time extraction (creates default if None)
        """
        self.time_from = time_from
        self.time_to = time_to
        if parser is None:
            from log_filter.processing.record_parser import StreamingRecordParser
            self.parser = StreamingRecordParser()
        else:
            self.parser = parser
        
        # Validate range
        if time_from and time_to and time_from > time_to:
            raise ValueError(
                f"Invalid time range: from={time_from} > to={time_to}"
            )
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record's time is within range.
        
        Args:
            record: LogRecord to check
            
        Returns:
            True if record's time is within range, False otherwise
        """
        # If no time filter, accept all
        if self.time_from is None and self.time_to is None:
            return True
        
        # Extract time from record (it's already a time object)
        record_time = record.time
        if record_time is None:
            return False
        
        # Check lower bound
        if self.time_from and record_time < self.time_from:
            return False
        
        # Check upper bound
        if self.time_to and record_time > self.time_to:
            return False
        
        return True


class CompositeFilter(RecordFilter):
    """Composite filter that combines multiple filters with AND logic.
    
    A record must pass all constituent filters to pass the composite.
    
    Attributes:
        filters: List of filters to apply
    """
    
    def __init__(self, *filters: RecordFilter) -> None:
        """Initialize composite filter.
        
        Args:
            ``*filters``: Variable number of filters to combine
        """
        self.filters = list(filters)
    
    def add_filter(self, filter: RecordFilter) -> None:
        """Add a filter to the composite.
        
        Args:
            filter: Filter to add
        """
        self.filters.append(filter)
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record passes all filters.
        
        Args:
            record: LogRecord to check
            
        Returns:
            True if record passes all filters, False otherwise
        """
        return all(f.matches(record) for f in self.filters)
    
    def __repr__(self) -> str:
        """String representation of the composite filter."""
        return f"CompositeFilter(filters={len(self.filters)})"


class AlwaysPassFilter(RecordFilter):
    """Filter that always passes (no filtering).
    
    Useful as a null object when no filtering is needed.
    """
    
    def matches(self, record: LogRecord) -> bool:
        """Always returns True.
        
        Args:
            record: LogRecord (unused)
            
        Returns:
            Always True
        """
        return True
