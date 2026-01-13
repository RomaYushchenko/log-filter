# Quick Start Guide

Get started with Log Filter in 5 minutes.

## Installation

### Option 1: From Source (Development/Local Use)

**For local development or if the package is not yet published to PyPI:**

1. **Clone or navigate to the project directory:**

   ```bash
   # If cloning from repository
   git clone https://github.com/RomaYushchenko/log-filter.git
   cd log-filter
   
   # Or navigate to your local project
   cd C:\Users\your-username\path\to\log-filter
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate it
   # On Windows:
   .\.venv\Scripts\activate
   
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install in development mode:**

   ```bash
   # Install package in editable mode
   pip install -e .
   
   # Or with development dependencies
   pip install -e ".[dev]"
   ```

   **What this does:**
   - Installs the package from local source code
   - Creates `log-filter` command in your PATH
   - Links to source directory (code changes take effect immediately)
   - Installs all required dependencies (pyyaml, etc.)

4. **Verify installation:**

   ```bash
   log-filter --version
   # Output: log-filter 2.0.0
   
   # Test import
   python -c "import log_filter; print(f'Version: {log_filter.__version__}')"
   
   # Show help
   log-filter --help
   ```

### Option 2: From PyPI (Production - When Published)

**Once the package is published to PyPI:**

```bash
pip install log-filter
```

Verify installation:

```bash
log-filter --version
# Output: log-filter 2.0.0
```

### Option 3: Using Docker

**No Python installation required - run directly from Docker:**

1. **Build the image:**

   ```powershell
   # Clone repository
   git clone https://github.com/RomaYushchenko/log-filter.git
   cd log-filter
   
   # Build production image
   docker build -t log-filter:latest .
   ```

2. **Run basic filter:**

   ```powershell
   # Windows PowerShell
   docker run --rm `
     -v ${PWD}/test-logs:/logs:ro `
     -v ${PWD}/output:/output `
     log-filter:latest `
     ERROR /logs -o /output/errors.txt --stats
   
   # Linux/Mac bash
   docker run --rm \
     -v $(pwd)/test-logs:/logs:ro \
     -v $(pwd)/output:/output \
     log-filter:latest \
     ERROR /logs -o /output/errors.txt --stats
   ```

3. **Using Docker Compose (recommended):**

   ```powershell
   # Run with local logs
   docker-compose -f docker-compose.local.yml run --rm log-filter-local
   
   # Development mode with live code reload
   docker-compose -f docker-compose.dev.yml run --rm log-filter-dev
   ```

**Benefits:**
- No Python environment setup
- Consistent across all platforms
- Isolated from system dependencies
- Perfect for production deployment

**See Also:** [Docker Local Setup Guide](../.github/docs/analize/docker-local-setup-analysis.md) for complete instructions.

### Troubleshooting Installation

**Issue: "pip: command not found"**
```bash
# Use python -m pip instead
python -m pip install -e .
```

**Issue: "No module named 'setuptools'"**
```bash
# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

**Issue: "Permission denied"**
```bash
# On Windows: Run PowerShell as Administrator
# Or use --user flag
pip install --user -e .
```

**Issue: Package already installed**
```bash
# Uninstall first, then reinstall
pip uninstall log-filter
pip install -e .
```

## Basic Usage

### 1. Simple Search

Search for a single keyword:

```bash
log-filter "ERROR" /var/log
```

This searches all log files in `/var/log` for lines containing "ERROR".

**Output**:
```text
=== File: /var/log/app.log (lines 142-144) ===
2026-01-08 10:30:45 ERROR Database connection timeout
  at DatabaseConnector.connect(db.py:42)
  Caused by: Network timeout after 30s

=== File: /var/log/system.log (line 89) ===
2026-01-08 10:31:12 ERROR Failed to load configuration
```

### 2. Boolean Expressions

Combine multiple keywords with boolean operators:

#### AND Operator

Find logs containing both keywords:

```bash
log-filter "ERROR AND database" /var/log
```

Matches: "ERROR: Database connection failed"

#### OR Operator

Find logs containing either keyword:

```bash
log-filter "ERROR OR WARNING" /var/log
```

Matches: "ERROR: ..." or "WARNING: ..."

#### NOT Operator

Exclude certain keywords:

```bash
log-filter "ERROR NOT timeout" /var/log
```

Matches: "ERROR" but not lines containing "timeout"

#### Complex Expressions

Use parentheses for grouping:

```bash
log-filter "(ERROR OR CRITICAL) AND database" /var/log
```

Matches: Lines with "database" and either "ERROR" or "CRITICAL"

### 3. Save Results to File

Redirect output to a file:

```bash
log-filter "ERROR" /var/log -o errors.txt
```

Verify results:

```bash
cat errors.txt
# or on Windows:
type errors.txt
```

### 4. Case-Insensitive Search

By default, searches are case-insensitive. To make it case-sensitive:

```bash
log-filter "error" /var/log           # Matches: error, Error, ERROR
log-filter "ERROR" /var/log -c        # Matches: ERROR only
```

### 5. Filter by Date/Time

Search within a date range:

```bash
# Specific date
log-filter "ERROR" /var/log --date-from 2026-01-01 --date-to 2026-01-31

# Specific time range
log-filter "ERROR" /var/log --time-from 09:00:00 --time-to 17:00:00

# Combine both
log-filter "ERROR" /var/log \
  --date-from 2026-01-08 \
  --time-from 09:00:00 \
  --time-to 17:00:00
```

### 6. File Pattern Filtering

Include/exclude specific file patterns:

```bash
# Only .log files
log-filter "ERROR" /var/log -i "*.log"

# Include multiple patterns
log-filter "ERROR" /var/log -i "*.log" -i "*.log.gz"

# Exclude patterns
log-filter "ERROR" /var/log -e "*.old" -e "debug.log"
```

### 7. Dry Run Mode

Count matches without saving:

```bash
log-filter "ERROR" /var/log --dry-run --stats
```

**Output**:
```text
[DRY RUN] No output file will be created

Files: 10 | Records: 15,000 | Matches: 240 (1.6%)
```

Show detailed file information:

```bash
log-filter "ERROR" /var/log --dry-run-details
```

**Output**:
```text
File: /var/log/app.log
  Size: 2.4 MB | Records: 1,500 | Est. Matches: 23
File: /var/log/db.log
  Size: 5.1 MB | Records: 2,400 | Est. Matches: 45
...
```

### 8. Highlight Matches

Highlight matched text in output:

```bash
log-filter "ERROR" /var/log --highlight
```

**Output**:
```text
2026-01-08 10:30:45 <<<ERROR>>> Database connection timeout
```

### 9. Show Statistics

Display processing statistics:

```bash
log-filter "ERROR" /var/log -o errors.txt --stats
```

**Output**:
```text
================================================================================
Processing Statistics
================================================================================

Files:
  Processed:     10
  Matched:       7 (70.0%)
  Skipped:       0

Records:
  Total:         15,000
  Matched:       240 (1.6%)

Performance:
  Time:          12.5s
  Throughput:    1,200 records/sec
  Speed:         4.0 MB/sec

================================================================================
```

### 10. Verbose Output

See detailed processing information:

```bash
log-filter "ERROR" /var/log --verbose
# or
log-filter "ERROR" /var/log --progress
```

**Output**:
```text
[INFO] Scanning directory: /var/log
[INFO] Found 10 files matching patterns
[INFO] Processing: /var/log/app.log
[INFO]   Records: 1500 | Matches: 23 | Time: 1.2s
[INFO] Processing: /var/log/db.log
[INFO]   Records: 2400 | Matches: 45 | Time: 2.1s
...
```

### 11. Debug Mode

Enable detailed debug logging:

```bash
log-filter "ERROR" /var/log --debug
```

Shows internal processing details, useful for troubleshooting.

### 12. Performance Tuning

Adjust worker threads for better performance:

```bash
# Use 8 worker threads
log-filter "ERROR" /var/log -w 8

# Auto-detect (uses CPU count)
log-filter "ERROR" /var/log  # Default behavior
```

## Common Use Cases

### Find All Errors Today

```bash
log-filter "ERROR OR CRITICAL" /var/log \
  --date-from $(date +%Y-%m-%d) \
  -o today-errors.txt \
  --stats
```

### Search Multiple Log Directories

```bash
# Process each directory
log-filter "ERROR" /var/log -o var-errors.txt
log-filter "ERROR" /opt/app/logs -o app-errors.txt

# Or combine
for dir in /var/log /opt/app/logs; do
  log-filter "ERROR" "$dir" -o "$(basename $dir)-errors.txt"
done
```

### Extract Database Errors

```bash
log-filter "(ERROR OR CRITICAL) AND (database OR sql OR query)" /var/log \
  -o db-errors.txt \
  --stats
```

### Find Errors During Business Hours

```bash
log-filter "ERROR" /var/log \
  --time-from 09:00:00 \
  --time-to 17:00:00 \
  -o business-hours-errors.txt
```

### Monitor Specific Application

```bash
log-filter "ERROR" /var/log/myapp \
  -i "myapp*.log" \
  -i "myapp*.log.gz" \
  -e "*.old" \
  -o myapp-errors.txt
```

## Expression Syntax Reference

### Basic Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `AND` | `A AND B` | Both A and B must be present |
| `OR` | `A OR B` | Either A or B must be present |
| `NOT` | `A NOT B` | A must be present, B must not |
| `()` | `(A OR B) AND C` | Grouping for precedence |

### Precedence Rules

1. Parentheses `()`
2. NOT
3. AND
4. OR

Example:
```bash
# Without parentheses (AND binds tighter)
log-filter "ERROR OR WARNING AND database" /var/log
# Interpreted as: ERROR OR (WARNING AND database)

# With parentheses (explicit)
log-filter "(ERROR OR WARNING) AND database" /var/log
# Interpreted as: (ERROR OR WARNING) AND database
```

## Tips & Tricks

### 1. Quote Your Expressions

Always quote expressions with spaces or special characters:

```bash
# Good
log-filter "ERROR AND database" /var/log

# Bad (shell interprets AND as a command)
log-filter ERROR AND database /var/log
```

### 2. Use Case-Insensitive Search

Default case-insensitive search catches more matches:

```bash
log-filter "error" /var/log  # Matches: error, Error, ERROR, ErRoR
```

### 3. Test with Dry Run First

Preview results before processing:

```bash
# See what will be found
log-filter "ERROR" /var/log --dry-run --stats

# If looks good, run for real
log-filter "ERROR" /var/log -o errors.txt
```

### 4. Combine with Other Tools

Pipe to other Unix tools:

```bash
# Count errors
log-filter "ERROR" /var/log | wc -l

# Extract timestamps
log-filter "ERROR" /var/log | cut -d' ' -f1-2

# View with pager
log-filter "ERROR" /var/log | less
```

### 5. Use Configuration Files

For repeated searches, use a config file.

#### Create Configuration File

Create `config.yaml` in one of these locations:

```bash
# Current directory (recommended for project-specific configs)
./config.yaml

# User home directory (recommended for personal configs)
~/.log-filter/config.yaml         # Linux/macOS
%USERPROFILE%\.log-filter\config.yaml  # Windows

# System-wide (recommended for server/shared configs)
/etc/log-filter/config.yaml       # Linux
C:\ProgramData\log-filter\config.yaml  # Windows

# Custom location (specify with --config)
/path/to/my-config.yaml
```

#### Basic Configuration

```yaml
# config.yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  path: "/var/log"
  include_patterns:
    - "*.log"
    - "*.log.gz"
  exclude_patterns:
    - "*.old"

output:
  output_file: "errors.txt"
  stats: true

processing:
  max_workers: 8
  buffer_size: 8192
```

#### Use Configuration

```bash
# Use config from current directory
log-filter --config config.yaml

# Use config from custom location
log-filter --config /etc/log-filter/config.yaml

# Use environment variable
export LOG_FILTER_CONFIG=~/.log-filter/config.yaml
log-filter

# Override config values with CLI arguments
log-filter --config config.yaml -w 16 --verbose
```

#### Complete Template

A complete configuration template with all options is available in `config.yaml.template`. Copy and customize it:

```bash
# Copy template
cp config.yaml.template config.yaml

# Edit for your needs
nano config.yaml  # or vim, code, notepad, etc.

# Use it
log-filter --config config.yaml
```

**Priority Order** (highest to lowest):
1. CLI arguments (override everything)
2. Environment variables
3. Configuration file
4. Default values

## Next Steps

- **[Configuration Guide](configuration.md)** - Learn about all configuration options
- **[CLI Reference](api/cli.rst)** - Complete command-line reference
- **[API Documentation](api/index.rst)** - Use Log Filter programmatically
- **[Troubleshooting](troubleshooting.md)** - Solve common problems

## Getting Help

If you need help:

```bash
# Built-in help
log-filter --help

# Check version
log-filter --version

# Read documentation
# Visit: https://log-filter.readthedocs.io
```

**Need more help?**
- GitHub Issues: https://github.com/your-org/log-filter/issues
- Discussions: https://github.com/your-org/log-filter/discussions
