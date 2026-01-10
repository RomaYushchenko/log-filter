"""
Unit tests for file handler modules.

Tests LogFileHandler and GzipFileHandler implementations:
- File reading with various encodings
- Error handling and fallback mechanisms
- Validation logic
"""

import gzip
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers.base import AbstractFileHandler
from log_filter.infrastructure.file_handlers.gzip_handler import GzipFileHandler
from log_filter.infrastructure.file_handlers.log_handler import LogFileHandler


class TestLogFileHandler:
    """Test LogFileHandler for plain text log files."""

    def test_initialization(self, tmp_path):
        """Test handler initialization with default params."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file)

        assert handler.file_path == test_file
        assert handler.encoding == "utf-8"
        assert handler.errors == "replace"

    def test_initialization_with_custom_encoding(self, tmp_path):
        """Test handler initialization with custom encoding."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file, encoding="latin-1", errors="ignore")

        assert handler.encoding == "latin-1"
        assert handler.errors == "ignore"

    def test_read_lines_basic(self, tmp_path):
        """Test reading lines from a plain text file."""
        test_file = tmp_path / "test.log"
        test_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

        handler = LogFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == ["line 1", "line 2", "line 3"]

    def test_read_lines_strips_newlines(self, tmp_path):
        """Test that read_lines strips different newline types."""
        test_file = tmp_path / "test.log"
        # Use binary write to ensure exact bytes
        test_file.write_bytes(b"line1\nline2\nline3\n")

        handler = LogFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == ["line1", "line2", "line3"]

    def test_read_lines_empty_file(self, tmp_path):
        """Test reading empty file returns no lines."""
        test_file = tmp_path / "empty.log"
        test_file.touch()

        handler = LogFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == []

    def test_read_lines_file_not_found(self, tmp_path):
        """Test creating handler for non-existent file raises error."""
        test_file = tmp_path / "nonexistent.log"

        with pytest.raises(FileHandlingError) as excinfo:
            handler = LogFileHandler(test_file)

        assert "not found" in str(excinfo.value).lower()
        assert excinfo.value.file_path == test_file

    def test_read_lines_with_latin1_encoding(self, tmp_path):
        """Test reading file with latin-1 encoding."""
        test_file = tmp_path / "latin1.log"
        # Write with latin-1 specific characters
        test_file.write_bytes(b"caf\xe9\n")  # café in latin-1

        handler = LogFileHandler(test_file, encoding="latin-1")
        lines = list(handler.read_lines())

        assert len(lines) == 1
        assert "caf" in lines[0]

    def test_read_lines_encoding_error_with_replace(self, tmp_path):
        """Test that encoding errors are handled with replace mode."""
        test_file = tmp_path / "invalid.log"
        # Write invalid UTF-8 sequence
        test_file.write_bytes(b"Hello\xff\xfeWorld\n")

        handler = LogFileHandler(test_file, encoding="utf-8", errors="replace")
        lines = list(handler.read_lines())

        assert len(lines) == 1
        assert "Hello" in lines[0]
        assert "World" in lines[0]

    def test_read_lines_fallback_encoding(self, tmp_path):
        """Test fallback to alternative encodings on decode error."""
        test_file = tmp_path / "fallback.log"
        # Write latin-1 content
        test_file.write_bytes(b"caf\xe9\n")

        handler = LogFileHandler(test_file, encoding="utf-8", errors="strict")

        # Should fall back to latin-1 or cp1252
        lines = list(handler.read_lines())
        assert len(lines) == 1

    def test_read_lines_all_fallbacks_fail(self, tmp_path):
        """Test that error is raised when all fallbacks fail."""
        test_file = tmp_path / "undecodable.log"
        test_file.write_bytes(b"test\n")

        handler = LogFileHandler(test_file)

        # Mock open to always raise UnicodeDecodeError
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error")):
            with pytest.raises(FileHandlingError) as excinfo:
                list(handler.read_lines())

            assert "decode" in str(excinfo.value).lower()

    def test_read_lines_os_error(self, tmp_path):
        """Test handling of OS errors during reading."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file)

        with patch("builtins.open", side_effect=OSError("Disk error")):
            with pytest.raises(FileHandlingError) as excinfo:
                list(handler.read_lines())

            assert "OS error" in str(excinfo.value)

    def test_validate_success(self, tmp_path):
        """Test validation of valid file."""
        test_file = tmp_path / "valid.log"
        test_file.write_text("line 1\nline 2\n", encoding="utf-8")

        handler = LogFileHandler(test_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    def test_validate_empty_file(self, tmp_path):
        """Test validation of empty file."""
        test_file = tmp_path / "empty.log"
        test_file.touch()

        handler = LogFileHandler(test_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    def test_validate_with_fallback_encoding(self, tmp_path):
        """Test validation succeeds with fallback encoding."""
        test_file = tmp_path / "latin.log"
        # Write latin-1 content
        test_file.write_bytes(b"caf\xe9\n")

        handler = LogFileHandler(test_file, encoding="utf-8")
        is_valid, error = handler.validate()

        # Should succeed with fallback
        assert is_valid is True
        assert error is None

    def test_validate_file_not_found(self, tmp_path):
        """Test creating handler for non-existent file raises error."""
        test_file = tmp_path / "nonexistent.log"

        # __init__ checks file existence
        with pytest.raises(FileHandlingError) as excinfo:
            handler = LogFileHandler(test_file)

        assert "not found" in str(excinfo.value).lower()

    def test_validate_os_error(self, tmp_path):
        """Test validation with OS error."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file)

        with patch("builtins.open", side_effect=OSError("Disk error")):
            is_valid, error = handler.validate()

        assert is_valid is False
        assert "OS error" in error

    def test_validate_unexpected_error(self, tmp_path):
        """Test validation with unexpected error."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file)

        with patch("builtins.open", side_effect=RuntimeError("Unexpected")):
            is_valid, error = handler.validate()

        assert is_valid is False
        assert "Unexpected" in error

    def test_fallback_encodings_list(self):
        """Test that fallback encodings are defined."""
        assert LogFileHandler.FALLBACK_ENCODINGS == ["utf-8", "latin-1", "cp1252"]

    def test_read_with_encoding_helper(self, tmp_path):
        """Test _read_with_encoding helper method."""
        test_file = tmp_path / "test.log"
        test_file.write_bytes(b"caf\xe9\n")

        handler = LogFileHandler(test_file)
        lines = list(handler._read_with_encoding("latin-1"))

        assert len(lines) == 1
        assert "caf" in lines[0]


class TestGzipFileHandler:
    """Test GzipFileHandler for compressed log files."""

    def test_initialization(self, tmp_path):
        """Test handler initialization with default params."""
        test_file = tmp_path / "test.log.gz"

        # Create a valid gzip file
        with gzip.open(test_file, "wt", encoding="utf-8") as f:
            f.write("test\n")

        handler = GzipFileHandler(test_file)

        assert handler.file_path == test_file
        assert handler.encoding == "utf-8"
        assert handler.errors == "replace"

    def test_initialization_with_custom_params(self, tmp_path):
        """Test handler initialization with custom parameters."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wt") as f:
            f.write("test\n")

        handler = GzipFileHandler(test_file, encoding="latin-1", errors="ignore")

        assert handler.encoding == "latin-1"
        assert handler.errors == "ignore"

    def test_read_lines_basic(self, tmp_path):
        """Test reading lines from gzip file."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wt", encoding="utf-8") as f:
            f.write("line 1\nline 2\nline 3\n")

        handler = GzipFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == ["line 1", "line 2", "line 3"]

    def test_read_lines_strips_newlines(self, tmp_path):
        """Test that read_lines strips newlines."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wb") as f:
            f.write(b"line1\nline2\nline3\n")

        handler = GzipFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == ["line1", "line2", "line3"]

    def test_read_lines_empty_file(self, tmp_path):
        """Test reading empty gzip file."""
        test_file = tmp_path / "empty.log.gz"

        with gzip.open(test_file, "wt") as f:
            pass  # Empty file

        handler = GzipFileHandler(test_file)
        lines = list(handler.read_lines())

        assert lines == []

    def test_read_lines_file_not_found(self, tmp_path):
        """Test creating handler for non-existent file raises error."""
        test_file = tmp_path / "nonexistent.log.gz"

        with pytest.raises(FileHandlingError) as excinfo:
            handler = GzipFileHandler(test_file)

        assert "not found" in str(excinfo.value).lower()

    def test_read_lines_invalid_gzip(self, tmp_path):
        """Test reading invalid gzip file raises error."""
        test_file = tmp_path / "invalid.log.gz"
        # Write invalid gzip data
        test_file.write_bytes(b"Not a gzip file")

        handler = GzipFileHandler(test_file)

        with pytest.raises(FileHandlingError) as excinfo:
            list(handler.read_lines())

        assert "gzip" in str(excinfo.value).lower() or "decompress" in str(excinfo.value).lower()

    def test_read_lines_encoding_error(self, tmp_path):
        """Test handling encoding errors in gzip file."""
        test_file = tmp_path / "invalid_encoding.log.gz"

        # Write gzipped data with invalid UTF-8
        with gzip.open(test_file, "wb") as f:
            f.write(b"Hello\xff\xfeWorld\n")

        handler = GzipFileHandler(test_file, encoding="utf-8", errors="replace")
        lines = list(handler.read_lines())

        assert len(lines) == 1
        assert "Hello" in lines[0]
        assert "World" in lines[0]

    def test_read_lines_fallback_encoding(self, tmp_path):
        """Test fallback to alternative encodings."""
        test_file = tmp_path / "latin.log.gz"

        # Write latin-1 content in gzip
        with gzip.open(test_file, "wb") as f:
            f.write(b"caf\xe9\n")

        handler = GzipFileHandler(test_file, encoding="utf-8", errors="strict")

        # Should fall back to latin-1
        lines = list(handler.read_lines())
        assert len(lines) == 1

    def test_read_lines_os_error(self, tmp_path):
        """Test handling OS errors during reading."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wt") as f:
            f.write("test\n")

        handler = GzipFileHandler(test_file)

        with patch("gzip.open", side_effect=OSError("Disk error")):
            with pytest.raises(FileHandlingError) as excinfo:
                list(handler.read_lines())

            assert "OS error" in str(excinfo.value)

    def test_validate_success(self, tmp_path):
        """Test validation of valid gzip file."""
        test_file = tmp_path / "valid.log.gz"

        with gzip.open(test_file, "wt") as f:
            f.write("line 1\nline 2\n")

        handler = GzipFileHandler(test_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    def test_validate_empty_gzip(self, tmp_path):
        """Test validation of empty gzip file."""
        test_file = tmp_path / "empty.log.gz"

        with gzip.open(test_file, "wt") as f:
            pass  # Empty

        handler = GzipFileHandler(test_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    def test_validate_invalid_gzip(self, tmp_path):
        """Test validation of invalid gzip file."""
        test_file = tmp_path / "invalid.log.gz"
        test_file.write_bytes(b"Not a gzip file")

        handler = GzipFileHandler(test_file)
        is_valid, error = handler.validate()

        assert is_valid is False
        assert "gzip" in error.lower() or "decompress" in error.lower()

    def test_validate_with_fallback_encoding(self, tmp_path):
        """Test validation succeeds with fallback encoding."""
        test_file = tmp_path / "latin.log.gz"

        # Write latin-1 content
        with gzip.open(test_file, "wb") as f:
            f.write(b"caf\xe9\n")

        handler = GzipFileHandler(test_file, encoding="utf-8")
        is_valid, error = handler.validate()

        # Should succeed with fallback
        assert is_valid is True
        assert error is None

    def test_validate_os_error(self, tmp_path):
        """Test validation with OS error."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wt") as f:
            f.write("test\n")

        handler = GzipFileHandler(test_file)

        with patch("gzip.open", side_effect=OSError("Disk error")):
            is_valid, error = handler.validate()

        assert is_valid is False
        assert "OS error" in error

    def test_validate_unexpected_error(self, tmp_path):
        """Test validation with unexpected error."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wt") as f:
            f.write("test\n")

        handler = GzipFileHandler(test_file)

        with patch("gzip.open", side_effect=RuntimeError("Unexpected")):
            is_valid, error = handler.validate()

        assert is_valid is False
        assert "Unexpected" in error

    def test_read_with_encoding_helper(self, tmp_path):
        """Test _read_with_encoding helper method."""
        test_file = tmp_path / "test.log.gz"

        with gzip.open(test_file, "wb") as f:
            f.write(b"caf\xe9\n")

        handler = GzipFileHandler(test_file)
        lines = list(handler._read_with_encoding("latin-1"))

        assert len(lines) == 1
        assert "caf" in lines[0]

    def test_fallback_encodings_list(self):
        """Test that fallback encodings are defined."""
        assert GzipFileHandler.FALLBACK_ENCODINGS == ["utf-8", "latin-1", "cp1252"]


class TestAbstractFileHandler:
    """Test AbstractFileHandler base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AbstractFileHandler cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AbstractFileHandler(Path("test.log"))

    def test_repr_implementation(self, tmp_path):
        """Test __repr__ implementation through subclass."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        handler = LogFileHandler(test_file)
        repr_str = repr(handler)

        assert "LogFileHandler" in repr_str
        assert "file_path=" in repr_str

    def test_subclass_must_implement_read_lines(self, tmp_path):
        """Test that subclasses must implement read_lines."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        # Create minimal subclass without read_lines
        class IncompleteHandler(AbstractFileHandler):
            pass

        # Should fail due to missing abstract method
        with pytest.raises(TypeError):
            IncompleteHandler(test_file)

    def test_subclass_must_implement_validate(self, tmp_path):
        """Test that subclasses must implement validate."""
        test_file = tmp_path / "test.log"
        test_file.touch()

        # Create minimal subclass without validate
        class IncompleteHandler(AbstractFileHandler):
            def read_lines(self):
                pass

        # Should fail due to missing abstract method
        with pytest.raises(TypeError):
            IncompleteHandler(test_file)
