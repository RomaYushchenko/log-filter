Command-Line Interface
======================

The CLI module provides the command-line interface for the log filter tool.

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

.. automodule:: log_filter.cli
   :members:
   :undoc-members:
   :show-inheritance:

Basic Usage
-----------

Simple search:

.. code-block:: bash

    log-filter "ERROR" /var/log

Search with boolean operators:

.. code-block:: bash

    log-filter "ERROR AND database" /var/log

Output to file:

.. code-block:: bash

    log-filter "ERROR" /var/log -o errors.txt

Command-Line Arguments
----------------------

Positional Arguments
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    log-filter EXPRESSION SEARCH_ROOT

* ``EXPRESSION``: Boolean search expression
* ``SEARCH_ROOT``: Directory to search for log files

Optional Arguments
^^^^^^^^^^^^^^^^^^

Search Options
""""""""""""""

.. code-block:: bash

    -c, --case-sensitive     # Enable case-sensitive matching
    --date-from DATE         # Filter from date (YYYY-MM-DD)
    --date-to DATE           # Filter to date (YYYY-MM-DD)
    --time-from TIME         # Filter from time (HH:MM:SS)
    --time-to TIME           # Filter to time (HH:MM:SS)

File Options
""""""""""""

.. code-block:: bash

    -i, --include PATTERN    # Include file patterns (*.log)
    -e, --exclude PATTERN    # Exclude file patterns (*.old)
    --follow-symlinks        # Follow symbolic links
    --max-depth N            # Maximum directory depth

Output Options
""""""""""""""

.. code-block:: bash

    -o, --output FILE        # Output file path
    --overwrite              # Overwrite existing output file
    -n, --dry-run            # Count matches without writing
    -s, --stats              # Show statistics
    -v, --verbose            # Verbose output
    -q, --quiet              # Suppress non-error output

Processing Options
""""""""""""""""""

.. code-block:: bash

    -w, --workers N          # Number of worker threads
    --buffer-size N          # I/O buffer size (bytes)
    --encoding ENC           # File encoding (default: utf-8)

Other Options
"""""""""""""

.. code-block:: bash

    --config FILE            # Load configuration from file
    --version                # Show version
    -h, --help               # Show help message

Examples
--------

Basic Search
^^^^^^^^^^^^

Search for "ERROR" in all log files:

.. code-block:: bash

    log-filter "ERROR" /var/log

Boolean Expressions
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # AND operator
    log-filter "ERROR AND database" /var/log

    # OR operator
    log-filter "ERROR OR WARNING" /var/log

    # NOT operator
    log-filter "ERROR NOT timeout" /var/log

    # Complex expression
    log-filter "(ERROR OR CRITICAL) AND database" /var/log

Date/Time Filtering
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Specific date range
    log-filter "ERROR" /var/log --date-from 2026-01-01 --date-to 2026-01-31

    # Specific time range
    log-filter "ERROR" /var/log --time-from 09:00:00 --time-to 17:00:00

    # Combine date and time
    log-filter "ERROR" /var/log \
        --date-from 2026-01-01 \
        --time-from 09:00:00 \
        --time-to 17:00:00

File Pattern Filtering
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Include specific patterns
    log-filter "ERROR" /var/log -i "*.log" -i "*.log.gz"

    # Exclude patterns
    log-filter "ERROR" /var/log -e "*.old" -e "*.tmp"

    # Combine include and exclude
    log-filter "ERROR" /var/log -i "*.log" -e "debug.log"

Output Control
^^^^^^^^^^^^^^

.. code-block:: bash

    # Write to file
    log-filter "ERROR" /var/log -o errors.txt

    # Overwrite existing file
    log-filter "ERROR" /var/log -o errors.txt --overwrite

    # Dry run (count only)
    log-filter "ERROR" /var/log --dry-run --stats

    # Quiet mode
    log-filter "ERROR" /var/log -o errors.txt --quiet

Performance Tuning
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Use 8 worker threads
    log-filter "ERROR" /var/log -w 8

    # Increase buffer size
    log-filter "ERROR" /var/log --buffer-size 65536

    # Specify encoding
    log-filter "ERROR" /var/log --encoding utf-16

Configuration File
------------------

Using Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    log-filter --config config.yaml

Example configuration file:

.. code-block:: yaml

    # config.yaml
    search:
      expression: "ERROR AND database"
      ignore_case: false
      date_from: "2026-01-01"
      date_to: "2026-01-31"

    files:
      search_root: "/var/log"
      include_patterns:
        - "*.log"
        - "*.log.gz"
      exclude_patterns:
        - "*.old"
      max_depth: 5

    output:
      output_file: "errors.txt"
      show_stats: true
      verbose: false

    processing:
      max_workers: 4
      buffer_size: 8192

Mixed Configuration
^^^^^^^^^^^^^^^^^^^

Command-line arguments override configuration file:

.. code-block:: bash

    # Use config but override expression and output
    log-filter "CRITICAL" /var/log \
        --config config.yaml \
        -o critical.txt

Output Format
-------------

Standard Output
^^^^^^^^^^^^^^^

Matching records are written with metadata:

.. code-block:: text

    === File: /var/log/app.log (lines 142-144) ===
    2026-01-08 10:30:45 ERROR Database connection timeout
      at DatabaseConnector.connect(db.py:42)
      Caused by: Network timeout after 30s

Statistics Output
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    log-filter "ERROR" /var/log --stats

Output:

.. code-block:: text

    ================================================================================
    Processing Statistics
    ================================================================================

    Files:
      Processed:     10
      Matched:       7 (70.0%)
      Skipped:       0

    Records:
      Total:         15,000
      Matched:       240 (1.6%)

    Performance:
      Time:          12.5s
      Throughput:    1,200 records/sec
      Speed:         4.0 MB/sec

    ================================================================================

Verbose Output
^^^^^^^^^^^^^^

.. code-block:: bash

    log-filter "ERROR" /var/log --verbose

Shows detailed progress:

.. code-block:: text

    [INFO] Scanning directory: /var/log
    [INFO] Found 10 files matching patterns
    [INFO] Processing: /var/log/app.log
    [INFO]   Records: 1500 | Matches: 23 | Time: 1.2s
    [INFO] Processing: /var/log/db.log
    [INFO]   Records: 2400 | Matches: 45 | Time: 2.1s
    ...

Dry Run Output
^^^^^^^^^^^^^^

.. code-block:: bash

    log-filter "ERROR" /var/log --dry-run --stats

Shows statistics without writing output:

.. code-block:: text

    [DRY RUN] No output file will be created

    Files: 10 | Records: 15,000 | Matches: 240 (1.6%)

Exit Codes
----------

The CLI returns standard exit codes:

.. code-block:: text

    0   Success - matches found
    1   Error - processing failed
    2   No matches found
    3   Configuration error
    4   File not found or permission denied

.. code-block:: bash

    log-filter "ERROR" /var/log
    echo $?  # Check exit code

Environment Variables
---------------------

Configure via environment variables:

.. code-block:: bash

    export LOG_FILTER_WORKERS=8
    export LOG_FILTER_ENCODING=utf-8
    export LOG_FILTER_BUFFER_SIZE=16384
    export LOG_FILTER_VERBOSE=1

    log-filter "ERROR" /var/log

Supported variables:
    * ``LOG_FILTER_WORKERS`` - Number of worker threads
    * ``LOG_FILTER_ENCODING`` - File encoding
    * ``LOG_FILTER_BUFFER_SIZE`` - I/O buffer size
    * ``LOG_FILTER_VERBOSE`` - Enable verbose output (1/0)
    * ``LOG_FILTER_QUIET`` - Enable quiet mode (1/0)
    * ``LOG_FILTER_CONFIG`` - Default config file path

Shell Integration
-----------------

Bash Completion
^^^^^^^^^^^^^^^

.. code-block:: bash

    # Add to ~/.bashrc
    eval "$(log-filter --completion bash)"

    # Then use tab completion
    log-filter "ERROR" /var/log --<TAB>

Aliases
^^^^^^^

.. code-block:: bash

    # Add to ~/.bashrc
    alias lferr='log-filter "ERROR" /var/log'
    alias lfwarn='log-filter "WARNING OR ERROR" /var/log'
    alias lfcrit='log-filter "CRITICAL" /var/log'

Piping
^^^^^^

.. code-block:: bash

    # Pipe to other commands
    log-filter "ERROR" /var/log | grep "database" | less

    # Count matches
    log-filter "ERROR" /var/log | wc -l

    # Extract timestamps
    log-filter "ERROR" /var/log | cut -d' ' -f1-2

Redirection
^^^^^^^^^^^

.. code-block:: bash

    # Redirect to file (alternative to -o)
    log-filter "ERROR" /var/log > errors.txt 2>&1

    # Append to existing file
    log-filter "ERROR" /var/log >> errors.txt

Advanced Usage
--------------

Cron Jobs
^^^^^^^^^

.. code-block:: bash

    # Daily error report
    0 0 * * * log-filter "ERROR OR CRITICAL" /var/log \
        --date-from $(date -d "yesterday" +\%Y-\%m-\%d) \
        --date-to $(date +\%Y-\%m-\%d) \
        -o /reports/daily-errors.txt \
        --overwrite

Monitoring
^^^^^^^^^^

.. code-block:: bash

    #!/bin/bash
    # alert-on-critical.sh

    MATCHES=$(log-filter "CRITICAL" /var/log --dry-run --quiet | grep -oP '\d+' | tail -1)

    if [ "$MATCHES" -gt 10 ]; then
        echo "ALERT: $MATCHES critical errors found!"
        # Send alert...
    fi

Log Rotation
^^^^^^^^^^^^

.. code-block:: bash

    # Process all log files including rotated ones
    log-filter "ERROR" /var/log \
        -i "*.log" \
        -i "*.log.[0-9]" \
        -i "*.log.gz" \
        -o today-errors.txt

Docker Usage
^^^^^^^^^^^^

.. code-block:: bash

    # Run in Docker container
    docker run -v /var/log:/logs log-filter:latest \
        "ERROR" /logs \
        -o /logs/errors.txt

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**No matches found:**

.. code-block:: bash

    # Check if files are readable
    log-filter "ERROR" /var/log --verbose

    # Try case-insensitive
    log-filter "error" /var/log

**Permission denied:**

.. code-block:: bash

    # Run with sudo
    sudo log-filter "ERROR" /var/log

    # Or change permissions
    chmod +r /var/log/*.log

**Out of memory:**

.. code-block:: bash

    # Reduce workers
    log-filter "ERROR" /var/log -w 2

    # Reduce buffer size
    log-filter "ERROR" /var/log --buffer-size 4096

Debug Mode
^^^^^^^^^^

.. code-block:: bash

    # Enable debug logging
    export LOG_LEVEL=DEBUG
    log-filter "ERROR" /var/log --verbose

Performance Optimization
------------------------

For Large Log Collections
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Optimize for many files
    log-filter "ERROR" /var/log \
        -w 8 \
        --buffer-size 65536 \
        --max-depth 3

For Large Individual Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Optimize for large files
    log-filter "ERROR" /var/log \
        -w 2 \
        --buffer-size 131072

For Fast Pattern Matching
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Use case-insensitive for better performance
    log-filter "error" /var/log  # Faster than "ERROR" with --case-sensitive

Best Practices
--------------

1. **Expressions**: Use parentheses for complex expressions
2. **Patterns**: Be specific with include/exclude patterns
3. **Workers**: Match worker count to workload (I/O vs CPU)
4. **Output**: Always specify output file for large result sets
5. **Dry Run**: Use ``--dry-run`` to preview before processing
6. **Stats**: Use ``--stats`` to monitor performance
7. **Verbose**: Use ``--verbose`` for troubleshooting
8. **Config Files**: Use config files for repeated searches
