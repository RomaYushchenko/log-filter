# Changelog

All notable changes to log-filter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-08

### 🎉 Major Release - Complete Rewrite

This is a major release with significant improvements and breaking changes. See the [Migration Guide](docs/migration.md) for detailed upgrade instructions.

### ✨ Added

#### Boolean Expression Support
- **Complex Search Patterns**: Full boolean expression support with AND, OR, NOT operators
- **Operator Precedence**: Proper precedence handling with parentheses support
- **Expression Parser**: Complete tokenizer/parser/evaluator pipeline
- **Syntax Validation**: Clear error messages for invalid expressions

#### Multi-threaded Processing
- **Parallel Execution**: Process multiple files concurrently
- **Auto Worker Detection**: Automatically detect optimal worker count (2x CPU cores)
- **Configurable Workers**: Control parallelism with `-w/--max-workers` option
- **Linear Scaling**: Performance scales linearly with CPU cores (5-10x speedup)
- **Buffer Optimization**: Configurable buffer size for optimal I/O performance

#### Statistics and Monitoring
- **Built-in Statistics**: Track files processed, lines scanned, matches found
- **Performance Metrics**: Throughput, processing time, files/sec
- **Progress Tracking**: Real-time progress display with tqdm integration
- **Statistics Reporter**: Export statistics in text, JSON, CSV formats

#### Date/Time Filtering
- **Date Range Filtering**: `--after` and `--before` options for date-based filtering
- **Time Range Filtering**: `--time-after` and `--time-before` for time-of-day filtering
- **Business Hours Support**: Easy filtering for business hours (9 AM - 5 PM)
- **Natural Date Parsing**: Support for "today", "yesterday", ISO 8601 dates

#### Configuration System
- **YAML Configuration**: Complete YAML-based configuration system
- **Environment Variables**: Support for LOG_FILTER_* environment variables
- **Configuration Priority**: CLI args > Environment > Config file > Defaults
- **Schema Validation**: Comprehensive validation with clear error messages
- **Multiple Config Sources**: Load configuration from multiple sources

#### Enhanced File Handling
- **File Pattern Matching**: Include/exclude patterns with glob support
- **Symlink Control**: Configurable symlink following behavior
- **Max Depth Control**: Limit directory traversal depth
- **Compressed File Support**: Handle .gz files with GzipFileHandler
- **Encoding Support**: Configurable encoding with error handling strategies

#### Testing and Quality
- **Comprehensive Test Suite**: 706 tests with 89.73% code coverage
- **Property-Based Testing**: Hypothesis integration for edge case discovery
- **Performance Testing**: Benchmarks validate 5,000 lines/sec throughput
- **Integration Tests**: End-to-end testing of complete workflows
- **Security Auditing**: Bandit security scanning, zero critical vulnerabilities

#### Documentation
- **API Documentation**: Complete API reference with Sphinx
- **User Guides**: Quick start, configuration, troubleshooting, performance tuning
- **Deployment Guide**: Docker, Kubernetes, systemd, cron examples
- **Migration Guide**: Detailed v1.x to v2.0 migration instructions
- **Code Examples**: Extensive examples throughout documentation

#### Developer Experience
- **Type Safety**: Full type hints for all public APIs
- **Better Errors**: Specific exception types with detailed messages
- **IDE Support**: Complete type information for autocomplete
- **Dry Run Mode**: Test expressions and configurations without execution
- **Verbose Mode**: Detailed logging for debugging

### 🔄 Changed

#### Breaking Changes
- **Minimum Python Version**: Now requires Python 3.10+ (was 3.7+)
- **CLI Argument Changes**: 
  - `--pattern` renamed to `-i/--include`
  - `--case-sensitive` now defaults to False (case-insensitive)
  - Output overwriting requires explicit `--overwrite` flag
- **Configuration Format**: INI format replaced with YAML
- **API Structure**: New module organization (core, domain, infrastructure, processing)
- **Import Paths**: Updated import paths for all modules
- **Symlink Behavior**: No longer follows symlinks by default

#### Improvements
- **5-10x Performance**: Multi-threaded processing provides significant speedup
- **Better Output**: Colored output with syntax highlighting
- **Improved Logging**: Structured logging with configurable levels
- **Resource Management**: Better memory management with streaming processing
- **Error Messages**: More informative error messages with context

### 🗑️ Removed

- **Deprecated Features**:
  - `--regex` flag (replaced by boolean expressions)
  - `--line-numbers` option (use external tools like grep -n)
  - `--count-only` option (replaced by `--stats` + `--quiet`)
- **Legacy APIs**:
  - Old `LogFilter` class (replaced by `ProcessingPipeline`)
  - Simple `Matcher` class (replaced by `Tokenizer/Parser/Evaluator`)
  - INI configuration support (replaced by YAML)

### 🐛 Fixed

- **Race Conditions**: Thread-safe statistics collection
- **Memory Leaks**: Proper resource cleanup in file handlers
- **Encoding Issues**: Better handling of various file encodings
- **Edge Cases**: Comprehensive testing revealed and fixed numerous edge cases
- **Error Recovery**: Improved error handling and recovery mechanisms

### 📊 Performance

- **Baseline**: ~5,000 lines/second (single worker)
- **Scaling**: Linear scaling with worker count up to CPU cores
- **Memory**: ~50-100 MB base + ~10 MB per worker
- **Latency**: ~30 μs per line (parsing + evaluation)
- **Throughput**: Tested up to 100 GB of logs, maintains consistent performance

### 🔐 Security

- **No Critical Vulnerabilities**: Bandit security scan passes
- **Input Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Safe error handling, no information leakage
- **Dependency Audit**: All dependencies audited for vulnerabilities

### 📦 Package

- **Build System**: Modern setuptools with pyproject.toml
- **Type Stubs**: Complete type information for mypy
- **Entry Points**: `log-filter` command-line tool
- **Optional Dependencies**: Modular dependencies for dev, async, etc.

### 🏗️ Architecture

- **Domain-Driven Design**: Clear separation of concerns
- **Pipeline Architecture**: Producer-consumer pattern for processing
- **Factory Pattern**: File handler factories for extensibility
- **Strategy Pattern**: Pluggable filter strategies
- **Observer Pattern**: Statistics collection and reporting

### 🧪 Testing

- **Unit Tests**: 500+ unit tests covering all components
- **Integration Tests**: 150+ integration tests for workflows
- **Property Tests**: 50+ property-based tests with Hypothesis
- **Performance Tests**: Benchmarks for key operations
- **Coverage**: 89.73% code coverage (target: 90%+)

### 📝 Documentation

- **9 API Documentation Files**: ~6,000 lines of API reference
- **6 User Guides**: Installation, quick start, configuration, troubleshooting, performance, deployment
- **Migration Guide**: Complete v1.x to v2.0 upgrade path
- **Code Examples**: 100+ code examples throughout documentation
- **Docker Support**: Complete Docker and Kubernetes examples

### 🚀 Deployment

- **Docker**: Multi-stage optimized Dockerfile
- **Docker Compose**: Multiple service configurations
- **Kubernetes**: CronJob and Job manifests with ConfigMaps
- **Systemd**: Service and timer unit files
- **Cloud**: Examples for AWS, Azure, GCP

### 🙏 Acknowledgments

Special thanks to all contributors, testers, and users who provided feedback during development.

---

## [1.9.0] - 2024-12-15 (Legacy)

### Added
- Basic string matching
- Single-threaded processing
- Simple file pattern matching
- INI configuration support

### Changed
- Performance improvements
- Bug fixes

---

## Migration Notes

**Upgrading from v1.x to v2.0:**

v2.0 is a major release with breaking changes. Please read the [Migration Guide](docs/migration.md) carefully before upgrading.

Key changes:
1. Python 3.10+ required
2. CLI argument changes (--pattern → -i/--include)
3. YAML configuration required (INI deprecated)
4. Python API restructured (new import paths)
5. Case-insensitive search by default
6. Overwrite protection by default
7. Multi-threaded by default

**Benefits of upgrading:**
- ✅ 5-10x faster with multi-threading
- ✅ Boolean expression support (AND, OR, NOT)
- ✅ Built-in statistics and monitoring
- ✅ Date/time filtering
- ✅ Better error messages
- ✅ Production-ready (706 tests, 89.73% coverage)

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes (v1.x → v2.0)
- **MINOR**: New features, backward compatible (v2.0 → v2.1)
- **PATCH**: Bug fixes, backward compatible (v2.0.0 → v2.0.1)

## Links

- **Homepage**: https://github.com/RomaYushchenko/log-filter
- **Documentation**: https://log-filter.readthedocs.io
- **Bug Tracker**: https://github.com/RomaYushchenko/log-filter/issues
- **PyPI**: https://pypi.org/project/log-filter/
