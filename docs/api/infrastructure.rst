Infrastructure Module
=====================

The infrastructure module handles file system operations, I/O, and file format handling.

.. contents:: Contents
   :local:
   :depth: 2

File Scanner
------------

.. automodule:: log_filter.infrastructure.file_scanner
   :members:
   :undoc-members:
   :show-inheritance:

Discovers files matching specified patterns.

.. code-block:: python

    from log_filter.infrastructure.file_scanner import FileScanner
    from pathlib import Path

    scanner = FileScanner(
        search_root=Path("/var/log"),
        include_patterns=("*.log", "*.log.gz"),
        exclude_patterns=("*.old", "*.tmp"),
        follow_symlinks=False,
        max_depth=3
    )
    
    # Scan for files
    files = scanner.scan()
    print(f"Found {len(files)} files")
    
    for file_path in files:
        print(f"  - {file_path}")

Features:
    * Glob pattern matching (``*.log``, ``app-*.gz``)
    * Include/exclude patterns
    * Maximum depth limiting
    * Symbolic link handling
    * Efficient directory traversal

File Handlers
-------------

Abstract Base Handler
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: log_filter.infrastructure.file_handlers.base
   :members:
   :undoc-members:
   :show-inheritance:

Base class for all file handlers.

.. code-block:: python

    from log_filter.infrastructure.file_handlers.base import AbstractFileHandler
    from pathlib import Path

    class CustomHandler(AbstractFileHandler):
        def can_handle(self, file_path: Path) -> bool:
            return file_path.suffix == ".custom"
        
        def read_lines(self, file_path: Path):
            # Custom reading logic
            with open(file_path, "r") as f:
                yield from f

Log File Handler
^^^^^^^^^^^^^^^^

.. automodule:: log_filter.infrastructure.file_handlers.log_handler
   :members:
   :undoc-members:
   :show-inheritance:

Handles plain text log files (``.log``, ``.txt``).

.. code-block:: python

    from log_filter.infrastructure.file_handlers.log_handler import LogFileHandler
    from pathlib import Path

    handler = LogFileHandler(encoding="utf-8", errors="replace")
    
    # Check if handler can process file
    file_path = Path("app.log")
    if handler.can_handle(file_path):
        # Read lines
        for line in handler.read_lines(file_path):
            print(line, end="")

Features:
    * Configurable encoding (default: UTF-8)
    * Error handling strategies (replace, ignore, strict)
    * Efficient line-by-line streaming
    * Large file support

Gzip File Handler
^^^^^^^^^^^^^^^^^

.. automodule:: log_filter.infrastructure.file_handlers.gzip_handler
   :members:
   :undoc-members:
   :show-inheritance:

Handles gzip-compressed log files (``.gz``).

.. code-block:: python

    from log_filter.infrastructure.file_handlers.gzip_handler import GzipFileHandler
    from pathlib import Path

    handler = GzipFileHandler(encoding="utf-8", errors="replace")
    
    # Read compressed file
    file_path = Path("app.log.gz")
    if handler.can_handle(file_path):
        for line in handler.read_lines(file_path):
            print(line, end="")

Features:
    * Transparent gzip decompression
    * Streaming decompression (memory-efficient)
    * Same interface as LogFileHandler
    * Automatic format detection

File Handler Factory
^^^^^^^^^^^^^^^^^^^^

.. automodule:: log_filter.infrastructure.file_handler_factory
   :members:
   :undoc-members:
   :show-inheritance:

Factory for creating appropriate file handlers.

.. code-block:: python

    from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
    from pathlib import Path

    factory = FileHandlerFactory(encoding="utf-8", errors="replace")
    
    # Get handler for any file
    file_path = Path("app.log.gz")
    handler = factory.get_handler(file_path)
    
    # Use handler
    for line in handler.read_lines(file_path):
        process_line(line)

Supported formats:
    * ``.log`` → LogFileHandler
    * ``.txt`` → LogFileHandler
    * ``.gz`` → GzipFileHandler
    * Others → Raises FileHandlingError

File Writer
-----------

.. automodule:: log_filter.infrastructure.file_writer
   :members:
   :undoc-members:
   :show-inheritance:

Handles output file writing with thread-safe operations.

.. code-block:: python

    from log_filter.infrastructure.file_writer import FileWriter
    from pathlib import Path

    writer = FileWriter(
        output_file=Path("results.txt"),
        encoding="utf-8",
        overwrite=False
    )
    
    # Write matching records
    with writer:
        writer.write("ERROR: Database connection timeout\n")
        writer.write("ERROR: Failed to execute query\n")
    
    print(f"Wrote {writer.bytes_written} bytes")

Features:
    * Thread-safe writing (lock-based)
    * Atomic operations
    * Context manager support
    * Progress tracking (bytes written)
    * Overwrite protection

Complete File Processing Example
---------------------------------

.. code-block:: python

    from log_filter.infrastructure.file_scanner import FileScanner
    from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
    from log_filter.infrastructure.file_writer import FileWriter
    from pathlib import Path

    # Step 1: Discover files
    scanner = FileScanner(
        search_root=Path("/var/log"),
        include_patterns=("*.log", "*.gz"),
        exclude_patterns=("*.old",)
    )
    files = scanner.scan()
    print(f"Found {len(files)} files")
    
    # Step 2: Set up file handling
    factory = FileHandlerFactory(encoding="utf-8")
    writer = FileWriter(output_file=Path("results.txt"))
    
    # Step 3: Process files
    with writer:
        for file_path in files:
            handler = factory.get_handler(file_path)
            
            for line in handler.read_lines(file_path):
                if "ERROR" in line:
                    writer.write(line)
    
    print(f"Wrote {writer.bytes_written} bytes")

Error Handling
--------------

.. code-block:: python

    from log_filter.core.exceptions import FileHandlingError
    from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
    from pathlib import Path

    factory = FileHandlerFactory()
    
    try:
        # Try to process file
        handler = factory.get_handler(Path("missing.log"))
        for line in handler.read_lines(Path("missing.log")):
            print(line)
    except FileHandlingError as e:
        print(f"Error: {e}")
        # Handle error (skip file, log, etc.)

Common errors:
    * File not found
    * Permission denied
    * Corrupted gzip file
    * Encoding errors
    * Disk full (writing)

Performance Considerations
--------------------------

File Reading
^^^^^^^^^^^^

* **Buffer Size**: Default 8KB, configurable for large files
* **Streaming**: Files processed line-by-line (memory-efficient)
* **Compression**: Gzip decompression adds ~20% overhead
* **Throughput**: ~100-200 MB/s for uncompressed, ~80-150 MB/s for gzip

File Scanning
^^^^^^^^^^^^^

* **Directory Traversal**: O(n) where n is the number of directories
* **Pattern Matching**: O(m) where m is the number of files
* **Optimization**: Use ``max_depth`` to limit traversal
* **Caching**: Scanner results can be cached for repeated scans

File Writing
^^^^^^^^^^^^

* **Locking**: Write operations are synchronized (thread-safe)
* **Buffering**: System buffer used for efficient writes
* **Atomic**: Each write operation is atomic
* **Throughput**: ~500 MB/s (depends on storage)

Best Practices
--------------

1. **Resource Management**: Always use context managers (``with`` statement)
2. **Error Handling**: Catch ``FileHandlingError`` for robust error handling
3. **Encoding**: Specify encoding explicitly, use ``errors="replace"`` for robustness
4. **Large Files**: Use streaming (default behavior) instead of loading into memory
5. **Compression**: Use GzipFileHandler for ``.gz`` files automatically via factory

Thread Safety
-------------

* **FileScanner**: Thread-safe (read-only operations)
* **FileHandlers**: Thread-safe for reading (no shared state)
* **FileWriter**: Thread-safe with internal locking
* **FileHandlerFactory**: Thread-safe (stateless)

All infrastructure components can be safely used in multi-threaded environments.

Extension Points
----------------

To add support for new file formats:

.. code-block:: python

    from log_filter.infrastructure.file_handlers.base import AbstractFileHandler
    from pathlib import Path

    class BZ2FileHandler(AbstractFileHandler):
        \"\"\"Handler for bzip2-compressed files.\"\"\"
        
        def can_handle(self, file_path: Path) -> bool:
            return file_path.suffix.lower() == ".bz2"
        
        def read_lines(self, file_path: Path):
            import bz2
            with bz2.open(file_path, "rt", encoding=self.encoding) as f:
                yield from f

    # Register with factory
    factory = FileHandlerFactory()
    factory.register_handler(BZ2FileHandler())
