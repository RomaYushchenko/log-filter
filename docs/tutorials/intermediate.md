# Intermediate Tutorial: Advanced Log Filtering Techniques

**Duration:** 20 minutes  
**Level:** Intermediate  
**Prerequisites:** Complete [Beginner Tutorial](beginner.md)  
**Last Updated:** January 8, 2026

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- ✅ Filter logs by date and time ranges
- ✅ Work with multiple files and directories
- ✅ Use file patterns and exclusions
- ✅ Configure multi-worker processing
- ✅ Handle compressed log files (.gz)
- ✅ Use advanced output formatting
- ✅ Optimize performance for your workload

---

## Setup: Sample Log Files

Let's create a realistic test environment:

```bash
# Create a logs directory
mkdir -p test-logs

# Create multiple log files
cat > test-logs/app-2026-01-01.log << 'EOF'
2026-01-01 09:15:30 INFO Application started
2026-01-01 09:16:00 ERROR Failed to load config
2026-01-01 09:17:00 INFO Config loaded successfully
2026-01-01 14:30:00 WARNING High memory usage
2026-01-01 18:45:00 ERROR Database connection lost
EOF

cat > test-logs/app-2026-01-02.log << 'EOF'
2026-01-02 08:00:00 INFO Application started
2026-01-02 10:30:00 ERROR Payment gateway timeout
2026-01-02 12:00:00 INFO User john logged in
2026-01-02 15:45:00 WARNING Slow API response
2026-01-02 20:00:00 INFO Scheduled backup completed
EOF

cat > test-logs/db-2026-01-01.log << 'EOF'
2026-01-01 09:00:00 INFO Database initialized
2026-01-01 11:30:00 WARNING Slow query (2.5s)
2026-01-01 15:00:00 ERROR Connection pool exhausted
2026-01-01 18:45:00 CRITICAL Database crashed
EOF

cat > test-logs/db-2026-01-02.log << 'EOF'
2026-01-02 08:30:00 INFO Database started
2026-01-02 13:00:00 WARNING High CPU usage (90%)
2026-01-02 16:30:00 ERROR Deadlock detected
2026-01-02 19:00:00 INFO Backup successful
EOF
```

**On Windows PowerShell:** (see beginner tutorial for PowerShell syntax)

---

## Step 1: Working with Multiple Files (3 minutes)

### Search All Files in a Directory

Search for errors across all log files:

```bash
log-filter --expr "ERROR" --input test-logs/
```

**Output:**
```
test-logs/app-2026-01-01.log:
2026-01-01 09:16:00 ERROR Failed to load config
2026-01-01 18:45:00 ERROR Database connection lost

test-logs/app-2026-01-02.log:
2026-01-02 10:30:00 ERROR Payment gateway timeout

test-logs/db-2026-01-01.log:
2026-01-01 15:00:00 ERROR Connection pool exhausted

test-logs/db-2026-01-02.log:
2026-01-02 16:30:00 ERROR Deadlock detected
```

### Using File Patterns

Search only application logs:

```bash
log-filter --expr "ERROR" --input test-logs/ --include "app-*.log"
```

Search only database logs:

```bash
log-filter --expr "ERROR" --input test-logs/ --include "db-*.log"
```

### Multiple Include Patterns

Search both application and database logs with specific patterns:

```yaml
# config.yaml
files:
  search_root: test-logs/
  include_patterns:
    - "app-*.log"
    - "db-*.log"
```

### Excluding Files

Exclude database logs:

```bash
log-filter --expr "ERROR" --input test-logs/ --exclude "db-*.log"
```

Using configuration:

```yaml
files:
  search_root: test-logs/
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "db-*.log"
    - "*.old"
    - "*.backup"
```

---

## Step 2: Date and Time Filtering (4 minutes)

### Filter by Date Range

Find errors from January 1st only:

```bash
log-filter --expr "ERROR" \
  --input test-logs/ \
  --start-date "2026-01-01" \
  --end-date "2026-01-01"
```

**Output:**
```
2026-01-01 09:16:00 ERROR Failed to load config
2026-01-01 18:45:00 ERROR Database connection lost
2026-01-01 15:00:00 ERROR Connection pool exhausted
```

### Filter by Date and Time Range

Find errors during business hours (9 AM - 5 PM):

```bash
log-filter --expr "ERROR" \
  --input test-logs/ \
  --start-time "09:00:00" \
  --end-time "17:00:00"
```

**Output:**
```
2026-01-01 09:16:00 ERROR Failed to load config
2026-01-01 15:00:00 ERROR Connection pool exhausted
2026-01-02 10:30:00 ERROR Payment gateway timeout
2026-01-02 16:30:00 ERROR Deadlock detected
```

### Combining Date and Time Filters

Find errors on Jan 1st during business hours:

```bash
log-filter --expr "ERROR" \
  --input test-logs/ \
  --start-date "2026-01-01" \
  --end-date "2026-01-01" \
  --start-time "09:00:00" \
  --end-time "17:00:00"
```

### Configuration File with Date/Time Filters

```yaml
# search-config.yaml
search:
  expression: "ERROR OR CRITICAL"
  start_date: "2026-01-01"
  end_date: "2026-01-02"
  start_time: "09:00:00"
  end_time: "18:00:00"

files:
  search_root: test-logs/
  include_patterns:
    - "*.log"

output:
  output_file: business-hours-errors.txt
  show_stats: true
```

Run it:

```bash
log-filter --config search-config.yaml
```

---

## Step 3: Compressed Files (2 minutes)

### Working with .gz Files

Create a compressed log file:

```bash
gzip -k test-logs/app-2026-01-01.log
# Creates app-2026-01-01.log.gz
```

Search compressed files automatically:

```bash
log-filter --expr "ERROR" --input test-logs/app-2026-01-01.log.gz
```

**💡 Log Filter automatically handles gzip-compressed files!**

### Search Both Compressed and Uncompressed

```yaml
files:
  search_root: test-logs/
  include_patterns:
    - "*.log"
    - "*.log.gz"
```

This searches both regular `.log` files and `.gz` compressed files.

---

## Step 4: Multi-Worker Processing (3 minutes)

### Understanding Workers

Workers process files in parallel. More workers = faster processing (up to CPU limit).

### Configure Worker Count

For 4 CPU cores, use 4-8 workers:

```yaml
# config.yaml
processing:
  max_workers: 4

files:
  search_root: test-logs/
  include_patterns:
    - "*.log"

search:
  expression: "ERROR"
```

### Performance Comparison

Test different worker counts:

```bash
# 1 worker (sequential)
time log-filter --expr "ERROR" --input test-logs/ --workers 1

# 4 workers (parallel)
time log-filter --expr "ERROR" --input test-logs/ --workers 4

# 8 workers (maximum parallelism)
time log-filter --expr "ERROR" --input test-logs/ --workers 8
```

### Auto-detect Optimal Workers

Use CPU count automatically:

```yaml
processing:
  max_workers: auto  # Uses os.cpu_count()
```

Or in Python:

```python
import os

workers = os.cpu_count() or 4
config = ProcessingConfig(max_workers=workers)
```

---

## Step 5: Advanced Output Options (3 minutes)

### Highlight Matching Terms

Highlight search terms in output:

```bash
log-filter --expr "ERROR" --input test-logs/ --highlight
```

**Output (with color):**
```
2026-01-01 09:16:00 ERROR Failed to load config
                    ^^^^^
```

### Quiet Mode

Suppress progress output:

```bash
log-filter --expr "ERROR" --input test-logs/ --quiet --output errors.txt
```

No progress messages, only results in file.

### JSON Output

Export results as JSON:

```bash
log-filter --expr "ERROR" --input test-logs/ --format json --output errors.json
```

**errors.json:**
```json
[
  {
    "timestamp": "2026-01-01T09:16:00",
    "level": "ERROR",
    "message": "Failed to load config",
    "file": "test-logs/app-2026-01-01.log",
    "line": 2
  },
  {
    "timestamp": "2026-01-01T18:45:00",
    "level": "ERROR",
    "message": "Database connection lost",
    "file": "test-logs/app-2026-01-01.log",
    "line": 5
  }
]
```

### CSV Output

Export as CSV for analysis:

```bash
log-filter --expr "ERROR" --input test-logs/ --format csv --output errors.csv
```

**errors.csv:**
```text
timestamp,level,message,file,line
2026-01-01T09:16:00,ERROR,Failed to load config,test-logs/app-2026-01-01.log,2
2026-01-01T18:45:00,ERROR,Database connection lost,test-logs/app-2026-01-01.log,5
```

---

## Step 6: Real-World Configuration (3 minutes)

### Production Configuration Example

```yaml
# production-config.yaml
search:
  expression: "(ERROR OR CRITICAL) AND NOT health-check"
  case_sensitive: false

files:
  search_root: /var/log/myapp
  include_patterns:
    - "application-*.log"
    - "application-*.log.gz"
  exclude_patterns:
    - "*.old"
    - "*.backup"
    - "*debug*.log"
  max_depth: 3  # Don't recurse too deep

output:
  output_file: /var/log/filtered/errors-{date}.txt
  show_stats: true
  quiet: false

processing:
  max_workers: 8
  buffer_size: 32768  # 32 KB chunks

logging:
  level: INFO
  file: /var/log/log-filter/app.log
```

### Development Configuration

```yaml
# dev-config.yaml
search:
  expression: "ERROR OR WARNING OR CRITICAL"
  case_sensitive: false

files:
  search_root: ./logs
  include_patterns:
    - "*.log"

output:
  output_file: filtered-logs.txt
  show_stats: true
  highlight: true

processing:
  max_workers: 2  # Light on resources

logging:
  level: DEBUG  # Verbose for debugging
```

---

## Step 7: Performance Tuning (2 minutes)

### Buffer Size Optimization

For many small files:

```yaml
processing:
  buffer_size: 4096  # 4 KB
```

For large files:

```yaml
processing:
  buffer_size: 65536  # 64 KB
```

### Worker Configuration by Workload

**I/O-Bound** (many small files on HDD):

```yaml
processing:
  max_workers: 8  # 2× CPU count
  buffer_size: 8192
```

**CPU-Bound** (complex expressions):

```yaml
processing:
  max_workers: 4  # = CPU count
  buffer_size: 16384
```

**Memory-Constrained**:

```yaml
processing:
  max_workers: 2  # Minimal workers
  buffer_size: 4096
```

### Monitor Performance

Add statistics to see throughput:

```bash
log-filter --expr "ERROR" --input test-logs/ --stats
```

**Output:**
```
Performance:
  Time:          0.15s
  Throughput:    266 records/sec
  Speed:         0.12 MB/sec
```

If throughput is low:
- Increase workers (if CPU idle)
- Increase buffer size
- Check storage speed
- Simplify expression

---

## Practice Exercises

### Exercise 1: Multi-Day Search

Search for database errors from Jan 1-2 during working hours:

```bash
log-filter --expr "ERROR AND database" \
  --input test-logs/ \
  --start-date "2026-01-01" \
  --end-date "2026-01-02" \
  --start-time "08:00:00" \
  --end-time "18:00:00"
```

<details>
<summary>Expected Output (Click to reveal)</summary>

```
2026-01-01 09:16:00 ERROR Failed to load config
2026-01-01 15:00:00 ERROR Connection pool exhausted
2026-01-02 16:30:00 ERROR Deadlock detected
```
</details>

### Exercise 2: Exclude Pattern

Search all logs except database logs:

<details>
<summary>Solution (Click to reveal)</summary>

```yaml
# config.yaml
files:
  search_root: test-logs/
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "db-*.log"
```

```bash
log-filter --expr "ERROR" --config config.yaml
```
</details>

### Exercise 3: Performance Comparison

Compare single-worker vs multi-worker performance:

```bash
# Single worker
time log-filter --expr "ERROR" --input test-logs/ --workers 1

# Multi worker
time log-filter --expr "ERROR" --input test-logs/ --workers 4
```

Which is faster? Why?

### Exercise 4: Complex Configuration

Create a config that:
- Searches for ERROR or CRITICAL
- Only in application logs
- From Jan 1-2
- During 9 AM - 5 PM
- Output to JSON
- Use 4 workers

<details>
<summary>Solution (Click to reveal)</summary>

```yaml
# exercise-config.yaml
search:
  expression: "ERROR OR CRITICAL"
  start_date: "2026-01-01"
  end_date: "2026-01-02"
  start_time: "09:00:00"
  end_time: "17:00:00"

files:
  search_root: test-logs/
  include_patterns:
    - "app-*.log"

output:
  output_file: results.json
  format: json
  show_stats: true

processing:
  max_workers: 4
```

```bash
log-filter --config exercise-config.yaml
```
</details>

---

## Common Intermediate Mistakes

### ❌ Mistake 1: Too Many Workers

```yaml
# On a 4-core system
processing:
  max_workers: 32  # Overkill!
```

**Problem:** Context switching overhead reduces performance.  
**Solution:** Use 1-2× CPU count.

### ❌ Mistake 2: Wrong Date Format

```bash
# Wrong format
--start-date "01/01/2026"

# Correct format
--start-date "2026-01-01"
```

**Format:** Always use `YYYY-MM-DD`

### ❌ Mistake 3: Forgetting Include Pattern

```yaml
files:
  search_root: test-logs/
  exclude_patterns:
    - "*.old"
  # Missing include_patterns!
```

**Problem:** No files will match.  
**Solution:** Always specify include patterns.

---

## Configuration Templates

### Template 1: Daily Error Report

```yaml
# daily-errors.yaml
search:
  expression: "ERROR OR CRITICAL"
  start_date: "{yesterday}"
  end_date: "{yesterday}"

files:
  search_root: /var/log/app
  include_patterns:
    - "*.log"
    - "*.log.gz"

output:
  output_file: /reports/errors-{date}.txt
  show_stats: true

processing:
  max_workers: 4
```

### Template 2: Performance Monitoring

```yaml
# perf-monitor.yaml
search:
  expression: "slow OR timeout OR latency"
  start_time: "00:00:00"
  end_time: "23:59:59"

files:
  search_root: /var/log/app
  include_patterns:
    - "application-*.log"

output:
  output_file: performance-issues.txt
  show_stats: true

processing:
  max_workers: 8
  buffer_size: 32768
```

### Template 3: Security Audit

```yaml
# security-audit.yaml
search:
  expression: "authentication OR authorization OR security OR injection"
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "auth.log"
    - "access.log"
    - "application*.log"

output:
  output_file: security-audit-{date}.txt
  format: json
  show_stats: true

processing:
  max_workers: 4
```

---

## Quick Reference: Advanced Options

### Date/Time Options

| Option | Format | Example |
|--------|--------|---------|
| `--start-date` | YYYY-MM-DD | `2026-01-01` |
| `--end-date` | YYYY-MM-DD | `2026-01-31` |
| `--start-time` | HH:MM:SS | `09:00:00` |
| `--end-time` | HH:MM:SS | `17:00:00` |

### File Pattern Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--include` | Include pattern | `"*.log"` |
| `--exclude` | Exclude pattern | `"*.old"` |
| `--max-depth` | Recursion depth | `3` |

### Processing Options

| Option | Default | Recommended |
|--------|---------|-------------|
| `--workers` | 4 | CPU count × 1-2 |
| `--buffer-size` | 8192 | 4096-65536 |

### Output Options

| Option | Purpose |
|--------|---------|
| `--format` | Output format (text, json, csv) |
| `--highlight` | Highlight matches |
| `--quiet` | Suppress progress |

---

## What's Next?

Congratulations! You've mastered intermediate log filtering. 🎉

### You learned:
- ✅ Date and time range filtering
- ✅ Multi-file processing with patterns
- ✅ Compressed file handling
- ✅ Multi-worker configuration
- ✅ Advanced output formatting
- ✅ Performance tuning basics

### Next Steps:

1. **[Advanced Tutorial](advanced.md)** - Master:
   - Complex expression patterns
   - Large file processing (GB+)
   - Custom Python integration
   - Production deployment strategies

2. **[Docker Tutorial](docker.md)** - Learn:
   - Docker container deployment
   - Volume mounting
   - Resource limits

3. **[Integration Guide](../integration_guide.md)** - Integrate with:
   - CI/CD pipelines
   - Monitoring systems
   - Cloud platforms

---

## Additional Resources

- [Advanced Usage Guide](../advanced_usage.md)
- [Configuration Reference](../configuration.md)
- [Performance Tuning](../performance.md)
- [Error Handling](../error_handling.md)

---

**Tutorial Version:** 1.0  
**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
