"""Unit tests for custom exceptions."""

import pytest

from log_filter.core.exceptions import (
    ConfigurationError,
    EvaluationError,
    FileHandlingError,
    LogFilterException,
    ParseError,
    RecordSizeExceededError,
    TokenizationError,
)


class TestLogFilterException:
    """Test base exception class."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        exc = LogFilterException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_base_exception_inheritance(self):
        """Test that all custom exceptions inherit from base."""
        assert issubclass(ParseError, LogFilterException)
        assert issubclass(TokenizationError, LogFilterException)
        assert issubclass(EvaluationError, LogFilterException)
        assert issubclass(ConfigurationError, LogFilterException)
        assert issubclass(FileHandlingError, LogFilterException)
        assert issubclass(RecordSizeExceededError, LogFilterException)

    def test_base_exception_can_be_raised(self):
        """Test that base exception can be raised and caught."""
        with pytest.raises(LogFilterException) as exc_info:
            raise LogFilterException("Test error")
        assert "Test error" in str(exc_info.value)


class TestParseError:
    """Test ParseError exception."""

    def test_simple_message(self):
        """Test ParseError with just a message."""
        exc = ParseError("Invalid syntax")
        assert "Invalid syntax" in str(exc)
        assert exc.message == "Invalid syntax"
        assert exc.position is None
        assert exc.expression == ""

    def test_with_position_no_expression(self):
        """Test ParseError with position but no expression."""
        exc = ParseError("Invalid syntax", position=5)
        assert "Invalid syntax" in str(exc)
        assert exc.position == 5
        assert exc.expression == ""

    def test_with_position_and_expression(self):
        """Test ParseError with position and expression."""
        exc = ParseError("Invalid syntax", position=5, expression="ERROR AND")
        error_str = str(exc)
        assert "Invalid syntax" in error_str
        assert "ERROR AND" in error_str
        assert "^" in error_str  # Pointer
        assert exc.position == 5
        assert exc.expression == "ERROR AND"

    def test_pointer_visualization(self):
        """Test that pointer appears at correct position."""
        exc = ParseError("Unexpected token", position=3, expression="AND OR NOT")
        error_str = str(exc)
        lines = error_str.split("\n")
        assert len(lines) >= 3
        # Pointer should be on third line with spaces before ^
        pointer_line = lines[2].strip()
        assert pointer_line == "^"
        # Should have exactly position+2 characters before ^ (2 spaces from formatting + position spaces)
        assert "^" in lines[2]
        assert lines[2].index("^") == 3 + 2  # position + 2 spaces prefix

    def test_position_zero(self):
        """Test ParseError with position at start."""
        exc = ParseError("Unexpected start", position=0, expression="ERROR")
        error_str = str(exc)
        assert "^" in error_str
        lines = error_str.split("\n")
        assert lines[2] == "  ^"  # No spaces before ^

    def test_long_expression_with_position(self):
        """Test ParseError with long expression."""
        long_expr = "ERROR AND WARN AND INFO AND DEBUG AND TRACE"
        exc = ParseError("Too many operators", position=20, expression=long_expr)
        error_str = str(exc)
        assert long_expr in error_str
        assert "^" in error_str

    def test_can_be_raised(self):
        """Test that ParseError can be raised and caught."""
        with pytest.raises(ParseError) as exc_info:
            raise ParseError("Test parse error", position=5, expression="test")
        assert "Test parse error" in str(exc_info.value)
        assert exc_info.value.position == 5

    def test_can_be_caught_as_base_exception(self):
        """Test that ParseError can be caught as LogFilterException."""
        with pytest.raises(LogFilterException):
            raise ParseError("Test error")


class TestTokenizationError:
    """Test TokenizationError exception."""

    def test_inherits_from_parse_error(self):
        """Test that TokenizationError inherits from ParseError."""
        assert issubclass(TokenizationError, ParseError)
        assert issubclass(TokenizationError, LogFilterException)

    def test_simple_message(self):
        """Test TokenizationError with simple message."""
        exc = TokenizationError("Unterminated string")
        assert "Unterminated string" in str(exc)

    def test_with_position_and_expression(self):
        """Test TokenizationError with position and expression."""
        exc = TokenizationError("Unterminated string", position=10, expression='"unclosed')
        error_str = str(exc)
        assert "Unterminated string" in error_str
        assert '"unclosed' in error_str
        assert "^" in error_str

    def test_can_be_caught_as_parse_error(self):
        """Test that TokenizationError can be caught as ParseError."""
        with pytest.raises(ParseError):
            raise TokenizationError("Test tokenization error")


class TestEvaluationError:
    """Test EvaluationError exception."""

    def test_simple_message(self):
        """Test EvaluationError with simple message."""
        exc = EvaluationError("Invalid regex pattern")
        assert "Invalid regex pattern" in str(exc)

    def test_detailed_message(self):
        """Test EvaluationError with detailed message."""
        exc = EvaluationError("Malformed AST node: expected tuple, got string")
        assert "Malformed AST node" in str(exc)

    def test_can_be_raised(self):
        """Test that EvaluationError can be raised and caught."""
        with pytest.raises(EvaluationError) as exc_info:
            raise EvaluationError("Invalid regex: [unclosed")
        assert "Invalid regex" in str(exc_info.value)

    def test_can_be_caught_as_base_exception(self):
        """Test that EvaluationError can be caught as LogFilterException."""
        with pytest.raises(LogFilterException):
            raise EvaluationError("Test error")


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_simple_message(self):
        """Test ConfigurationError with simple message."""
        exc = ConfigurationError("Invalid configuration")
        assert "Invalid configuration" in str(exc)

    def test_validation_error_message(self):
        """Test ConfigurationError for validation failures."""
        exc = ConfigurationError("date_from must be <= date_to")
        assert "date_from" in str(exc)
        assert "date_to" in str(exc)

    def test_missing_field_error(self):
        """Test ConfigurationError for missing required fields."""
        exc = ConfigurationError("Search expression cannot be empty")
        assert "Search expression" in str(exc)

    def test_can_be_raised(self):
        """Test that ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Invalid worker count: -1")
        assert "Invalid worker count" in str(exc_info.value)


class TestFileHandlingError:
    """Test FileHandlingError exception."""

    def test_simple_message(self):
        """Test FileHandlingError with just a message."""
        exc = FileHandlingError("File not found")
        assert "File not found" in str(exc)
        assert exc.file_path == ""
        assert exc.cause is None

    def test_with_file_path(self):
        """Test FileHandlingError with file path."""
        exc = FileHandlingError("Permission denied", file_path="/var/log/test.log")
        error_str = str(exc)
        assert "Permission denied" in error_str
        assert "/var/log/test.log" in error_str
        assert exc.file_path == "/var/log/test.log"

    def test_with_cause(self):
        """Test FileHandlingError with cause exception."""
        original_error = OSError("No such file or directory")
        exc = FileHandlingError("Cannot read file", cause=original_error)
        error_str = str(exc)
        assert "Cannot read file" in error_str
        assert "caused by" in error_str
        assert "No such file or directory" in error_str
        assert exc.cause is original_error

    def test_with_file_path_and_cause(self):
        """Test FileHandlingError with both file path and cause."""
        original_error = PermissionError("Access denied")
        exc = FileHandlingError(
            "Cannot open file", file_path="/root/protected.log", cause=original_error
        )
        error_str = str(exc)
        assert "Cannot open file" in error_str
        assert "/root/protected.log" in error_str
        assert "caused by" in error_str
        assert "Access denied" in error_str

    def test_cause_preservation(self):
        """Test that original exception is preserved."""
        original_error = ValueError("Invalid format")
        exc = FileHandlingError("Parse error", cause=original_error)
        assert exc.cause is original_error
        assert isinstance(exc.cause, ValueError)

    def test_can_be_raised(self):
        """Test that FileHandlingError can be raised and caught."""
        with pytest.raises(FileHandlingError) as exc_info:
            raise FileHandlingError("Test error", file_path="test.log")
        assert "test.log" in str(exc_info.value)

    def test_windows_path(self):
        """Test FileHandlingError with Windows path."""
        exc = FileHandlingError("File not found", file_path=r"C:\logs\test.log")
        assert r"C:\logs\test.log" in str(exc)

    def test_empty_file_path_string(self):
        """Test FileHandlingError with explicitly empty file path."""
        exc = FileHandlingError("Generic error", file_path="")
        error_str = str(exc)
        assert "Generic error" in error_str
        # Should not have extra colon or path separator
        assert error_str.count(":") == 0 or "caused by" not in error_str


class TestRecordSizeExceededError:
    """Test RecordSizeExceededError exception."""

    def test_simple_case(self):
        """Test RecordSizeExceededError with simple values."""
        exc = RecordSizeExceededError(size_kb=150.5, max_size_kb=100)
        error_str = str(exc)
        assert "150.50" in error_str or "150.5" in error_str
        assert "100" in error_str
        assert "exceeds limit" in error_str
        assert exc.size_kb == 150.5
        assert exc.max_size_kb == 100

    def test_small_size(self):
        """Test RecordSizeExceededError with small sizes."""
        exc = RecordSizeExceededError(size_kb=0.5, max_size_kb=0)
        error_str = str(exc)
        assert "0.50" in error_str or "0.5" in error_str
        assert "0KB" in error_str or "0 KB" in error_str

    def test_large_size(self):
        """Test RecordSizeExceededError with large sizes."""
        exc = RecordSizeExceededError(size_kb=10000.0, max_size_kb=1000)
        error_str = str(exc)
        assert "10000" in error_str
        assert "1000" in error_str

    def test_formatting(self):
        """Test that size is formatted with 2 decimal places."""
        exc = RecordSizeExceededError(size_kb=123.456789, max_size_kb=100)
        error_str = str(exc)
        assert "123.46" in error_str  # Should be rounded to 2 decimals

    def test_attributes_accessible(self):
        """Test that size attributes are accessible."""
        exc = RecordSizeExceededError(size_kb=200.0, max_size_kb=150)
        assert exc.size_kb == 200.0
        assert exc.max_size_kb == 150
        assert isinstance(exc.size_kb, float)
        assert isinstance(exc.max_size_kb, int)

    def test_can_be_raised(self):
        """Test that RecordSizeExceededError can be raised and caught."""
        with pytest.raises(RecordSizeExceededError) as exc_info:
            raise RecordSizeExceededError(size_kb=500.0, max_size_kb=100)
        assert exc_info.value.size_kb == 500.0
        assert exc_info.value.max_size_kb == 100

    def test_can_be_caught_as_base_exception(self):
        """Test that RecordSizeExceededError can be caught as LogFilterException."""
        with pytest.raises(LogFilterException):
            raise RecordSizeExceededError(size_kb=200.0, max_size_kb=100)


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_parse_error_from_tokenization_error(self):
        """Test catching TokenizationError as ParseError."""
        try:
            raise TokenizationError("Token error")
        except ParseError as e:
            assert isinstance(e, TokenizationError)
            assert isinstance(e, ParseError)

    def test_all_exceptions_from_base(self):
        """Test catching any custom exception as LogFilterException."""
        exceptions = [
            ParseError("test"),
            TokenizationError("test"),
            EvaluationError("test"),
            ConfigurationError("test"),
            FileHandlingError("test"),
            RecordSizeExceededError(100.0, 50),
        ]

        for exc in exceptions:
            try:
                raise exc
            except LogFilterException:
                pass  # Should catch all
            else:
                pytest.fail(f"{type(exc).__name__} not caught as LogFilterException")

    def test_exception_chaining_with_cause(self):
        """Test exception chaining with explicit cause."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise FileHandlingError("Wrapped error", cause=e) from e
        except FileHandlingError as exc:
            assert exc.cause is not None
            assert isinstance(exc.cause, ValueError)
            assert "Original error" in str(exc.cause)


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_multiline_parse_error_format(self):
        """Test that ParseError with position creates proper multiline format."""
        exc = ParseError("Error here", position=4, expression="test expression")
        lines = str(exc).split("\n")
        assert len(lines) == 3
        assert "Error here" in lines[0]
        assert "test expression" in lines[1]
        assert "^" in lines[2]

    def test_file_handling_error_format_consistency(self):
        """Test FileHandlingError message format consistency."""
        # With path only
        exc1 = FileHandlingError("Error", file_path="file.log")
        assert str(exc1) == "Error: file.log"

        # With cause only
        exc2 = FileHandlingError("Error", cause=OSError("OS error"))
        assert "Error (caused by: OS error)" in str(exc2)

        # With both
        exc3 = FileHandlingError("Error", file_path="file.log", cause=OSError("OS error"))
        msg = str(exc3)
        assert "Error: file.log" in msg
        assert "(caused by: OS error)" in msg

    def test_record_size_error_format(self):
        """Test RecordSizeExceededError message format."""
        exc = RecordSizeExceededError(size_kb=123.45, max_size_kb=100)
        msg = str(exc)
        assert "Record size" in msg
        assert "123.45KB" in msg or "123.45 KB" in msg
        assert "exceeds limit" in msg
        assert "100KB" in msg or "100 KB" in msg
