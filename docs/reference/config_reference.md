# Configuration Reference

**Complete reference for log-filter configuration files**  
**Version:** 2.0.0  
**Last Updated:** January 8, 2026

---

## Table of Contents

- [Overview](#overview)
- [Configuration Formats](#configuration-formats)
- [Configuration Structure](#configuration-structure)
- [Search Configuration](#search-configuration)
- [Files Configuration](#files-configuration)
- [Output Configuration](#output-configuration)
- [Processing Configuration](#processing-configuration)
- [Logging Configuration](#logging-configuration)
- [Complete Examples](#complete-examples)
- [Environment Variables](#environment-variables)
- [Validation Rules](#validation-rules)
- [Best Practices](#best-practices)

---

## Overview

Log Filter supports configuration via YAML or JSON files, providing a structured way to define complex filtering operations.

**Benefits of Configuration Files:**
- ✅ **Reusable** - Save and share configurations
- ✅ **Version Control** - Track changes in Git
- ✅ **Complex Expressions** - Easier to write multi-line expressions
- ✅ **Team Collaboration** - Standardize across team
- ✅ **Documentation** - Self-documenting with comments

**Basic Usage:**
```bash
log-filter --config config.yaml
log-filter -c config.json
```

---

## Configuration Formats

### YAML Format (Recommended)

**File:** `config.yaml`

```yaml
# Search configuration
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

# File selection
files:
  path: /var/log
  include_patterns:
    - "*.log"
    - "*.txt"
  exclude_patterns:
    - "*debug*.log"
    - "*test*.log"
  recursive: true

# Output settings
output:
  output_file: filtered-logs.txt
  format: text
  show_stats: true
  quiet: false

# Processing configuration
processing:
  max_workers: 8
  buffer_size: 8192
  chunk_size: 1000

# Logging configuration
logging:
  level: INFO
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

### JSON Format

**File:** `config.json`

```json
{
  "search": {
    "expression": "ERROR OR CRITICAL",
    "ignore_case": false
  },
  "files": {
    "search_root": "/var/log",
    "include_patterns": ["*.log", "*.txt"],
    "exclude_patterns": ["*debug*.log", "*test*.log"],
    "recursive": true
  },
  "output": {
    "output_file": "filtered-logs.txt",
    "format": "text",
    "show_stats": true,
    "quiet": false
  },
  "processing": {
    "max_workers": 8,
    "buffer_size": 8192,
    "chunk_size": 1000
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  }
}
```

---

## Configuration Structure

### Top-Level Sections

```yaml
search:       # Search expression and matching behavior
files:        # File selection and scanning
output:       # Output destination and formatting
processing:   # Performance and processing behavior
logging:      # Application logging configuration
filters:      # Optional: Date/time filtering
```

**Section Dependencies:**
```
search    → Required
files     → Required
output    → Optional (defaults to stdout)
processing → Optional (auto-detected defaults)
logging   → Optional (default: INFO level)
filters   → Optional (no filtering by default)
```

---

## Search Configuration

### Basic Options

```yaml
search:
  expression: string    # Boolean expression (required)
  ignore_case: bool  # Case-sensitive matching (default: false)
```

#### `expression` (required)

**Type:** `string`  
**Description:** Boolean search expression

**Syntax:**
- `AND` - Both terms must match
- `OR` - Either term must match
- `NOT` - Term must not match
- `( )` - Grouping for precedence
- `"quoted"` - Exact phrase matching

**Examples:**
```yaml
# Simple term
expression: "ERROR"

# Boolean OR
expression: "ERROR OR WARNING"

# Boolean AND
expression: "ERROR AND database"

# Complex expression
expression: "(ERROR OR CRITICAL) AND (database OR connection) AND NOT test"

# Multi-line for readability
expression: |
  (ERROR OR CRITICAL OR FATAL) AND
  (database OR connection OR timeout) AND
  NOT (test OR debug OR mock)

# Exact phrases
expression: '"database connection failed" OR "out of memory"'
```

#### `ignore_case` (optional)

**Type:** `boolean`  
**Default:** `false`  
**Description:** Enable case-sensitive matching

**Examples:**
```yaml
# Case-insensitive (default)
search:
  expression: "error"
  ignore_case: false
# Matches: error, Error, ERROR, eRRoR

# Case-sensitive
search:
  expression: "Error"
  ignore_case: true
# Matches: Error only
```

---

## Files Configuration

### Basic Options

```yaml
files:
  path: string | list       # Root directory/directories (required)
  include_patterns: list           # Include file patterns (optional)
  exclude_patterns: list           # Exclude file patterns (optional)
  recursive: bool                  # Recursive scanning (default: true)
  follow_symlinks: bool            # Follow symbolic links (default: false)
  max_depth: int                   # Maximum directory depth (optional)
```

#### `search_root` (required)

**Type:** `string` or `list[string]`  
**Description:** Root directory or directories to scan

**Examples:**
```yaml
# Single directory
files:
  path: /var/log

# Multiple directories
files:
  path:
    - /var/log
    - /tmp/logs
    - /opt/app/logs

# Absolute and relative paths
files:
  path:
    - /var/log        # Absolute
    - ./logs          # Relative
    - ~/application/logs  # Home directory
```

#### `include_patterns` (optional)

**Type:** `list[string]`  
**Default:** `["*"]` (all files)  
**Description:** Glob patterns for files to include

**Pattern Syntax:**
- `*` - Matches any characters
- `?` - Matches single character
- `[abc]` - Matches a, b, or c
- `[!abc]` - Matches any except a, b, c

**Examples:**
```yaml
# Include only .log files
files:
  include_patterns:
    - "*.log"

# Multiple extensions
files:
  include_patterns:
    - "*.log"
    - "*.txt"
    - "*.out"

# Specific file names
files:
  include_patterns:
    - "application.log"
    - "error.log"
    - "access.log"

# Pattern matching
files:
  include_patterns:
    - "app-*.log"      # app-2026-01-08.log
    - "server-?.log"   # server-1.log, server-2.log
    - "log.[0-9]"      # log.1, log.2, ...
```

#### `exclude_patterns` (optional)

**Type:** `list[string]`  
**Default:** `[]` (no exclusions)  
**Description:** Glob patterns for files to exclude

**Examples:**
```yaml
# Exclude debug logs
files:
  exclude_patterns:
    - "*debug*.log"

# Exclude multiple patterns
files:
  exclude_patterns:
    - "*debug*.log"
    - "*test*.log"
    - "*.tmp"
    - ".*.swp"

# Exclude by directory
files:
  exclude_patterns:
    - "*/old/*"
    - "*/archive/*"
    - "*/backup/*"
```

#### `recursive` (optional)

**Type:** `boolean`  
**Default:** `true`  
**Description:** Enable recursive directory scanning

**Examples:**
```yaml
# Recursive (default)
files:
  recursive: true
  # Scans: /var/log, /var/log/app, /var/log/app/2026, ...

# Non-recursive
files:
  recursive: false
  # Scans: /var/log only (not subdirectories)
```

#### `follow_symlinks` (optional)

**Type:** `boolean`  
**Default:** `false`  
**Description:** Follow symbolic links during scanning

**Examples:**
```yaml
# Don't follow symlinks (default)
files:
  follow_symlinks: false

# Follow symlinks
files:
  follow_symlinks: true
  # Warning: Can cause infinite loops if circular links exist
```

#### `max_depth` (optional)

**Type:** `integer`  
**Default:** `null` (unlimited)  
**Description:** Maximum directory depth to scan

**Examples:**
```yaml
# Limit to 2 levels deep
files:
  max_depth: 2
  # Scans: /var/log and /var/log/app but not /var/log/app/2026

# Only top level
files:
  max_depth: 1
```

---

## Output Configuration

### Basic Options

```yaml
output:
  output_file: string            # Output file path (optional)
  format: string                 # Output format (default: "text")
  show_stats: bool               # Show statistics (default: true)
  quiet: bool                    # Suppress output (default: false)
  append: bool                   # Append to file (default: false)
  include_context: int           # Context lines (optional)
  highlight: bool                # Highlight matches (default: false)
```

#### `output_file` (optional)

**Type:** `string`  
**Default:** `null` (stdout)  
**Description:** Path to output file

**Examples:**
```yaml
# Write to file
output:
  output_file: results.txt

# Absolute path
output:
  output_file: /tmp/filtered-logs.txt

# Relative path
output:
  output_file: ./output/errors.log

# With timestamp
output:
  output_file: "errors-{timestamp}.txt"
  # Expands to: errors-2026-01-08_14-30-00.txt

# With date
output:
  output_file: "errors-{date}.txt"
  # Expands to: errors-2026-01-08.txt
```

#### `format` (optional)

**Type:** `string`  
**Default:** `"text"`  
**Options:** `text`, `json`, `csv`  
**Description:** Output format

**Examples:**
```yaml
# Text format (default)
output:
  format: text
# Output: Raw log lines

# JSON format
output:
  format: json
# Output:
# {"content": "2026-01-08 ERROR ...", "line": 123, "file": "/var/log/app.log"}
# {"content": "2026-01-08 ERROR ...", "line": 456, "file": "/var/log/app.log"}

# CSV format
output:
  format: csv
# Output:
# timestamp,file,line,content
# 2026-01-08T10:00:00,/var/log/app.log,123,"ERROR: database timeout"
```

#### `show_stats` (optional)

**Type:** `boolean`  
**Default:** `true`  
**Description:** Show processing statistics after completion

**Examples:**
```yaml
# Show statistics (default)
output:
  show_stats: true
# Displays:
# ================================================================================
# Processing Statistics
# ================================================================================
# ...

# Hide statistics
output:
  show_stats: false
```

#### `quiet` (optional)

**Type:** `boolean`  
**Default:** `false`  
**Description:** Suppress all non-result output

**Examples:**
```yaml
# Normal output
output:
  quiet: false

# Quiet mode (only results)
output:
  quiet: true
```

#### `append` (optional)

**Type:** `boolean`  
**Default:** `false`  
**Description:** Append to output file instead of overwriting

**Examples:**
```yaml
# Overwrite (default)
output:
  output_file: results.txt
  append: false

# Append to existing file
output:
  output_file: results.txt
  append: true
```

#### `include_context` (optional)

**Type:** `integer`  
**Default:** `0` (no context)  
**Description:** Number of context lines before and after each match

**Examples:**
```yaml
# No context (default)
output:
  include_context: 0

# 3 lines before and after
output:
  include_context: 3
# Shows: 3 lines before match + match + 3 lines after

# 5 lines context
output:
  include_context: 5
```

#### `highlight` (optional)

**Type:** `boolean`  
**Default:** `false`  
**Description:** Highlight matching terms in output

**Examples:**
```yaml
# No highlighting (default)
output:
  highlight: false

# Highlight matches
output:
  highlight: true
  # Colorizes matching terms in terminal output
```

---

## Processing Configuration

### Basic Options

```yaml
processing:
  max_workers: int              # Worker thread count (default: auto)
  buffer_size: int              # Output buffer size (default: 8192)
  chunk_size: int               # Records per chunk (default: 1000)
  timeout: int                  # Processing timeout (optional)
```

#### `max_workers` (optional)

**Type:** `integer`  
**Default:** `null` (auto-detect CPU count)  
**Range:** `1` to `64`  
**Description:** Number of parallel worker threads

**Guidelines:**
- **CPU-bound**: Set to CPU core count
- **I/O-bound**: Set to 2× CPU core count
- **Mixed workload**: Set to 1.5× CPU core count
- **Low memory**: Use fewer workers (1-2)

**Examples:**
```yaml
# Auto-detect (default)
processing:
  max_workers: null

# Single-threaded
processing:
  max_workers: 1

# Fixed worker count
processing:
  max_workers: 8

# High throughput
processing:
  max_workers: 16
```

#### `buffer_size` (optional)

**Type:** `integer`  
**Default:** `8192` (8 KB)  
**Range:** `1024` to `1048576` (1 KB to 1 MB)  
**Description:** Output buffer size in bytes

**Guidelines:**
- **Low memory**: 4096 (4 KB)
- **Default**: 8192 (8 KB)
- **High performance**: 65536 (64 KB)
- **Network storage**: 32768 (32 KB)

**Examples:**
```yaml
# Small buffer (low memory)
processing:
  buffer_size: 4096

# Default buffer
processing:
  buffer_size: 8192

# Large buffer (high performance)
processing:
  buffer_size: 65536
```

#### `chunk_size` (optional)

**Type:** `integer`  
**Default:** `1000`  
**Range:** `100` to `100000`  
**Description:** Number of records processed per chunk

**Examples:**
```yaml
# Small chunks (low memory)
processing:
  chunk_size: 100

# Default
processing:
  chunk_size: 1000

# Large chunks (high throughput)
processing:
  chunk_size: 10000
```

#### `timeout` (optional)

**Type:** `integer`  
**Default:** `null` (no timeout)  
**Unit:** seconds  
**Description:** Maximum processing time

**Examples:**
```yaml
# No timeout (default)
processing:
  timeout: null

# 5 minute timeout
processing:
  timeout: 300

# 1 hour timeout
processing:
  timeout: 3600
```

---

## Logging Configuration

### Basic Options

```yaml
logging:
  level: string                 # Log level (default: "INFO")
  format: string                # Log format (optional)
  file: string                  # Log file path (optional)
```

#### `level` (optional)

**Type:** `string`  
**Default:** `"INFO"`  
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Description:** Logging level

**Examples:**
```yaml
# Default level
logging:
  level: INFO

# Debug level (verbose)
logging:
  level: DEBUG

# Only errors
logging:
  level: ERROR
```

#### `format` (optional)

**Type:** `string`  
**Default:** `"%(levelname)s: %(message)s"`  
**Description:** Python logging format string

**Examples:**
```yaml
# Simple format (default)
logging:
  format: "%(levelname)s: %(message)s"

# With timestamp
logging:
  format: "%(asctime)s - %(levelname)s - %(message)s"

# Detailed format
logging:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
```

#### `file` (optional)

**Type:** `string`  
**Default:** `null` (stderr)  
**Description:** Path to log file

**Examples:**
```yaml
# Log to stderr (default)
logging:
  file: null

# Log to file
logging:
  file: /var/log/log-filter.log

# Relative path
logging:
  file: ./log-filter.log
```

---

## Complete Examples

### Example 1: Production Error Monitoring

```yaml
# production-errors.yaml
search:
  expression: |
    (ERROR OR CRITICAL OR FATAL) AND
    NOT (test OR debug OR mock)
  ignore_case: false

files:
  path: /var/log/production
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*debug*.log"
    - "*test*.log"
  recursive: true

output:
  output_file: /monitoring/errors-{date}.txt
  format: json
  show_stats: true
  include_context: 3

processing:
  max_workers: 8
  buffer_size: 32768

logging:
  level: INFO
  format: "%(asctime)s - %(levelname)s - %(message)s"
  file: /var/log/log-filter.log
```

### Example 2: Development Debugging

```yaml
# development-debug.yaml
search:
  expression: "ERROR OR WARNING"
  ignore_case: false

files:
  path: ./logs
  include_patterns:
    - "*.log"
    - "*.txt"
  recursive: true

output:
  output_file: debug-errors.txt
  format: text
  show_stats: true
  highlight: true
  include_context: 5

processing:
  max_workers: 2
  buffer_size: 4096

logging:
  level: DEBUG
```

### Example 3: Security Audit

```yaml
# security-audit.yaml
search:
  expression: |
    (
      (authentication OR auth OR login) AND
      (failed OR denied OR invalid)
    ) OR
    (
      (authorization OR access) AND
      (forbidden OR denied)
    ) OR
    (sql AND injection) OR
    (xss OR csrf)
  ignore_case: false

files:
  path:
    - /var/log/auth
    - /var/log/security
    - /var/log/app
  include_patterns:
    - "*.log"
    - "auth.log"
    - "security.log"
  recursive: true

output:
  output_file: /security/audit-{timestamp}.json
  format: json
  show_stats: true

processing:
  max_workers: 4
  buffer_size: 16384

logging:
  level: INFO
  file: /var/log/security-audit.log
```

### Example 4: Performance Analysis

```yaml
# performance-analysis.yaml
search:
  expression: |
    (slow OR latency OR timeout) AND
    (query OR request OR response)
  ignore_case: false

files:
  path: /var/log/app
  include_patterns:
    - "performance.log"
    - "access.log"
  recursive: false

output:
  output_file: performance-issues-{date}.csv
  format: csv
  show_stats: true

processing:
  max_workers: 4
  buffer_size: 8192

logging:
  level: WARNING
```

### Example 5: Multi-Service Log Aggregation

```yaml
# log-aggregation.yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  path:
    - /var/log/api
    - /var/log/web
    - /var/log/worker
    - /var/log/database
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*debug*"
    - "*test*"
    - "*.gz"
  recursive: true

output:
  output_file: /data/aggregated-{date}.txt
  format: text
  show_stats: true
  append: false

processing:
  max_workers: 16
  buffer_size: 65536
  chunk_size: 5000

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /var/log/aggregation.log
```

---

## Environment Variables

Configuration values can reference environment variables using `${VAR}` syntax:

```yaml
files:
  path: ${LOG_DIR}

output:
  output_file: ${OUTPUT_DIR}/errors-{date}.txt

processing:
  max_workers: ${MAX_WORKERS}
```

**Usage:**
```bash
export LOG_DIR=/var/log
export OUTPUT_DIR=/tmp/output
export MAX_WORKERS=8

log-filter --config config.yaml
```

---

## Validation Rules

### Required Fields

- `search.expression` - Must be non-empty string
- `files.search_root` - Must exist and be accessible

### Value Constraints

```yaml
processing:
  max_workers: 1-64       # Must be positive integer
  buffer_size: 1024-1048576  # 1 KB to 1 MB
  chunk_size: 100-100000   # Positive integer

logging:
  level: DEBUG|INFO|WARNING|ERROR|CRITICAL  # Must be valid level
```

### Path Validation

- All paths must be valid for the operating system
- Output directory must exist or be creatable
- Search root must be readable

---

## Best Practices

### 1. Use YAML for Readability

```yaml
# ✅ Good: Easy to read and maintain
search:
  expression: |
    (ERROR OR CRITICAL) AND
    (database OR connection) AND
    NOT test
```

### 2. Comment Your Configuration

```yaml
# Search for database errors in production logs
search:
  expression: "ERROR AND database"
  ignore_case: false  # Case-insensitive by default

# Scan production log directory
files:
  path: /var/log/production
  include_patterns:
    - "*.log"  # Only .log files
  exclude_patterns:
    - "*test*"  # Exclude test logs
```

### 3. Use Environment Variables

```yaml
# ✅ Good: Flexible across environments
files:
  path: ${LOG_DIR}

output:
  output_file: ${OUTPUT_DIR}/errors.txt
```

### 4. Organize by Purpose

Create separate configs for different use cases:
```
configs/
├── production-errors.yaml
├── development-debug.yaml
├── security-audit.yaml
└── performance-analysis.yaml
```

### 5. Version Control Configurations

```bash
git add configs/
git commit -m "Add log filtering configurations"
```

### 6. Tune for Workload

```yaml
# CPU-bound (complex expressions, fast storage)
processing:
  max_workers: 8  # Match CPU cores

# I/O-bound (network storage, slow disks)
processing:
  max_workers: 16  # 2× CPU cores
```

---

## See Also

- **[CLI Reference](cli_reference.md)** - Command-line options
- **[Quickstart Guide](../quickstart.md)** - Getting started
- **[Examples](../examples/)** - Real-world configurations
- **[Performance Guide](../performance.md)** - Optimization tips

---

**Version:** 2.0  
**Last Updated:** January 8, 2026  
**Schema:** [config-schema.json](config-schema.json)
