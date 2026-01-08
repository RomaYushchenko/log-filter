# Error Handling Guide

**Last Updated:** January 8, 2026  
**Version:** 2.0.0  
**Target Audience:** Developers, System Administrators, DevOps Engineers

---

## Table of Contents

- [Exception Hierarchy](#exception-hierarchy)
- [Common Error Scenarios](#common-error-scenarios)
- [Error Recovery Strategies](#error-recovery-strategies)
- [Debugging Guide](#debugging-guide)
- [Error Logging](#error-logging)
- [Handling Errors in Production](#handling-errors-in-production)
- [Error Codes Reference](#error-codes-reference)

---

## Exception Hierarchy

### Core Exception Classes

```
BaseException
└── Exception
    └── LogFilterError (Base for all log-filter exceptions)
        ├── ExpressionError (Expression parsing/evaluation errors)
        │   ├── ParseError
        │   ├── TokenizationError
        │   └── EvaluationError
        ├── FileHandlingError (File I/O errors)
        │   ├── FileNotFoundError
        │   ├── PermissionError
        │   ├── EncodingError
        │   └── CompressionError
        ├── ConfigurationError (Configuration errors)
        │   ├── InvalidConfigError
        │   ├── MissingConfigError
        │   └── ValidationError
        └── ProcessingError (Processing pipeline errors)
            ├── WorkerError
            ├── TimeoutError
            └── ResourceError
```

### Exception Descriptions

#### LogFilterError

Base exception for all log-filter specific errors.

```python
from log_filter.core.exceptions import LogFilterError

try:
    # Your code here
    pass
except LogFilterError as e:
    print(f"Log Filter error: {e}")
```

#### ExpressionError

Raised when expression parsing or evaluation fails.

```python
from log_filter.core.exceptions import ExpressionError, ParseError
from log_filter.core.parser import parse

try:
    ast = parse("ERROR AND (")  # Unclosed parenthesis
except ParseError as e:
    print(f"Parse error: {e}")
    print(f"Position: {e.position}")
    print(f"Token: {e.token}")
```

**Common causes:**
- Unclosed parentheses: `ERROR AND (`
- Invalid operators: `ERROR && OR WARNING`
- Empty expressions: ``
- Invalid syntax: `AND ERROR`

#### FileHandlingError

Raised when file operations fail.

```python
from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory

try:
    factory = FileHandlerFactory()
    handler = factory.get_handler(Path("/nonexistent/file.log"))
    lines = list(handler.read_lines(Path("/nonexistent/file.log")))
except FileHandlingError as e:
    print(f"File error: {e}")
    print(f"File path: {e.file_path}")
    print(f"Error code: {e.error_code}")
```

**Common causes:**
- File not found
- Permission denied
- Corrupted compressed files
- Unsupported file format
- Disk read errors

#### ConfigurationError

Raised when configuration is invalid or missing.

```python
from log_filter.core.exceptions import ConfigurationError
from log_filter.config.loader import load_config

try:
    config = load_config(Path("config.yaml"))
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Config key: {e.config_key}")
    print(f"Expected type: {e.expected_type}")
```

**Common causes:**
- Missing required fields
- Invalid field types
- Invalid file paths
- Invalid worker count
- Invalid buffer size

#### ProcessingError

Raised during pipeline processing.

```python
from log_filter.core.exceptions import ProcessingError
from log_filter.processing.pipeline import ProcessingPipeline

try:
    pipeline = ProcessingPipeline(config)
    result = pipeline.run()
except ProcessingError as e:
    print(f"Processing error: {e}")
    print(f"Worker ID: {e.worker_id}")
    print(f"File: {e.file_path}")
```

**Common causes:**
- Worker thread crashes
- Resource exhaustion (memory, disk)
- Processing timeouts
- Data corruption

---

## Common Error Scenarios

### Scenario 1: File Not Found

**Error Message:**
```
FileHandlingError: File not found: /var/log/app.log
```

**Cause:** The specified file or directory doesn't exist.

**Solution:**

1. **Verify file path exists:**
   ```bash
   ls -la /var/log/app.log
   ```

2. **Check configuration:**
   ```yaml
   files:
     search_root: /var/log  # Verify this path exists
     include_patterns:
       - "app.log"
   ```

3. **Use wildcards for flexibility:**
   ```yaml
   files:
     search_root: /var/log
     include_patterns:
       - "app*.log"  # Matches app.log, app-2026.log, etc.
   ```

4. **Handle missing files gracefully:**
   ```python
   from log_filter.infrastructure.file_scanner import FileScanner
   from pathlib import Path
   
   scanner = FileScanner(search_root=Path("/var/log"))
   files = scanner.scan()
   
   if not files:
       print("No files found")
       exit(0)
   
   # Process files
   ```

### Scenario 2: Permission Denied

**Error Message:**
```
FileHandlingError: Permission denied: /var/log/secure.log
```

**Cause:** Insufficient permissions to read the file.

**Solution:**

1. **Check file permissions:**
   ```bash
   ls -l /var/log/secure.log
   # -rw------- 1 root root 1234 Jan 8 10:00 /var/log/secure.log
   ```

2. **Run with appropriate permissions:**
   ```bash
   # Option 1: Use sudo (not recommended for production)
   sudo log-filter --config config.yaml
   
   # Option 2: Add user to appropriate group
   sudo usermod -a -G adm username
   
   # Option 3: Adjust file permissions
   sudo chmod 644 /var/log/secure.log
   ```

3. **Skip permission-denied files:**
   ```python
   from log_filter.core.exceptions import FileHandlingError
   from pathlib import Path
   
   for file_path in files:
       try:
           process_file(file_path)
       except FileHandlingError as e:
           if "permission denied" in str(e).lower():
               print(f"Skipping {file_path}: permission denied")
               continue
           raise
   ```

### Scenario 3: Encoding Errors

**Error Message:**
```
FileHandlingError: Encoding error in file: /var/log/app.log
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff
```

**Cause:** File contains characters that can't be decoded with the specified encoding.

**Solution:**

1. **Use error handling mode:**
   ```yaml
   files:
     encoding: "utf-8"
     errors: "replace"  # Replace invalid characters with �
   ```

2. **Try different encodings:**
   ```python
   from log_filter.infrastructure.file_handlers import LogFileHandler
   
   encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
   
   for encoding in encodings:
       try:
           handler = LogFileHandler(encoding=encoding, errors='strict')
           lines = list(handler.read_lines(file_path))
           print(f"Success with {encoding}")
           break
       except UnicodeDecodeError:
           continue
   ```

3. **Use 'ignore' to skip invalid characters:**
   ```python
   handler = LogFileHandler(encoding='utf-8', errors='ignore')
   ```

4. **Use 'replace' to substitute invalid characters:**
   ```python
   handler = LogFileHandler(encoding='utf-8', errors='replace')
   ```

### Scenario 4: Corrupted Compressed Files

**Error Message:**
```
FileHandlingError: Compression error: gzip file is corrupt
```

**Cause:** Gzip file is incomplete or corrupted.

**Solution:**

1. **Verify file integrity:**
   ```bash
   gzip -t app.log.gz
   # If corrupt: "gzip: app.log.gz: invalid compressed data--format violated"
   ```

2. **Skip corrupted files:**
   ```python
   from log_filter.core.exceptions import FileHandlingError
   
   for file_path in files:
       try:
           handler = factory.get_handler(file_path)
           lines = handler.read_lines(file_path)
       except FileHandlingError as e:
           if "corrupt" in str(e).lower():
               print(f"Skipping corrupted file: {file_path}")
               continue
           raise
   ```

3. **Recover partial data (advanced):**
   ```python
   import gzip
   
   def read_partial_gzip(file_path):
       """Read as much as possible from corrupted gzip."""
       with gzip.open(file_path, 'rt', errors='replace') as f:
           while True:
               try:
                   line = f.readline()
                   if not line:
                       break
                   yield line
               except Exception:
                   # Stop at corruption point
                   break
   ```

### Scenario 5: Expression Parsing Errors

**Error Message:**
```
ParseError: Unexpected token 'AND' at position 0
Expected identifier or opening parenthesis
```

**Cause:** Invalid boolean expression syntax.

**Solution:**

1. **Common syntax errors:**
   ```python
   # ❌ Wrong: Operator at start
   "AND ERROR"
   
   # ✅ Correct
   "ERROR AND WARNING"
   
   # ❌ Wrong: Unclosed parenthesis
   "ERROR AND (WARNING OR"
   
   # ✅ Correct
   "ERROR AND (WARNING OR CRITICAL)"
   
   # ❌ Wrong: Double operators
   "ERROR AND AND WARNING"
   
   # ✅ Correct
   "ERROR AND WARNING"
   ```

2. **Validate expressions before processing:**
   ```python
   from log_filter.core.parser import parse
   from log_filter.core.exceptions import ParseError
   
   def validate_expression(expr: str) -> bool:
       """Validate expression syntax."""
       try:
           ast = parse(expr)
           return True
       except ParseError as e:
           print(f"Invalid expression: {e}")
           return False
   
   # Validate user input
   expr = input("Enter expression: ")
   if validate_expression(expr):
       # Process logs
       pass
   ```

3. **Provide helpful error messages:**
   ```python
   try:
       ast = parse(expression)
   except ParseError as e:
       print(f"Expression syntax error:")
       print(f"  Expression: {expression}")
       print(f"  Position:   {' ' * e.position}^")
       print(f"  Error:      {e}")
       print(f"\nValid syntax:")
       print(f"  - Use AND, OR, NOT operators")
       print(f"  - Use parentheses for grouping")
       print(f"  - Example: (ERROR OR WARNING) AND database")
   ```

### Scenario 6: Out of Memory

**Error Message:**
```
ProcessingError: Resource exhausted: Out of memory
MemoryError: Unable to allocate array
```

**Cause:** Too many workers or large files consuming all available memory.

**Solution:**

1. **Reduce worker count:**
   ```yaml
   processing:
     max_workers: 2  # Reduce from 8 to 2
   ```

2. **Reduce buffer size:**
   ```yaml
   processing:
     buffer_size: 4096  # Reduce from 32768
   ```

3. **Process files sequentially:**
   ```python
   config = ProcessingConfig(
       max_workers=1,  # Sequential processing
       buffer_size=4096
   )
   ```

4. **Monitor memory usage:**
   ```python
   import psutil
   
   def check_memory():
       """Check available memory."""
       mem = psutil.virtual_memory()
       if mem.percent > 90:
           print(f"WARNING: High memory usage: {mem.percent}%")
           return False
       return True
   
   # Before processing
   if not check_memory():
       print("Insufficient memory, reducing workers")
       config.processing.max_workers = 1
   ```

5. **Process in batches:**
   ```python
   from log_filter.infrastructure.file_scanner import FileScanner
   
   scanner = FileScanner(search_root=Path("/var/log"))
   all_files = scanner.scan()
   
   # Process in batches of 10 files
   batch_size = 10
   for i in range(0, len(all_files), batch_size):
       batch = all_files[i:i+batch_size]
       process_batch(batch)
       
       # Force garbage collection
       import gc
       gc.collect()
   ```

### Scenario 7: Disk Full

**Error Message:**
```
FileHandlingError: No space left on device
```

**Cause:** Output disk is full.

**Solution:**

1. **Check disk space before processing:**
   ```python
   import shutil
   
   def check_disk_space(path: Path, required_gb: float = 1.0) -> bool:
       """Check if sufficient disk space is available."""
       stat = shutil.disk_usage(path)
       free_gb = stat.free / (1024**3)
       
       if free_gb < required_gb:
           print(f"Insufficient disk space: {free_gb:.2f} GB available")
           return False
       return True
   
   if not check_disk_space(output_dir, required_gb=5.0):
       print("ERROR: Need at least 5 GB free space")
       exit(1)
   ```

2. **Write to different location:**
   ```yaml
   output:
     output_file: /mnt/large-disk/filtered.txt
   ```

3. **Compress output:**
   ```python
   import gzip
   
   # Write compressed output
   output_file = Path("filtered.txt.gz")
   with gzip.open(output_file, 'wt') as f:
       for match in matches:
           f.write(match + '\n')
   ```

4. **Stream to stdout instead:**
   ```bash
   log-filter --config config.yaml --output - | gzip > filtered.txt.gz
   ```

---

## Error Recovery Strategies

### Graceful Degradation

```python
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.core.exceptions import FileHandlingError, ProcessingError

class ResilientPipeline:
    """Pipeline with error recovery."""
    
    def __init__(self, config):
        self.config = config
        self.pipeline = ProcessingPipeline(config)
        self.failed_files = []
        self.skipped_files = []
    
    def process_with_recovery(self):
        """Process files with error recovery."""
        files = self.scan_files()
        
        for file_path in files:
            try:
                self.process_single_file(file_path)
            except FileHandlingError as e:
                self.handle_file_error(file_path, e)
            except ProcessingError as e:
                self.handle_processing_error(file_path, e)
            except Exception as e:
                self.handle_unexpected_error(file_path, e)
    
    def handle_file_error(self, file_path, error):
        """Handle file-related errors."""
        if "permission denied" in str(error).lower():
            print(f"SKIP: {file_path} - permission denied")
            self.skipped_files.append(file_path)
        elif "not found" in str(error).lower():
            print(f"SKIP: {file_path} - not found")
            self.skipped_files.append(file_path)
        else:
            print(f"FAIL: {file_path} - {error}")
            self.failed_files.append((file_path, error))
    
    def handle_processing_error(self, file_path, error):
        """Handle processing errors."""
        print(f"FAIL: {file_path} - processing error: {error}")
        self.failed_files.append((file_path, error))
    
    def handle_unexpected_error(self, file_path, error):
        """Handle unexpected errors."""
        print(f"ERROR: {file_path} - unexpected: {error}")
        self.failed_files.append((file_path, error))
        
        # Continue processing despite unexpected errors
    
    def report_results(self):
        """Report processing results."""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Skipped files: {len(self.skipped_files)}")
        print(f"Failed files:  {len(self.failed_files)}")
        
        if self.failed_files:
            print("\nFailed files:")
            for file_path, error in self.failed_files:
                print(f"  - {file_path}: {error}")

# Usage
pipeline = ResilientPipeline(config)
pipeline.process_with_recovery()
pipeline.report_results()
```

### Retry Logic

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1.0, backoff=2.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    
                    print(f"Attempt {attempt} failed: {e}")
                    print(f"Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    
                    attempt += 1
                    current_delay *= backoff
        
        return wrapper
    return decorator

# Usage
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def process_file(file_path):
    """Process file with retry logic."""
    handler = factory.get_handler(file_path)
    return list(handler.read_lines(file_path))

# Will retry up to 3 times with exponential backoff
try:
    lines = process_file(Path("app.log"))
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Checkpoint and Resume

```python
import pickle
from pathlib import Path

class CheckpointManager:
    """Manage processing checkpoints."""
    
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.processed_files = self.load_checkpoint()
    
    def load_checkpoint(self) -> set:
        """Load checkpoint from file."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'rb') as f:
                return pickle.load(f)
        return set()
    
    def save_checkpoint(self):
        """Save checkpoint to file."""
        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(self.processed_files, f)
    
    def is_processed(self, file_path: Path) -> bool:
        """Check if file was already processed."""
        return str(file_path) in self.processed_files
    
    def mark_processed(self, file_path: Path):
        """Mark file as processed."""
        self.processed_files.add(str(file_path))
        self.save_checkpoint()

# Usage
checkpoint = CheckpointManager(Path("checkpoint.pkl"))

for file_path in files:
    if checkpoint.is_processed(file_path):
        print(f"SKIP: {file_path} - already processed")
        continue
    
    try:
        process_file(file_path)
        checkpoint.mark_processed(file_path)
    except Exception as e:
        print(f"ERROR: {file_path} - {e}")
        # Don't mark as processed so it will be retried
```

---

## Debugging Guide

### Enable Debug Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log-filter-debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug mode
config.logging.level = "DEBUG"

# Run pipeline
pipeline = ProcessingPipeline(config)
result = pipeline.run()
```

### Debug Expression Evaluation

```python
from log_filter.core.parser import parse
from log_filter.core.evaluator import Evaluator
from log_filter.core.tokenizer import Tokenizer

def debug_expression(expression: str, test_text: str):
    """Debug expression evaluation."""
    print(f"Expression: {expression}")
    print(f"Test text: {test_text}")
    print()
    
    # Tokenize
    print("1. Tokenization:")
    tokenizer = Tokenizer(expression)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(f"   {token}")
    print()
    
    # Parse
    print("2. Parsing:")
    ast = parse(expression)
    print(f"   AST: {ast}")
    print()
    
    # Evaluate
    print("3. Evaluation:")
    evaluator = Evaluator(ast, case_sensitive=False)
    result = evaluator.evaluate(test_text)
    print(f"   Result: {result}")
    print()

# Test
debug_expression(
    expression="(ERROR OR WARNING) AND database",
    test_text="2026-01-08 ERROR database connection failed"
)
```

### Profile Performance

```python
import cProfile
import pstats
from log_filter.processing.pipeline import ProcessingPipeline

def profile_pipeline():
    """Profile pipeline performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run pipeline
    pipeline = ProcessingPipeline(config)
    result = pipeline.run()
    
    profiler.disable()
    
    # Print statistics
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

profile_pipeline()
```

### Trace File Processing

```python
import sys

class ProcessingTracer:
    """Trace file processing steps."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def trace_file_start(self, file_path):
        """Trace file processing start."""
        if self.verbose:
            print(f">>> Processing: {file_path}")
    
    def trace_file_progress(self, file_path, records_processed):
        """Trace file processing progress."""
        if self.verbose and records_processed % 1000 == 0:
            print(f"    {file_path}: {records_processed} records")
    
    def trace_file_complete(self, file_path, records, matches, time_taken):
        """Trace file processing completion."""
        if self.verbose:
            print(f"<<< Completed: {file_path}")
            print(f"    Records: {records}, Matches: {matches}, Time: {time_taken:.2f}s")
    
    def trace_error(self, file_path, error):
        """Trace error."""
        print(f"!!! Error in {file_path}: {error}", file=sys.stderr)

# Usage
tracer = ProcessingTracer(verbose=True)

for file_path in files:
    tracer.trace_file_start(file_path)
    
    try:
        # Process file
        tracer.trace_file_complete(file_path, 1000, 50, 1.2)
    except Exception as e:
        tracer.trace_error(file_path, e)
```

---

## Error Logging

### Structured Error Logging

```python
import logging
import json
from datetime import datetime

class StructuredErrorLogger:
    """Log errors in structured format."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.logger = logging.getLogger('log_filter_errors')
        self.logger.setLevel(logging.ERROR)
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
    
    def log_error(self, error_type: str, file_path: Path, error: Exception, context: dict = None):
        """Log error in structured format."""
        error_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'file_path': str(file_path),
            'error_message': str(error),
            'error_class': error.__class__.__name__,
            'context': context or {}
        }
        
        self.logger.error(json.dumps(error_record))
    
    def get_error_statistics(self) -> dict:
        """Get error statistics from log."""
        errors = []
        with open(self.log_file) as f:
            for line in f:
                errors.append(json.loads(line))
        
        stats = {
            'total_errors': len(errors),
            'by_type': {},
            'by_file': {}
        }
        
        for error in errors:
            error_type = error['error_type']
            file_path = error['file_path']
            
            stats['by_type'][error_type] = stats['by_type'].get(error_type, 0) + 1
            stats['by_file'][file_path] = stats['by_file'].get(file_path, 0) + 1
        
        return stats

# Usage
error_logger = StructuredErrorLogger(Path("errors.jsonl"))

try:
    process_file(file_path)
except FileHandlingError as e:
    error_logger.log_error(
        error_type='file_handling',
        file_path=file_path,
        error=e,
        context={'encoding': 'utf-8'}
    )

# Get statistics
stats = error_logger.get_error_statistics()
print(f"Total errors: {stats['total_errors']}")
```

---

## Handling Errors in Production

### Production Error Handler

```python
class ProductionErrorHandler:
    """Production-grade error handling."""
    
    def __init__(self, config, alert_threshold=10):
        self.config = config
        self.alert_threshold = alert_threshold
        self.error_count = 0
        self.critical_errors = []
    
    def handle_error(self, error: Exception, context: str):
        """Handle error in production."""
        self.error_count += 1
        
        # Log error
        logging.error(f"{context}: {error}", exc_info=True)
        
        # Check if critical
        if self.is_critical(error):
            self.critical_errors.append((context, error))
            self.send_alert(error, context)
        
        # Check threshold
        if self.error_count >= self.alert_threshold:
            self.send_threshold_alert()
    
    def is_critical(self, error: Exception) -> bool:
        """Determine if error is critical."""
        critical_types = (
            MemoryError,
            KeyboardInterrupt,
            SystemExit
        )
        return isinstance(error, critical_types)
    
    def send_alert(self, error: Exception, context: str):
        """Send alert for critical error."""
        # Send to monitoring system
        alert_data = {
            'severity': 'critical',
            'message': f"Critical error in {context}",
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to Slack, PagerDuty, etc.
        self.notify_team(alert_data)
    
    def send_threshold_alert(self):
        """Send alert when error threshold exceeded."""
        alert_data = {
            'severity': 'warning',
            'message': f"Error threshold exceeded: {self.error_count} errors",
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.notify_team(alert_data)
    
    def notify_team(self, alert_data: dict):
        """Notify team of issue."""
        # Implementation depends on your notification system
        pass
```

---

## Error Codes Reference

| Code | Name | Description | Recovery |
|------|------|-------------|----------|
| E001 | ParseError | Expression syntax error | Fix expression syntax |
| E002 | TokenizationError | Invalid tokens in expression | Check expression characters |
| E003 | EvaluationError | Error evaluating expression | Simplify expression |
| E101 | FileNotFoundError | File or directory not found | Verify path exists |
| E102 | PermissionError | Insufficient file permissions | Check permissions |
| E103 | EncodingError | File encoding error | Use error='replace' |
| E104 | CompressionError | Corrupted compressed file | Skip or repair file |
| E201 | InvalidConfigError | Configuration validation failed | Fix configuration |
| E202 | MissingConfigError | Required config missing | Add required fields |
| E301 | WorkerError | Worker thread crashed | Reduce workers |
| E302 | TimeoutError | Processing timeout | Increase timeout |
| E303 | ResourceError | Resource exhausted | Free resources |

---

## Summary

This guide covered:

✅ **Exception hierarchy** - Understanding all error types  
✅ **Common scenarios** - Solutions for frequent errors  
✅ **Recovery strategies** - Graceful error handling  
✅ **Debugging** - Tools and techniques for troubleshooting  
✅ **Error logging** - Structured logging for production  
✅ **Production handling** - Enterprise error management  
✅ **Error codes** - Complete reference

### Next Steps

- [Advanced Usage Guide](advanced_usage.md) - Optimize performance
- [Integration Guide](integration_guide.md) - Integrate with other systems
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

---

**Document Version:** 1.0  
**Last Review:** January 8, 2026
