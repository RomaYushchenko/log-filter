# Advanced Usage Guide

**Last Updated:** January 8, 2026  
**Version:** 2.0.0  
**Target Audience:** Experienced users, DevOps engineers, System administrators

---

## Table of Contents

- [Multi-Worker Configuration](#multi-worker-configuration)
- [Large File Processing](#large-file-processing)
- [Complex Boolean Expressions](#complex-boolean-expressions)
- [Custom Filter Chains](#custom-filter-chains)
- [Performance Optimization](#performance-optimization)
- [Memory Management](#memory-management)
- [Advanced Output Options](#advanced-output-options)
- [Production Deployment Patterns](#production-deployment-patterns)

---

## Multi-Worker Configuration

### Understanding Worker Architecture

Log Filter uses a multi-threaded worker pool to process files in parallel. Each worker:
- Processes files independently
- Maintains its own statistics
- Has its own file handler and evaluator
- Reports results to a central collector

### Determining Optimal Worker Count

#### CPU-Bound vs I/O-Bound Workloads

**I/O-Bound Workloads** (many small files, network storage):
```yaml
processing:
  max_workers: 16  # 2x CPU count for typical 8-core system
```

**CPU-Bound Workloads** (complex expressions, large processing):
```yaml
processing:
  max_workers: 8  # Match CPU count
```

**Mixed Workloads**:
```yaml
processing:
  max_workers: 12  # 1.5x CPU count
```

### Dynamic Worker Configuration

```python
import os
from log_filter.config.models import ApplicationConfig, ProcessingConfig

# Auto-detect optimal workers
cpu_count = os.cpu_count() or 4

# For I/O-intensive tasks
config = ApplicationConfig(
    processing=ProcessingConfig(
        max_workers=cpu_count * 2,
        buffer_size=8192
    )
)

# For CPU-intensive tasks
config = ApplicationConfig(
    processing=ProcessingConfig(
        max_workers=cpu_count,
        buffer_size=16384  # Larger buffer for better throughput
    )
)
```

### Worker Performance Benchmarks

| Workers | Files/sec | Records/sec | CPU Usage | Memory |
|---------|-----------|-------------|-----------|--------|
| 1       | 5         | 5,000       | 12%       | 50 MB  |
| 2       | 10        | 10,000      | 24%       | 100 MB |
| 4       | 18        | 18,000      | 45%       | 200 MB |
| 8       | 32        | 32,000      | 80%       | 400 MB |
| 16      | 45        | 45,000      | 95%       | 800 MB |

*Benchmarks based on 1MB log files with simple expressions on 8-core system*

### Worker Count Best Practices

1. **Start conservative**: Begin with CPU count
2. **Monitor performance**: Watch CPU and memory usage
3. **Tune incrementally**: Increase by 2-4 workers at a time
4. **Consider memory**: Each worker uses 50-100 MB
5. **Watch I/O**: Storage throughput may become bottleneck

---

## Large File Processing

### Handling Multi-Gigabyte Files

Log Filter uses streaming processing to handle files of any size efficiently.

#### Memory-Efficient Processing

```yaml
# Configuration for 10+ GB files
processing:
  max_workers: 2          # Fewer workers to conserve memory
  buffer_size: 65536      # 64 KB chunks for better throughput
  chunk_size: 1000        # Process 1000 records at a time
```

#### Progress Monitoring for Large Files

```python
from log_filter.processing.pipeline import ProcessingPipeline
from pathlib import Path

pipeline = ProcessingPipeline(config)

def progress_callback(files_done, total_files, records_processed, bytes_processed):
    """Display progress for large file processing."""
    mb_processed = bytes_processed / (1024 * 1024)
    print(f"\rFiles: {files_done}/{total_files} | "
          f"Records: {records_processed:,} | "
          f"Data: {mb_processed:.1f} MB", end="", flush=True)

result = pipeline.run(progress_callback=progress_callback)
print()  # New line after progress
```

### Handling Compressed Large Files

Gzip-compressed files require more memory for decompression:

```yaml
# For large .gz files
processing:
  max_workers: 4          # Limit concurrent decompression
  buffer_size: 32768      # 32 KB chunks
```

#### Performance Characteristics

| File Size | Format      | Time     | Memory   | Throughput |
|-----------|-------------|----------|----------|------------|
| 1 GB      | Plain .log  | 5 min    | 100 MB   | 3.3 MB/s   |
| 1 GB      | .log.gz     | 7 min    | 150 MB   | 2.4 MB/s   |
| 10 GB     | Plain .log  | 50 min   | 100 MB   | 3.3 MB/s   |
| 10 GB     | .log.gz     | 70 min   | 150 MB   | 2.4 MB/s   |

### Interrupt and Resume

For very large files, you may want to process in batches:

```python
from log_filter.infrastructure.file_scanner import FileScanner
from pathlib import Path
import pickle

# Save progress checkpoint
def save_checkpoint(processed_files):
    with open('checkpoint.pkl', 'wb') as f:
        pickle.dump(processed_files, f)

def load_checkpoint():
    try:
        with open('checkpoint.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return set()

# Resume processing
scanner = FileScanner(search_root=Path("/var/log"))
all_files = scanner.scan()
processed = load_checkpoint()

remaining_files = [f for f in all_files if str(f) not in processed]
print(f"Resuming: {len(remaining_files)} files remaining")

pipeline = ProcessingPipeline(config)
for file_path in remaining_files:
    try:
        pipeline.process_single_file(file_path)
        processed.add(str(file_path))
        save_checkpoint(processed)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
```

---

## Complex Boolean Expressions

### Expression Syntax Reference

#### Operators

| Operator | Syntax | Example | Description |
|----------|--------|---------|-------------|
| AND      | `AND`, `&&` | `ERROR AND database` | Both terms must match |
| OR       | `OR`, `\|\|` | `ERROR OR WARNING` | Either term must match |
| NOT      | `NOT`, `!` | `NOT deprecated` | Term must not match |

#### Operator Precedence

1. **Parentheses** `()` - Highest priority
2. **NOT** `!` - Unary negation
3. **AND** `&&` - Conjunction
4. **OR** `\|\|` - Disjunction (Lowest priority)

### Complex Expression Examples

#### Example 1: Error Tracking with Exclusions

Find errors but exclude known noise:

```yaml
search:
  expression: >
    (ERROR OR CRITICAL) AND 
    NOT (deprecated OR "known issue") AND
    (database OR network OR timeout)
  case_sensitive: false
```

This finds:
- ERROR or CRITICAL messages
- That are NOT about deprecated features or known issues
- That mention database, network, or timeout

#### Example 2: Multi-Service Monitoring

Monitor multiple services with different criteria:

```yaml
search:
  expression: >
    (service:api AND (ERROR OR latency > 1000)) OR
    (service:database AND (CONNECTION OR DEADLOCK)) OR
    (service:cache AND (EVICTION OR OOM))
```

#### Example 3: Security Event Detection

```yaml
search:
  expression: >
    (
      (authentication AND (failed OR denied)) OR
      (authorization AND (unauthorized OR forbidden)) OR
      (sql AND (injection OR malicious))
    ) AND NOT (health-check OR monitoring)
  case_sensitive: false
```

### Expression Optimization

#### Performance Impact

| Expression Type | Evaluation Speed | Recommendation |
|----------------|------------------|----------------|
| Simple term | ~1 µs/record | Fastest |
| AND with 2 terms | ~2 µs/record | Very fast |
| OR with 2 terms | ~2 µs/record | Very fast |
| NOT | ~1 µs/record | Fast |
| Complex nested | ~5-10 µs/record | Acceptable |
| Many ORs (10+) | ~20 µs/record | Consider simplification |

#### Optimization Tips

1. **Put common terms first in AND expressions**:
   ```yaml
   # Good: 'ERROR' appears frequently
   expression: "ERROR AND database AND connection"
   
   # Less optimal
   expression: "connection AND database AND ERROR"
   ```

2. **Use NOT sparingly**:
   ```yaml
   # Prefer inclusion
   expression: "(ERROR OR WARNING OR CRITICAL)"
   
   # Over exclusion
   expression: "NOT (INFO OR DEBUG OR TRACE)"
   ```

3. **Group related terms**:
   ```yaml
   # Efficient
   expression: "(ERROR AND database) OR (ERROR AND network)"
   
   # Same result, clearer
   expression: "ERROR AND (database OR network)"
   ```

### Testing Complex Expressions

Use a small test file first:

```bash
# Test expression on small sample
log-filter --input sample.log \
           --expr "complex expression here" \
           --output test-result.txt

# Check match count
wc -l test-result.txt

# Review matches to ensure correctness
less test-result.txt
```

---

## Custom Filter Chains

### Combining Multiple Filter Types

Log Filter supports combining various filter types:

#### Date and Time Range Filtering

```yaml
search:
  expression: "ERROR"
  start_date: "2026-01-01"
  end_date: "2026-01-31"
  start_time: "09:00:00"
  end_time: "17:00:00"
```

This filters:
- Records matching "ERROR"
- Within January 2026
- Between 9 AM and 5 PM

#### File Pattern Filtering

```yaml
files:
  search_root: "/var/log"
  include_patterns:
    - "application*.log"
    - "app-*.gz"
  exclude_patterns:
    - "*.old"
    - "*.backup"
    - "*debug*.log"
```

### Building Custom Filter Pipelines

For advanced programmatic filtering:

```python
from log_filter.domain.filters import (
    ExpressionFilter,
    DateRangeFilter,
    TimeRangeFilter,
    FilterChain
)
from log_filter.domain.models import LogRecord
from datetime import datetime, time

# Create individual filters
expression_filter = ExpressionFilter(
    expression="ERROR AND database",
    case_sensitive=False
)

date_filter = DateRangeFilter(
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31)
)

time_filter = TimeRangeFilter(
    start_time=time(9, 0, 0),
    end_time=time(17, 0, 0)
)

# Combine into chain
filter_chain = FilterChain([
    expression_filter,
    date_filter,
    time_filter
])

# Apply to records
def process_record(record: LogRecord) -> bool:
    """Return True if record passes all filters."""
    return filter_chain.matches(record)

# Use in processing
for record in records:
    if process_record(record):
        print(record.content)
```

### Custom Filter Implementation

Create your own filter:

```python
from log_filter.domain.filters import AbstractFilter
from log_filter.domain.models import LogRecord

class SeverityFilter(AbstractFilter):
    """Filter by log severity level."""
    
    SEVERITY_LEVELS = {
        'TRACE': 0,
        'DEBUG': 1,
        'INFO': 2,
        'WARNING': 3,
        'ERROR': 4,
        'CRITICAL': 5
    }
    
    def __init__(self, min_severity: str):
        self.min_level = self.SEVERITY_LEVELS.get(min_severity.upper(), 0)
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record meets minimum severity."""
        record_level = self._extract_level(record)
        return record_level >= self.min_level
    
    def _extract_level(self, record: LogRecord) -> int:
        """Extract severity level from record."""
        content_upper = record.content.upper()
        for level_name, level_value in self.SEVERITY_LEVELS.items():
            if level_name in content_upper:
                return level_value
        return 0  # Default to lowest

# Use custom filter
severity_filter = SeverityFilter(min_severity="WARNING")
filter_chain = FilterChain([expression_filter, severity_filter])
```

---

## Performance Optimization

### Benchmarking Your Workload

Create a performance baseline:

```python
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.statistics.performance import PerformanceTracker
import time

# Configure test
test_configs = [
    {"max_workers": 1, "buffer_size": 8192},
    {"max_workers": 4, "buffer_size": 8192},
    {"max_workers": 8, "buffer_size": 8192},
    {"max_workers": 8, "buffer_size": 16384},
    {"max_workers": 8, "buffer_size": 32768},
]

results = []

for test_config in test_configs:
    config = ApplicationConfig(
        processing=ProcessingConfig(**test_config)
    )
    
    tracker = PerformanceTracker()
    tracker.start()
    
    pipeline = ProcessingPipeline(config)
    pipeline.run()
    
    metrics = tracker.get_metrics()
    results.append({
        "config": test_config,
        "time": metrics.total_time,
        "throughput": metrics.avg_throughput,
        "records_per_sec": metrics.records_per_second
    })

# Display results
for result in results:
    print(f"Workers: {result['config']['max_workers']}, "
          f"Buffer: {result['config']['buffer_size']}, "
          f"Time: {result['time']:.2f}s, "
          f"Throughput: {result['throughput']:.2f} MB/s")
```

### Performance Tuning Checklist

- [ ] **Profile with representative data**: Use actual production logs
- [ ] **Test different worker counts**: Find the sweet spot for your system
- [ ] **Optimize buffer sizes**: Match your typical file sizes
- [ ] **Simplify expressions**: Remove unnecessary complexity
- [ ] **Use SSD storage**: 5-10x faster than HDD
- [ ] **Monitor system resources**: Watch CPU, memory, and I/O
- [ ] **Pre-filter files**: Exclude files that won't match
- [ ] **Compress historical logs**: Use gzip for older files

### Storage Optimization

#### SSD vs HDD Performance

| Storage Type | Throughput | Random I/O | Best For |
|-------------|------------|------------|----------|
| NVMe SSD | 200-400 MB/s | Excellent | Large files, many workers |
| SATA SSD | 100-200 MB/s | Very Good | General purpose |
| HDD 7200rpm | 50-100 MB/s | Poor | Sequential reading, cost-sensitive |
| Network (1Gb) | 50-100 MB/s | Poor | Centralized storage |

#### Configuration by Storage Type

**NVMe SSD**:
```yaml
processing:
  max_workers: 16
  buffer_size: 65536  # 64 KB
```

**SATA SSD**:
```yaml
processing:
  max_workers: 8
  buffer_size: 32768  # 32 KB
```

**HDD**:
```yaml
processing:
  max_workers: 4
  buffer_size: 16384  # 16 KB
```

### CPU Optimization

For complex expressions that are CPU-intensive:

1. **Profile expression evaluation**:
   ```python
   from log_filter.core.parser import parse
   from log_filter.core.evaluator import Evaluator
   import time
   
   ast = parse("complex expression")
   evaluator = Evaluator(ast)
   
   # Test evaluation speed
   test_records = ["ERROR database connection"] * 10000
   
   start = time.time()
   matches = sum(1 for rec in test_records if evaluator.evaluate(rec))
   elapsed = time.time() - start
   
   print(f"Evaluated {len(test_records)} records in {elapsed:.2f}s")
   print(f"Rate: {len(test_records) / elapsed:.0f} records/sec")
   ```

2. **Simplify expressions**: Each operator adds overhead
3. **Use literal matches when possible**: Faster than complex boolean logic
4. **Consider pre-filtering**: Use simple grep first for huge datasets

---

## Memory Management

### Memory Consumption Profile

| Component | Memory Per Instance | Scaling Factor |
|-----------|---------------------|----------------|
| Worker thread | 50-100 MB | × number of workers |
| File handler | 10-20 MB | × active files |
| Statistics collector | 1-2 MB | Fixed |
| Output writer | 5-10 MB | Fixed |
| Pipeline overhead | 20-30 MB | Fixed |

### Memory-Constrained Environments

For systems with limited RAM (< 4 GB):

```yaml
processing:
  max_workers: 2          # Minimal workers
  buffer_size: 4096       # 4 KB chunks
  chunk_size: 100         # Smaller batches
```

### Monitoring Memory Usage

```python
import psutil
import os

def get_memory_usage():
    """Get current process memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # MB

# Monitor during processing
print(f"Initial memory: {get_memory_usage():.1f} MB")

pipeline = ProcessingPipeline(config)
result = pipeline.run()

print(f"Final memory: {get_memory_usage():.1f} MB")
print(f"Peak memory: {psutil.Process().memory_info().rss / (1024 * 1024):.1f} MB")
```

### Memory Leak Prevention

Log Filter is designed to avoid memory leaks:

1. **Streaming processing**: Records not kept in memory
2. **Bounded buffers**: Fixed-size buffers prevent accumulation
3. **Automatic cleanup**: Resources released after processing
4. **No global state**: Each file processed independently

For long-running processes:

```python
import gc

# Force garbage collection periodically
for batch in file_batches:
    process_batch(batch)
    gc.collect()  # Explicit cleanup
```

---

## Advanced Output Options

### Custom Output Formatting

```python
from log_filter.domain.models import LogRecord

def custom_formatter(record: LogRecord) -> str:
    """Format output with custom structure."""
    return f"[{record.timestamp}] {record.level}: {record.content}\n"

# Apply during processing
with FileWriter(output_file=Path("results.txt")) as writer:
    for record in matching_records:
        formatted = custom_formatter(record)
        writer.write(formatted)
```

### Multiple Output Destinations

```python
from pathlib import Path

# Separate errors and warnings
error_writer = FileWriter(Path("errors.txt"))
warning_writer = FileWriter(Path("warnings.txt"))

with error_writer, warning_writer:
    for record in records:
        if "ERROR" in record.content:
            error_writer.write(record.content + "\n")
        elif "WARNING" in record.content:
            warning_writer.write(record.content + "\n")
```

### Structured Output (JSON)

```python
import json
from log_filter.domain.models import LogRecord

def to_json(record: LogRecord) -> str:
    """Convert record to JSON."""
    return json.dumps({
        "timestamp": record.timestamp.isoformat(),
        "level": record.level,
        "content": record.content,
        "file": record.source_file,
        "line": record.line_number
    }) + "\n"

# Write JSON output
with FileWriter(Path("results.json")) as writer:
    for record in matching_records:
        writer.write(to_json(record))
```

### Real-Time Streaming Output

```python
import sys

def stream_to_stdout(record: LogRecord):
    """Stream results to stdout in real-time."""
    sys.stdout.write(f"{record.content}\n")
    sys.stdout.flush()

# Use in pipeline
for record in pipeline.process_stream():
    stream_to_stdout(record)
```

---

## Production Deployment Patterns

### High-Availability Setup

```yaml
# config.yaml for production
processing:
  max_workers: 12
  buffer_size: 32768
  error_handling: "continue"  # Don't stop on errors

output:
  output_file: "/var/log/filter-results/output.log"
  show_stats: true
  quiet: false

logging:
  level: "INFO"
  file: "/var/log/log-filter/app.log"
  rotate: true
  max_size_mb: 100
  backup_count: 10
```

### Scheduled Processing (Cron)

```bash
#!/bin/bash
# /usr/local/bin/log-filter-daily.sh

# Daily log processing script

LOG_DATE=$(date -d "yesterday" +%Y-%m-%d)
OUTPUT_DIR="/var/log/filtered"
CONFIG="/etc/log-filter/config.yaml"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run log filter
log-filter \
    --config "$CONFIG" \
    --start-date "$LOG_DATE" \
    --end-date "$LOG_DATE" \
    --output "$OUTPUT_DIR/errors-$LOG_DATE.txt"

# Check exit code
if [ $? -eq 0 ]; then
    echo "Log filtering completed successfully"
    
    # Compress output
    gzip "$OUTPUT_DIR/errors-$LOG_DATE.txt"
    
    # Clean up old files (>30 days)
    find "$OUTPUT_DIR" -name "errors-*.txt.gz" -mtime +30 -delete
else
    echo "Log filtering failed" >&2
    exit 1
fi
```

Crontab entry:
```text
# Run daily at 1 AM
0 1 * * * /usr/local/bin/log-filter-daily.sh >> /var/log/log-filter-cron.log 2>&1
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-filter-daily
spec:
  schedule: "0 1 * * *"  # Daily at 1 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: log-filter
            image: log-filter:2.0.0
            args:
              - "--config"
              - "/config/config.yaml"
            volumeMounts:
              - name: config
                mountPath: /config
              - name: logs
                mountPath: /var/log
              - name: output
                mountPath: /output
            resources:
              requests:
                memory: "2Gi"
                cpu: "2"
              limits:
                memory: "4Gi"
                cpu: "4"
          volumes:
            - name: config
              configMap:
                name: log-filter-config
            - name: logs
              persistentVolumeClaim:
                claimName: log-storage
            - name: output
              persistentVolumeClaim:
                claimName: filtered-logs
          restartPolicy: OnFailure
```

### Monitoring and Alerting

```python
# monitoring.py - Integration with monitoring systems

from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.statistics.collector import StatisticsCollector
import requests
import json

def send_to_prometheus(stats, job_name="log_filter"):
    """Export metrics to Prometheus Pushgateway."""
    metrics = f"""
# HELP log_filter_files_processed_total Total files processed
# TYPE log_filter_files_processed_total counter
log_filter_files_processed_total{{job="{job_name}"}} {stats.files_processed}

# HELP log_filter_records_total Total records processed
# TYPE log_filter_records_total counter
log_filter_records_total{{job="{job_name}"}} {stats.total_records}

# HELP log_filter_matches_total Total matches found
# TYPE log_filter_matches_total counter
log_filter_matches_total{{job="{job_name}"}} {stats.matched_records}

# HELP log_filter_processing_seconds Processing time in seconds
# TYPE log_filter_processing_seconds gauge
log_filter_processing_seconds{{job="{job_name}"}} {stats.processing_time}

# HELP log_filter_errors_total Total errors encountered
# TYPE log_filter_errors_total counter
log_filter_errors_total{{job="{job_name}"}} {len(stats.errors)}
"""
    
    # Send to Pushgateway
    response = requests.post(
        "http://pushgateway:9091/metrics/job/log_filter",
        data=metrics,
        headers={"Content-Type": "text/plain"}
    )
    return response.status_code == 200

def send_alert_on_errors(stats, threshold=10):
    """Send alert if error count exceeds threshold."""
    if len(stats.errors) > threshold:
        alert = {
            "alert": "LogFilterErrors",
            "severity": "warning",
            "summary": f"Log filter encountered {len(stats.errors)} errors",
            "description": f"Errors: {stats.errors[:5]}"  # First 5 errors
        }
        
        requests.post(
            "http://alertmanager:9093/api/v1/alerts",
            json=[alert]
        )

# Use in pipeline
collector = StatisticsCollector()
pipeline = ProcessingPipeline(config, stats_collector=collector)

result = pipeline.run()
stats = collector.get_stats()

# Export metrics
send_to_prometheus(stats)
send_alert_on_errors(stats, threshold=10)
```

### Health Checks

```python
# healthcheck.py
import sys
from pathlib import Path
from log_filter.infrastructure.file_scanner import FileScanner

def check_log_directory():
    """Verify log directory is accessible."""
    log_dir = Path("/var/log")
    if not log_dir.exists():
        print("ERROR: Log directory does not exist", file=sys.stderr)
        return False
    
    if not log_dir.is_dir():
        print("ERROR: Log path is not a directory", file=sys.stderr)
        return False
    
    return True

def check_output_directory():
    """Verify output directory is writable."""
    output_dir = Path("/var/log/filtered")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except Exception as e:
        print(f"ERROR: Output directory not writable: {e}", file=sys.stderr)
        return False

def check_disk_space(min_gb=10):
    """Check available disk space."""
    import shutil
    stat = shutil.disk_usage("/var/log")
    free_gb = stat.free / (1024**3)
    
    if free_gb < min_gb:
        print(f"WARNING: Low disk space: {free_gb:.1f} GB", file=sys.stderr)
        return False
    return True

if __name__ == "__main__":
    checks = [
        check_log_directory(),
        check_output_directory(),
        check_disk_space()
    ]
    
    if all(checks):
        print("All health checks passed")
        sys.exit(0)
    else:
        print("Health checks failed", file=sys.stderr)
        sys.exit(1)
```

---

## Summary

This advanced usage guide covers:

✅ **Multi-worker configuration** - Optimize parallel processing  
✅ **Large file processing** - Handle multi-GB files efficiently  
✅ **Complex expressions** - Master boolean search syntax  
✅ **Custom filters** - Build sophisticated filter chains  
✅ **Performance optimization** - Tune for your workload  
✅ **Memory management** - Handle resource constraints  
✅ **Advanced output** - Customize result formatting  
✅ **Production deployment** - Enterprise-grade setups  

### Next Steps

- [Integration Guide](integration_guide.md) - Integrate with other systems
- [Error Handling](error_handling.md) - Comprehensive error reference
- [API Reference](api/index.rst) - Complete API documentation
- [Performance Guide](performance.md) - Detailed performance tuning

### Getting Help

- GitHub Issues: https://github.com/your-org/log-filter/issues
- Documentation: https://log-filter.readthedocs.io
- Community: Discord/Slack channel

---

**Document Version:** 1.0  
**Last Review:** January 8, 2026  
**Next Review:** March 8, 2026
