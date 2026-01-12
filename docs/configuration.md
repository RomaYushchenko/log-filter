# Configuration Guide

Complete reference for configuring Log Filter.

## Configuration File Locations

Log-filter searches for configuration files in these locations (in order):

### 1. Specified with --config flag (highest priority)
```bash
log-filter --config /path/to/config.yaml
```

### 2. Environment variable
```bash
# Linux/macOS
export LOG_FILTER_CONFIG=/path/to/config.yaml
log-filter

# Windows
set LOG_FILTER_CONFIG=C:\path\to\config.yaml
log-filter
```

### 3. Current directory
```bash
./config.yaml
```

### 4. User home directory
```bash
~/.log-filter/config.yaml                    # Linux/macOS
%USERPROFILE%\.log-filter\config.yaml        # Windows (typically C:\Users\YourName\.log-filter\config.yaml)
```

### 5. System directory
```bash
/etc/log-filter/config.yaml                  # Linux
C:\ProgramData\log-filter\config.yaml        # Windows
```

### Recommended Locations

**For personal use:**
```bash
# Create user config directory
mkdir -p ~/.log-filter                       # Linux/macOS
mkdir %USERPROFILE%\.log-filter              # Windows

# Copy template
cp config.yaml.template ~/.log-filter/config.yaml

# Edit
nano ~/.log-filter/config.yaml               # or vim, code, etc.
```

**For project use:**
```bash
# Keep in project directory
cp config.yaml.template ./config.yaml
git add config.yaml  # Track in version control
```

**For server/shared use:**
```bash
# System-wide configuration
sudo mkdir -p /etc/log-filter
sudo cp config.yaml.template /etc/log-filter/config.yaml
sudo nano /etc/log-filter/config.yaml
```

## Configuration Methods

Log Filter supports three configuration methods with the following precedence:

1. **Command-line arguments** (highest priority - overrides everything)
2. **Environment variables** (overrides config file)
3. **Configuration file** (lowest priority - defaults)

## Configuration File

### YAML Format

Create a `config.yaml` file:

```yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false
  date_from: "2026-01-01"
  date_to: "2026-01-31"
  time_from: "09:00:00"
  time_to: "17:00:00"

files:
  search_root: "/var/log"
  include_patterns:
    - "*.log"
    - "*.log.gz"
  exclude_patterns:
    - "*.old"
    - "*.tmp"
    - "debug.log"
  follow_symlinks: false
  max_depth: 5

output:
  output_file: "errors.txt"
  overwrite: false
  dry_run: false
  show_stats: true
  verbose: false
  quiet: false

processing:
  max_workers: 4
  buffer_size: 8192
  encoding: "utf-8"
  errors: "replace"
```

### Using Configuration File

```bash
log-filter --config config.yaml
```

### Override Config with CLI

Command-line arguments override config file:

```bash
# Use config but override expression
log-filter "CRITICAL" --config config.yaml

# Override output file
log-filter --config config.yaml -o critical.txt
```

## Search Configuration

### Expression

Boolean search expression.

```yaml
search:
  expression: "(ERROR OR WARNING) AND database"
```

**CLI**:
```bash
log-filter "(ERROR OR WARNING) AND database" /var/log
```

### Case Sensitivity

Control case-sensitive matching.

```yaml
search:
  ignore_case: false  # Default: case-insensitive
```

**CLI**:
```bash
log-filter "ERROR" /var/log -c  # Enable case-sensitive
```

### Date Range

Filter records by date.

```yaml
search:
  date_from: "2026-01-01"
  date_to: "2026-01-31"
```

**CLI**:
```bash
log-filter "ERROR" /var/log --date-from 2026-01-01 --date-to 2026-01-31
```

**Format**: `YYYY-MM-DD`

### Time Range

Filter records by time of day.

```yaml
search:
  time_from: "09:00:00"
  time_to: "17:00:00"
```

**CLI**:
```bash
log-filter "ERROR" /var/log --time-from 09:00:00 --time-to 17:00:00
```

**Format**: `HH:MM:SS`

## File Configuration

### Search Root

Root directory to search.

```yaml
files:
  search_root: "/var/log"
```

**CLI** (positional argument):
```bash
log-filter "ERROR" /var/log
```

### Include Patterns

Glob patterns for files to include.

```yaml
files:
  include_patterns:
    - "*.log"
    - "*.log.gz"
    - "app-*.txt"
```

**CLI**:
```bash
log-filter "ERROR" /var/log -i "*.log" -i "*.log.gz"
```

**Pattern Syntax**:
- `*.log` - All .log files
- `app*.log` - Files starting with "app"
- `**/*.log` - Recursive (all depths)
- `log.202[0-9]` - Character ranges

### Exclude Patterns

Glob patterns for files to exclude.

```yaml
files:
  exclude_patterns:
    - "*.old"
    - "*.tmp"
    - "debug.log"
    - "test-*.log"
```

**CLI**:
```bash
log-filter "ERROR" /var/log -e "*.old" -e "debug.log"
```

### Follow Symlinks

Whether to follow symbolic links.

```yaml
files:
  follow_symlinks: false  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --follow-symlinks
```

**Warning**: Following symlinks can cause infinite loops if circular links exist.

### Max Depth

Maximum directory depth to traverse.

```yaml
files:
  max_depth: 5  # Default: unlimited
```

**CLI**:
```bash
log-filter "ERROR" /var/log --max-depth 3
```

### Max File Size

Skip files larger than specified size (in megabytes).

```yaml
files:
  max_file_size: 100  # Skip files > 100 MB
```

**CLI**:
```bash
log-filter "ERROR" /var/log --max-file-size 100
```

### Max Record Size

Skip log records larger than specified size (in kilobytes).

```yaml
files:
  max_record_size: 512  # Skip records > 512 KB
```

**CLI**:
```bash
log-filter "ERROR" /var/log --max-record-size 512
```

## Output Configuration

### Output File

Path to output file.

```yaml
output:
  output_file: "errors.txt"
```

**CLI**:
```bash
log-filter "ERROR" /var/log -o errors.txt
```

**Note**: Omit for stdout output.

### Overwrite

Whether to overwrite existing output file.

```yaml
output:
  overwrite: false  # Default: false (error if exists)
```

**CLI**:
```bash
log-filter "ERROR" /var/log -o errors.txt --overwrite
```

### Include File Path

Include or exclude source file path in output.

```yaml
output:
  no_path: false  # Default: false (include paths)
```

**CLI**:
```bash
log-filter "ERROR" /var/log --no-path  # Exclude file paths
```

### Highlight Matches

Highlight matched text with `<<<` `>>>` markers.

```yaml
output:
  highlight: true  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --highlight
```

### Dry Run

Count matches without writing output.

```yaml
output:
  dry_run: false  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --dry-run
```

### Dry Run Details

Show detailed file statistics without processing.

```yaml
output:
  dry_run_details: false  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --dry-run-details
```

### Show Statistics

Display processing statistics.

```yaml
output:
  stats: true  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --stats
```

### Verbose/Progress

Enable verbose output with progress information.

```yaml
output:
  verbose: true  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --verbose
# or
log-filter "ERROR" /var/log --progress
```

### Quiet

Suppress non-error output.

```yaml
output:
  quiet: false  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --quiet
```

## Processing Configuration

### Max Workers

Number of worker threads.

```yaml
processing:
  max_workers: 4  # Default: CPU count
```

**CLI**:
```bash
log-filter "ERROR" /var/log -w 8
```

**Recommendations**:
- **I/O-bound** (many files): 2× CPU count
- **CPU-bound** (complex expressions): 1× CPU count
- **Large files**: Fewer workers (memory constraint)

### Buffer Size

I/O buffer size in bytes.

```yaml
processing:
  buffer_size: 8192  # Default: 8192 (8 KB)
```

**CLI**:
```bash
log-filter "ERROR" /var/log --buffer-size 65536
```

**Recommendations**:
- **Small files**: 4-8 KB
- **Large files**: 32-64 KB
- **SSD**: Larger buffers (32 KB+)
- **Network storage**: Smaller buffers (8 KB)

### Debug

Enable debug logging for troubleshooting.

```yaml
processing:
  debug: true  # Default: false
```

**CLI**:
```bash
log-filter "ERROR" /var/log --debug
```

Shows detailed information about:
- File scanning and selection
- Worker thread activity
- Expression parsing and evaluation
- Performance metrics

### Encoding

File encoding.

```yaml
processing:
  encoding: "utf-8"  # Default: utf-8
```

**CLI**:
```bash
log-filter "ERROR" /var/log --encoding utf-16
```

**Common encodings**:
- `utf-8` - Unicode (most common)
- `utf-16` - Unicode (Windows)
- `latin-1` - Western Europe
- `ascii` - ASCII only
- `cp1252` - Windows Western Europe

### Error Handling

How to handle encoding errors.

```yaml
processing:
  errors: "replace"  # Default: replace
```

**CLI**:
```bash
log-filter "ERROR" /var/log --errors ignore
```

**Options**:
- `replace` - Replace invalid chars with �
- `ignore` - Skip invalid chars
- `strict` - Raise exception on errors

## Environment Variables

Configure via environment variables:

```bash
# Worker count
export LOG_FILTER_WORKERS=8

# Encoding
export LOG_FILTER_ENCODING=utf-8

# Buffer size
export LOG_FILTER_BUFFER_SIZE=16384

# Verbose mode
export LOG_FILTER_VERBOSE=1

# Quiet mode
export LOG_FILTER_QUIET=0

# Default config file
export LOG_FILTER_CONFIG=/etc/log-filter/config.yaml
```

Use in scripts:

```bash
#!/bin/bash
export LOG_FILTER_WORKERS=8
export LOG_FILTER_VERBOSE=1

log-filter "ERROR" /var/log -o errors.txt
```

## Complete Examples

### Basic Error Monitoring

```yaml
# error-monitor.yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  search_root: "/var/log"
  include_patterns:
    - "*.log"
    - "*.log.gz"
  exclude_patterns:
    - "debug.log"

output:
  output_file: "errors.txt"
  show_stats: true
```

### Business Hours Analysis

```yaml
# business-hours.yaml
search:
  expression: "ERROR"
  time_from: "09:00:00"
  time_to: "17:00:00"

files:
  search_root: "/var/log/app"
  include_patterns:
    - "app-*.log"

output:
  output_file: "business-errors.txt"
  show_stats: true
  verbose: true

processing:
  max_workers: 4
```

### Database Log Analysis

```yaml
# database-errors.yaml
search:
  expression: "(ERROR OR CRITICAL) AND (database OR sql OR query)"
  ignore_case: false
  date_from: "2026-01-01"
  date_to: "2026-01-31"

files:
  search_root: "/var/log/mysql"
  include_patterns:
    - "*.log"
    - "*.log.gz"

output:
  output_file: "db-errors.txt"
  show_stats: true

processing:
  max_workers: 8
  buffer_size: 32768
```

### High-Performance Configuration

```yaml
# performance.yaml
search:
  expression: "ERROR"

files:
  search_root: "/var/log"
  include_patterns:
    - "*.log"
    - "*.gz"
  max_depth: 3

output:
  quiet: true
  output_file: "errors.txt"

processing:
  max_workers: 16
  buffer_size: 65536
  encoding: "utf-8"
  errors: "ignore"
```

## Configuration Validation

Validate your configuration:

```bash
# Test with dry run
log-filter --config config.yaml --dry-run --verbose

# Check syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## Best Practices

### 1. Use Configuration Files for Repeated Tasks

Store common searches in config files:

```bash
log-filter --config daily-errors.yaml
log-filter --config database-analysis.yaml
```

### 2. Start with Dry Run

Always test with `--dry-run` first:

```bash
log-filter --config config.yaml --dry-run --stats
```

### 3. Use Verbose Mode for Debugging

Enable verbose output when troubleshooting:

```bash
log-filter --config config.yaml --verbose
```

### 4. Tune Performance Settings

Adjust workers and buffer size based on workload:

```yaml
# Many small files
processing:
  max_workers: 8
  buffer_size: 4096

# Few large files
processing:
  max_workers: 2
  buffer_size: 65536
```

### 5. Document Your Configurations

Add comments to config files:

```yaml
# Daily error monitoring configuration
# Run with: log-filter --config daily.yaml
search:
  expression: "ERROR OR CRITICAL"
  # ... rest of config
```

## Configuration Schema Reference

Complete YAML schema:

```yaml
search:
  expression: str                # Required
  ignore_case: bool           # Optional, default: false
  date_from: str (YYYY-MM-DD)   # Optional
  date_to: str (YYYY-MM-DD)     # Optional
  time_from: str (HH:MM:SS)     # Optional
  time_to: str (HH:MM:SS)       # Optional

files:
  search_root: str               # Required
  include_patterns: list[str]    # Optional
  exclude_patterns: list[str]    # Optional
  follow_symlinks: bool          # Optional, default: false
  max_depth: int                 # Optional, default: unlimited

output:
  output_file: str               # Optional, default: stdout
  overwrite: bool                # Optional, default: false
  dry_run: bool                  # Optional, default: false
  show_stats: bool               # Optional, default: false
  verbose: bool                  # Optional, default: false
  quiet: bool                    # Optional, default: false

processing:
  max_workers: int               # Optional, default: CPU count
  buffer_size: int               # Optional, default: 8192
  encoding: str                  # Optional, default: utf-8
  errors: str                    # Optional, default: replace
```

## Next Steps

- **[Quick Start](quickstart.md)** - Basic usage examples
- **[CLI Reference](api/cli.rst)** - Complete command-line options
- **[Troubleshooting](troubleshooting.md)** - Solve common issues
- **[API Documentation](api/index.rst)** - Programmatic usage
