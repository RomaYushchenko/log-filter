---
applyTo: '**'
---

# Internal Python Code Writing Guidelines

## 📋 General Principles

This guideline is mandatory for all code generation in this project. It is applied automatically without explicit user request.

---

## 1️⃣ Code Quality

### Code Standards
- **Always follow PEP 8** (Style Guide for Python Code)
  - Maximum line length: 100 characters (as adopted in the project)
  - Indentation: 4 spaces
  - Blank lines: 2 between classes and top-level functions, 1 inside classes
  
### Clean Code
- Code should be **self-documenting** and easy to read
- Avoid **magic numbers** — use constants with descriptive names
- Apply the **DRY principle** (Don't Repeat Yourself)
- Follow **SOLID principles** for object-oriented code
- Limit **function complexity** (cyclomatic complexity ≤ 10)

### Naming Conventions
- **Functions and methods**: `snake_case` — `def process_log_file()`
- **Classes**: `PascalCase` — `class LogFileParser:`
- **Constants**: `UPPER_SNAKE_CASE` — `MAX_BUFFER_SIZE = 8192`
- **Private attributes**: `_leading_underscore` — `def _internal_method()`
- **Names must be descriptive** and reflect their purpose
  - ❌ Bad: `def proc(d):`
  - ✅ Good: `def process_log_data(log_entries):`

### Comments
- Comments explain **"why"**, not **"what"**
- Code should be clear enough without comments
- Use comments for complex logic or non-standard solutions
- Comments start with a capital letter and end with a period

```python
# Using binary search instead of linear search for O(log n) optimization.
result = binary_search(sorted_list, target)
```

---

## 2️⃣ Explanation Before Code

### Action Plan
Before writing code, **always formulate**:
1. **Goal**: what needs to be implemented
2. **Approach**: which algorithms/data structures are chosen
3. **Justification**: why this particular approach
4. **Dependencies**: which modules/classes will be used

### Example Explanation
```
Goal: Create a function to filter logs by time range.

Approach:
- Use datetime for parsing timestamps
- Apply a generator to save memory when processing large files
- Implement input parameter validation

Justification:
- Generators allow processing files larger than RAM
- datetime provides reliable parsing of various time formats
- Validation prevents errors at runtime
```

---

## 3️⃣ Static Analysis & Autofix

### Tools
Use the following tools for code verification:

1. **black** — automatic formatting
   ```bash
   black --line-length 100 <file.py>
   ```

2. **pylint** — static analysis
   ```bash
   pylint --max-line-length=100 <file.py>
   ```

3. **flake8** — style checking
   ```bash
   flake8 --max-line-length=100 <file.py>
   ```

4. **mypy** — type checking (if using type hints)
   ```bash
   mypy --strict <file.py>
   ```

### Verification Process
1. After writing code, **run verification** using pylint/flake8
2. **Automatically fix** style violations using black
3. **Manually fix** logical errors and complex logic
4. **Add a report**: what violations were found and fixed

### Example Report
```
✅ Static analysis completed:
- black: 3 files formatted
- pylint: score 9.8/10
  - Fixed: missing docstrings (C0114, C0115)
  - Fixed: lines too long (C0301)
- flake8: no violations found
```

---

## 4️⃣ Documentation

### Docstrings
**Every function, class, and module** must have a docstring in Google Style or NumPy Style format.

#### Google Style Format (recommended)
```python
def filter_logs_by_time(log_file: str, start_time: datetime, end_time: datetime) -> List[str]:
    """Filters logs by the specified time range.
    
    Reads the log file and returns only those entries whose timestamp
    is between start_time and end_time (inclusive).
    
    Args:
        log_file: Path to the log file.
        start_time: Start of the time range (inclusive).
        end_time: End of the time range (inclusive).
        
    Returns:
        List of log lines that match the filter criteria.
        
    Raises:
        FileNotFoundError: If the log_file does not exist.
        ValueError: If start_time > end_time.
        
    Example:
        >>> logs = filter_logs_by_time(
        ...     "app.log",
        ...     datetime(2026, 2, 1, 10, 0, 0),
        ...     datetime(2026, 2, 1, 12, 0, 0)
        ... )
        >>> len(logs)
        42
    """
    pass
```

#### Docstrings for Classes
```python
class LogFileParser:
    """Parser for processing structured log files.
    
    Supports various log formats (JSON, plain text, syslog) and
    provides a unified interface for their processing.
    
    Attributes:
        file_path: Path to the log file.
        encoding: File encoding (default 'utf-8').
        buffer_size: Read buffer size (bytes).
        
    Example:
        >>> parser = LogFileParser("app.log")
        >>> for entry in parser.parse():
        ...     print(entry.timestamp, entry.message)
    """
    
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        """Initializes the log parser.
        
        Args:
            file_path: Path to the log file.
            encoding: File encoding.
        """
        pass
```

### Documentation References
When using non-standard constructs or complex APIs, add references:

```python
# Using concurrent.futures for parallel processing.
# Documentation: https://docs.python.org/3/library/concurrent.futures.html
from concurrent.futures import ThreadPoolExecutor

# Context Manager pattern for safe resource handling.
# PEP 343: https://www.python.org/dev/peps/pep-0343/
with open(file_path, 'r') as f:
    data = f.read()
```

---

## 5️⃣ Result and Code Readiness

### Production-Ready Code
Code must be:
- ✅ **Complete** — without missing implementations
- ✅ **Tested** — works without errors
- ✅ **Documented** — with docstrings and comments
- ✅ **Verified** — passed static analysis
- ✅ **Formatted** — complies with PEP 8

### Drafts and Templates
If code is **incomplete** or a **template**, clearly mark it:

```python
def process_data(data: List[Dict]) -> List[Dict]:
    """[TEMPLATE] Processes input data.
    
    TODO: Implement specific processing logic.
    
    Args:
        data: Input data for processing.
        
    Returns:
        Processed data.
    """
    # TODO: Add data validation
    # TODO: Add data transformation
    raise NotImplementedError("This method requires implementation")
```

### Comments About Limitations
If there are limitations or known issues:

```python
def parse_logs(file_path: str) -> Iterator[LogEntry]:
    """Parses a log file.
    
    Note:
        Current implementation supports only UTF-8 encoding.
        For other encodings, add an encoding parameter.
        
    Limitations:
        - Maximum file size: 10 GB
        - Does not support compressed files (.gz, .zip)
    """
    pass
```

---

## 6️⃣ Type Hints

### Always Use Type Hints
Type hints improve readability and allow detection of errors during static analysis.

```python
from typing import List, Dict, Optional, Union, Tuple, Iterator

def parse_config(
    file_path: str,
    default_values: Optional[Dict[str, str]] = None
) -> Dict[str, Union[str, int, bool]]:
    """Parses a configuration file.
    
    Args:
        file_path: Path to the configuration file.
        default_values: Default values (optional).
        
    Returns:
        Dictionary with settings.
    """
    pass
```

### Complex Types
For complex types, use `typing`:

```python
from typing import Callable, TypeVar, Generic

T = TypeVar('T')

def apply_transformation(
    data: List[T],
    transform_fn: Callable[[T], T]
) -> List[T]:
    """Applies a transformation function to each element.
    
    Args:
        data: Input data list.
        transform_fn: Transformation function.
        
    Returns:
        Transformed list.
    """
    return [transform_fn(item) for item in data]
```

---

## 7️⃣ Error Handling

### Use Specific Exceptions
```python
# ❌ Bad
try:
    data = parse_file(file_path)
except Exception:
    pass

# ✅ Good
try:
    data = parse_file(file_path)
except FileNotFoundError as e:
    logger.error(f"File not found: {file_path}")
    raise
except json.JSONDecodeError as e:
    logger.error(f"JSON parsing error: {e}")
    raise ValueError(f"Invalid file format: {file_path}") from e
```

### Custom Exceptions
Create custom exceptions for specific errors:

```python
class LogParsingError(Exception):
    """Exception raised for log parsing errors."""
    pass

class InvalidLogFormatError(LogParsingError):
    """Exception raised for invalid log format."""
    pass
```

---

## 8️⃣ Testing

### Test Structure
Every function should have corresponding unit tests:

```python
import pytest
from log_filter.parser import parse_log_entry

def test_parse_log_entry_valid():
    """Test parsing a valid log entry."""
    log_line = "2026-02-03 10:30:45 [INFO] Application started"
    entry = parse_log_entry(log_line)
    
    assert entry.timestamp == datetime(2026, 2, 3, 10, 30, 45)
    assert entry.level == "INFO"
    assert entry.message == "Application started"

def test_parse_log_entry_invalid():
    """Test parsing an invalid log entry."""
    with pytest.raises(ValueError):
        parse_log_entry("invalid log format")
```

---

## 9️⃣ Control Checklist

Before completing, verify:

- [ ] Code complies with PEP 8
- [ ] All functions have docstrings
- [ ] Type hints are used
- [ ] Error handling is added
- [ ] Variable/function/class names are clear
- [ ] No magic numbers
- [ ] Comments added for complex logic
- [ ] black/pylint/flake8 executed
- [ ] Code is ready for use or marked as template
- [ ] Documentation references added (if needed)

---

## 🎯 Application

**This guideline is applied automatically** when generating any code without explicit user request.

Each generated code should be accompanied by:
1. Brief plan/justification
2. Fully documented and verified code
3. Static analysis report (if applicable)
