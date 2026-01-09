# Real-World Examples

**Last Updated:** January 8, 2026  
**Version:** 2.0.0

This directory contains real-world examples of using Log Filter for common use cases.

---

## 📂 Example Categories

### 1. [Application Monitoring](monitoring.md)
Monitor application health and track errors in production:
- Web application error tracking
- API performance monitoring
- Database connection issues
- Memory leak detection
- Service health checks

### 2. [DevOps Workflows](devops.md)
Integrate Log Filter into your DevOps pipelines:
- Post-deployment health checks
- Incident investigation and analysis
- Performance regression detection
- Log aggregation pipelines
- Automated alerting

### 3. [Security Analysis](security.md)
Detect security issues and anomalies:
- Failed authentication attempts
- Suspicious access patterns
- SQL injection detection
- API abuse monitoring
- Compliance auditing

### 4. [Code Examples](devops.md)
Working Python code for custom integrations:
- Custom filter implementations
- Pipeline integration
- Monitoring system exports
- Alert triggers
- Report generation

---

## Quick Start Examples

### Example 1: Find Today's Errors

```bash
log-filter --expr "ERROR OR CRITICAL" \
  --input /var/log/app \
  --start-date "$(date +%Y-%m-%d)" \
  --output today-errors.txt \
  --stats
```

### Example 2: Monitor Payment Failures

```bash
log-filter --expr "payment AND (failed OR timeout OR error)" \
  --input /var/log/app \
  --output payment-failures.txt \
  --highlight
```

### Example 3: Database Performance Issues

```bash
log-filter --expr "(slow AND query) OR (database AND timeout)" \
  --input /var/log \
  --include "db-*.log" \
  --output db-performance.txt
```

### Example 4: Security Audit

```bash
log-filter --expr "authentication AND (failed OR denied)" \
  --input /var/log/auth.log \
  --start-date "2026-01-01" \
  --end-date "2026-01-31" \
  --output security-audit-jan.txt
```

---

## Examples by Use Case

### Production Monitoring

| Use Case | Example | Link |
|----------|---------|------|
| Error rate monitoring | Track ERROR/CRITICAL over time | [monitoring.md#error-rate](monitoring.md#error-rate-monitoring) |
| Performance tracking | Find slow queries and timeouts | [monitoring.md#performance](monitoring.md#performance-tracking) |
| Health checks | Verify service availability | [monitoring.md#health-checks](monitoring.md#health-checks) |

### Development & Testing

| Use Case | Example | Link |
|----------|---------|------|
| Test failure analysis | Find test failures and stack traces | [devops.md#test-analysis](devops.md#test-failure-analysis) |
| Debug log extraction | Extract debug info for issues | [devops.md#debugging](devops.md#debugging) |
| Performance regression | Compare before/after metrics | [devops.md#regression](devops.md#performance-regression) |

### Security & Compliance

| Use Case | Example | Link |
|----------|---------|------|
| Failed logins | Track authentication failures | [security.md#auth-failures](security.md#authentication-failures) |
| Suspicious activity | Detect unusual patterns | [security.md#anomalies](security.md#anomaly-detection) |
| Compliance reporting | Generate audit reports | [security.md#compliance](security.md#compliance-reporting) |

---

## Configuration Templates

### Production Error Monitoring

```yaml
# production-errors.yaml
search:
  expression: "ERROR OR CRITICAL"
  case_sensitive: false

files:
  search_root: /var/log/app
  include_patterns:
    - "application-*.log"
    - "application-*.log.gz"

output:
  output_file: /var/log/filtered/errors-{date}.txt
  show_stats: true

processing:
  max_workers: 8

logging:
  level: INFO
  file: /var/log/log-filter/app.log
```

### Development Debugging

```yaml
# debug-config.yaml
search:
  expression: "ERROR OR WARNING OR DEBUG"
  case_sensitive: false

files:
  search_root: ./logs
  include_patterns:
    - "*.log"

output:
  output_file: debug-output.txt
  highlight: true
  show_stats: true

processing:
  max_workers: 2

logging:
  level: DEBUG
```

---

## Integration Examples

### GitHub Actions

```yaml
# .github/workflows/log-analysis.yml
- name: Analyze deployment logs
  run: |
    log-filter --expr "ERROR OR CRITICAL" \
      --input ./deployment-logs \
      --output errors.txt
    
    if [ -s errors.txt ]; then
      echo "::error::Errors found in deployment logs"
      exit 1
    fi
```

### Cron Job

```bash
#!/bin/bash
# /usr/local/bin/daily-error-report.sh

DATE=$(date -d "yesterday" +%Y-%m-%d)

log-filter --expr "ERROR OR CRITICAL" \
  --input /var/log/app \
  --start-date "$DATE" \
  --end-date "$DATE" \
  --output "/reports/errors-$DATE.txt" \
  --stats

# Email if errors found
if [ -s "/reports/errors-$DATE.txt" ]; then
  mail -s "Daily Error Report: $DATE" team@company.com < "/reports/errors-$DATE.txt"
fi
```

### Docker

```dockerfile
FROM python:3.10-slim

RUN pip install log-filter

WORKDIR /app
COPY config.yaml /app/

CMD ["log-filter", "--config", "/app/config.yaml"]
```

---

## Code Examples

### Python Integration

```python
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.config.models import ApplicationConfig

# Configure
config = ApplicationConfig(
    search=SearchConfig(expression="ERROR"),
    files=FileConfig(search_root="/var/log"),
    output=OutputConfig(output_file="errors.txt")
)

# Process
pipeline = ProcessingPipeline(config)
result = pipeline.run()

print(f"Found {result.total_matches} errors")
```

### Custom Filter

```python
from log_filter.domain.filters import AbstractFilter

class SeverityFilter(AbstractFilter):
    def __init__(self, min_level):
        self.min_level = min_level
    
    def matches(self, record):
        return record.level >= self.min_level
```

---

## Performance Benchmarks

### Small Files (< 10 MB)

```bash
# 100 files × 1 MB each
log-filter --expr "ERROR" --input ./logs --workers 8
# Result: ~5,000 lines/sec, 0.2s total
```

### Large Files (> 100 MB)

```bash
# 10 files × 100 MB each
log-filter --expr "ERROR" --input ./logs --workers 4 --buffer-size 65536
# Result: ~3,000 lines/sec, 5-10s total
```

### Compressed Files

```bash
# 50 files × 10 MB .gz each
log-filter --expr "ERROR" --input ./logs --workers 6
# Result: ~2,500 lines/sec (decompression overhead)
```

---

## Troubleshooting Examples

### Problem: Slow Performance

```bash
# Check with stats
log-filter --expr "ERROR" --input ./logs --stats

# If throughput < 1000 records/sec:
# 1. Increase workers
# 2. Increase buffer size
# 3. Simplify expression
```

### Problem: Out of Memory

```yaml
# Reduce resource usage
processing:
  max_workers: 2
  buffer_size: 4096
```

### Problem: No Matches Found

```bash
# Test expression
log-filter --expr "test" --input sample.log --highlight

# Check case sensitivity
log-filter --expr "ERROR" --input sample.log  # Case-insensitive (default)
log-filter --expr "ERROR" --input sample.log --case-sensitive  # Case-sensitive
```

---

## Getting Help

- **Detailed Guides:** See [monitoring.md](monitoring.md), [devops.md](devops.md), [security.md](security.md)
- **Code Examples:** Browse [DevOps examples](devops.md) for CI/CD and automation recipes
- **API Reference:** [../api/index.rst](../api/index.rst)
- **Tutorials:** [../tutorials/beginner.md](../tutorials/beginner.md)

---

## Contributing Examples

Have a great example? Contribute to this directory!

1. Fork the repository
2. Add your example to the appropriate file
3. Include working code and sample output
4. Submit a pull request

See [../contributing.md](../contributing.md) for guidelines.

---

**Document Version:** 1.0  
**Last Updated:** January 8, 2026
