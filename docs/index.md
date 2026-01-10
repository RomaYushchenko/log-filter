# Log Filter Documentation

Welcome to the Log Filter documentation - a high-performance log filtering tool with boolean expression support.

## Quick Links

### Getting Started
- **[Installation Guide](installation.md)** - Get started quickly
- **[Quick Start](quickstart.md)** - Learn the basics in 5 minutes
- **[Configuration](configuration.md)** - Complete configuration reference

### Tutorials (Step-by-Step)
- **[Beginner Tutorial](tutorials/beginner.md)** - First steps with log-filter (10 min)
- **[Intermediate Tutorial](tutorials/intermediate.md)** - Advanced filtering techniques (20 min)
- **[Advanced Tutorial](tutorials/advanced.md)** - Production deployment (30 min)
- **[Docker Tutorial](tutorials/docker.md)** - Containerization guide (15 min)
- **[Kubernetes Tutorial](tutorials/kubernetes.md)** - K8s deployment (20 min)

### User Guides
- **[Advanced Usage](advanced_usage.md)** - Multi-worker configuration, large files, complex expressions
- **[Integration Guide](integration_guide.md)** - CI/CD, monitoring, log aggregation systems
- **[Error Handling](error_handling.md)** - Exception reference, debugging, error recovery

### Reference Documentation
- **[CLI Reference](reference/cli_reference.md)** - Complete command-line options
- **[Configuration Reference](reference/config_reference.md)** - YAML/JSON configuration guide
- **[API Reference](api/index.rst)** - Complete API documentation
- **[Architecture](architecture.md)** - System design and architecture
- **[Performance Tuning](performance.md)** - Optimize for maximum speed
- **[Troubleshooting](troubleshooting.md)** - Solve common issues

### Examples & Use Cases
- **[Examples Overview](examples/README.md)** - Real-world scenarios
- **[Monitoring Examples](examples/monitoring.md)** - Application monitoring patterns
- **[DevOps Examples](examples/devops.md)** - CI/CD integration patterns
- **[Security Examples](examples/security.md)** - Security analysis patterns

### Contributing
- **[Contributing](contributing.md)** - Contribution guidelines

## Features

- **Boolean Expressions**: Search with AND, OR, NOT operators
- **High Performance**: Multi-threaded processing (200K+ lines/sec on 8-core CPU)
- **Type-Safe**: Full type hints with mypy validation
- **Comprehensive Testing**: 706 tests with 89.73% coverage
- **Production-Ready**: Robust error handling and monitoring
- **Flexible Configuration**: YAML/JSON config files with environment variable support
- **Multiple Output Formats**: Text, JSON, CSV with customizable formatting
- **Large File Support**: Streaming processing handles GB+ files efficiently

## Quick Start

Install via pip:

```bash
pip install log-filter
```

Basic usage:

```bash
# Search for errors
log-filter "ERROR" /var/log

# Boolean expression
log-filter "(ERROR OR CRITICAL) AND database" /var/log

# Output to file
log-filter "ERROR" /var/log -o errors.txt --stats
```

## API Modules

- **[Core](api/core.rst)** - Expression parsing and evaluation
- **[Domain](api/domain.rst)** - Business models and filtering
- **[Config](api/config.rst)** - Configuration management
- **[Infrastructure](api/infrastructure.rst)** - File I/O and handlers
- **[Processing](api/processing.rst)** - Multi-threaded processing pipeline
- **[Statistics](api/statistics.rst)** - Metrics and reporting
- **[Utils](api/utils.rst)** - Logging, progress, highlighting
- **[CLI](api/cli.rst)** - Command-line interface
200,000+ lines/second (8-core CPU, optimized)
- **Single Worker**: ~25,000 lines/second
- **Scalability**: Linear scaling up to CPU core count
- **Memory**: ~50-100 MB base + ~10 MB per worker
- **CPU Efficiency**: ~90% utilization on multi-core systems
- **Large Files**: Handles 100+ GB datasets with streaming
- **Test Coverage**: 89.73% (706 tests passing)
- **Scalability**: Linear scaling with CPU cores
- **Memory**: Efficient streaming (handles GB+ files)

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
quickstart
configuration
```

```{toctree}
:maxdepth: 2
:caption: Tutorials

tutorials/beginner
tutorials/intermediate
tutorials/advanced
tutorials/docker
tutorials/kubernetes
```

```{toctree}
:maxdepth: 2
:caption: User Guides

advanced_usage
integration_guide
error_handling
performance
troubleshooting
deployment
migration
```

```{toctree}
:maxdepth: 2
:caption: Reference

reference/cli_reference
reference/config_reference
architecture
```

```{toctree}
:maxdepth: 2
:caption: Examples

examples/README
examples/monitoring
examples/devops
examples/security
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
```

```{toctree}
:maxdepth: 2
:caption: Developer Guide

contributing
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
