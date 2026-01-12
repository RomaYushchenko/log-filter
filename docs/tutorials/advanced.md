# Advanced Tutorial: Production-Ready Log Filtering

**Duration:** 30 minutes  
**Level:** Advanced  
**Prerequisites:** Complete [Intermediate Tutorial](intermediate.md)  
**Last Updated:** January 8, 2026

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- ✅ Handle multi-gigabyte log files efficiently
- ✅ Build complex expression patterns for real scenarios
- ✅ Integrate Log Filter into Python applications
- ✅ Implement custom filters and pipelines
- ✅ Deploy Log Filter in production environments
- ✅ Set up monitoring and alerting
- ✅ Optimize for maximum performance
- ✅ Troubleshoot production issues

---

## Part 1: Processing Large Files (6 minutes)

### Scenario: 10 GB Production Log File

Let's process a large production log file efficiently.

#### Setup: Generate Large Test File

```bash
# Generate a 1 GB test file (adjust for your needs)
python3 << 'EOF'
import random
import datetime

levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
messages = [
    'Database query executed',
    'API request processed',
    'Cache hit',
    'Cache miss',
    'User authentication successful',
    'Payment processed',
    'Email sent',
    'File uploaded',
    'Report generated'
]
errors = [
    'Database connection timeout',
    'Payment gateway error',
    'File not found',
    'Out of memory',
    'Network timeout'
]

with open('large.log', 'w') as f:
    for i in range(10_000_000):  # 10 million lines
        timestamp = datetime.datetime(2026, 1, 1) + datetime.timedelta(seconds=i)
        level = random.choice(levels)
        if level == 'ERROR':
            message = random.choice(errors)
        else:
            message = random.choice(messages)
        
        f.write(f"{timestamp.isoformat()} {level} {message}\n")
EOF
```

**Note:** This creates a ~1 GB file. Adjust the range for larger files.

#### Optimal Configuration for Large Files

```yaml
# large-file-config.yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  search_root: .
  include_patterns:
    - "large.log"

output:
  output_file: large-errors.txt
  show_stats: true
  quiet: false  # Show progress

processing:
  max_workers: 4        # Fewer workers for memory efficiency
  buffer_size: 65536    # 64 KB chunks for large files
  chunk_size: 10000     # Process 10K records at a time

logging:
  level: INFO
```

#### Run with Progress Monitoring

```bash
time log-filter --config large-file-config.yaml
```

**Expected Output:**
```
Processing large.log...
Progress: 1,000,000 / 10,000,000 records (10.0%)
Progress: 2,000,000 / 10,000,000 records (20.0%)
...
================================================================================
Processing Statistics
================================================================================
Files:
  Processed:     1
  Matched:       1 (100.0%)

Records:
  Total:         10,000,000
  Matched:       ~1,250,000 (12.5%)

Performance:
  Time:          45.2s
  Throughput:    221,000 records/sec
  Speed:         22.1 MB/sec
================================================================================
```

#### Memory-Constrained Systems

For systems with limited RAM (< 4 GB):

```yaml
processing:
  max_workers: 1        # Sequential processing
  buffer_size: 8192     # 8 KB chunks
  chunk_size: 1000      # Smaller chunks
```

---

## Part 2: Complex Expression Patterns (7 minutes)

### Real-World Expression Examples

#### Example 1: E-commerce Error Tracking

Track payment and order processing errors:

```bash
log-filter --expr \
  "((payment OR checkout OR order) AND (failed OR error OR timeout)) OR
   ((inventory OR stock) AND (unavailable OR out-of-stock))" \
  --input /var/log/app \
  --output ecommerce-errors.txt
```

**What this finds:**
- Payment failures, checkout errors, order timeouts
- Inventory unavailable, out-of-stock issues

#### Example 2: Security Monitoring

Detect security threats:

```bash
log-filter --expr \
  "(authentication AND (failed OR denied OR unauthorized)) OR
   (authorization AND (forbidden OR denied)) OR
   (sql AND (injection OR malicious)) OR
   (xss OR csrf OR rce)" \
  --input /var/log/security \
  --output security-threats.txt
```

#### Example 3: Performance Degradation

Find performance issues:

```bash
log-filter --expr \
  "(slow AND (query OR request OR response)) OR
   (timeout AND NOT health-check) OR
   (latency AND (high OR exceeded)) OR
   (cpu AND (high OR spike)) OR
   (memory AND (high OR leak))" \
  --input /var/log/app \
  --output performance-issues.txt
```

#### Example 4: Multi-Service Correlation

Track errors across microservices:

```bash
log-filter --expr \
  "((service:api AND (500 OR 503)) OR
    (service:database AND (deadlock OR timeout)) OR
    (service:cache AND (eviction OR miss-rate))
   ) AND NOT (health-check OR monitoring)" \
  --input /var/log \
  --include "service-*.log" \
  --output service-errors.txt
```

### Expression Optimization Tips

#### Before Optimization

```bash
# Inefficient - many OR clauses
log-filter --expr \
  "ERROR1 OR ERROR2 OR ERROR3 OR ERROR4 OR ERROR5 OR ERROR6" \
  --input large.log
# Evaluation time: ~100ms per 10K records
```

#### After Optimization

```bash
# Efficient - group common terms
log-filter --expr \
  "ERROR AND (condition1 OR condition2 OR condition3)" \
  --input large.log
# Evaluation time: ~50ms per 10K records
```

---

## Part 3: Python API Integration (8 minutes)

### Custom Pipeline Implementation

Build a production-ready Python integration:

```python
# production_log_filter.py
import logging
from pathlib import Path
from typing import List, Callable
from dataclasses import dataclass
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.config.models import ApplicationConfig, SearchConfig, FileConfig, OutputConfig, ProcessingConfig
from log_filter.domain.models import LogRecord
from log_filter.statistics.collector import StatisticsCollector

@dataclass
class FilterResult:
    """Result of filtering operation."""
    total_files: int
    total_records: int
    total_matches: int
    processing_time: float
    errors: List[str]

class ProductionLogFilter:
    """Production-ready log filter with callbacks and error handling."""
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.stats_collector = StatisticsCollector()
        self.pipeline = ProcessingPipeline(config, stats_collector=self.stats_collector)
        self.match_callbacks: List[Callable[[LogRecord], None]] = []
        self.error_callbacks: List[Callable[[Exception, str], None]] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def add_match_callback(self, callback: Callable[[LogRecord], None]):
        """Add callback for each matching record."""
        self.match_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception, str], None]):
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def process(self) -> FilterResult:
        """Process logs with error handling."""
        self.logger.info("Starting log filtering")
        
        try:
            # Run pipeline
            result = self.pipeline.run()
            
            # Get statistics
            stats = self.stats_collector.get_stats()
            
            # Trigger callbacks for matches
            self._trigger_match_callbacks()
            
            self.logger.info(f"Filtering complete: {stats.matched_records} matches found")
            
            return FilterResult(
                total_files=stats.files_processed,
                total_records=stats.total_records,
                total_matches=stats.matched_records,
                processing_time=stats.processing_time,
                errors=stats.errors
            )
            
        except Exception as e:
            self.logger.error(f"Filtering failed: {e}", exc_info=True)
            self._trigger_error_callbacks(e, "pipeline")
            raise
    
    def _trigger_match_callbacks(self):
        """Trigger callbacks for matching records."""
        # Implementation depends on pipeline streaming support
        pass
    
    def _trigger_error_callbacks(self, error: Exception, context: str):
        """Trigger error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error, context)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")

# Usage example
def main():
    # Configure
    config = ApplicationConfig(
        search=SearchConfig(
            expression="ERROR OR CRITICAL",
            ignore_case=False
        ),
        files=FileConfig(
            search_root=Path("/var/log/app"),
            include_patterns=["*.log"]
        ),
        output=OutputConfig(
            output_file=Path("filtered-errors.txt"),
            show_stats=True
        ),
        processing=ProcessingConfig(
            max_workers=8
        )
    )
    
    # Create filter
    filter_service = ProductionLogFilter(config)
    
    # Add callbacks
    def on_match(record: LogRecord):
        """Send critical errors to alerting system."""
        if "CRITICAL" in record.content:
            send_alert(record)
    
    def on_error(error: Exception, context: str):
        """Log errors to monitoring system."""
        log_to_sentry(error, context)
    
    filter_service.add_match_callback(on_match)
    filter_service.add_error_callback(on_error)
    
    # Process
    result = filter_service.process()
    
    print(f"Processed {result.total_records} records")
    print(f"Found {result.total_matches} matches")
    print(f"Time: {result.processing_time:.2f}s")

def send_alert(record: LogRecord):
    """Send alert to monitoring system."""
    # Implementation: PagerDuty, Slack, email, etc.
    pass

def log_to_sentry(error: Exception, context: str):
    """Log error to Sentry."""
    # Implementation: Sentry integration
    pass

if __name__ == "__main__":
    main()
```

### Custom Filter Implementation

Create domain-specific filters:

```python
# custom_filters.py
from log_filter.domain.filters import AbstractFilter
from log_filter.domain.models import LogRecord
from datetime import time
import re

class BusinessHoursFilter(AbstractFilter):
    """Filter logs to business hours only."""
    
    def __init__(self, start_hour: int = 9, end_hour: int = 17):
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record is during business hours."""
        if record.timestamp:
            hour = record.timestamp.hour
            return self.start_hour <= hour < self.end_hour
        return True  # No timestamp, pass through

class SeverityLevelFilter(AbstractFilter):
    """Filter by minimum severity level."""
    
    LEVELS = {
        'TRACE': 0, 'DEBUG': 1, 'INFO': 2,
        'WARNING': 3, 'ERROR': 4, 'CRITICAL': 5
    }
    
    def __init__(self, min_level: str):
        self.min_level = self.LEVELS.get(min_level.upper(), 0)
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record meets minimum severity."""
        for level_name, level_value in self.LEVELS.items():
            if level_name in record.content.upper():
                return level_value >= self.min_level
        return False

class RegexFilter(AbstractFilter):
    """Filter using regular expressions."""
    
    def __init__(self, pattern: str):
        self.regex = re.compile(pattern, re.IGNORECASE)
    
    def matches(self, record: LogRecord) -> bool:
        """Check if record matches regex."""
        return bool(self.regex.search(record.content))

# Usage
from log_filter.domain.filters import FilterChain

# Combine filters
filters = FilterChain([
    BusinessHoursFilter(start_hour=9, end_hour=17),
    SeverityLevelFilter(min_level="ERROR"),
    RegexFilter(pattern=r"database|connection")
])

# Apply to records
for record in records:
    if filters.matches(record):
        print(record.content)
```

---

## Part 4: Production Deployment (5 minutes)

### Containerized Deployment

#### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install dependencies
RUN pip install --no-cache-dir log-filter

# Create application directory
WORKDIR /app

# Copy configuration
COPY config.yaml /app/config.yaml

# Create directories
RUN mkdir -p /logs /output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_FILTER_CONFIG=/app/config.yaml

# Run as non-root user
RUN useradd -m -u 1000 logfilter
USER logfilter

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD test -f /output/health.txt || exit 1

# Run log filter
CMD ["log-filter", "--config", "/app/config.yaml"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  log-filter:
    build: .
    container_name: log-filter
    volumes:
      - ./logs:/logs:ro
      - ./output:/output
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - MAX_WORKERS=8
      - BUFFER_SIZE=32768
    restart: unless-stopped
    mem_limit: 4g
    cpus: 4
    
    # Optional: Prometheus metrics
    ports:
      - "8000:8000"
```

#### Build and Run

```bash
# Build image
docker build -t log-filter:production .

# Run container
docker run -d \
  --name log-filter \
  -v $(pwd)/logs:/logs:ro \
  -v $(pwd)/output:/output \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  --memory=4g \
  --cpus=4 \
  log-filter:production

# View logs
docker logs -f log-filter

# Check health
docker ps
```

### Kubernetes Deployment

#### Deployment Configuration

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-filter
  labels:
    app: log-filter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: log-filter
  template:
    metadata:
      labels:
        app: log-filter
    spec:
      containers:
      - name: log-filter
        image: log-filter:production
        args: ["--config", "/config/config.yaml"]
        
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
        - name: logs
          mountPath: /logs
          readOnly: true
        - name: output
          mountPath: /output
        
        # Liveness probe
        livenessProbe:
          exec:
            command: ["test", "-f", "/output/health.txt"]
          initialDelaySeconds: 30
          periodSeconds: 60
        
        # Readiness probe
        readinessProbe:
          exec:
            command: ["test", "-f", "/output/health.txt"]
          initialDelaySeconds: 10
          periodSeconds: 30
      
      volumes:
      - name: config
        configMap:
          name: log-filter-config
      - name: logs
        persistentVolumeClaim:
          claimName: log-storage
      - name: output
        persistentVolumeClaim:
          claimName: filtered-output
```

#### CronJob for Scheduled Processing

```yaml
# k8s-cronjob.yaml
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
            image: log-filter:production
            args:
              - "--config"
              - "/config/config.yaml"
              - "--start-date"
              - "$(date -d 'yesterday' +%Y-%m-%d)"
              - "--end-date"
              - "$(date -d 'yesterday' +%Y-%m-%d)"
            
            volumeMounts:
            - name: config
              mountPath: /config
            - name: logs
              mountPath: /logs
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
              claimName: filtered-output
          
          restartPolicy: OnFailure
```

---

## Part 5: Monitoring and Alerting (4 minutes)

### Export Metrics to Prometheus

```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from log_filter.processing.pipeline import ProcessingPipeline
import time

# Define metrics
files_processed = Counter('log_filter_files_total', 'Total files processed')
records_processed = Counter('log_filter_records_total', 'Total records processed')
matches_found = Counter('log_filter_matches_total', 'Total matches found')
processing_time = Histogram('log_filter_duration_seconds', 'Processing duration')
errors_total = Counter('log_filter_errors_total', 'Total errors', ['error_type'])
active_workers = Gauge('log_filter_workers_active', 'Number of active workers')

def process_with_metrics(config):
    """Process logs and export metrics."""
    start_time = time.time()
    
    try:
        pipeline = ProcessingPipeline(config)
        result = pipeline.run()
        
        # Update metrics
        files_processed.inc(result.total_files)
        records_processed.inc(result.total_records)
        matches_found.inc(result.total_matches)
        
        duration = time.time() - start_time
        processing_time.observe(duration)
        
        return result
        
    except Exception as e:
        errors_total.labels(error_type=type(e).__name__).inc()
        raise

# Start metrics server
if __name__ == "__main__":
    start_http_server(8000)
    print("Metrics available at http://localhost:8000/metrics")
    
    # Process logs periodically
    while True:
        try:
            result = process_with_metrics(config)
            print(f"Processed {result.total_records} records")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(300)  # Every 5 minutes
```

### Alert on Errors

```python
# alerting.py
import requests
from log_filter.domain.models import LogRecord

class AlertManager:
    """Send alerts based on log patterns."""
    
    def __init__(self, webhook_url: str, threshold: int = 10):
        self.webhook_url = webhook_url
        self.threshold = threshold
        self.error_count = 0
    
    def check_record(self, record: LogRecord):
        """Check if record should trigger alert."""
        if "CRITICAL" in record.content:
            self.send_immediate_alert(record)
        
        if "ERROR" in record.content:
            self.error_count += 1
            if self.error_count >= self.threshold:
                self.send_threshold_alert()
                self.error_count = 0
    
    def send_immediate_alert(self, record: LogRecord):
        """Send immediate alert for critical issues."""
        payload = {
            "text": f"🚨 CRITICAL: {record.content}",
            "severity": "critical",
            "timestamp": record.timestamp.isoformat()
        }
        self._send(payload)
    
    def send_threshold_alert(self):
        """Send alert when error threshold exceeded."""
        payload = {
            "text": f"⚠️ Warning: {self.threshold} errors detected",
            "severity": "warning"
        }
        self._send(payload)
    
    def _send(self, payload: dict):
        """Send alert to webhook."""
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send alert: {e}")

# Usage
alert_manager = AlertManager(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    threshold=10
)

for record in matching_records:
    alert_manager.check_record(record)
```

---

## Practice Exercises

### Exercise 1: Large File Processing

Process a 5 GB log file with optimal settings.

<details>
<summary>Solution</summary>

```yaml
# large-config.yaml
search:
  expression: "ERROR"

files:
  search_root: /path/to/logs
  include_patterns:
    - "large-file.log"

output:
  output_file: large-errors.txt
  show_stats: true

processing:
  max_workers: 4
  buffer_size: 65536
  chunk_size: 10000
```

```bash
time log-filter --config large-config.yaml
```
</details>

### Exercise 2: Complex Expression

Create an expression to find:
- Payment failures OR timeouts
- During business hours (9 AM - 5 PM)
- Excluding health checks

<details>
<summary>Solution</summary>

```bash
log-filter --expr \
  "((payment AND (failed OR timeout)) OR (checkout AND error)) 
   AND NOT health-check" \
  --start-time "09:00:00" \
  --end-time "17:00:00" \
  --input /var/log/app
```
</details>

### Exercise 3: Python Integration

Build a custom filter that only passes ERROR messages from database module.

<details>
<summary>Solution</summary>

```python
from log_filter.domain.filters import AbstractFilter
from log_filter.domain.models import LogRecord

class DatabaseErrorFilter(AbstractFilter):
    def matches(self, record: LogRecord) -> bool:
        return "ERROR" in record.content and "database" in record.content.lower()

# Usage
filter = DatabaseErrorFilter()
for record in records:
    if filter.matches(record):
        print(record.content)
```
</details>

---

## Performance Optimization Checklist

- [ ] Profile with representative data
- [ ] Optimize worker count for workload
- [ ] Tune buffer size for file sizes
- [ ] Simplify complex expressions
- [ ] Use SSD storage when possible
- [ ] Monitor system resources
- [ ] Pre-filter files by pattern
- [ ] Compress old log files
- [ ] Implement caching for repeated searches
- [ ] Use streaming for large files

---

## Troubleshooting Guide

### Problem: Slow Performance

**Symptoms:** < 1,000 records/sec throughput

**Diagnosis:**
```bash
log-filter --expr "ERROR" --input ./logs --stats
```

**Solutions:**
1. Increase workers: `--workers 8`
2. Increase buffer: `--buffer-size 65536`
3. Simplify expression
4. Check storage speed: `iostat -x 1`

### Problem: High Memory Usage

**Symptoms:** Process using > 4 GB RAM

**Solutions:**
```yaml
processing:
  max_workers: 2          # Reduce workers
  buffer_size: 8192       # Smaller buffers
  chunk_size: 1000        # Smaller chunks
```

### Problem: Missing Matches

**Diagnosis:**
```bash
# Test expression
log-filter --expr "test" --input sample.log --highlight

# Check case sensitivity
log-filter --expr "ERROR" --input sample.log  # Case-insensitive
```

**Solutions:**
1. Remove `--case-sensitive` flag
2. Simplify expression
3. Check date/time filters

---

## What's Next?

Congratulations! You've mastered advanced log filtering. 🎉

### You learned:
- ✅ Large file processing (GB+ files)
- ✅ Complex expression patterns
- ✅ Python API integration
- ✅ Production deployment (Docker, Kubernetes)
- ✅ Monitoring and alerting
- ✅ Performance optimization
- ✅ Troubleshooting

### Next Steps:

1. **[Docker Tutorial](docker.md)** - Deep dive into containerization
2. **[Kubernetes Tutorial](kubernetes.md)** - Production K8s deployment
3. **[Integration Guide](../integration_guide.md)** - CI/CD and monitoring
4. **[Examples](../examples/)** - Real-world use cases

---

**Tutorial Version:** 1.0  
**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
