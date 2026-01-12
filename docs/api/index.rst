API Reference
=============

This section provides detailed documentation for all public APIs in the Log Filter package.

.. toctree::
   :maxdepth: 2
   :caption: API Modules:

   core
   domain
   config
   infrastructure
   processing
   statistics
   utils
   cli

Overview
--------

The Log Filter API is organized into the following modules:

* **core** - Core expression parsing and evaluation
* **domain** - Domain models and business logic
* **config** - Configuration models and validation
* **infrastructure** - File handling and I/O operations
* **processing** - Log record processing pipeline
* **statistics** - Metrics collection and reporting
* **utils** - Utility functions and helpers
* **cli** - Command-line interface

Quick Start
-----------

Basic usage example:

.. code-block:: python

    from log_filter.core.parser import parse
    from log_filter.core.evaluator import Evaluator
    from log_filter.domain.models import LogRecord
    from datetime import datetime

    # Parse a boolean expression
    ast = parse("ERROR AND database")

    # Create evaluator
    evaluator = Evaluator(ast, ignore_case=False)

    # Evaluate against a log record
    record = LogRecord(
        timestamp=datetime.now(),
        level="ERROR",
        content="Database connection failed",
        source_file="app.log",
        line_number_start=10,
        line_number_end=10
    )

    result = evaluator.evaluate(record.content)
    print(f"Match: {result}")  # True

Advanced Usage
--------------

For more complex scenarios, see the individual module documentation.
