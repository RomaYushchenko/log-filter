Utilities Module
================

The utilities module provides helper functions for logging, progress tracking, and text highlighting.

.. contents:: Contents
   :local:
   :depth: 2

Logging
-------

.. automodule:: log_filter.utils.logging
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Structured logging configuration and utilities.

Basic Setup
^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.logging import configure_logging, get_logger

    # Configure logging
    configure_logging(
        level="INFO",
        log_file="app.log",
        format="json"  # or "text"
    )
    
    # Get logger
    logger = get_logger(__name__)
    
    # Log messages
    logger.info("Processing started")
    logger.error("Failed to open file", extra={"file": "app.log"})

Log Levels
^^^^^^^^^^

.. code-block:: python

    # Set different log levels
    configure_logging(level="DEBUG")    # Show all messages
    configure_logging(level="INFO")     # Info and above
    configure_logging(level="WARNING")  # Warnings and errors only
    configure_logging(level="ERROR")    # Errors only

Structured Logging
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    logger = get_logger(__name__)
    
    # JSON-formatted structured logs
    logger.info(
        "File processed",
        extra={
            "file": "app.log",
            "records": 1500,
            "matches": 45,
            "duration_ms": 1250
        }
    )
    
    # Output (JSON):
    # {
    #   "timestamp": "2026-01-08T10:30:45.123Z",
    #   "level": "INFO",
    #   "message": "File processed",
    #   "file": "app.log",
    #   "records": 1500,
    #   "matches": 45,
    #   "duration_ms": 1250
    # }

Component Logging
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.logging import configure_component_logging

    # Configure different levels for different components
    configure_component_logging({
        "log_filter.core": "DEBUG",
        "log_filter.infrastructure": "INFO",
        "log_filter.processing": "WARNING"
    })

File Logging
^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.logging import create_file_logger
    from pathlib import Path

    # Create logger that writes to file
    logger = create_file_logger(Path("processing.log"))
    
    logger.info("Processing started")
    # Writes to processing.log

Progress Tracking
-----------------

.. automodule:: log_filter.utils.progress
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Real-time progress tracking and display.

ProgressTracker
^^^^^^^^^^^^^^^

Thread-safe progress tracking with visual feedback.

.. code-block:: python

    from log_filter.utils.progress import ProgressTracker

    files = ["app.log", "db.log", "web.log"]
    
    tracker = ProgressTracker(
        total=len(files),
        desc="Processing files",
        unit="files"
    )
    
    for file in files:
        # Process file
        process_file(file)
        
        # Update progress
        tracker.update(1)
    
    tracker.close()

Output:

.. code-block:: text

    Processing files: 100%|██████████| 3/3 [00:12<00:00,  4.2s/files]

Advanced Progress
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.progress import ProgressTracker

    tracker = ProgressTracker(
        total=1000,
        desc="Processing records",
        unit="records",
        leave=True,          # Keep progress bar after completion
        ncols=80,            # Width in characters
        miniters=1,          # Update frequency
        dynamic_ncols=True   # Auto-adjust to terminal width
    )
    
    for i in range(1000):
        # Process record
        process_record(i)
        
        # Update with custom stats
        tracker.update(1)
        tracker.set_postfix(
            matches=matched_count,
            rate=f"{records_per_sec:.0f}/s"
        )

Context Manager
^^^^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.progress import ProgressTracker

    with ProgressTracker(total=len(files), desc="Processing") as tracker:
        for file in files:
            process_file(file)
            tracker.update(1)
    # Automatically closes

ProgressCounter
^^^^^^^^^^^^^^^

Simple counter without visual display.

.. code-block:: python

    from log_filter.utils.progress import ProgressCounter

    counter = ProgressCounter()
    
    for item in items:
        process(item)
        counter.increment()
    
    print(f"Processed {counter.count} items")

Text Highlighting
-----------------

.. automodule:: log_filter.utils.highlighter
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Terminal text highlighting and formatting.

TextHighlighter
^^^^^^^^^^^^^^^

ANSI color highlighting for terminal output.

.. code-block:: python

    from log_filter.utils.highlighter import TextHighlighter

    highlighter = TextHighlighter()
    
    # Highlight matching terms
    text = "ERROR: Database connection failed"
    highlighted = highlighter.highlight(text, ["ERROR", "database"])
    print(highlighted)
    # Output: \x1b[91mERROR\x1b[0m: \x1b[91mDatabase\x1b[0m connection failed

Colors
^^^^^^

.. code-block:: python

    from log_filter.utils.highlighter import TextHighlighter

    highlighter = TextHighlighter(
        match_color="red",        # Highlight color for matches
        background=False,         # No background color
        bold=True                 # Bold text
    )
    
    highlighted = highlighter.highlight(text, ["ERROR"])

Available colors:
    * ``red``, ``green``, ``yellow``, ``blue``, ``magenta``, ``cyan``, ``white``
    * ``bright_red``, ``bright_green``, etc.

Case-Insensitive Highlighting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    highlighter = TextHighlighter()
    
    text = "Error in database connection"
    highlighted = highlighter.highlight(
        text, 
        ["ERROR", "DATABASE"],
        case_sensitive=False
    )
    # Highlights "Error" and "database"

Disable Highlighting
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # For non-terminal output or plain text
    highlighter = TextHighlighter(enabled=False)
    
    highlighted = highlighter.highlight(text, ["ERROR"])
    # Returns original text without ANSI codes

Helper Functions
^^^^^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.highlighter import highlight_text

    # Convenience function
    highlighted = highlight_text(
        text="ERROR: Connection failed",
        terms=["ERROR"],
        color="red",
        bold=True
    )

Complete Utilities Example
---------------------------

.. code-block:: python

    from log_filter.utils.logging import configure_logging, get_logger
    from log_filter.utils.progress import ProgressTracker
    from log_filter.utils.highlighter import TextHighlighter

    # Setup
    configure_logging(level="INFO")
    logger = get_logger(__name__)
    highlighter = TextHighlighter()
    
    files = ["app.log", "db.log", "web.log"]
    matches = []
    
    # Process with progress tracking
    with ProgressTracker(total=len(files), desc="Scanning") as progress:
        for file in files:
            logger.info("Processing file", extra={"file": file})
            
            # Simulated processing
            for line in read_file(file):
                if "ERROR" in line:
                    highlighted = highlighter.highlight(line, ["ERROR"])
                    matches.append(highlighted)
            
            progress.update(1)
    
    # Display results
    logger.info("Processing complete", extra={
        "files": len(files),
        "matches": len(matches)
    })
    
    for match in matches:
        print(match)

Performance Considerations
--------------------------

Logging
^^^^^^^

* **Overhead**: <1% for INFO level, <5% for DEBUG level
* **I/O**: Asynchronous handlers minimize blocking
* **Memory**: Rotating logs prevent disk fill
* **Thread Safety**: All loggers are thread-safe

Progress Tracking
^^^^^^^^^^^^^^^^^

* **Overhead**: ~0.1-1% depending on update frequency
* **Terminal**: Uses ANSI escape codes (minimal overhead)
* **Network**: Avoid frequent updates over slow connections
* **Thread Safety**: ProgressTracker is thread-safe

Text Highlighting
^^^^^^^^^^^^^^^^^

* **Overhead**: ~1-5% for complex highlighting
* **ANSI Codes**: Negligible size increase (~20 bytes per highlight)
* **Regex**: Pre-compiled patterns for performance
* **Memory**: Minimal (original string + highlighted string)

Best Practices
--------------

Logging
^^^^^^^

1. **Structured**: Use structured logging for machine-readable logs
2. **Levels**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
3. **Context**: Include context in ``extra`` dict
4. **Rotation**: Configure log rotation for production
5. **Performance**: Avoid logging in tight loops

Progress Tracking
^^^^^^^^^^^^^^^^^

1. **Granularity**: Update every 1-100 items (avoid per-line updates)
2. **Description**: Use clear, concise descriptions
3. **Units**: Specify appropriate units (files, records, MB)
4. **Cleanup**: Always close or use context manager
5. **TTY Detection**: Disable in non-interactive environments

Text Highlighting
^^^^^^^^^^^^^^^^^

1. **Terminal Detection**: Auto-detect terminal capabilities
2. **Disable**: Disable for piped output or log files
3. **Colors**: Use consistent color scheme
4. **Performance**: Avoid highlighting very long lines
5. **Accessibility**: Consider color-blind users

Thread Safety
-------------

* **Logging**: All logging functions are thread-safe
* **ProgressTracker**: Thread-safe with internal locking
* **TextHighlighter**: Thread-safe (stateless operations)

All utility components can be safely used in multi-threaded applications.

Configuration Examples
----------------------

Production Logging
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from log_filter.utils.logging import configure_logging

    configure_logging(
        level="INFO",
        log_file="/var/log/log-filter/app.log",
        format="json",
        max_bytes=10485760,  # 10 MB
        backup_count=5,       # Keep 5 backup files
        enable_console=False  # Log to file only
    )

Development Logging
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    configure_logging(
        level="DEBUG",
        format="text",
        enable_console=True,
        enable_colors=True
    )

Silent Mode
^^^^^^^^^^^

.. code-block:: python

    # Minimal output
    configure_logging(level="ERROR")
    tracker = ProgressTracker(total=files, disable=True)

Verbose Mode
^^^^^^^^^^^^

.. code-block:: python

    # Maximum verbosity
    configure_logging(level="DEBUG")
    tracker = ProgressTracker(
        total=files,
        desc="Processing",
        leave=True,
        unit="files",
        dynamic_ncols=True
    )
