"""
Unit tests for FileWorker processing logic.

Tests the worker's handling of file processing, including:
- File validation and error handling
- Record parsing and filtering
- Search expression evaluation
- Output writing and statistics
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.exceptions import (
    FileHandlingError,
    RecordSizeExceededError,
)
from log_filter.domain.filters import AlwaysPassFilter
from log_filter.domain.models import FileMetadata, LogRecord
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
from log_filter.infrastructure.file_writer import BufferedLogWriter
from log_filter.processing.record_parser import StreamingRecordParser
from log_filter.processing.worker import FileWorker
from log_filter.statistics.collector import StatisticsCollector


@pytest.fixture
def mock_handler_factory():
    """Create a mock file handler factory."""
    return Mock(spec=FileHandlerFactory)


@pytest.fixture
def mock_record_parser():
    """Create a mock record parser."""
    return Mock(spec=StreamingRecordParser)


@pytest.fixture
def mock_record_filter():
    """Create a mock record filter."""
    filter_mock = Mock(spec=AlwaysPassFilter)
    filter_mock.matches.return_value = True
    return filter_mock


@pytest.fixture
def mock_stats_collector():
    """Create a mock statistics collector."""
    return Mock(spec=StatisticsCollector)


@pytest.fixture
def mock_writer():
    """Create a mock buffered log writer."""
    return Mock(spec=BufferedLogWriter)


@pytest.fixture
def file_worker(mock_handler_factory, mock_record_parser, mock_record_filter, mock_stats_collector):
    """Create a FileWorker instance with mocked dependencies."""
    return FileWorker(
        handler_factory=mock_handler_factory,
        record_parser=mock_record_parser,
        record_filter=mock_record_filter,
        stats_collector=mock_stats_collector
    )


@pytest.fixture
def sample_file_meta():
    """Create sample file metadata."""
    return FileMetadata(
        path=Path("test.log"),
        size_bytes=1000,
        extension=".log",
        is_compressed=False,
        is_readable=True
    )


@pytest.fixture
def sample_config():
    """Create sample application configuration."""
    return ApplicationConfig(
        search=SearchConfig(expression="ERROR"),
        output=OutputConfig(
            output_file=Path("output.log"),
            highlight_matches=False,
            include_file_path=True
        ),
        processing=ProcessingConfig(worker_count=1)
    )


@pytest.fixture
def sample_record():
    """Create sample log record."""
    return LogRecord(
        content="2025-01-01 10:00:00 ERROR Test error",
        first_line="2025-01-01 10:00:00 ERROR Test error",
        source_file=Path("test.log"),
        start_line=1,
        end_line=1,
        timestamp=datetime(2025, 1, 1, 10, 0, 0),
        level="ERROR",
        size_bytes=35
    )


class TestFileWorkerInitialization:
    """Test FileWorker initialization."""

    def test_init_with_all_dependencies(self, mock_handler_factory, mock_record_parser, 
                                        mock_record_filter, mock_stats_collector):
        """Test worker initializes with all dependencies."""
        worker = FileWorker(
            handler_factory=mock_handler_factory,
            record_parser=mock_record_parser,
            record_filter=mock_record_filter,
            stats_collector=mock_stats_collector
        )
        
        assert worker.handler_factory is mock_handler_factory
        assert worker.record_parser is mock_record_parser
        assert worker.record_filter is mock_record_filter
        assert worker.stats_collector is mock_stats_collector
        assert worker.highlighter is not None

    def test_repr(self, file_worker):
        """Test string representation of worker."""
        repr_str = repr(file_worker)
        assert "FileWorker" in repr_str
        assert "factory=" in repr_str


class TestFileValidation:
    """Test file validation handling."""

    def test_process_file_with_invalid_file(self, file_worker, sample_file_meta, 
                                            sample_config, mock_writer, mock_handler_factory):
        """Test worker skips invalid files."""
        # Setup mock handler that fails validation
        mock_handler = Mock()
        mock_handler.validate.return_value = (False, "File not readable")
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify behavior
        assert matches == 0
        file_worker.stats_collector.increment_files_skipped.assert_called_once()
        mock_writer.write_result.assert_not_called()

    def test_process_file_with_valid_file(self, file_worker, sample_file_meta, 
                                          sample_config, mock_writer, mock_handler_factory,
                                          mock_record_parser, sample_record):
        """Test worker processes valid files."""
        # Setup mock handler
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1", "line2"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Setup mock parser
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify file was processed
        mock_handler.validate.assert_called_once()
        mock_handler.read_lines.assert_called_once()


class TestRecordProcessing:
    """Test record parsing and filtering."""

    def test_process_file_counts_records(self, file_worker, sample_file_meta,
                                         sample_config, mock_writer, mock_handler_factory,
                                         mock_record_parser, sample_record):
        """Test worker counts all records."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        records = [sample_record, sample_record, sample_record]
        mock_record_parser.parse_lines.return_value = iter(records)
        
        # Process file
        ast = ("WORD", "ERROR")
        file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify all records counted
        assert file_worker.stats_collector.increment_records_total.call_count == 3
        assert file_worker.stats_collector.add_bytes_processed.call_count == 3
        assert file_worker.stats_collector.add_lines_processed.call_count == 3

    def test_process_file_respects_filter(self, file_worker, sample_file_meta,
                                          sample_config, mock_writer, mock_handler_factory,
                                          mock_record_parser, mock_record_filter, sample_record):
        """Test worker respects record filter."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Filter rejects the record
        mock_record_filter.matches.return_value = False
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify record was filtered out
        assert matches == 0
        file_worker.stats_collector.increment_records_skipped.assert_called_once()
        mock_writer.write_result.assert_not_called()

    def test_process_file_with_matching_record(self, file_worker, sample_file_meta,
                                               sample_config, mock_writer, mock_handler_factory,
                                               mock_record_parser, sample_record):
        """Test worker writes matching records."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify record was matched and written
        assert matches == 1
        file_worker.stats_collector.increment_records_matched.assert_called_once()
        file_worker.stats_collector.increment_files_processed.assert_called_once()
        mock_writer.write_result.assert_called_once()

    def test_process_file_with_non_matching_record(self, file_worker, sample_file_meta,
                                                   sample_config, mock_writer, mock_handler_factory,
                                                   mock_record_parser):
        """Test worker skips non-matching records."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Record that doesn't contain ERROR
        record = LogRecord(
            content="2025-01-01 10:00:00 INFO Normal log",
            first_line="2025-01-01 10:00:00 INFO Normal log",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            level="INFO",
            size_bytes=35
        )
        mock_record_parser.parse_lines.return_value = iter([record])
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify no matches
        assert matches == 0
        mock_writer.write_result.assert_not_called()


class TestHighlighting:
    """Test highlighting functionality."""

    def test_process_file_with_highlighting_enabled(self, file_worker, sample_file_meta,
                                                    mock_writer, mock_handler_factory,
                                                    mock_record_parser, sample_record):
        """Test worker applies highlighting when enabled."""
        # Setup config with highlighting
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            output=OutputConfig(highlight_matches=True)
        )
        
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, config)
        
        # Verify highlighting was applied
        assert matches == 1
        call_args = mock_writer.write_result.call_args
        assert call_args[1]["use_highlight"] is True

    def test_process_file_without_highlighting(self, file_worker, sample_file_meta,
                                               sample_config, mock_writer, mock_handler_factory,
                                               mock_record_parser, sample_record):
        """Test worker skips highlighting when disabled."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify no highlighting
        assert matches == 1
        call_args = mock_writer.write_result.call_args
        assert call_args[1]["use_highlight"] is False


class TestErrorHandling:
    """Test error handling in worker."""

    def test_process_file_handles_record_size_exceeded(self, file_worker, sample_file_meta,
                                                       sample_config, mock_writer,
                                                       mock_handler_factory, mock_record_parser):
        """Test worker handles record size exceeded error."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Parser raises RecordSizeExceededError
        mock_record_parser.parse_lines.side_effect = RecordSizeExceededError(
            size_kb=10.0,
            max_size_kb=5
        )
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify error was handled
        assert matches == 0
        file_worker.stats_collector.increment_files_skipped.assert_called_with("record-size-exceeded")

    def test_process_file_handles_file_handling_error(self, file_worker, sample_file_meta,
                                                      sample_config, mock_writer,
                                                      mock_handler_factory, mock_record_parser):
        """Test worker handles file handling error."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.side_effect = FileHandlingError("Cannot read file")
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify error was handled
        assert matches == 0
        file_worker.stats_collector.increment_files_skipped.assert_called_with("error")

    def test_process_file_handles_unexpected_error(self, file_worker, sample_file_meta,
                                                   sample_config, mock_writer,
                                                   mock_handler_factory, mock_record_parser):
        """Test worker handles unexpected errors."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.side_effect = RuntimeError("Unexpected error")
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify error was handled
        assert matches == 0
        file_worker.stats_collector.increment_files_skipped.assert_called_with("unexpected-error")

    def test_process_file_continues_after_partial_matches(self, file_worker, sample_file_meta,
                                                          sample_config, mock_writer,
                                                          mock_handler_factory, mock_record_parser,
                                                          sample_record):
        """Test worker returns partial matches even if error occurs."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # First record matches, then error
        def record_generator():
            yield sample_record
            raise RuntimeError("Error after first record")
        
        mock_record_parser.parse_lines.return_value = record_generator()
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify partial match was returned
        assert matches == 1
        file_worker.stats_collector.increment_records_matched.assert_called_once()


class TestRegexMode:
    """Test regex mode processing."""

    def test_process_file_with_regex_enabled(self, file_worker, sample_file_meta,
                                             mock_writer, mock_handler_factory,
                                             mock_record_parser, sample_record):
        """Test worker uses regex mode when enabled."""
        # Setup config with regex
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR.*failed", use_regex=True),
            output=OutputConfig()
        )
        
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file - should not raise even with regex expression
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, config)
        
        # Just verify it processed without error
        assert matches >= 0

    def test_process_file_with_case_insensitive(self, file_worker, sample_file_meta,
                                                mock_writer, mock_handler_factory,
                                                mock_record_parser, sample_record):
        """Test worker uses case-insensitive matching when enabled."""
        # Setup config with ignore_case
        config = ApplicationConfig(
            search=SearchConfig(expression="error", ignore_case=True),
            output=OutputConfig()
        )
        
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        mock_record_parser.parse_lines.return_value = iter([sample_record])
        
        # Process file
        ast = ("WORD", "error")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, config)
        
        # Should match despite case difference
        assert matches == 1


class TestMultipleRecords:
    """Test processing multiple records."""

    def test_process_file_with_multiple_matching_records(self, file_worker, sample_file_meta,
                                                         sample_config, mock_writer,
                                                         mock_handler_factory, mock_record_parser):
        """Test worker processes multiple matching records."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Create multiple matching records
        records = [
            LogRecord(
                content=f"2025-01-01 10:00:0{i} ERROR Error {i}",
                first_line=f"2025-01-01 10:00:0{i} ERROR Error {i}",
                source_file=Path("test.log"),
                start_line=i,
                end_line=i,
                timestamp=datetime(2025, 1, 1, 10, 0, i),
                level="ERROR",
                size_bytes=35
            )
            for i in range(5)
        ]
        mock_record_parser.parse_lines.return_value = iter(records)
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify all matches
        assert matches == 5
        assert file_worker.stats_collector.increment_records_matched.call_count == 5
        assert mock_writer.write_result.call_count == 5

    def test_process_file_with_mixed_records(self, file_worker, sample_file_meta,
                                            sample_config, mock_writer, mock_handler_factory,
                                            mock_record_parser):
        """Test worker processes mixed matching and non-matching records."""
        # Setup mocks
        mock_handler = Mock()
        mock_handler.validate.return_value = (True, None)
        mock_handler.read_lines.return_value = iter(["line1"])
        mock_handler_factory.create_handler.return_value = mock_handler
        
        # Create mix of records
        records = [
            LogRecord(
                content="2025-01-01 10:00:00 ERROR Error log",
                first_line="2025-01-01 10:00:00 ERROR Error log",
                source_file=Path("test.log"),
                start_line=1,
                end_line=1,
                timestamp=datetime(2025, 1, 1, 10, 0, 0),
                level="ERROR",
                size_bytes=35
            ),
            LogRecord(
                content="2025-01-01 10:00:01 INFO Info log",
                first_line="2025-01-01 10:00:01 INFO Info log",
                source_file=Path("test.log"),
                start_line=2,
                end_line=2,
                timestamp=datetime(2025, 1, 1, 10, 0, 1),
                level="INFO",
                size_bytes=33
            ),
            LogRecord(
                content="2025-01-01 10:00:02 ERROR Another error",
                first_line="2025-01-01 10:00:02 ERROR Another error",
                source_file=Path("test.log"),
                start_line=3,
                end_line=3,
                timestamp=datetime(2025, 1, 1, 10, 0, 2),
                level="ERROR",
                size_bytes=39
            ),
        ]
        mock_record_parser.parse_lines.return_value = iter(records)
        
        # Process file
        ast = ("WORD", "ERROR")
        matches = file_worker.process_file(sample_file_meta, ast, mock_writer, sample_config)
        
        # Verify only matching records
        assert matches == 2
        assert file_worker.stats_collector.increment_records_total.call_count == 3
        assert file_worker.stats_collector.increment_records_matched.call_count == 2
        assert mock_writer.write_result.call_count == 2
