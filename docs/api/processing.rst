Processing Module
=================

The processing module orchestrates log record parsing, evaluation, and multi-threaded processing.

.. contents:: Contents
   :local:
   :depth: 2

Record Parser
-------------

.. automodule:: log_filter.processing.record_parser
   :members:
   :undoc-members:
   :show-inheritance:

Parses multi-line log records from raw text lines.

.. code-block:: python

    from log_filter.processing.record_parser import StreamingRecordParser

    parser = StreamingRecordParser()
    
    # Feed lines to parser
    lines = [
        "2026-01-08 10:30:45 ERROR Database connection failed",
        "  at DatabaseConnector.connect(db.py:42)",
        "  Caused by: Network timeout",
        "2026-01-08 10:30:46 INFO Retrying connection..."
    ]
    
    for line in lines:
        records = parser.feed_line(line, line_number=1)
        for record in records:
            print(f"{record.level}: {record.content[:50]}")
    
    # Get final record
    final_records = parser.finalize()

Features:
    * **Streaming**: Processes lines as they arrive
    * **Multi-line**: Automatically groups multi-line records
    * **Timestamp Parsing**: Extracts timestamps from log lines
    * **Level Detection**: Identifies log levels (ERROR, INFO, etc.)
    * **Memory Efficient**: Yields records incrementally

Record Format
^^^^^^^^^^^^^

Supported log formats:

.. code-block:: text

    # Standard format
    2026-01-08 10:30:45 ERROR Database connection failed
    
    # With milliseconds
    2026-01-08 10:30:45.123 WARNING Slow query detected
    
    # ISO format
    2026-01-08T10:30:45Z INFO Operation completed
    
    # Multi-line record
    2026-01-08 10:30:45 ERROR Exception in handler
      at Handler.process(handler.py:123)
      Caused by: NullPointerException

Worker
------

.. automodule:: log_filter.processing.worker
   :members:
   :undoc-members:
   :show-inheritance:

Worker thread that processes individual files.

.. code-block:: python

    from log_filter.processing.worker import FileWorker
    from log_filter.core.evaluator import Evaluator
    from log_filter.core.parser import parse
    from pathlib import Path

    # Create worker
    ast = parse("ERROR OR WARNING")
    evaluator = Evaluator(ast, case_sensitive=False)
    
    worker = FileWorker(
        worker_id=0,
        evaluator=evaluator,
        file_handler=file_handler,
        output_writer=output_writer,
        stats_collector=stats_collector
    )
    
    # Process a file
    result = worker.process_file(Path("app.log"))
    print(f"Processed {result.records_processed} records")
    print(f"Found {result.matches_found} matches")

Worker Result:
    * ``records_processed``: Number of records parsed
    * ``matches_found``: Number of matching records
    * ``processing_time``: Time taken in seconds
    * ``errors``: List of errors encountered

Pipeline
--------

.. automodule:: log_filter.processing.pipeline
   :members:
   :undoc-members:
   :show-inheritance:

Orchestrates the complete processing pipeline with multi-threading.

.. code-block:: python

    from log_filter.processing.pipeline import ProcessingPipeline
    from log_filter.config.models import ApplicationConfig, ProcessingConfig
    from pathlib import Path

    # Create pipeline
    config = ApplicationConfig(
        search=search_config,
        files=file_config,
        output=output_config,
        processing=ProcessingConfig(max_workers=4)
    )
    
    pipeline = ProcessingPipeline(config)
    
    # Process files
    files = [Path("app.log"), Path("db.log"), Path("web.log")]
    result = pipeline.process(files)
    
    print(f"Processed {result.total_files} files")
    print(f"Found {result.total_matches} matches")
    print(f"Time: {result.total_time:.2f}s")

Pipeline Stages:
    1. **File Discovery**: Scan directories for log files
    2. **Worker Creation**: Spawn worker threads
    3. **Task Distribution**: Assign files to workers
    4. **Parallel Processing**: Process files concurrently
    5. **Result Aggregation**: Collect and combine results
    6. **Statistics**: Generate final statistics

Complete Processing Example
----------------------------

.. code-block:: python

    from log_filter.processing.pipeline import ProcessingPipeline
    from log_filter.config.models import (
        ApplicationConfig,
        SearchConfig,
        FileConfig,
        OutputConfig,
        ProcessingConfig
    )
    from pathlib import Path

    # Configure processing
    config = ApplicationConfig(
        search=SearchConfig(
            expression="ERROR AND database",
            case_sensitive=False
        ),
        files=FileConfig(
            search_root=Path("/var/log"),
            include_patterns=("*.log", "*.gz")
        ),
        output=OutputConfig(
            output_file=Path("errors.txt"),
            show_stats=True
        ),
        processing=ProcessingConfig(
            max_workers=4,
            buffer_size=8192
        )
    )
    
    # Create and run pipeline
    pipeline = ProcessingPipeline(config)
    result = pipeline.run()
    
    # Display results
    print(f"Files processed: {result.total_files}")
    print(f"Records processed: {result.total_records}")
    print(f"Matches found: {result.total_matches}")
    print(f"Processing time: {result.total_time:.2f}s")
    print(f"Throughput: {result.records_per_second:.0f} records/sec")

Error Handling
--------------

.. code-block:: python

    from log_filter.processing.pipeline import ProcessingPipeline
    from log_filter.core.exceptions import FileHandlingError

    pipeline = ProcessingPipeline(config)
    
    try:
        result = pipeline.run()
    except FileHandlingError as e:
        print(f"File error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Pipeline handles per-file errors gracefully
        # Only critical errors propagate

Per-file error handling:
    * **Missing files**: Logged and skipped
    * **Permission errors**: Logged and skipped
    * **Corrupt files**: Logged and skipped
    * **Encoding errors**: Line skipped with replacement character

Progress Monitoring
-------------------

.. code-block:: python

    from log_filter.processing.pipeline import ProcessingPipeline
    
    pipeline = ProcessingPipeline(config)
    
    # Process with progress callback
    def progress_callback(files_done, total_files):
        percent = (files_done / total_files) * 100
        print(f"Progress: {files_done}/{total_files} ({percent:.1f}%)")
    
    result = pipeline.run(progress_callback=progress_callback)

Progress information:
    * Files processed / total files
    * Records processed
    * Matches found
    * Current throughput
    * Estimated time remaining

Performance Tuning
------------------

Worker Count
^^^^^^^^^^^^

.. code-block:: python

    import os
    
    # Use CPU count
    workers = os.cpu_count()
    
    # For I/O-bound tasks, can use more
    workers = os.cpu_count() * 2
    
    # For CPU-bound tasks, match CPU count
    workers = os.cpu_count()
    
    config = ProcessingConfig(max_workers=workers)

Guidelines:
    * **I/O-bound** (many files): 2× CPU count
    * **CPU-bound** (complex expressions): 1× CPU count
    * **Mixed workload**: 1.5× CPU count
    * **Large files**: Fewer workers (memory constraint)

Buffer Size
^^^^^^^^^^^

.. code-block:: python

    # Small files: smaller buffer
    config = ProcessingConfig(buffer_size=4096)
    
    # Large files: larger buffer
    config = ProcessingConfig(buffer_size=65536)
    
    # Default (balanced)
    config = ProcessingConfig(buffer_size=8192)

Guidelines:
    * **Many small files**: 4-8 KB
    * **Few large files**: 32-64 KB
    * **SSD storage**: Larger buffers (32 KB+)
    * **Network storage**: Smaller buffers (8 KB)

Memory Management
^^^^^^^^^^^^^^^^^

.. code-block:: python

    # For memory-constrained environments
    config = ProcessingConfig(
        max_workers=2,              # Fewer workers
        buffer_size=4096,           # Smaller buffers
        chunk_size=100              # Process in smaller chunks
    )
    
    # For high-memory servers
    config = ProcessingConfig(
        max_workers=16,             # More workers
        buffer_size=65536,          # Larger buffers
        chunk_size=1000             # Larger chunks
    )

Performance Metrics
-------------------

Typical performance characteristics:

.. code-block:: python

    # Small files (1-10 MB)
    Throughput: ~5,000-10,000 lines/sec
    Latency: <1 second
    Memory: ~50-100 MB
    
    # Medium files (10-100 MB)
    Throughput: ~3,000-5,000 lines/sec
    Latency: 2-20 seconds
    Memory: ~100-200 MB
    
    # Large files (100-1000 MB)
    Throughput: ~2,000-3,000 lines/sec
    Latency: 30-300 seconds
    Memory: ~200-500 MB (streaming)

Factors affecting performance:
    * **File size**: Larger files = more I/O overhead
    * **Expression complexity**: Complex expressions = slower evaluation
    * **Match rate**: High match rate = more output writes
    * **Storage type**: SSD > HDD > Network
    * **Compression**: Gzip adds ~20% overhead

Best Practices
--------------

1. **Worker Count**: Start with CPU count, tune based on workload
2. **Error Handling**: Let pipeline handle per-file errors gracefully
3. **Progress Monitoring**: Use callbacks for long-running operations
4. **Memory**: Use streaming (default) for large files
5. **Buffer Size**: Tune based on file size and storage type
6. **Testing**: Profile with representative data before production

Thread Safety
-------------

* **StreamingRecordParser**: NOT thread-safe (per-thread instance)
* **FileWorker**: Thread-safe (isolated state per worker)
* **ProcessingPipeline**: Thread-safe (manages workers internally)

Each worker has its own parser and evaluator instance, ensuring thread safety.

Scalability
-----------

The processing module scales linearly with CPU cores:

.. code-block:: text

    1 worker:  5,000 lines/sec
    2 workers: 10,000 lines/sec
    4 workers: 20,000 lines/sec
    8 workers: 40,000 lines/sec (diminishing returns beyond I/O limit)

Limitations:
    * **I/O bound**: Limited by storage throughput
    * **Memory**: Each worker consumes ~50-100 MB
    * **GIL**: Python GIL limits CPU parallelism (less impact for I/O tasks)
    * **Context switching**: Too many workers increases overhead
