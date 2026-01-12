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
- **📊 Statistics**: Built-in metrics tracking and performance monitoring
- **🗓️ Date/Time Filtering**: Native support for date and time range filtering
- **🔧 Flexible Configuration**: YAML config files, environment variables, CLI arguments
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

processing:
  max_workers: 8
  buffer_size: 32768
  encoding: "utf-8"
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
