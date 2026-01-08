# Installation

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Basic Installation

Install from PyPI:

```bash
pip install log-filter
```

## Development Installation

For development, clone the repository and install with dev dependencies:

```bash
git clone https://github.com/akvelon/log-filter.git
cd log-filter
pip install -r requirements-dev.txt
pip install -e .
```

## Optional Dependencies

### Async Support

For async file operations:

```bash
pip install log-filter[async]
```

### All Features

To install all optional dependencies:

```bash
pip install log-filter[all]
```

## Verify Installation

Verify the installation:

```bash
log-filter --version
```

## Next Steps

Continue to the [Quick Start Guide](quickstart.md) to learn how to use Log Filter.
