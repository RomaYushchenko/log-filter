Configuration Module
====================

The configuration module handles application configuration through dataclasses with validation.

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

.. automodule:: log_filter.config.models
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Models
--------------------

SearchConfig
^^^^^^^^^^^^

Configuration for search behavior.

.. code-block:: python

    from log_filter.config.models import SearchConfig

    config = SearchConfig(
        expression="ERROR AND database",
        case_sensitive=False,
        include_patterns=("*.log", "*.txt"),
        exclude_patterns=("*.old",)
    )
    
    print(f"Expression: {config.expression}")
    print(f"Case sensitive: {config.case_sensitive}")

Attributes:
    * ``expression`` (str): Boolean search expression
    * ``case_sensitive`` (bool): Whether search is case-sensitive (default: False)
    * ``include_patterns`` (tuple[str, ...]): File patterns to include
    * ``exclude_patterns`` (tuple[str, ...]): File patterns to exclude
    * ``date_from`` (Optional[date]): Filter records from this date
    * ``date_to`` (Optional[date]): Filter records until this date
    * ``time_from`` (Optional[time]): Filter records from this time
    * ``time_to`` (Optional[time]): Filter records until this time

FileConfig
^^^^^^^^^^

Configuration for file discovery and handling.

.. code-block:: python

    from log_filter.config.models import FileConfig
    from pathlib import Path

    config = FileConfig(
        search_root=Path("/var/log"),
        include_patterns=("*.log", "*.gz"),
        exclude_patterns=("*.old", "*.tmp"),
        follow_symlinks=False,
        max_depth=5
    )
    
    print(f"Search in: {config.search_root}")
    print(f"Max depth: {config.max_depth}")

Attributes:
    * ``search_root`` (Path): Root directory for file search
    * ``include_patterns`` (tuple[str, ...]): Glob patterns to include
    * ``exclude_patterns`` (tuple[str, ...]): Glob patterns to exclude
    * ``follow_symlinks`` (bool): Whether to follow symbolic links
    * ``max_depth`` (Optional[int]): Maximum directory depth to traverse

OutputConfig
^^^^^^^^^^^^

Configuration for output generation.

.. code-block:: python

    from log_filter.config.models import OutputConfig
    from pathlib import Path

    config = OutputConfig(
        output_file=Path("results.txt"),
        overwrite=False,
        dry_run=False,
        show_stats=True,
        verbose=False
    )
    
    print(f"Output to: {config.output_file}")
    print(f"Show stats: {config.show_stats}")

Attributes:
    * ``output_file`` (Optional[Path]): Output file path (None for stdout)
    * ``overwrite`` (bool): Whether to overwrite existing output file
    * ``dry_run`` (bool): If True, only count matches without writing
    * ``show_stats`` (bool): Whether to display statistics
    * ``verbose`` (bool): Enable verbose output
    * ``quiet`` (bool): Suppress non-error output

ProcessingConfig
^^^^^^^^^^^^^^^^

Configuration for processing behavior.

.. code-block:: python

    from log_filter.config.models import ProcessingConfig

    config = ProcessingConfig(
        max_workers=4,
        buffer_size=8192,
        encoding="utf-8",
        errors="replace"
    )
    
    print(f"Workers: {config.max_workers}")
    print(f"Buffer: {config.buffer_size} bytes")

Attributes:
    * ``max_workers`` (int): Number of worker threads (default: CPU count)
    * ``buffer_size`` (int): I/O buffer size in bytes (default: 8192)
    * ``encoding`` (str): File encoding (default: "utf-8")
    * ``errors`` (str): Error handling strategy (default: "replace")
    * ``chunk_size`` (int): Records per processing chunk

ApplicationConfig
^^^^^^^^^^^^^^^^^

Top-level application configuration combining all sub-configs.

.. code-block:: python

    from log_filter.config.models import (
        ApplicationConfig, 
        SearchConfig,
        FileConfig, 
        OutputConfig,
        ProcessingConfig
    )
    from pathlib import Path

    config = ApplicationConfig(
        search=SearchConfig(expression="ERROR"),
        files=FileConfig(search_root=Path("/var/log")),
        output=OutputConfig(show_stats=True),
        processing=ProcessingConfig(max_workers=4)
    )
    
    # Access nested configuration
    print(f"Expression: {config.search.expression}")
    print(f"Workers: {config.processing.max_workers}")

Complete Configuration Example
-------------------------------

.. code-block:: python

    from log_filter.config.models import (
        ApplicationConfig,
        SearchConfig,
        FileConfig,
        OutputConfig,
        ProcessingConfig
    )
    from pathlib import Path
    from datetime import date, time

    # Create comprehensive configuration
    config = ApplicationConfig(
        search=SearchConfig(
            expression="(ERROR OR CRITICAL) AND database",
            case_sensitive=False,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            time_from=time(9, 0),
            time_to=time(17, 0)
        ),
        files=FileConfig(
            search_root=Path("/var/log/myapp"),
            include_patterns=("*.log", "*.log.gz"),
            exclude_patterns=("*.old", "*.tmp"),
            follow_symlinks=False,
            max_depth=3
        ),
        output=OutputConfig(
            output_file=Path("errors.txt"),
            overwrite=False,
            dry_run=False,
            show_stats=True,
            verbose=True
        ),
        processing=ProcessingConfig(
            max_workers=8,
            buffer_size=16384,
            encoding="utf-8",
            errors="replace"
        )
    )

Configuration from YAML
-----------------------

Example YAML configuration file:

.. code-block:: yaml

    # config.yaml
    search:
      expression: "ERROR AND database"
      case_sensitive: false
      date_from: "2026-01-01"
      date_to: "2026-01-31"
    
    files:
      search_root: "/var/log"
      include_patterns:
        - "*.log"
        - "*.log.gz"
      exclude_patterns:
        - "*.old"
      follow_symlinks: false
      max_depth: 5
    
    output:
      output_file: "results.txt"
      show_stats: true
      verbose: false
    
    processing:
      max_workers: 4
      buffer_size: 8192
      encoding: "utf-8"

Loading configuration from YAML:

.. code-block:: python

    import yaml
    from pathlib import Path
    from log_filter.config.models import ApplicationConfig, SearchConfig, FileConfig

    with open("config.yaml") as f:
        data = yaml.safe_load(f)
    
    # Construct configuration from dict
    config = ApplicationConfig(
        search=SearchConfig(**data["search"]),
        files=FileConfig(**data["files"]),
        # ... other configs
    )

Validation
----------

Configuration models validate inputs at construction:

.. code-block:: python

    from log_filter.config.models import ProcessingConfig

    # Invalid: negative workers
    try:
        config = ProcessingConfig(max_workers=-1)
    except ValueError as e:
        print(f"Validation error: {e}")
    
    # Invalid: invalid encoding
    try:
        config = ProcessingConfig(encoding="invalid_codec")
    except ValueError as e:
        print(f"Validation error: {e}")

Configuration Precedence
-------------------------

When configuration comes from multiple sources, the precedence is:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file**
4. **Default values** (lowest priority)

.. code-block:: python

    # Merge configurations with precedence
    def merge_configs(cli_config, file_config, defaults):
        return ApplicationConfig(
            search=cli_config.search or file_config.search or defaults.search,
            files=cli_config.files or file_config.files or defaults.files,
            # ... merge other configs
        )

Best Practices
--------------

1. **Immutability**: Configuration objects are frozen dataclasses - create new instances for changes
2. **Validation**: Always validate configuration before use
3. **Type Safety**: Use type hints and dataclass annotations
4. **Defaults**: Provide sensible defaults for all optional parameters
5. **Documentation**: Document all configuration options with examples

Environment Variables
---------------------

Common environment variables:

.. code-block:: bash

    export LOG_FILTER_WORKERS=8              # Number of worker threads
    export LOG_FILTER_ENCODING=utf-8         # File encoding
    export LOG_FILTER_BUFFER_SIZE=16384      # I/O buffer size
    export LOG_FILTER_VERBOSE=1              # Enable verbose output

Thread Safety
-------------

Configuration objects are immutable and thread-safe. They can be safely shared across threads.
