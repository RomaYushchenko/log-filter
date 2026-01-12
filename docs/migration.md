# Migration Guide: v1.x to v2.0

Upgrade from log-filter v1.x to v2.0.

## Overview

Version 2.0 is a major release with significant improvements and breaking changes:

**New Features:**
- ✨ Boolean expression support (AND, OR, NOT)
- ⚡ Multi-threaded processing (5-10x faster)
- 📊 Statistics and monitoring
- 🔧 Comprehensive configuration system
- 🛡️ Type safety with full type hints
- 📦 Better error handling and reporting

**Breaking Changes:**
- Command-line argument changes
- Configuration file format (YAML required)
- Python API changes
- Minimum Python version: 3.10+ (was 3.7+)
- Removed deprecated features

## Quick Migration Checklist

- [ ] Upgrade Python to 3.10+ if needed
- [ ] Update installation: `pip install --upgrade log-filter`
- [ ] Update CLI arguments (see below)
- [ ] Convert config files to YAML format
- [ ] Update custom scripts using Python API
- [ ] Test with `--dry-run` before production
- [ ] Update cron jobs and scheduled tasks
- [ ] Update Docker containers if applicable

## Installation

### Upgrade from v1.x

```bash
# Uninstall v1.x
pip uninstall log-filter

# Install v2.0
pip install log-filter>=2.0.0

# Verify
log-filter --version
# Output: log-filter 2.0.0
```

### Python Version Requirement

**v1.x:** Python 3.7+
**v2.0:** Python 3.10+

```bash
# Check Python version
python --version

# If needed, upgrade Python
# Ubuntu
sudo apt install python3.10

# macOS
brew install python@3.12

# Windows
# Download from python.org
```

## Command-Line Changes

### Basic Search Syntax

**v1.x:**
```bash
# Simple string search only
log-filter ERROR /var/log
log-filter "error message" /var/log
```

**v2.0:**
```bash
# Same basic syntax works
log-filter "ERROR" /var/log

# New: Boolean expressions
log-filter "ERROR AND database" /var/log
log-filter "(ERROR OR CRITICAL) AND NOT test" /var/log
```

**Migration:** Simple searches work unchanged. Add quotes around expressions.

### Output Options

**v1.x:**
```bash
log-filter ERROR /var/log -o output.txt
log-filter ERROR /var/log --output-file output.txt
```

**v2.0:**
```bash
# Same syntax
log-filter "ERROR" /var/log -o output.txt

# New: Overwrite protection
log-filter "ERROR" /var/log -o output.txt --overwrite
```

**Migration:** Add `--overwrite` if you want to replace existing files (v1.x default behavior).

### File Filtering

**v1.x:**
```bash
log-filter ERROR /var/log --pattern "*.log"
log-filter ERROR /var/log --exclude "*.gz"
```

**v2.0:**
```bash
# Changed: -i/--include instead of --pattern
log-filter "ERROR" /var/log -i "*.log"

# Changed: -e/--exclude (same but different short form)
log-filter "ERROR" /var/log -e "*.gz"
```

**Migration:**
- `--pattern` → `-i` or `--include`
- Both versions support multiple patterns

### Performance Options

**v1.x:**
```bash
# Single-threaded only
log-filter ERROR /var/log
```

**v2.0:**
```bash
# Multi-threaded by default
log-filter "ERROR" /var/log

# Control workers
log-filter "ERROR" /var/log -w 8
log-filter "ERROR" /var/log --max-workers 8

# Control buffer size
log-filter "ERROR" /var/log --buffer-size 65536
```

**Migration:** No changes needed. v2.0 auto-detects optimal workers.

### Statistics

**v1.x:**
```bash
# No built-in statistics
log-filter ERROR /var/log
# (count manually with wc -l)
```

**v2.0:**
```bash
# New: Built-in statistics
log-filter "ERROR" /var/log --stats

# Output:
# Statistics:
#   Files Processed: 127
#   Lines Processed: 1,234,567
#   Matches Found: 5,432
#   Processing Time: 45.67s
#   Throughput: 27,024 lines/sec
```

**Migration:** Add `--stats` to see processing statistics.

### Verbosity

**v1.x:**
```bash
log-filter ERROR /var/log -v
log-filter ERROR /var/log --verbose
```

**v2.0:**
```bash
# Same syntax
log-filter "ERROR" /var/log --verbose

# New: Quiet mode
log-filter "ERROR" /var/log --quiet
```

**Migration:** No changes needed.

### Date/Time Filtering

**v1.x:**
```bash
# Not supported in v1.x
# (had to use grep or other tools)
```

**v2.0:**
```bash
# New: Date filtering
log-filter "ERROR" /var/log --after 2024-01-01
log-filter "ERROR" /var/log --before 2024-12-31
log-filter "ERROR" /var/log --after 2024-01-01 --before 2024-01-31

# New: Time filtering
log-filter "ERROR" /var/log --time-after 09:00
log-filter "ERROR" /var/log --time-before 17:00
log-filter "ERROR" /var/log --time-after 09:00 --time-before 17:00
```

**Migration:** Replace complex grep pipelines with native date/time filters.

### Configuration Files

**v1.x:**
```bash
# INI format
log-filter --config config.ini
```

**v2.0:**
```bash
# YAML format required
log-filter --config config.yaml
```

**Migration:** Convert INI to YAML (see Configuration section below).

### Dry Run

**v1.x:**
```bash
# Not supported
# (had to test with limited scope)
```

**v2.0:**
```bash
# New: Dry run mode
log-filter "ERROR" /var/log --dry-run

# Shows what would be processed without executing
```

**Migration:** Use `--dry-run` to test before production runs.

### Removed Options

These options were removed in v2.0:

| v1.x Option | v2.0 Alternative | Reason |
|-------------|------------------|---------|
| `--pattern` | `-i` / `--include` | Renamed for clarity |
| `--regex` | Use expressions | Replaced by boolean expressions |
| `--case-sensitive` | `--case-sensitive` (same) | Kept but default changed to false |
| `--line-numbers` | Not supported | Use external tools (grep -n) |
| `--count-only` | Use `--stats` + `--quiet` | Replaced by statistics |

## Configuration File Migration

### v1.x Configuration (INI format)

```ini
# config.ini
[search]
pattern = ERROR
ignore_case = false
files = /var/log

[output]
output_file = errors.txt
```

### v2.0 Configuration (YAML format)

```yaml
# config.yaml
search:
  expression: "ERROR"
  ignore_case: true

files:
  search_root: "/var/log"
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*.gz"
  follow_symlinks: false
  max_depth: null

output:
  output_file: "errors.txt"
  overwrite: false
  stats: true
  verbose: false
  quiet: false

processing:
  max_workers: null  # auto-detect
  buffer_size: 8192
  encoding: "utf-8"
  errors: "replace"
```

### Conversion Script

```python
#!/usr/bin/env python3
"""Convert v1.x INI config to v2.0 YAML config."""

import configparser
import yaml
from pathlib import Path

def convert_config(ini_path: str, yaml_path: str):
    """Convert INI config to YAML."""
    # Read INI
    config = configparser.ConfigParser()
    config.read(ini_path)
    
    # Convert to v2.0 format
    yaml_config = {
        'search': {
            'expression': config.get('search', 'pattern', fallback='ERROR'),
            'ignore_case': config.getboolean('search', 'case_sensitive', fallback=False)
        },
        'files': {
            'search_root': config.get('search', 'files', fallback='/var/log'),
            'include_patterns': ['*.log'],
            'exclude_patterns': [],
            'follow_symlinks': False,
            'max_depth': None
        },
        'output': {
            'output_file': config.get('output', 'output_file', fallback=None),
            'overwrite': False,
            'stats': True,
            'verbose': False,
            'quiet': False
        },
        'processing': {
            'max_workers': None,
            'buffer_size': 8192,
            'encoding': 'utf-8',
            'errors': 'replace'
        }
    }
    
    # Write YAML
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Converted {ini_path} → {yaml_path}")

if __name__ == '__main__':
    convert_config('config.ini', 'config.yaml')
```

**Usage:**

```bash
python convert_config.py
log-filter --config config.yaml
```

## Python API Migration

### Import Changes

**v1.x:**
```python
from log_filter import LogFilter, FileScanner
```

**v2.0:**
```python
# More granular imports
from log_filter.core import Tokenizer, Parser, Evaluator
from log_filter.infrastructure import FileScanner
from log_filter.processing import ProcessingPipeline
from log_filter.config import ApplicationConfig
```

**Migration:** Update import paths to new module structure.

### Basic Usage

**v1.x:**
```python
from log_filter import LogFilter

# Simple API
filter = LogFilter(pattern="ERROR")
results = filter.search("/var/log")

for result in results:
    print(result.line)
```

**v2.0:**
```python
from log_filter.config import ApplicationConfig
from log_filter.processing import ProcessingPipeline

# Configure
config = ApplicationConfig(
    search=SearchConfig(expression="ERROR"),
    files=FileConfig(search_root="/var/log")
)

# Process
pipeline = ProcessingPipeline(config)
results = pipeline.process()

for result in results:
    print(result.content)
```

**Migration:** v2.0 uses configuration-based approach instead of simple constructor.

### File Scanning

**v1.x:**
```python
from log_filter import FileScanner

scanner = FileScanner("/var/log")
files = scanner.scan(pattern="*.log")
```

**v2.0:**
```python
from log_filter.infrastructure import FileScanner
from log_filter.config import FileConfig

config = FileConfig(
    search_root="/var/log",
    include_patterns=["*.log"],
    exclude_patterns=["*.gz"]
)

scanner = FileScanner(config)
files = list(scanner.scan())
```

**Migration:** Use FileConfig instead of constructor parameters.

### Expression Evaluation

**v1.x:**
```python
from log_filter import Matcher

# Simple string matching only
matcher = Matcher("ERROR")
if matcher.matches("ERROR: Database connection failed"):
    print("Match!")
```

**v2.0:**
```python
from log_filter.core import Tokenizer, Parser, Evaluator
from log_filter.domain import LogRecord

# Boolean expression support
expression = "ERROR AND database"
tokenizer = Tokenizer(expression)
tokens = tokenizer.tokenize()
parser = Parser(tokens)
ast = parser.parse()
evaluator = Evaluator(ast)

record = LogRecord(
    content="ERROR: Database connection failed",
    line_number=42,
    file_path="/var/log/app.log"
)

if evaluator.evaluate(record):
    print("Match!")
```

**Migration:** Use new tokenizer/parser/evaluator pipeline for boolean expressions.

### Statistics Collection

**v1.x:**
```python
# No built-in statistics
# Had to track manually
```

**v2.0:**
```python
from log_filter.statistics import StatisticsCollector

collector = StatisticsCollector()

# Track during processing
collector.increment_files()
collector.increment_lines(100)
collector.increment_matches(5)

# Get summary
summary = collector.get_summary()
print(f"Files: {summary.files_processed}")
print(f"Lines: {summary.lines_processed}")
print(f"Matches: {summary.matches_found}")
print(f"Throughput: {summary.throughput_lines_per_sec:.2f} lines/sec")
```

**Migration:** Use StatisticsCollector for tracking metrics.

### Error Handling

**v1.x:**
```python
from log_filter import LogFilter, FilterError

try:
    filter = LogFilter(pattern="ERROR")
    results = filter.search("/var/log")
except FilterError as e:
    print(f"Error: {e}")
```

**v2.0:**
```python
from log_filter.core import ParseError, EvaluationError
from log_filter.config import ConfigurationError
from log_filter.infrastructure import FileHandlingError

try:
    # ... processing ...
    pass
except ParseError as e:
    print(f"Expression parse error: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except FileHandlingError as e:
    print(f"File handling error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**Migration:** Use specific exception types for better error handling.

## Behavioral Changes

### Case Sensitivity

**v1.x:** Case-sensitive by default
**v2.0:** Case-insensitive by default

```bash
# v1.x: "ERROR" only matches "ERROR"
log-filter ERROR /var/log

# v2.0: "ERROR" matches "ERROR", "Error", "error"
log-filter "ERROR" /var/log

# v2.0: Force case-sensitive
log-filter "ERROR" /var/log --case-sensitive
```

**Migration:** Add `--case-sensitive` if you relied on v1.x default behavior.

### Output Overwriting

**v1.x:** Overwrites existing files by default
**v2.0:** Refuses to overwrite (requires `--overwrite`)

```bash
# v1.x: Silently overwrites
log-filter ERROR /var/log -o errors.txt
log-filter ERROR /var/log -o errors.txt  # Overwrites

# v2.0: Requires explicit flag
log-filter "ERROR" /var/log -o errors.txt
log-filter "ERROR" /var/log -o errors.txt  # Error: file exists
log-filter "ERROR" /var/log -o errors.txt --overwrite  # OK
```

**Migration:** Add `--overwrite` to scripts that reuse output filenames.

### Empty Result Behavior

**v1.x:** Returns exit code 0 even with no matches
**v2.0:** Returns exit code 0 (success) regardless of match count

Both versions: Use `--stats` to check match count programmatically.

### Symlink Following

**v1.x:** Follows symlinks by default
**v2.0:** Does not follow symlinks by default

```bash
# v1.x: Follows symlinks
log-filter ERROR /var/log

# v2.0: Skip symlinks
log-filter "ERROR" /var/log

# v2.0: Follow symlinks explicitly
log-filter "ERROR" /var/log --follow-symlinks
```

**Migration:** Add `--follow-symlinks` if you need v1.x behavior.

## Performance Comparison

### Single-threaded (v1.x equivalent)

```bash
# Force single-threaded in v2.0
log-filter "ERROR" /var/log -w 1
```

### Multi-threaded (v2.0 default)

```bash
# Auto-detect workers (typically 2x CPU cores)
log-filter "ERROR" /var/log

# Or specify
log-filter "ERROR" /var/log -w 8
```

### Benchmark Results

| Workload | v1.x | v2.0 (1 worker) | v2.0 (8 workers) | Speedup |
|----------|------|-----------------|------------------|---------|
| 1 GB logs | 180s | 175s | 25s | 7.2x |
| 10 GB logs | 1800s | 1750s | 245s | 7.3x |
| 100 GB logs | 18000s | 17500s | 2500s | 7.2x |

**Note:** Actual speedup depends on CPU cores and storage I/O.

## Migration Steps

### Step 1: Backup

```bash
# Backup existing installation
pip freeze > requirements-old.txt

# Backup configurations
cp -r /etc/log-filter /etc/log-filter.backup
```

### Step 2: Update Python

```bash
# Check current version
python --version

# Install Python 3.10+ if needed
# (method depends on OS - see Installation section)
```

### Step 3: Install v2.0

```bash
# Uninstall v1.x
pip uninstall log-filter

# Install v2.0
pip install log-filter>=2.0.0

# Verify
log-filter --version
```

### Step 4: Convert Configurations

```bash
# Convert INI to YAML
python convert_config.py

# Test configuration
log-filter --config config.yaml --dry-run
```

### Step 5: Update Scripts

```bash
# Find all usages
grep -r "log-filter" /scripts
grep -r "log_filter" /app

# Update CLI arguments
# Update Python imports
# Update configuration references
```

### Step 6: Test

```bash
# Test with dry run
log-filter "ERROR" /var/log --dry-run --verbose

# Test with limited scope
log-filter "ERROR" /var/log/test --stats

# Compare with v1.x results
diff v1-output.txt v2-output.txt
```

### Step 7: Update Scheduled Jobs

```bash
# Update cron jobs
crontab -e

# Example change:
# Old: 0 * * * * log-filter ERROR /var/log -o /output/errors.txt
# New: 0 * * * * log-filter "ERROR" /var/log -o /output/errors.txt --overwrite --stats

# Update systemd services
sudo systemctl edit log-filter.service

# Update Docker containers
docker pull log-filter:2.0.0
docker-compose up -d
```

### Step 8: Monitor

```bash
# Check logs for errors
tail -f /var/log/log-filter.log

# Check output
ls -lh /output/errors.txt

# Verify statistics
log-filter "ERROR" /var/log --stats
```

## Compatibility Mode

v2.0 does not include a v1.x compatibility mode. All v1.x features have direct equivalents in v2.0.

### Running Both Versions

If you need to run both versions temporarily:

```bash
# Install v2.0 in virtual environment
python -m venv venv-v2
source venv-v2/bin/activate
pip install log-filter>=2.0.0

# Use v2.0
log-filter "ERROR" /var/log

# Deactivate to use v1.x
deactivate
```

## Common Migration Issues

### Issue: ImportError after upgrade

**Symptom:**
```python
ImportError: cannot import name 'LogFilter' from 'log_filter'
```

**Solution:** Update imports to v2.0 structure (see Python API Migration).

### Issue: Configuration file not loaded

**Symptom:**
```
ConfigurationError: Invalid configuration file format
```

**Solution:** Convert INI to YAML format (see Configuration File Migration).

### Issue: No matches found (but v1.x found matches)

**Symptom:** v2.0 returns 0 matches, v1.x found matches.

**Solution:** Check case sensitivity:
```bash
# Try case-sensitive mode
log-filter "ERROR" /var/log --case-sensitive
```

### Issue: Output file exists error

**Symptom:**
```
FileHandlingError: Output file exists: errors.txt
```

**Solution:** Add `--overwrite` flag:
```bash
log-filter "ERROR" /var/log -o errors.txt --overwrite
```

### Issue: Slower performance than v1.x

**Symptom:** v2.0 runs slower than expected.

**Solution:** Check worker count:
```bash
# Increase workers
log-filter "ERROR" /var/log -w 16

# Check system resources
top
iostat
```

### Issue: Python version too old

**Symptom:**
```
ERROR: Package 'log-filter' requires Python >=3.10
```

**Solution:** Upgrade Python (see Installation section).

## Rollback Procedure

If you need to rollback to v1.x:

```bash
# Uninstall v2.0
pip uninstall log-filter

# Reinstall v1.x
pip install log-filter==1.9.0

# Restore configurations
cp -r /etc/log-filter.backup /etc/log-filter

# Verify
log-filter --version
```

**Note:** v1.x is no longer maintained. Consider fixing v2.0 issues instead.

## Getting Help

### Documentation

- **[Quick Start](quickstart.md)** - Learn v2.0 basics
- **[Configuration](configuration.md)** - Complete configuration reference
- **[API Documentation](api/index.rst)** - Python API reference
- **[Troubleshooting](troubleshooting.md)** - Common issues

### Support

- **GitHub Issues:** https://github.com/your-org/log-filter/issues
- **Discussions:** https://github.com/your-org/log-filter/discussions
- **Migration Questions:** Tag with `migration` label

### Migration Checklist Summary

- [ ] Python 3.10+ installed
- [ ] v2.0 installed and verified
- [ ] Configuration files converted to YAML
- [ ] CLI arguments updated (quotes, --include, --overwrite)
- [ ] Python API imports updated
- [ ] Case sensitivity checked (add --case-sensitive if needed)
- [ ] Symlink behavior verified (add --follow-symlinks if needed)
- [ ] Scripts tested with --dry-run
- [ ] Cron jobs/scheduled tasks updated
- [ ] Docker containers updated
- [ ] Production deployment tested
- [ ] Monitoring and logging verified
- [ ] Performance validated
- [ ] Rollback plan prepared
- [ ] Team trained on v2.0 features

## Benefits of v2.0

After migration, you'll benefit from:

✅ **Boolean Expressions** - Complex search patterns with AND/OR/NOT
✅ **5-10x Faster** - Multi-threaded processing
✅ **Better Monitoring** - Built-in statistics and reporting
✅ **Type Safety** - Full type hints for better IDE support
✅ **Improved Errors** - Specific exception types and better messages
✅ **Date/Time Filtering** - Native support for temporal queries
✅ **Dry Run Mode** - Test before executing
✅ **Production Ready** - Comprehensive testing (706 tests, 89.73% coverage)

## Next Steps

1. **Complete migration checklist above**
2. **Read [Quick Start Guide](quickstart.md)** to learn new features
3. **Explore [Configuration Options](configuration.md)** for advanced usage
4. **Review [Performance Tuning](performance.md)** for optimization
5. **Check [Deployment Guide](deployment.md)** for production setup
