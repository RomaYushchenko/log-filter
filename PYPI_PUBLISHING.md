# PyPI Publishing Guide

Complete guide for publishing log-filter to PyPI.

## 📋 Pre-Publishing Checklist

Before publishing to PyPI, ensure:

- [x] All tests passing (706 tests, 89.73% coverage)
- [x] Documentation complete and builds successfully
- [x] CHANGELOG.md updated with v2.0.0 release notes
- [x] README.md updated with current features
- [x] LICENSE file present (MIT)
- [x] pyproject.toml configured correctly
- [x] Version number updated (2.0.0)
- [x] Git repository tagged with release version
- [x] Package builds successfully (wheel and sdist)

## 🏗️ Build Package

### Install Build Tools

```bash
pip install --upgrade build twine
```

### Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build

# Verify output
ls -lh dist/
# Expected:
#   log_filter-2.0.0-py3-none-any.whl
#   log_filter-2.0.0.tar.gz
```

### Check Package Contents

```bash
# Inspect wheel contents
unzip -l dist/log_filter-2.0.0-py3-none-any.whl

# Inspect source distribution
tar -tzf dist/log_filter-2.0.0.tar.gz
```

### Verify Package Metadata

```bash
# Check package metadata
python -m twine check dist/*

# Should output:
# Checking dist/log_filter-2.0.0-py3-none-any.whl: PASSED
# Checking dist/log_filter-2.0.0.tar.gz: PASSED
```

## 🧪 Test Installation

### Local Installation Test

```bash
# Create test virtual environment
python -m venv test-venv
source test-venv/bin/activate  # or test-venv\Scripts\activate on Windows

# Install from wheel
pip install dist/log_filter-2.0.0-py3-none-any.whl

# Verify installation
log-filter --version
python -c "import log_filter; print(log_filter.__version__)"

# Test functionality
log-filter "ERROR" /tmp/test.log --dry-run

# Deactivate
deactivate
rm -rf test-venv
```

### Install from Source Distribution

```bash
# Create test environment
python -m venv test-sdist
source test-sdist/bin/activate

# Install from source
pip install dist/log_filter-2.0.0.tar.gz

# Verify
log-filter --version

# Cleanup
deactivate
rm -rf test-sdist
```

## 🧪 TestPyPI (Recommended First)

Test the package on TestPyPI before publishing to production PyPI.

### 1. Register on TestPyPI

Create account at: https://test.pypi.org/account/register/

### 2. Configure TestPyPI

Create/update `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PYPI-TOKEN-HERE
```

**Security**: Use API tokens, not passwords!

### 3. Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Expected output:
# Uploading distributions to https://test.pypi.org/legacy/
# Uploading log_filter-2.0.0-py3-none-any.whl
# Uploading log_filter-2.0.0.tar.gz
# View at: https://test.pypi.org/project/log-filter/2.0.0/
```

### 4. Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test-testpypi
source test-testpypi/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ log-filter

# Note: --extra-index-url allows installing dependencies from main PyPI

# Verify
log-filter --version
log-filter "ERROR" /tmp/test.log --dry-run

# Cleanup
deactivate
rm -rf test-testpypi
```

### 5. Verify TestPyPI Page

Visit: https://test.pypi.org/project/log-filter/

Check:
- [ ] Package name and version correct
- [ ] README renders correctly
- [ ] Classifiers displayed properly
- [ ] Dependencies listed
- [ ] License shown
- [ ] Project links work
- [ ] Download buttons present

## 🚀 Production PyPI

After successful TestPyPI verification, publish to production PyPI.

### 1. Register on PyPI

Create account at: https://pypi.org/account/register/

### 2. Generate API Token

1. Go to: https://pypi.org/manage/account/token/
2. Create token for: "Entire account" or "Project: log-filter"
3. Copy token (starts with `pypi-`)
4. Store securely (you won't see it again!)

### 3. Configure PyPI

Update `~/.pypirc`:

```ini
[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE
```

Or use environment variables:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-PRODUCTION-TOKEN-HERE
```

### 4. Final Verification

Before uploading:

```bash
# Verify package again
python -m twine check dist/*

# Check version
cat pyproject.toml | grep version

# Ensure clean git state
git status

# Ensure all changes committed
git diff

# Tag release
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0
```

### 5. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Expected output:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading log_filter-2.0.0-py3-none-any.whl
# Uploading log_filter-2.0.0.tar.gz
# View at: https://pypi.org/project/log-filter/2.0.0/
```

**⚠️ Warning**: Once uploaded, you CANNOT replace or delete a release. Version numbers are permanent.

### 6. Verify Production Installation

```bash
# Wait 1-2 minutes for PyPI to update

# Create test environment
python -m venv test-pypi
source test-pypi/bin/activate

# Install from PyPI
pip install log-filter

# Verify
log-filter --version  # Should show 2.0.0
python -c "import log_filter; print(log_filter.__version__)"

# Test functionality
echo "ERROR: Test error" > /tmp/test.log
log-filter "ERROR" /tmp/test.log

# Cleanup
deactivate
rm -rf test-pypi
```

### 7. Verify PyPI Page

Visit: https://pypi.org/project/log-filter/

Verify:
- [ ] Version 2.0.0 listed
- [ ] README displays correctly with badges
- [ ] All project links functional
- [ ] Classifiers accurate
- [ ] Dependencies correct
- [ ] Download stats initializing
- [ ] Release history shown

## 📢 Post-Release Actions

### 1. GitHub Release

Create GitHub release:

```bash
# Already tagged: git tag -a v2.0.0 -m "Release v2.0.0"

# Push tag
git push origin v2.0.0

# Create release on GitHub
# Go to: https://github.com/RomaYushchenko/log-filter/releases/new
# - Tag: v2.0.0
# - Title: "log-filter v2.0.0 - Production Ready"
# - Description: Copy from RELEASE_NOTES.md
# - Attach: dist/log_filter-2.0.0-py3-none-any.whl
# - Attach: dist/log_filter-2.0.0.tar.gz
```

### 2. Update Documentation

```bash
# Build and deploy documentation
cd docs
sphinx-build -b html . _build

# If using Read the Docs:
# - Go to https://readthedocs.org/projects/log-filter/
# - Trigger new build
# - Set v2.0.0 as latest version
```

### 3. Announcement

**Email/Blog Post:**

Subject: "log-filter v2.0.0 Released - 5-10x Faster with Boolean Expressions"

Key points:
- Major performance improvements (5-10x faster)
- Boolean expression support
- Production-ready quality (706 tests, 89.73% coverage)
- Comprehensive documentation
- Migration guide available

**Social Media:**

```
🚀 log-filter v2.0.0 is here!

✨ Boolean expressions (AND, OR, NOT)
⚡ 5-10x faster with multi-threading
📊 Built-in statistics
🐳 Docker & Kubernetes ready
✅ Production tested (706 tests, 89.73% coverage)

pip install log-filter

https://pypi.org/project/log-filter/
https://log-filter.readthedocs.io

#python #logging #devtools
```

**GitHub Discussions:**

Create announcement post at: https://github.com/RomaYushchenko/log-filter/discussions

### 4. Monitor Initial Adoption

```bash
# Check PyPI stats
# https://pypistats.org/packages/log-filter

# Monitor issues
# https://github.com/RomaYushchenko/log-filter/issues

# Watch discussions
# https://github.com/RomaYushchenko/log-filter/discussions
```

## 🔄 Update Process for Future Releases

### Patch Release (2.0.x)

Bug fixes, no breaking changes:

```bash
# Update version in pyproject.toml
version = "2.0.1"

# Update CHANGELOG.md
## [2.0.1] - 2026-01-15
### Fixed
- Fixed issue #123: ...

# Build and upload
python -m build
python -m twine upload dist/*
```

### Minor Release (2.x.0)

New features, backward compatible:

```bash
# Update version
version = "2.1.0"

# Update CHANGELOG.md
## [2.1.0] - 2026-02-01
### Added
- New feature: ...
### Changed
- Improved: ...

# Build and upload
python -m build
python -m twine upload dist/*
```

### Major Release (x.0.0)

Breaking changes:

```bash
# Update version
version = "3.0.0"

# Update CHANGELOG.md with migration guide
# Build and upload
python -m build
python -m twine upload dist/*

# Create comprehensive migration guide
```

## 🛠️ Troubleshooting

### "Filename already exists"

**Problem**: Version already uploaded to PyPI.

**Solution**: 
- Cannot replace releases on PyPI
- Increment version number
- Re-build and re-upload

```bash
# Update version in pyproject.toml
version = "2.0.1"

# Rebuild
rm -rf dist/
python -m build

# Upload
python -m twine upload dist/*
```

### "Invalid authentication"

**Problem**: API token incorrect or expired.

**Solution**:
1. Generate new token at https://pypi.org/manage/account/token/
2. Update `~/.pypirc` with new token
3. Retry upload

### "Package name not found"

**Problem**: Package name not registered or typo.

**Solution**:
- First upload automatically registers name
- Check spelling matches pyproject.toml
- Ensure not using reserved name

### Upload Verification Failed

**Problem**: `twine check` fails.

**Solution**:

```bash
# Check what's wrong
python -m twine check dist/* --strict

# Common issues:
# - Missing README.md
# - Invalid RST/Markdown in README
# - Missing LICENSE
# - Invalid pyproject.toml

# Fix issues and rebuild
python -m build
```

## 📚 References

- **PyPI Documentation**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **PEP 517**: Build system specification
- **PEP 518**: pyproject.toml specification
- **Semantic Versioning**: https://semver.org/

## 🔐 Security Best Practices

1. **Use API Tokens**: Never use passwords for PyPI
2. **Limit Token Scope**: Use project-specific tokens when possible
3. **Rotate Tokens**: Change tokens periodically
4. **Secure Storage**: Store tokens in environment variables or secure vaults
5. **CI/CD Secrets**: Use GitHub Secrets or similar for automated publishing
6. **Two-Factor Auth**: Enable 2FA on PyPI account

## ✅ Release Checklist

Final checklist before publishing:

- [ ] All tests pass (pytest)
- [ ] Code coverage ≥ 89% (pytest-cov)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (pylint, flake8)
- [ ] Documentation builds (sphinx)
- [ ] CHANGELOG.md updated
- [ ] README.md current
- [ ] Version bumped in pyproject.toml
- [ ] Git changes committed
- [ ] Git tag created (v2.0.0)
- [ ] Package built (python -m build)
- [ ] Package verified (twine check)
- [ ] Tested on TestPyPI
- [ ] Uploaded to PyPI
- [ ] Installation verified
- [ ] GitHub release created
- [ ] Documentation deployed
- [ ] Announcement published

## 🎉 Success!

Congratulations on publishing log-filter v2.0.0 to PyPI! 🎊

Monitor adoption and be ready to:
- Respond to issues quickly
- Fix critical bugs (patch releases)
- Gather user feedback
- Plan next features

**Good luck!** 🚀
