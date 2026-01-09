# Architecture

**Version:** 2.0.0  
**Last Updated:** January 8, 2026  
**Status:** Stable Production Release

---

## Table of Contents

- [Overview](#overview)
- [Architectural Principles](#architectural-principles)
- [System Architecture](#system-architecture)
- [Module Structure](#module-structure)
- [Design Patterns](#design-patterns)
- [Concurrency Model](#concurrency-model)
- [Data Flow](#data-flow)
- [Performance Architecture](#performance-architecture)
- [Extension Points](#extension-points)
- [Deployment Architectures](#deployment-architectures)

---

## Overview

Log Filter is a high-performance log filtering system built on **Clean Architecture** principles with clear separation of concerns and dependency inversion. The system processes log files in parallel, applying boolean expression filters to extract relevant records.

**Key Characteristics:**
- ⚡ **High Performance**: 200K+ records/second throughput
- 🔀 **Parallel Processing**: Multi-threaded worker pool architecture
- 📦 **Modular Design**: Clean separation of concerns
- 🔌 **Extensible**: Plugin-based handler and filter system
- 🛡️ **Robust**: Comprehensive error handling and recovery
- 📊 **Observable**: Built-in statistics and monitoring

### Architectural Goals

1. **Separation of Concerns**: Each layer has a single, well-defined responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level details
3. **Testability**: All components are independently testable
4. **Extensibility**: New features can be added without modifying existing code
5. **Performance**: Optimized for high-throughput log processing
6. **Maintainability**: Clear structure and documentation

---

## Architectural Principles

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                         │
│              (User Input/Output, Formatting)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  cli.py, main.py                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Application Layer                            │
│          (Use Cases, Pipeline Orchestration)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  processing/pipeline.py                                   │  │
│  │  processing/processor.py                                  │  │
│  │  processing/worker.py                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                       Domain Layer                              │
│     (Business Logic, Entities, Expression Evaluation)          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  core/tokenizer.py - Boolean expression parsing          │  │
│  │  core/parser.py - AST construction                        │  │
│  │  core/evaluator.py - Expression evaluation               │  │
│  │  domain/models.py - Domain entities                       │  │
│  │  domain/filters.py - Filter strategies                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  Infrastructure Layer                           │
│        (File I/O, Configuration, External Services)            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  infrastructure/file_handlers/ - File reading            │  │
│  │  infrastructure/file_scanner.py - File discovery         │  │
│  │  infrastructure/file_writer.py - Output writing          │  │
│  │  config/loader.py - Configuration loading                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Flow

**Rule:** Dependencies point inward. Outer layers depend on inner layers, never the reverse.

```
CLI ──→ Application ──→ Domain ←── Infrastructure
                          ↑
                    (Abstractions)
```

**Benefits:**
- Domain logic remains independent of frameworks and tools
- Easy to test domain logic in isolation
- Infrastructure can be swapped without affecting business logic

---

## System Architecture

### High-Level Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                           CLI Entry                            │
│                    (Argument Processing)                        │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                  ┌───────▼────────┐
                  │  Configuration │
                  │     Loader     │
                  └───────┬────────┘
                          │
         ┌────────────────▼────────────────┐
         │     Processing Pipeline         │
         │   (Main Orchestrator)           │
         └────┬──────────────────────┬─────┘
              │                      │
    ┌─────────▼────────┐   ┌────────▼─────────┐
    │  File Scanner    │   │ Expression       │
    │  (Discovery)     │   │ Parser           │
    └─────────┬────────┘   └────────┬─────────┘
              │                      │
    ┌─────────▼──────────────────────▼─────────┐
    │         Worker Thread Pool               │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐│
    │  │Worker│  │Worker│  │Worker│  │Worker││
    │  │  1   │  │  2   │  │  3   │  │  N   ││
    │  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘│
    └──────┼─────────┼─────────┼─────────┼────┘
           │         │         │         │
    ┌──────▼─────────▼─────────▼─────────▼────┐
    │         Buffered File Writer             │
    │         (Thread-Safe Output)             │
    └──────────────────┬───────────────────────┘
                       │
             ┌─────────▼──────────┐
             │  Statistics        │
             │  Collector         │
             └────────────────────┘
```

### Processing Flow

```
Input Phase:
  CLI Args ──→ Config Loader ──→ Validated Config

Discovery Phase:
  Search Root ──→ File Scanner ──→ File List
                       ↓
                  Apply Filters
                       ↓
                  Filtered List

Distribution Phase:
  File List ──→ Work Queue ──→ Worker Threads

Processing Phase (Per Worker):
  File ──→ File Handler ──→ Line Reader
           ↓                     ↓
      Decompress          Parse Record
           ↓                     ↓
      Lines Stream        Apply Expression
                               ↓
                          Match/No Match
                               ↓
                          Buffer Results

Output Phase:
  Worker Buffers ──→ File Writer ──→ Output File
         ↓
  Statistics ──→ Collector ──→ Report
```

---

## Module Structure

### Core Module (`log_filter/core/`)

**Purpose:** Boolean expression parsing and evaluation engine

#### Components:

**`tokenizer.py`** - Lexical Analysis
```python
class Tokenizer:
    """Converts boolean expression strings into tokens.
    
    Supports: AND, OR, NOT, parentheses, quoted strings
    """
```
- Converts input string to token stream
- Handles quoted strings and escape sequences
- Validates token syntax

**`parser.py`** - Syntax Analysis
```python
class Parser:
    """Builds Abstract Syntax Tree from tokens.
    
    Grammar:
      expression → and_expr ( OR and_expr )*
      and_expr   → not_expr ( AND not_expr )*
      not_expr   → NOT? primary
      primary    → TERM | ( expression )
    """
```
- Recursive descent parser
- Builds AST for expression evaluation
- Validates expression structure

**`evaluator.py`** - Expression Evaluation
```python
class Evaluator:
    """Evaluates AST against log records.
    
    Features:
    - Lazy evaluation (short-circuit)
    - Case-sensitive/insensitive matching
    - Regex and substring matching
    """
```
- Traverses AST and evaluates nodes
- Matches against log record content
- Returns boolean result

**`exceptions.py`** - Exception Hierarchy
```python
LogFilterException
├── ParseException        # Expression parsing errors
├── EvaluationException   # Runtime evaluation errors
├── ConfigurationException # Config validation errors
└── FileProcessingException # File handling errors
```

---

### Domain Module (`log_filter/domain/`)

**Purpose:** Business logic and domain entities

#### Components:

**`models.py`** - Domain Entities
```python
@dataclass
class LogRecord:
    """Represents a single log record.
    
    Attributes:
        content: Raw log line
        timestamp: Parsed timestamp (optional)
        line_number: Line number in file
        file_path: Source file path
    """

@dataclass
class SearchResult:
    """Results of a search operation.
    
    Attributes:
        matched_records: List of matching records
        total_records: Total records processed
        files_processed: Number of files scanned
    """
```

**`filters.py`** - Filter Strategies
```python
class AbstractFilter(ABC):
    """Base class for all filters."""
    
    @abstractmethod
    def matches(self, record: LogRecord) -> bool:
        """Check if record matches filter."""

class DateFilter(AbstractFilter):
    """Filter by date range."""

class TimeFilter(AbstractFilter):
    """Filter by time range."""

class ExpressionFilter(AbstractFilter):
    """Filter by boolean expression."""

class FilterChain:
    """Combines multiple filters with AND logic."""
```

**`matchers.py`** - Match Strategies
```python
class AbstractMatcher(ABC):
    """Base class for matching strategies."""

class SubstringMatcher:
    """Fast substring matching."""

class RegexMatcher:
    """Regex pattern matching with caching."""

class CaseInsensitiveMatcher:
    """Case-insensitive matching wrapper."""
```

---

### Infrastructure Module (`log_filter/infrastructure/`)

**Purpose:** External dependencies and I/O operations

#### Components:

**`file_handlers/`** - File Format Support
```python
class AbstractFileHandler(ABC):
    """Base interface for file handlers."""
    
    @abstractmethod
    def read_lines(self) -> Generator[str, None, None]:
        """Stream lines from file."""

class PlainTextHandler(AbstractFileHandler):
    """Handles .log, .txt files."""

class GzipHandler(AbstractFileHandler):
    """Handles .gz compressed files."""

class FileHandlerFactory:
    """Creates appropriate handler for file type."""
```

**`file_scanner.py`** - File Discovery
```python
class FileScanner:
    """Scans directories for log files.
    
    Features:
    - Recursive directory traversal
    - Pattern matching (glob, regex)
    - File filtering (size, date, extension)
    - Exclusion patterns
    """
```

**`file_writer.py`** - Output Writing
```python
class BufferedLogWriter:
    """Thread-safe buffered file writer.
    
    Features:
    - Automatic buffer flushing
    - Thread-safe operations
    - Configurable buffer size
    - Memory-efficient for large outputs
    """
```

**`file_reader.py`** - Unified Reading Interface
```python
class FileReader:
    """Unified interface for reading files.
    
    Automatically selects appropriate handler
    based on file extension.
    """
```

---

### Processing Module (`log_filter/processing/`)

**Purpose:** Parallel processing coordination

#### Components:

**`pipeline.py`** - Processing Orchestration
```python
class ProcessingPipeline:
    """Coordinates the entire processing workflow.
    
    Stages:
    1. File discovery
    2. Worker distribution
    3. Parallel processing
    4. Result aggregation
    5. Statistics collection
    """
```

**`processor.py`** - File Processing
```python
class FileProcessor:
    """Processes a single file.
    
    Responsibilities:
    - Open file with appropriate handler
    - Parse records
    - Apply filters
    - Buffer results
    """
```

**`worker.py`** - Thread Worker
```python
class Worker:
    """Worker thread for processing files.
    
    Features:
    - Processes files from queue
    - Isolated error handling
    - Per-worker statistics
    - Graceful shutdown
    """
```

**`record_parser.py`** - Log Parsing
```python
class RecordParser:
    """Parses raw log lines into LogRecord objects.
    
    Features:
    - Timestamp extraction
    - Multi-format support
    - Lazy parsing (parse on demand)
    """
```

---

### Configuration Module (`log_filter/config/`)

**Purpose:** Configuration management and validation

#### Components:

**`models.py`** - Configuration Data Models
```python
@dataclass
class SearchConfig:
    """Search expression configuration."""
    expression: str
    case_sensitive: bool = False

@dataclass
class FileConfig:
    """File scanning configuration."""
    search_root: Path
    include_patterns: List[str]
    exclude_patterns: List[str]

@dataclass
class ProcessingConfig:
    """Processing behavior configuration."""
    max_workers: int
    buffer_size: int
    chunk_size: int

@dataclass
class ApplicationConfig:
    """Complete application configuration."""
    search: SearchConfig
    files: FileConfig
    output: OutputConfig
    processing: ProcessingConfig
```

**`loader.py`** - Configuration Loading
```python
class ConfigLoader:
    """Loads configuration from files.
    
    Supports: YAML, JSON
    Features: Environment variable substitution
    """
```

**`validator.py`** - Configuration Validation
```python
class ConfigValidator:
    """Validates configuration completeness and correctness.
    
    Checks:
    - Required fields present
    - Valid paths
    - Reasonable values
    - Cross-field consistency
    """
```

---

### Statistics Module (`log_filter/statistics/`)

**Purpose:** Metrics collection and reporting

#### Components:

**`collector.py`** - Thread-Safe Collection
```python
class StatisticsCollector:
    """Thread-safe statistics collection.
    
    Metrics:
    - Files processed/matched
    - Records processed/matched
    - Processing time
    - Throughput
    - Error counts
    
    Thread-safety: Uses locks for atomic updates
    """
```

**`reporter.py`** - Report Generation
```python
class StatisticsReporter:
    """Formats statistics for display.
    
    Formats:
    - Console (pretty-printed tables)
    - JSON (for tools)
    - CSV (for analysis)
    """
```

**`performance.py`** - Performance Tracking
```python
class PerformanceTracker:
    """Tracks performance metrics per file and overall."""

class FilePerformance:
    """Per-file performance data."""
```

---

### Utilities Module (`log_filter/utils/`)

**Purpose:** Common utilities and helpers

#### Components:

**`logging.py`** - Structured Logging
```python
def setup_logging(level: str, format: str):
    """Configures application logging."""
```

**`progress.py`** - Progress Display
```python
class ProgressBar:
    """Thread-safe progress bar for CLI."""
```

**`highlighter.py`** - Text Highlighting
```python
class TextHighlighter:
    """Highlights matching terms in output."""
```

**`decorators.py`** - Reusable Decorators
```python
def timer(func):
    """Times function execution."""

def retry(attempts=3, delay=1):
    """Retries function on failure."""
```

---

## Design Patterns

### 1. Strategy Pattern

**Used In:** Filters, Matchers, File Handlers

```python
# Abstract strategy
class AbstractFilter(ABC):
    @abstractmethod
    def matches(self, record: LogRecord) -> bool:
        pass

# Concrete strategies
class DateFilter(AbstractFilter):
    def matches(self, record: LogRecord) -> bool:
        return self.start_date <= record.timestamp <= self.end_date

class ExpressionFilter(AbstractFilter):
    def matches(self, record: LogRecord) -> bool:
        return self.evaluator.evaluate(record.content)

# Client code
filters = [DateFilter(...), ExpressionFilter(...)]
for filter in filters:
    if filter.matches(record):
        # Process matching record
```

**Benefits:**
- New filters can be added without modifying existing code
- Filters are independently testable
- Runtime filter selection

### 2. Factory Pattern

**Used In:** File Handler Creation

```python
class FileHandlerFactory:
    """Creates appropriate handler based on file type."""
    
    _handlers = {
        '.log': PlainTextHandler,
        '.txt': PlainTextHandler,
        '.gz': GzipHandler,
        '.bz2': Bz2Handler,
    }
    
    @classmethod
    def create_handler(cls, file_path: Path) -> AbstractFileHandler:
        ext = file_path.suffix.lower()
        handler_class = cls._handlers.get(ext, PlainTextHandler)
        return handler_class(file_path)
    
    @classmethod
    def register_handler(cls, extension: str, handler_class: Type):
        """Register custom file handler."""
        cls._handlers[extension] = handler_class
```

**Benefits:**
- Centralized handler creation logic
- Easy to add new file formats
- Extensible by third-party code

### 3. Builder Pattern

**Used In:** Configuration Construction

```python
class ConfigBuilder:
    """Fluent API for building configuration."""
    
    def __init__(self):
        self._config = {}
    
    def with_expression(self, expr: str) -> 'ConfigBuilder':
        self._config['expression'] = expr
        return self
    
    def with_workers(self, count: int) -> 'ConfigBuilder':
        self._config['max_workers'] = count
        return self
    
    def build(self) -> ApplicationConfig:
        return ApplicationConfig(**self._config)

# Usage
config = (ConfigBuilder()
    .with_expression("ERROR OR CRITICAL")
    .with_workers(8)
    .build())
```

**Benefits:**
- Fluent, readable API
- Validation during construction
- Immutable result

### 4. Pipeline Pattern

**Used In:** Processing Workflow

```python
class ProcessingPipeline:
    """Chain of processing stages."""
    
    def __init__(self):
        self.stages = []
    
    def add_stage(self, stage: Callable):
        self.stages.append(stage)
        return self
    
    def run(self, input_data):
        result = input_data
        for stage in self.stages:
            result = stage(result)
        return result

# Setup pipeline
pipeline = (ProcessingPipeline()
    .add_stage(scan_files)
    .add_stage(filter_files)
    .add_stage(distribute_to_workers)
    .add_stage(process_files)
    .add_stage(aggregate_results))
```

**Benefits:**
- Clear separation of processing stages
- Easy to add/remove/reorder stages
- Testable stages

### 5. Observer Pattern

**Used In:** Statistics Collection

```python
class StatisticsCollector:
    """Observes processing events and collects metrics."""
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, event: str, data: dict):
        for observer in self._observers:
            observer.on_event(event, data)

# Usage
collector = StatisticsCollector()
collector.attach(ConsoleObserver())
collector.attach(PrometheusObserver())
collector.notify('file_processed', {'file': 'app.log', 'records': 1000})
```

**Benefits:**
- Decoupled statistics consumers
- Multiple observers can listen simultaneously
- Easy to add new monitoring integrations

### 6. Dependency Injection

**Used Throughout:** Constructor Injection

```python
class FileProcessor:
    """Processes files with injected dependencies."""
    
    def __init__(
        self,
        file_scanner: FileScanner,
        expression_evaluator: Evaluator,
        statistics_collector: StatisticsCollector,
        output_writer: BufferedLogWriter
    ):
        self.file_scanner = file_scanner
        self.evaluator = expression_evaluator
        self.stats = statistics_collector
        self.writer = output_writer
```

**Benefits:**
- Testable with mock dependencies
- Flexible component replacement
- Clear dependencies

---

## Concurrency Model

### Thread Pool Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Main Thread                        │
│  ┌──────────────┐  ┌────────────────┐              │
│  │ File Scanner │→│  Work Queue    │              │
│  └──────────────┘  └────────┬───────┘              │
└─────────────────────────────┼──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐  ┌─────▼───────┐  ┌───▼────────┐
    │   Worker 1     │  │  Worker 2   │  │  Worker N  │
    │  ┌──────────┐  │  │ ┌──────────┐│  │┌──────────┐│
    │  │ Process  │  │  │ │ Process  ││  ││ Process  ││
    │  │   File   │  │  │ │   File   ││  ││   File   ││
    │  └────┬─────┘  │  │ └────┬─────┘│  │└────┬─────┘│
    │       │        │  │      │      │  │     │      │
    │  ┌────▼─────┐  │  │ ┌────▼─────┐│  │┌────▼─────┐│
    │  │  Buffer  │  │  │ │  Buffer  ││  ││  Buffer  ││
    │  └────┬─────┘  │  │ └────┬─────┘│  │└────┬─────┘│
    └───────┼────────┘  └──────┼──────┘  └─────┼──────┘
            │                  │                │
            └──────────────────┼────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Output Writer      │
                    │   (Thread-Safe)      │
                    └──────────────────────┘
```

### Threading Strategy

**Worker Threads:**
- Fixed-size thread pool
- Each worker processes one file at a time
- Independent error handling per worker
- Graceful shutdown on SIGINT/SIGTERM

**Work Distribution:**
```python
# Thread-safe queue
work_queue = Queue()

# Main thread: Add files to queue
for file_path in discovered_files:
    work_queue.put(file_path)

# Worker threads: Process files
def worker_loop():
    while True:
        try:
            file_path = work_queue.get(timeout=1.0)
            process_file(file_path)
            work_queue.task_done()
        except Empty:
            break  # No more work
```

### Synchronization Mechanisms

**1. Thread-Safe Queue (Work Distribution)**
```python
from queue import Queue

work_queue = Queue(maxsize=100)  # Bounded queue
```
- Lock-free for most operations
- Bounded to prevent memory issues
- Automatic blocking when full/empty

**2. Locks (Statistics Collection)**
```python
class StatisticsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._stats = {}
    
    def increment(self, metric: str):
        with self._lock:  # Atomic update
            self._stats[metric] = self._stats.get(metric, 0) + 1
```
- Fine-grained locking (per-metric vs global)
- Short critical sections
- No nested locks (avoid deadlocks)

**3. Thread-Local Storage (Per-Worker Data)**
```python
import threading

thread_local = threading.local()

def worker_func():
    # Each thread has its own buffer
    thread_local.buffer = []
    thread_local.stats = {}
```
- No synchronization needed
- Better cache locality
- Aggregate at end

### Lock-Free Design Principles

**1. Immutable Data Structures**
```python
@dataclass(frozen=True)
class LogRecord:
    """Immutable record - safe to share between threads."""
    content: str
    timestamp: datetime
```

**2. Message Passing (vs Shared State)**
```python
# Workers send results via queue instead of shared list
result_queue = Queue()

def worker():
    matches = process_file(file)
    result_queue.put(matches)  # Thread-safe

def collector():
    all_matches = []
    while not done:
        matches = result_queue.get()
        all_matches.extend(matches)
```

**3. Per-Worker Buffers**
```python
class Worker:
    def __init__(self):
        self.local_buffer = []  # No locking needed
    
    def process_record(self, record):
        if matches(record):
            self.local_buffer.append(record)
        
        # Flush when full
        if len(self.local_buffer) >= BUFFER_SIZE:
            self.flush()  # Only locks during flush
```

### Performance Optimizations

**1. Reduce Lock Contention**
- Minimize critical section size
- Use lock-free structures where possible
- Batch operations before locking

**2. Avoid False Sharing**
```python
# Bad: Workers update adjacent array elements (same cache line)
shared_array = [0] * num_workers

# Good: Each worker has own object (separate cache lines)
worker_stats = [WorkerStats() for _ in range(num_workers)]
```

**3. Thread Pool Sizing**
```python
def optimal_worker_count(workload_type: str) -> int:
    cpu_count = os.cpu_count()
    
    if workload_type == 'cpu_bound':
        return cpu_count
    elif workload_type == 'io_bound':
        return cpu_count * 2
    else:
        return int(cpu_count * 1.5)
```

---

## Data Flow

### Complete Processing Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT PHASE                                                  │
│                                                                 │
│ CLI Args ──→ Arg Parser ──→ Config Loader ──→ Config Validator │
│                                  ↓                               │
│                          Application Config                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│ 2. DISCOVERY PHASE                                              │
│                                                                 │
│ Search Root ──→ File Scanner ──→ Apply Filters ──→ File List   │
│                      ↓                  ↓                        │
│                 Recursive          Include/Exclude              │
│                  Traverse           Patterns                    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│ 3. EXPRESSION PARSING                                           │
│                                                                 │
│ Expression ──→ Tokenizer ──→ Parser ──→ AST                    │
│   String          ↓             ↓          ↓                    │
│               Tokens        Syntax      Compiled                │
│                            Analysis    Expression               │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│ 4. DISTRIBUTION PHASE                                           │
│                                                                 │
│ File List ──→ Work Queue ──→ Worker Pool                       │
│                    ↓              ↓                              │
│             Thread-Safe      N Workers                          │
│                Queue        (Parallel)                          │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│ 5. PROCESSING PHASE (Per Worker)                               │
│                                                                 │
│ File ──→ Handler ──→ Line Stream ──→ Record Parser             │
│           ↓             ↓                  ↓                    │
│      Decompress    Read Lines        Parse Record              │
│      (if .gz)      (Streaming)                                  │
│                                            ↓                    │
│                    Apply Filters (Date, Time, Expression)      │
│                                            ↓                    │
│                           Match? ───────── Yes ──→ Buffer       │
│                             │                        ↓          │
│                            No                   Full?           │
│                             │                        │          │
│                          Skip                   Yes ↓ No        │
│                                              Flush   │          │
│                                                ↓   Continue     │
│                                          Writer ←───┘           │
└─────────────────────────────────────────────┬───────────────────┘
                                              │
┌─────────────────────────────────────────────▼───────────────────┐
│ 6. OUTPUT PHASE                                                 │
│                                                                 │
│ Worker Buffers ──→ File Writer ──→ Output File                 │
│       ↓                ↓                                         │
│  Thread-Safe     Buffered I/O                                  │
│   Merging        Auto Flush                                    │
└─────────────────────────────────────────────┬───────────────────┘
                                              │
┌─────────────────────────────────────────────▼───────────────────┐
│ 7. STATISTICS PHASE                                             │
│                                                                 │
│ Worker Stats ──→ Collector ──→ Reporter ──→ Console/File       │
│      ↓               ↓             ↓                             │
│  Per-Worker    Thread-Safe     Format                          │
│   Metrics      Aggregation    (Table/JSON)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Structures

**1. LogRecord**
```python
@dataclass(frozen=True)
class LogRecord:
    content: str           # Raw log line
    timestamp: Optional[datetime]  # Parsed timestamp
    line_number: int       # Line number in file
    file_path: Path        # Source file
    
    # Memory: ~200 bytes per record
    # Immutable: Thread-safe
```

**2. Work Queue**
```python
work_queue: Queue[Path]  # File paths to process
# Capacity: 100 files
# Thread-safe: Built-in locking
```

**3. Result Buffer**
```python
class ResultBuffer:
    def __init__(self, capacity: int = 1000):
        self.buffer: List[str] = []
        self.capacity = capacity
    
    def add(self, line: str):
        self.buffer.append(line)
        if len(self.buffer) >= self.capacity:
            self.flush()
```

**4. Statistics**
```python
@dataclass
class ProcessingStatistics:
    files_processed: int = 0
    files_matched: int = 0
    total_records: int = 0
    matched_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
```

## Error Handling

### Exception Hierarchy

```python
LogFilterException
├── ParseException
│   ├── TokenizationError
│   ├── SyntaxError
│   └── InvalidExpressionError
├── ConfigurationException
│   ├── MissingConfigError
│   ├── InvalidConfigError
│   └── ValidationError
├── FileProcessingException
│   ├── FileNotFoundError
│   ├── PermissionError
│   └── DecompressionError
└── EvaluationException
    ├── MatchingError
    └── FilterError
```

### Error Isolation Strategy

**Per-File Isolation:**
```python
def process_file(file_path: Path):
    try:
        # Process file
        with open(file_path) as f:
            for line in f:
                process_line(line)
    except Exception as e:
        # Log error but continue with other files
        logger.error(f"Failed to process {file_path}: {e}")
        stats.record_error(file_path, str(e))
        return  # Skip this file, continue with others
```

**Graceful Degradation:**
- Single file error doesn't stop entire process
- Worker thread failures are caught and logged
- Partial results are still written
- Statistics track all errors

---

## Extension Points

### 1. Custom File Handlers

Add support for new file formats:

```python
from log_filter.infrastructure.file_handlers import AbstractFileHandler

class CustomFormatHandler(AbstractFileHandler):
    """Handler for custom log format."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
    
    def read_lines(self) -> Generator[str, None, None]:
        """Stream lines from custom format."""
        # Your parsing logic here
        with open(self.file_path, 'rb') as f:
            for line in self.custom_parse(f):
                yield line

# Register handler
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
FileHandlerFactory.register_handler('.custom', CustomFormatHandler)
```

### 2. Custom Filters via `FilterStrategy`

Add domain-specific filtering:

```python
from log_filter.domain.filters import AbstractFilter

class SeverityFilter(AbstractFilter):
    """Filter by log severity level."""
    
    def matches(self, record: LogRecord) -> bool:
        # Your filtering logic
        pass
```

### 3. Custom Matchers via `MatchStrategy`

Add specialized matching logic:

```python
from log_filter.domain.matchers import AbstractMatcher

class IPAddressMatcher(AbstractMatcher):
    """Matches IP address patterns."""
    
    def matches(self, text: str) -> bool:
        # Your matching logic
        pass
```

### 4. Pipeline Stages via Composition

Add custom processing stages:

```python
class CustomStage:
    """Custom pipeline stage."""
    
    def process(self, records: Iterator[LogRecord]) -> Iterator[LogRecord]:
        for record in records:
            yield self.transform(record)
```

---

## Performance Architecture

### Performance Characteristics

**Baseline Metrics:**
- **Throughput**: 200,000+ records/second (8-core system)
- **Latency**: ~5 μs per record
- **Memory**: 50-100 MB base + 10 MB per worker
- **Scalability**: Linear up to CPU core count

### Key Performance Optimizations

**1. Streaming Record Parsing**
- No full file accumulation in memory
- Constant memory usage regardless of file size
- Can process GB+ files on limited RAM

**2. Compiled Regex Caching**
- Regex compilation is expensive (~100 μs)
- Cache hit: ~0.1 μs (1000x speedup)
- Shared across all workers

**3. Buffered I/O Operations**
- Reduces system calls
- Better disk I/O patterns
- 10-20x throughput improvement

**4. Lazy Evaluation**
- Short-circuit evaluation where possible
- Avoid unnecessary work
- Faster with common patterns

**5. Parallel Processing with Optimal Worker Count**
- Linear scaling up to CPU cores
- Auto-detection of CPU count
- Configurable for different workloads

---

## Deployment Architectures

### 1. Standalone CLI
```
User Machine → log-filter CLI → Local Logs
```
**Use Cases:** Local development, ad-hoc analysis

### 2. Docker Container
```
Docker Container → Mounted Volumes → Logs
```
**Use Cases:** CI/CD pipelines, reproducible environments

### 3. Kubernetes CronJob
```
K8s CronJob → Pod → PersistentVolumes
```
**Use Cases:** Scheduled processing, production deployment

### 4. Distributed Processing
```
Orchestrator → Multiple Workers → Aggregation
```
**Use Cases:** Large-scale processing, multi-TB logs

---

## Related Documentation

- **[Performance Tuning Guide](performance.md)** - Optimization strategies
- **[API Reference](api/index.rst)** - Complete API documentation
- **[Advanced Usage](advanced_usage.md)** - Production patterns
- **[Integration Guide](integration_guide.md)** - System integration
- **[Deployment Guide](deployment.md)** - Deployment patterns

---

**Document Version:** 2.0  
**Last Updated:** January 8, 2026  
**Maintainer:** Development Team
