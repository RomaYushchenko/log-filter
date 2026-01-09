# CLI Reference Card

**Quick reference for log-filter command-line interface**  
**Version:** 2.0.0  
**Last Updated:** January 8, 2026

---

## Table of Contents

- [Basic Usage](#basic-usage)
- [Search Options](#search-options)
- [File Selection](#file-selection)
- [Output Options](#output-options)
- [Processing Options](#processing-options)
- [Filtering Options](#filtering-options)
- [Display Options](#display-options)
- [Examples](#examples)
- [Exit Codes](#exit-codes)

---

## Basic Usage

```bash
log-filter [OPTIONS] [EXPRESSION] [FILES...]
```

**Simplest form:**
```bash
log-filter "ERROR" /var/log/app.log
```

**With configuration file:**
```bash
log-filter --config config.yaml
```

---

## Search Options

### Expression

```bash
log-filter "ERROR"                    # Simple term
log-filter "ERROR OR WARNING"         # Boolean OR
log-filter "ERROR AND database"       # Boolean AND
log-filter "NOT success"              # Boolean NOT
log-filter "(ERROR OR CRITICAL) AND NOT test"  # Complex
```

**Syntax:**
- `AND` - Both terms must match
- `OR` - Either term must match
- `NOT` - Term must not match
- `( )` - Grouping
- `"quoted strings"` - Exact phrases

### Case Sensitivity

```bash
--case-sensitive          # Case-sensitive matching (default: false)
```

**Examples:**
```bash
log-filter "error"                    # Matches: error, Error, ERROR
log-filter "error" --case-sensitive   # Matches: error only
```

---

## File Selection

### Input Specification

```bash
-i, --input <path>        # Input file or directory
FILES...                  # Files as positional arguments
```

**Examples:**
```bash
log-filter "ERROR" /var/log/app.log              # Single file
log-filter "ERROR" /var/log                      # Directory
log-filter "ERROR" file1.log file2.log file3.log # Multiple files
log-filter "ERROR" -i /var/log -i /tmp/logs      # Multiple directories
```

### Pattern Matching

```bash
--include <pattern>       # Include files matching pattern
--exclude <pattern>       # Exclude files matching pattern
```

**Examples:**
```bash
# Include only .log files
log-filter "ERROR" /var/log --include "*.log"

# Exclude test logs
log-filter "ERROR" /var/log --exclude "*test*.log"

# Multiple patterns
log-filter "ERROR" /var/log \
  --include "*.log" \
  --include "*.txt" \
  --exclude "*debug*"
```

### Recursive Scanning

```bash
-r, --recursive           # Scan directories recursively (default: true)
--no-recursive            # Don't scan subdirectories
```

**Examples:**
```bash
log-filter "ERROR" /var/log              # Recursive by default
log-filter "ERROR" /var/log --no-recursive  # Top-level only
```

---

## Output Options

### Output Destination

```bash
-o, --output <file>       # Write results to file (default: stdout)
```

**Examples:**
```bash
log-filter "ERROR" app.log                   # Print to stdout
log-filter "ERROR" app.log -o errors.txt     # Write to file
log-filter "ERROR" app.log > errors.txt      # Shell redirection
```

### Output Format

```bash
--format <format>         # Output format: text, json, csv
```

**Examples:**
```bash
# Text format (default)
log-filter "ERROR" app.log --format text

# JSON format (for tools)
log-filter "ERROR" app.log --format json
# Output: {"content": "...", "line": 123, "file": "..."}

# CSV format (for spreadsheets)
log-filter "ERROR" app.log --format csv
# Output: timestamp,file,line,content
```

### Context Lines

```bash
-B, --before-context <n>  # Include N lines before match
-A, --after-context <n>   # Include N lines after match
-C, --context <n>         # Include N lines before and after
```

**Examples:**
```bash
# Show 3 lines before each match
log-filter "ERROR" app.log -B 3

# Show 2 lines after each match
log-filter "ERROR" app.log -A 2

# Show 5 lines before and after (10 total + match)
log-filter "ERROR" app.log -C 5
```

---

## Processing Options

### Worker Threads

```bash
-w, --workers <count>     # Number of worker threads (default: auto)
```

**Examples:**
```bash
log-filter "ERROR" /var/log -w 1     # Single-threaded
log-filter "ERROR" /var/log -w 4     # 4 workers
log-filter "ERROR" /var/log -w 16    # 16 workers
log-filter "ERROR" /var/log          # Auto-detect CPU count
```

**Guidelines:**
- **CPU-bound**: workers = CPU cores
- **I/O-bound**: workers = 2 × CPU cores
- **Mixed**: workers = 1.5 × CPU cores

### Buffer Size

```bash
--buffer-size <bytes>     # Output buffer size (default: 8192)
```

**Examples:**
```bash
log-filter "ERROR" /var/log --buffer-size 4096    # 4 KB (low memory)
log-filter "ERROR" /var/log --buffer-size 8192    # 8 KB (default)
log-filter "ERROR" /var/log --buffer-size 65536   # 64 KB (high performance)
```

---

## Filtering Options

### Date Range

```bash
--start-date <date>       # Start date (YYYY-MM-DD)
--end-date <date>         # End date (YYYY-MM-DD)
```

**Examples:**
```bash
# Single day
log-filter "ERROR" /var/log \
  --start-date 2026-01-08 \
  --end-date 2026-01-08

# Date range
log-filter "ERROR" /var/log \
  --start-date 2026-01-01 \
  --end-date 2026-01-31

# From date onwards
log-filter "ERROR" /var/log --start-date 2026-01-01
```

### Time Range

```bash
--start-time <time>       # Start time (HH:MM:SS)
--end-time <time>         # End time (HH:MM:SS)
```

**Examples:**
```bash
# Business hours
log-filter "ERROR" /var/log \
  --start-time 09:00:00 \
  --end-time 17:00:00

# Night hours
log-filter "ERROR" /var/log \
  --start-time 22:00:00 \
  --end-time 06:00:00
```

### Relative Time

```bash
--since <duration>        # Process logs from duration ago
--until <duration>        # Process logs until duration ago
```

**Duration format:** `<number><unit>` where unit is `s`, `m`, `h`, `d`

**Examples:**
```bash
log-filter "ERROR" /var/log --since 1h      # Last hour
log-filter "ERROR" /var/log --since 30m     # Last 30 minutes
log-filter "ERROR" /var/log --since 7d      # Last 7 days
log-filter "ERROR" /var/log --since 1h --until 30m  # Between 1h and 30m ago
```

---

## Display Options

### Verbosity

```bash
-v, --verbose             # Increase verbosity (can be repeated)
-q, --quiet               # Suppress non-error output
```

**Examples:**
```bash
log-filter "ERROR" app.log -q          # Quiet (only results)
log-filter "ERROR" app.log             # Normal
log-filter "ERROR" app.log -v          # Verbose (show progress)
log-filter "ERROR" app.log -vv         # Very verbose (debug info)
```

### Statistics

```bash
--stats                   # Show processing statistics
--no-stats                # Don't show statistics
```

**Examples:**
```bash
log-filter "ERROR" app.log --stats

# Output:
# ================================================================================
# Processing Statistics
# ================================================================================
# Files:
#   Processed:     10
#   Matched:       8 (80.0%)
# 
# Records:
#   Total:         1,234,567
#   Matched:       12,345 (1.0%)
# 
# Performance:
#   Time:          5.2s
#   Throughput:    237,417 records/sec
# ================================================================================
```

### Highlighting

```bash
--highlight               # Highlight matching terms
--no-highlight            # Don't highlight
```

**Examples:**
```bash
log-filter "ERROR" app.log --highlight     # Colorize matches
```

### Progress Bar

```bash
--progress                # Show progress bar
--no-progress             # Don't show progress bar
```

---

## Configuration File

### Load Configuration

```bash
-c, --config <file>       # Load configuration from file
```

**Supported formats:** YAML, JSON

**Example:**
```bash
log-filter --config config.yaml
```

**Configuration file (`config.yaml`):**
```yaml
search:
  expression: "ERROR OR CRITICAL"
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*debug*.log"

output:
  output_file: errors.txt
  show_stats: true

processing:
  max_workers: 8
  buffer_size: 8192
```

---

## Examples

### Basic Search

```bash
# Find all ERROR messages
log-filter "ERROR" /var/log/app.log

# Find ERROR or WARNING
log-filter "ERROR OR WARNING" /var/log/app.log

# Find ERROR but not in test logs
log-filter "ERROR NOT test" /var/log
```

### Advanced Search

```bash
# Complex expression
log-filter "(ERROR OR CRITICAL) AND (database OR connection)" /var/log

# With case sensitivity
log-filter "Error" /var/log --case-sensitive

# With date range
log-filter "ERROR" /var/log \
  --start-date 2026-01-01 \
  --end-date 2026-01-31

# Recent errors
log-filter "ERROR" /var/log --since 1h
```

### File Selection

```bash
# Only .log files
log-filter "ERROR" /var/log --include "*.log"

# Exclude test logs
log-filter "ERROR" /var/log --exclude "*test*"

# Multiple directories
log-filter "ERROR" /var/log /tmp/logs /opt/app/logs
```

### Output Control

```bash
# Save to file
log-filter "ERROR" /var/log -o errors.txt

# JSON output
log-filter "ERROR" /var/log --format json -o errors.json

# With context
log-filter "ERROR" /var/log -C 3 -o errors-with-context.txt

# Quiet mode
log-filter "ERROR" /var/log -q -o errors.txt
```

### Performance Tuning

```bash
# High performance (fast storage, powerful CPU)
log-filter "ERROR" /var/log -w 16 --buffer-size 65536

# Low memory (limited RAM)
log-filter "ERROR" /var/log -w 2 --buffer-size 4096

# Network storage (I/O bound)
log-filter "ERROR" /mnt/network/logs -w 8 --buffer-size 32768
```

### Pipeline Integration

```bash
# Pipe to other tools
log-filter "ERROR" /var/log | grep -i "database"

# Count matches
log-filter "ERROR" /var/log | wc -l

# With grep for further filtering
log-filter "ERROR" /var/log | grep "payment" | sort | uniq

# To mail
log-filter "CRITICAL" /var/log --since 5m | mail -s "Critical Errors" admin@example.com
```

---

## Exit Codes

```bash
0   # Success (matches found or no errors)
1   # Error (configuration error, file not found, etc.)
2   # No matches found (when --require-matches is set)
```

**Examples:**
```bash
# Check if errors exist
if log-filter "ERROR" /var/log -q; then
  echo "Errors found!"
else
  echo "No errors"
fi

# Fail if no matches
log-filter "ERROR" /var/log --require-matches || echo "No errors found"
```

---

## Environment Variables

```bash
LOG_FILTER_CONFIG      # Default configuration file
LOG_FILTER_WORKERS     # Default worker count
LOG_FILTER_BUFFER_SIZE # Default buffer size
```

**Examples:**
```bash
# Set defaults
export LOG_FILTER_CONFIG=/etc/log-filter/config.yaml
export LOG_FILTER_WORKERS=8

# Run with defaults
log-filter "ERROR" /var/log
```

---

## Common Patterns

### Daily Error Report

```bash
#!/bin/bash
DATE=$(date -d yesterday +%Y-%m-%d)
log-filter "ERROR OR CRITICAL" /var/log \
  --start-date $DATE \
  --end-date $DATE \
  --stats \
  -o /reports/errors-$DATE.txt
```

### Real-Time Monitoring

```bash
# Monitor last 5 minutes, check every minute
watch -n 60 'log-filter "ERROR" /var/log --since 5m | tail -20'
```

### Performance Analysis

```bash
# Find slow queries
log-filter "slow query" /var/log/mysql \
  --since 1h \
  --format json \
  -o slow-queries.json
```

### Security Audit

```bash
# Find failed login attempts
log-filter "failed login OR authentication failed" /var/log \
  --since 24h \
  --stats \
  -o security-events.txt
```

---

## Tips & Tricks

### Performance

1. **Use specific patterns** - `"ERROR AND database"` is faster than `"ERROR"`
2. **Limit date range** - Use `--start-date` and `--end-date` when possible
3. **Tune workers** - Match your workload type (CPU vs I/O bound)
4. **Increase buffer** - Use larger buffers for high throughput

### Debugging

1. **Use --verbose** - See what's happening: `log-filter "ERROR" -vv`
2. **Test expression** - Use small file first: `log-filter "expr" test.log`
3. **Check stats** - Use `--stats` to see performance metrics

### Automation

1. **Use config files** - Easier to maintain and version control
2. **Set environment variables** - Consistent defaults across scripts
3. **Check exit codes** - Handle errors appropriately in scripts

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Simple search | `log-filter "ERROR" file.log` |
| Boolean search | `log-filter "ERROR OR WARNING" file.log` |
| Save to file | `log-filter "ERROR" file.log -o output.txt` |
| Multiple files | `log-filter "ERROR" file1.log file2.log` |
| Directory scan | `log-filter "ERROR" /var/log` |
| Date range | `log-filter "ERROR" /var/log --start-date 2026-01-01` |
| Last hour | `log-filter "ERROR" /var/log --since 1h` |
| With context | `log-filter "ERROR" file.log -C 3` |
| JSON output | `log-filter "ERROR" file.log --format json` |
| High performance | `log-filter "ERROR" /var/log -w 16 --buffer-size 65536` |
| Quiet mode | `log-filter "ERROR" file.log -q` |
| With stats | `log-filter "ERROR" file.log --stats` |
| Config file | `log-filter --config config.yaml` |

---

## See Also

- **[Quickstart Guide](../quickstart.md)** - Getting started tutorial
- **[Configuration Reference](config_reference.md)** - Complete configuration options
- **[Examples](../examples/README.md)** - Real-world usage examples
- **[API Documentation](../api/index.rst)** - Python API reference

---

**Version:** 2.0  
**Last Updated:** January 8, 2026  
**Print-Friendly:** Use your browser's print dialog to export a PDF.
