# Contributing to Log Filter

Thank you for considering contributing to Log Filter! This document provides guidelines for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/log-filter.git
   cd log-filter
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality Standards

### Formatting

We use Black for code formatting:
```bash
black src/ tests/
```

### Import Sorting

We use isort for import sorting:
```bash
isort src/ tests/
```

### Linting

Run flake8 for linting:
```bash
flake8 src/ tests/
```

### Type Checking

Run mypy for type checking:
```bash
mypy src/log_filter/
```

### All Quality Checks

Run all checks at once:
```bash
pre-commit run --all-files
```

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/performance/    # Performance tests only
```

### Test Coverage

Generate coverage report:
```bash
pytest --cov=log_filter --cov-report=html
```

View the report by opening `htmlcov/index.html`.

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_parser_handles_nested_expressions`
- Follow AAA pattern: Arrange, Act, Assert
- Mock external dependencies

## Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Write or update tests

4. Ensure all tests pass and code quality checks pass

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all CI checks pass
- Update documentation if needed
- Add tests for new features
- Keep changes focused and atomic

## Code Style Guidelines

- Follow PEP 8
- Maximum line length: 100 characters
- Use type hints for all functions
- Write docstrings in Google style
- Keep functions small and focused
- Prefer explicit over implicit

## Documentation

- Update relevant documentation for any changes
- Add docstrings to new functions and classes
- Use type hints in signatures
- Include examples in docstrings when helpful

## Release Process

Releases are handled by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push tag to trigger release workflow

## Questions?

If you have questions, please:
- Open an issue for discussion
- Check existing issues and documentation
- Reach out to maintainers

Thank you for contributing! 🎉
