Domain Module
=============

The domain module contains core business entities and filtering logic.

.. contents:: Contents
   :local:
   :depth: 2

Models
------

.. automodule:: log_filter.domain.models
   :members:
   :undoc-members:
   :show-inheritance:

Core domain models representing log records, search results, and file metadata.

LogRecord
^^^^^^^^^

Represents a parsed log record with timestamp, level, and content.

.. code-block:: python

    from log_filter.domain.models import LogRecord
    from datetime import datetime

    # Create a log record
    record = LogRecord(
        timestamp=datetime(2026, 1, 8, 10, 30, 45),
        level="ERROR",
        content="Database connection timeout after 30s",
        source_file="app.log",
        line_number_start=142,
        line_number_end=144
    )

    print(record.timestamp)  # 2026-01-08 10:30:45
    print(record.level)      # ERROR
    print(record.content)    # Database connection timeout after 30s

SearchResult
^^^^^^^^^^^^

Represents the result of a search operation against a log record.

.. code-block:: python

    from log_filter.domain.models import SearchResult, LogRecord

    result = SearchResult(
        matched=True,
        record=record,
        match_positions=[(0, 5), (10, 20)]  # Byte positions of matches
    )

    if result.matched:
        print(f"Found match in {result.record.source_file}")

FileMetadata
^^^^^^^^^^^^

Metadata about a processed file.

.. code-block:: python

    from log_filter.domain.models import FileMetadata
    from pathlib import Path

    metadata = FileMetadata(
        path=Path("/logs/app.log"),
        size_bytes=1024000,
        is_compressed=False,
        records_count=150,
        matches_count=12
    )

    print(f"File: {metadata.path}")
    print(f"Size: {metadata.size_bytes / 1024:.1f} KB")
    print(f"Match rate: {metadata.matches_count / metadata.records_count:.1%}")

Filters
-------

.. automodule:: log_filter.domain.filters
   :members:
   :undoc-members:
   :show-inheritance:

Filter strategies for filtering log records by date, time, or composite criteria.

RecordFilter (Abstract Base)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Base class for all filters.

.. code-block:: python

    from log_filter.domain.filters import RecordFilter
    from log_filter.domain.models import LogRecord

    class CustomFilter(RecordFilter):
        def filter(self, record: LogRecord) -> bool:
            # Custom filtering logic
            return "CRITICAL" in record.level

DateRangeFilter
^^^^^^^^^^^^^^^

Filter records by date range.

.. code-block:: python

    from log_filter.domain.filters import DateRangeFilter
    from datetime import date

    # Filter records from January 1-7, 2026
    filter = DateRangeFilter(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 7)
    )

    # Check if record passes filter
    if filter.filter(record):
        print("Record is within date range")

TimeRangeFilter
^^^^^^^^^^^^^^^

Filter records by time of day.

.. code-block:: python

    from log_filter.domain.filters import TimeRangeFilter
    from datetime import time

    # Filter records between 9 AM and 5 PM
    filter = TimeRangeFilter(
        start_time=time(9, 0, 0),
        end_time=time(17, 0, 0)
    )

    if filter.filter(record):
        print("Record is within business hours")

CompositeFilter
^^^^^^^^^^^^^^^

Combine multiple filters with AND logic.

.. code-block:: python

    from log_filter.domain.filters import (
        CompositeFilter,
        DateRangeFilter,
        TimeRangeFilter
    )
    from datetime import date, time

    # Filter records from Jan 1-7 between 9 AM - 5 PM
    composite = CompositeFilter([
        DateRangeFilter(date(2026, 1, 1), date(2026, 1, 7)),
        TimeRangeFilter(time(9, 0), time(17, 0))
    ])

    if composite.filter(record):
        print("Record passes all filters")

AlwaysPassFilter
^^^^^^^^^^^^^^^^

A filter that always passes (no-op filter).

.. code-block:: python

    from log_filter.domain.filters import AlwaysPassFilter

    # No filtering
    filter = AlwaysPassFilter()
    result = filter.filter(record)  # Always True

Filter Chain Example
^^^^^^^^^^^^^^^^^^^^

Complex filtering scenario:

.. code-block:: python

    from log_filter.domain.filters import CompositeFilter, DateRangeFilter
    from log_filter.domain.models import LogRecord
    from datetime import date, datetime

    # Create multiple filters
    date_filter = DateRangeFilter(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31)
    )

    # Combine filters
    composite = CompositeFilter([date_filter])

    # Filter records
    records = [...]  # List of LogRecord objects
    filtered = [r for r in records if composite.filter(r)]

    print(f"Filtered {len(filtered)} / {len(records)} records")

Design Patterns
---------------

The domain module uses several design patterns:

* **Value Objects**: ``LogRecord``, ``SearchResult`` are immutable value objects
* **Strategy Pattern**: ``RecordFilter`` implementations provide different filtering strategies
* **Composite Pattern**: ``CompositeFilter`` combines multiple filters
* **Null Object Pattern**: ``AlwaysPassFilter`` provides a safe no-op filter

Best Practices
--------------

1. **Immutability**: Domain models are immutable (frozen dataclasses) - create new instances for modifications
2. **Type Safety**: All fields are strongly typed with dataclass annotations
3. **Filter Composition**: Use ``CompositeFilter`` to combine multiple filters instead of nested if statements
4. **Validation**: Models validate their inputs at construction time

Thread Safety
-------------

All domain models are immutable and thread-safe. Filters are stateless and can be safely shared across threads.

Performance Considerations
--------------------------

* **Model Creation**: Dataclasses are optimized for fast creation (~1-2μs per instance)
* **Filtering**: O(1) for most filters, O(n) for composite filters with n sub-filters
* **Memory**: Models use ``__slots__`` where applicable to minimize memory overhead
