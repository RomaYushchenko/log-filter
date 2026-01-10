# Installation

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation Methods

### Method 1: Development/Local Installation (Recommended for Development)

**Use this method if:**
- You're developing or modifying the code
- The package is not yet published to PyPI
- You want changes to take effect immediately without reinstalling

#### Step 1: Get the Source Code

```bash
# Option A: Clone from GitHub
git clone https://github.com/RomaYushchenko/log-filter.git
cd log-filter

# Option B: Navigate to your local project directory
cd C:\Users\your-username\path\to\log-filter
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\activate

# On Windows (CMD):
.venv\Scripts\activate.bat

# On Linux/macOS:
source .venv/bin/activate
```

#### Step 3: Install in Editable Mode

```bash
# Basic installation (runtime dependencies only)
pip install -e .

# With development dependencies (testing, linting, etc.)
pip install -e ".[dev]"

# With async support
pip install -e ".[async]"

# With all optional dependencies
pip install -e ".[all]"
```

**What `-e` (editable mode) does:**
- Links package to source directory
- Code changes take effect immediately (no reinstall needed)
- Perfect for development and testing
- Creates `log-filter` command in PATH

#### Step 4: Verify Installation

```bash
# Check version
log-filter --version
# Expected: log-filter 2.0.0

# Verify Python import
python -c "import log_filter; print(log_filter.__version__)"
# Expected: 2.0.0

# Run help command
log-filter --help

# Quick functionality test
echo "2026-01-10 ERROR Test message" > test.log
log-filter "ERROR" test.log
rm test.log
```

---

### Method 2: Production Installation from PyPI

**Use this method when:**
- Package is published to PyPI
- You want stable release
- You're an end user (not developing)

```bash
# Install latest stable version
pip install log-filter

# Install specific version
pip install log-filter==2.0.0

# Upgrade to latest
pip install --upgrade log-filter
```

---

### Method 3: Install from Built Wheel

**Use this method for:**
- Testing the build before publishing
- Sharing with team members without PyPI

#### Build the Package

```bash
# Install build tools
pip install --upgrade build

# Build wheel and source distribution
python -m build

# Output in dist/ directory:
# - log_filter-2.0.0-py3-none-any.whl
# - log_filter-2.0.0.tar.gz
```

#### Install from Wheel

```bash
# Install from wheel
pip install dist/log_filter-2.0.0-py3-none-any.whl

# Or from source distribution
pip install dist/log_filter-2.0.0.tar.gz
```

---

## Optional Dependencies

### Async Support

For async file operations:

```bash
# From PyPI
pip install log-filter[async]

# Development mode
pip install -e ".[async]"
```

### Development Tools

Includes testing, linting, type checking, documentation:

```bash
# Development mode with all dev tools
pip install -e ".[dev]"
```

This installs:
- **Testing**: pytest, pytest-cov, hypothesis
- **Code Quality**: black, isort, flake8, mypy, pylint
- **Documentation**: sphinx, sphinx-rtd-theme
- **Utilities**: pre-commit, tqdm

### All Features

To install all optional dependencies:

```bash
# From PyPI
pip install log-filter[all]

# Development mode
pip install -e ".[all]"
```

---

## Platform-Specific Notes

### Windows

#### PowerShell Execution Policy

If you get "cannot be loaded because running scripts is disabled":

```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run with bypass (one-time)
powershell -ExecutionPolicy Bypass
```

#### Long Path Support

For handling files with long paths:

```powershell
# Enable long path support (requires admin)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Linux/macOS

#### System-Wide Installation

```bash
# Install for current user (no sudo needed)
pip install --user -e .

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### Permission Issues

```bash
# Use --user flag
pip install --user -e .

# Or fix ownership
sudo chown -R $USER:$USER /path/to/log-filter
```

---

## Upgrading

### Development Installation

```bash
# Code changes take effect immediately (no upgrade needed)
# If dependencies changed:
pip install -e . --upgrade
```

### Production Installation

```bash
# Upgrade to latest version
pip install --upgrade log-filter

# Upgrade to specific version
pip install --upgrade log-filter==2.1.0
```

---

## Uninstalling

```bash
# Uninstall package
pip uninstall log-filter

# Clean build artifacts (optional)
rm -rf dist/ build/ *.egg-info
```

---

## Troubleshooting

### Issue: "pip: command not found"

**Solution:**
```bash
# Use python -m pip instead
python -m pip install -e .

# Or install pip
python -m ensurepip --upgrade
```

### Issue: "No module named 'setuptools'"

**Solution:**
```bash
# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

### Issue: "Permission denied"

**Solution:**
```bash
# Option 1: Use --user flag
pip install --user -e .

# Option 2: Use virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -e .

# Option 3: Run as administrator (Windows)
# Right-click PowerShell → Run as Administrator
```

### Issue: "Microsoft Visual C++ required" (Windows)

**Solution:**
```bash
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or use pre-built wheels
pip install --only-binary :all: -e .
```

### Issue: Package already installed

**Solution:**
```bash
# Uninstall first
pip uninstall log-filter

# Reinstall
pip install -e .
```

### Issue: Changes not reflected after editing code

**Causes & Solutions:**

1. **Not installed in editable mode:**
   ```bash
   pip install -e .  # Use -e flag
   ```

2. **Wrong virtual environment:**
   ```bash
   which python  # Linux/macOS
   where python  # Windows
   # Ensure it's in your .venv directory
   ```

3. **Python bytecode cache:**
   ```bash
   # Clear cache
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name "*.pyc" -delete
   ```

---

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Command is available
log-filter --version

# 2. Python import works
python -c "import log_filter; print(log_filter.__version__)"

# 3. Help is accessible
log-filter --help

# 4. Basic functionality works
echo "2026-01-10 10:00:00 ERROR Test error" > test.log
echo "2026-01-10 10:00:01 INFO Test info" >> test.log
log-filter "ERROR" test.log
rm test.log

# 5. Dependencies installed
pip show pyyaml

# 6. (Optional) Run tests
pytest
```

---

## Next Steps

- **[Quick Start Guide](quickstart.md)** - Learn basic usage
- **[Configuration](configuration.md)** - Configure log-filter
- **[CLI Reference](reference/cli_reference.md)** - Complete command reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
