# Log Filter

[![PyPI version](https://badge.fury.io/py/log-filter.svg)](https://pypi.org/project/log-filter/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-706%20passed-brightgreen.svg)](https://github.com/RomaYushchenko/log-filter)
[![Coverage](https://img.shields.io/badge/coverage-89.73%25-brightgreen.svg)](https://github.com/RomaYushchenko/log-filter)

**High-performance log filtering tool with boolean expression support and multi-threaded processing.**

## ✨ Features

- **🔍 Boolean Expressions**: Search with AND, OR, NOT operators for complex patterns
- **⚡ Multi-threaded**: Parallel processing delivers 5-10x speedup (5,000+ lines/sec)
- **🏷️ Log Level Normalization**: Automatically matches abbreviated levels (E→ERROR, W→WARN, etc.)
- **📊 Statistics**: Built-in metrics tracking and performance monitoring
- **🗓️ Date/Time Filtering**: Native support for date and time range filtering
- **� Smart Sorting**: Chronological ordering with file pre-sorting and timestamp sorting
- **📦 Chunked Output**: Automatic file splitting to prevent large output files
- **�🔧 Flexible Configuration**: YAML config files, environment variables, CLI arguments
- **🐳 Docker Ready**: Production-ready containers and Kubernetes manifests
- **🛡️ Type Safe**: Full type hints for better IDE support
- **✅ Production Tested**: 706 tests with 89.73% coverage, zero critical vulnerabilities

## 🚀 Quick Start

### Installation

#### From Source (Development/Local)

```bash
# Clone the repository
git clone https://github.com/RomaYushchenko/log-filter.git
cd log-filter

# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

#### From PyPI (When Published)

```bash
pip install log-filter
```

### Check Version

```bash
# Display installed version
log-filter --version
```

### Basic Usage

```bash
# Search for errors
log-filter "ERROR" /var/log

# Works with abbreviated levels (E, W, I, D, T, F)
# Searches for "ERROR" will match logs with both "ERROR" and "E" levels
log-filter "ERROR" /var/log/production

# Boolean expression
log-filter "ERROR AND database" /var/log

# Complex query
log-filter "(ERROR OR CRITICAL) AND NOT test" /var/log

# Save results
log-filter "ERROR" /var/log -o errors.txt --stats

# Date filtering
log-filter "ERROR" /var/log --after 2024-01-01

# Show statistics
log-filter "ERROR" /var/log --stats

# Disable level normalization (match exact text only)
log-filter "ERROR" /var/log --no-normalize-levels
```

### Example Output

```
Processing logs from /var/log...
✓ app.log (25 matches)
✓ system.log (13 matches)
✓ database.log (8 matches)

Statistics:
  Files Processed: 127
  Lines Processed: 1,234,567
  Matches Found: 5,432
  Processing Time: 45.67s
  Throughput: 27,024 lines/sec
```

### Docker Quick Start

#### Using Docker

```powershell
# Build image
docker build -t log-filter:latest .

# Run on local logs
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  log-filter:latest \
  ERROR /logs -o /output/errors.txt --stats
```

#### Using Docker Compose

```powershell
# Run with local logs
docker-compose -f docker-compose.local.yml run --rm log-filter-local

# Development mode with live reload
docker-compose -f docker-compose.dev.yml run --rm log-filter-dev
```

See [Docker Deployment Guide](docs/deployment.md#local-machine-setup-windowsmaclinux) for detailed instructions.

## 📚 Documentation

- **[Quick Start Guide](https://log-filter.readthedocs.io/en/latest/quickstart.html)** - Learn the basics in 5 minutes
- **[Configuration](https://log-filter.readthedocs.io/en/latest/configuration.html)** - Complete configuration reference
- **[API Documentation](https://log-filter.readthedocs.io/en/latest/api/index.html)** - Python API reference
- **[Deployment Guide](https://log-filter.readthedocs.io/en/latest/deployment.html)** - Docker, Kubernetes, production setup
- **[Migration Guide](https://log-filter.readthedocs.io/en/latest/migration.html)** - Upgrade from v1.x to v2.0

## 💡 Use Cases

### Error Monitoring

```bash
# Find all errors from today
log-filter "ERROR" /var/log --after today -o errors-today.txt

# Monitor specific application
log-filter "ERROR AND myapp" /var/log --stats
```

### Database Analysis

```bash
# Extract database errors
log-filter "ERROR AND (database OR sql OR connection)" /var/log -o db-errors.txt

# Find slow queries
log-filter "slow query" /var/log/mysql --time-after 09:00 --time-before 17:00
```

### Business Hours Filtering

```bash
# Only business hours (9 AM - 5 PM)
log-filter "ERROR" /var/log \
  --time-after 09:00 \
  --time-before 17:00 \
  -o business-hours-errors.txt
```

### Multi-Directory Search

```bash
# Search multiple directories
log-filter "ERROR" /var/log/app /var/log/system /var/log/nginx
```

### Log Level Normalization

Production logs often use abbreviated log levels (E, W, I, D) to save space. Log Filter automatically normalizes these abbreviations, allowing you to search using full level names:

```bash
# Search for "ERROR" matches both "ERROR" and "E" in logs
log-filter "ERROR" /var/log/production

# Supported abbreviations:
# E → ERROR
# W → WARN (also WARN, WARNING)
# I → INFO  
# D → DEBUG
# T → TRACE
# F → FATAL

# Example: Your production log format
# 2025-01-08 10:00:00.000+0000 E Database connection failed
# 2025-01-08 10:00:01.000+0000 W Connection pool exhausted

# Both will be matched by:
log-filter "ERROR OR WARN" /var/log

# Disable normalization if needed (exact match only)
log-filter "ERROR" /var/log --no-normalize-levels

# Configure in YAML
# processing:
#   normalize_log_levels: true  # default
```

### Sorted Chunked Output

Log Filter can automatically sort results by timestamp and split large output into manageable chunks:

```bash
# Automatic file splitting (default: 500 records per file)
log-filter "ERROR" /var/log -o results.log
# Creates: results-001.log, results-002.log, results-003.log, ...

# Custom chunk size (1000 records per file)
log-filter "ERROR" /var/log -o results.log --max-records-per-file 1000

# Custom filename pattern
log-filter "ERROR" /var/log -o results.log \
  --output-pattern "{base}_part{index:02d}{ext}"
# Creates: results_part01.log, results_part02.log, ...

# Disable chunking (single file)
log-filter "ERROR" /var/log -o results.log --max-records-per-file 0

# Sort results by timestamp (chronological order)
log-filter "ERROR" /var/log -o results.log
# Results sorted: oldest → newest

# Disable timestamp sorting
log-filter "ERROR" /var/log -o results.log --no-sort-timestamps

# File pre-sorting (process files in date order)
# Automatically sorts input files like: app-01-15-2026-1.log, app-01-16-2026-1.log
log-filter "ERROR" /var/log -o results.log
# Files processed in chronological order

# Disable file sorting
log-filter "ERROR" /var/log -o results.log --no-sort-files

# Example: Large production log analysis
log-filter "(ERROR OR CRITICAL)" /var/log/production \
  -o critical-errors.log \
  --max-records-per-file 500 \
  --output-pattern "{base}-{index:03d}{ext}"
# Output: critical-errors-001.log (500 records)
#         critical-errors-002.log (500 records)
#         critical-errors-003.log (remaining records)
# All sorted chronologically
```

#### Supported Filename Patterns for Pre-sorting

Log Filter recognizes these date patterns in filenames:
- `DD-MM-YYYY-N` (e.g., app-15-01-2026-1.log)
- `YYYY-MM-DD-N` (e.g., app-2026-01-15-1.log)
- `YYYYMMDD_N` (e.g., app_20260115_1.log)
- Index-only (e.g., app-001.log, app-002.log)

Files are processed in chronological order based on date + index.

## 🔧 Advanced Configuration

Create `config.yaml`:

```yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  path: "/var/log"
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*.gz"
  max_depth: 3
  max_file_size: 100      # Skip files > 100 MB
  max_record_size: 512    # Skip records > 512 KB

output:
  output_file: "/var/log-filter/errors.txt"
  overwrite: true
  no_path: false          # Include file paths
  highlight: false        # Highlight matches
  stats: true
  verbose: false
  quiet: false
  dry_run: false
  # Chunked output configuration
  max_records_per_file: 500                    # Records per file (0 = unlimited)
  output_file_pattern: "{base}-{index:03d}{ext}"  # Filename template
  sort_by_timestamp: true                      # Sort results chronologically

processing:
  max_workers: 8
  buffer_size: 32768
  encoding: "utf-8"
  normalize_log_levels: true  # Enable level normalization (default)
  sort_input_files: true      # Pre-sort input files by date/index
  debug: false
```

Run with config:

```bash
log-filter --config config.yaml
```

## 🐳 Docker Deployment

```bash
# Pull image
docker pull log-filter/log-filter:2.0.0

# Run
docker run --rm \
  -v /var/log:/logs:ro \
  -v $(pwd)/output:/output \
  log-filter:2.0.0 \
  "ERROR" "/logs" "-o" "/output/errors.txt" "--stats"
```

### Docker Compose

```yaml
version: '3.8'
services:
  log-filter:
    image: log-filter:2.0.0
    volumes:
      - /var/log:/logs:ro
      - ./output:/output
    environment:
      - LOG_FILTER_WORKERS=8
    command: ["ERROR", "/logs", "-o", "/output/errors.txt", "--stats"]
```

## ☸️ Kubernetes Deployment

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-filter-hourly
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: log-filter
            image: log-filter:2.0.0
            args: ["--config", "/config/config.yaml"]
            volumeMounts:
              - name: logs
                mountPath: /logs
                readOnly: true
          restartPolicy: OnFailure
```

## 📊 Performance

| Workload | Throughput | Workers | Time (1 GB) |
|----------|-----------|---------|-------------|
| Single-threaded | 5,000 lines/sec | 1 | 180s |
| Multi-threaded | 40,000 lines/sec | 8 | 25s |
| High-performance | 80,000 lines/sec | 16 | 12s |

**Scaling**: Linear with CPU cores up to 16 workers
**Memory**: ~50-100 MB base + ~10 MB per worker
**Tested**: Up to 100 GB of logs with consistent performance

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/RomaYushchenko/log-filter
cd log-filter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=log_filter --cov-report=html

# Run specific test
pytest tests/test_parser.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
flake8 src/
```

## 🏗️ Architecture

```
log-filter/
├── src/log_filter/
│   ├── core/           # Expression parsing & evaluation
│   ├── domain/         # Business models & filters
│   ├── config/         # Configuration management
│   ├── infrastructure/ # File I/O & handlers
│   ├── processing/     # Multi-threaded pipeline
│   ├── statistics/     # Metrics & reporting
│   └── utils/          # Logging, progress, highlighting
├── tests/              # Comprehensive test suite
└── docs/               # Sphinx documentation
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](https://github.com/RomaYushchenko/log-filter/docs/CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Homepage**: https://github.com/RomaYushchenko/log-filter
- **Documentation**: https://log-filter.readthedocs.io
- **PyPI**: https://pypi.org/project/log-filter/
- **Bug Tracker**: https://github.com/RomaYushchenko/log-filter/issues
- **Discussions**: https://github.com/RomaYushchenko/log-filter/discussions

## 📈 Project Status

- **Version**: 2.0.0
- **Status**: Production Ready
- **Python**: 3.10+ required
- **Tests**: 706 tests, 89.73% coverage
- **Security**: Zero critical vulnerabilities
- **Performance**: 5,000+ lines/sec (single), 40,000+ (multi-threaded)

## 🙏 Acknowledgments

Developed by [Roman Yushchenko](https://www.linkedin.com/in/ryushchenko/) with contributions from the community.

Special thanks to all contributors, testers, and users who provided feedback.

## 📞 Support

- **Documentation**: https://log-filter.readthedocs.io
- **Issues**: https://github.com/RomaYushchenko/log-filter/issues
- **Discussions**: https://github.com/RomaYushchenko/log-filter/discussions
- **Email**: yushenkoromaf7@gmail.com

---

**Made with ❤️ by Roman Yushchenko**
