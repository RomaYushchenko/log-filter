"""
Integration tests for file processing infrastructure.

Tests the complete file reading, parsing, and writing pipeline.
"""

import gzip
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from log_filter.domain.models import FileMetadata, LogRecord
from log_filter.infrastructure.file_handlers import (
    GzipFileHandler,
    LogFileHandler,
)
from log_filter.infrastructure.file_scanner import FileScanner
from log_filter.infrastructure.file_writer import BufferedLogWriter
from log_filter.processing.record_parser import StreamingRecordParser


class TestFileHandlers:
    """Test file handler implementations."""

    def test_log_handler_reads_plain_file(self, tmp_path):
        """Test LogFileHandler reads plain text files correctly."""
        # Create test file
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 INFO App started\n"
            "2025-01-01 10:00:01.000+0000 ERROR Something failed\n",
            encoding="utf-8",
        )

        # Read with handler
        handler = LogFileHandler(log_file)
        lines = list(handler.read_lines())

        assert len(lines) == 2
        assert "INFO App started" in lines[0]
        assert "ERROR Something failed" in lines[1]

    def test_log_handler_validates_file(self, tmp_path):
        """Test LogFileHandler validation."""
        log_file = tmp_path / "test.log"
        log_file.write_text("test content", encoding="utf-8")

        handler = LogFileHandler(log_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    @pytest.mark.skipif(
        sys.platform == "win32", reason="File permissions don't work the same on Windows"
    )
    def test_log_handler_handles_permission_error(self, tmp_path):
        """Test LogFileHandler handles permission errors."""
        log_file = tmp_path / "test.log"
        log_file.write_text("test", encoding="utf-8")
        log_file.chmod(0o000)

        try:
            handler = LogFileHandler(log_file)
            is_valid, error = handler.validate()

            assert is_valid is False
            assert "Permission denied" in error
        finally:
            log_file.chmod(0o644)

    def test_gzip_handler_reads_compressed_file(self, tmp_path):
        """Test GzipFileHandler reads gzip files correctly."""
        # Create gzip file
        gz_file = tmp_path / "test.log.gz"
        content = (
            "2025-01-01 10:00:00.000+0000 INFO App started\n"
            "2025-01-01 10:00:01.000+0000 ERROR Something failed\n"
        )
        with gzip.open(gz_file, "wt", encoding="utf-8") as f:
            f.write(content)

        # Read with handler
        handler = GzipFileHandler(gz_file)
        lines = list(handler.read_lines())

        assert len(lines) == 2
        assert "INFO App started" in lines[0]
        assert "ERROR Something failed" in lines[1]

    def test_gzip_handler_validates_file(self, tmp_path):
        """Test GzipFileHandler validation."""
        gz_file = tmp_path / "test.log.gz"
        with gzip.open(gz_file, "wt", encoding="utf-8") as f:
            f.write("test content")

        handler = GzipFileHandler(gz_file)
        is_valid, error = handler.validate()

        assert is_valid is True
        assert error is None

    def test_gzip_handler_detects_invalid_gzip(self, tmp_path):
        """Test GzipFileHandler detects invalid gzip files."""
        # Create fake gzip file (not actually gzipped)
        gz_file = tmp_path / "test.log.gz"
        gz_file.write_bytes(b"not gzip content")

        handler = GzipFileHandler(gz_file)
        is_valid, error = handler.validate()

        assert is_valid is False
        assert "gzip" in error.lower()


class TestStreamingRecordParser:
    """Test streaming record parser."""

    def test_parser_splits_records_correctly(self):
        """Test parser correctly splits multiline records."""
        lines = [
            "2025-01-01 10:00:00.000+0000 INFO App started",
            "  Additional context line 1",
            "  Additional context line 2",
            "2025-01-01 10:00:01.000+0000 ERROR Something failed",
            "  Stack trace line 1",
        ]

        parser = StreamingRecordParser()
        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 2
        assert records[0].line_count == 3
        assert records[1].line_count == 2
        assert records[0].level == "INFO"
        assert records[1].level == "ERROR"

    def test_parser_extracts_metadata(self):
        """Test parser extracts date, time, and level."""
        lines = ["2025-01-01 10:00:00.000+0000 WARN Test warning"]

        parser = StreamingRecordParser()
        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 1
        assert str(records[0].date) == "2025-01-01"
        assert str(records[0].time) == "10:00:00"
        assert records[0].level == "WARN"

    def test_parser_respects_size_limit(self):
        """Test parser respects max record size."""
        # Create large record
        lines = [
            "2025-01-01 10:00:00.000+0000 INFO Start",
            "x" * 1000,  # Large line
        ]

        parser = StreamingRecordParser(max_record_size_bytes=500)

        with pytest.raises(Exception) as exc_info:
            list(parser.parse_lines(iter(lines)))

        assert "size" in str(exc_info.value).lower()

    def test_parser_handles_empty_input(self):
        """Test parser handles empty input."""
        parser = StreamingRecordParser()
        records = list(parser.parse_lines(iter([])))

        assert len(records) == 0


class TestFileScanner:
    """Test file scanner."""

    def test_scanner_finds_log_files(self, tmp_path):
        """Test scanner finds log files."""
        # Create test files
        (tmp_path / "app.log").write_text("log1")
        (tmp_path / "app.log.gz").write_bytes(b"log2")
        (tmp_path / "readme.txt").write_text("not a log")

        scanner = FileScanner(tmp_path, recursive=False)
        files = list(scanner.scan())

        # Should find .log and .gz, skip .txt
        log_files = [f for f in files if not f.should_skip]
        assert len(log_files) == 2

    def test_scanner_filters_by_mask(self, tmp_path):
        """Test scanner filters by file mask."""
        (tmp_path / "kafka.log").write_text("log1")
        (tmp_path / "tomcat.log").write_text("log2")

        scanner = FileScanner(tmp_path, file_masks=["kafka"], recursive=False)
        files = list(scanner.scan())

        eligible = [f for f in files if not f.should_skip]
        assert len(eligible) == 1
        assert "kafka" in eligible[0].path.name

    def test_scanner_respects_size_limit(self, tmp_path):
        """Test scanner respects file size limit."""
        small_file = tmp_path / "small.log"
        large_file = tmp_path / "large.log"

        small_file.write_text("x" * 100)
        large_file.write_text("x" * 2_000_000)  # ~2 MB

        scanner = FileScanner(tmp_path, max_file_size_mb=1, recursive=False)
        files = list(scanner.scan())

        for f in files:
            if "large" in f.path.name:
                assert f.should_skip
                assert f.skip_reason == "size-limit"
            elif "small" in f.path.name:
                assert not f.should_skip

    def test_scanner_counts_files(self, tmp_path):
        """Test scanner provides accurate counts."""
        (tmp_path / "app.log").write_text("log1")
        (tmp_path / "readme.txt").write_text("not a log")

        scanner = FileScanner(tmp_path, recursive=False)
        counts = scanner.count_files()

        assert counts["total"] == 2
        assert counts["eligible"] == 1
        assert counts["skipped"] == 1


class TestBufferedLogWriter:
    """Test buffered log writer."""

    def test_writer_creates_output_file(self, tmp_path):
        """Test writer creates output file."""
        output_file = tmp_path / "output.log"

        with BufferedLogWriter(output_file) as writer:
            writer.write_text("test content\n")

        assert output_file.exists()
        assert "test content" in output_file.read_text()

    def test_writer_buffers_records(self, tmp_path):
        """Test writer buffers records before flushing."""
        output_file = tmp_path / "output.log"

        record = LogRecord(
            content="test log",
            first_line="2025-01-01 10:00:00 INFO test log",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            level="INFO",
            size_bytes=8,
        )

        with BufferedLogWriter(output_file, buffer_size=10) as writer:
            writer.write_record(record)
            # Should be buffered, not written yet
            writer.flush()  # Force flush

        assert "test log" in output_file.read_text()

    def test_writer_includes_source_path(self, tmp_path):
        """Test writer includes source path header."""
        output_file = tmp_path / "output.log"
        source_path = Path("/var/log/app.log")

        record = LogRecord(
            content="test log",
            first_line="2025-01-01 10:00:00 INFO test log",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            level="INFO",
            size_bytes=8,
        )

        with BufferedLogWriter(output_file, include_path=True) as writer:
            writer.write_record(record, source_path=source_path)

        content = output_file.read_text()
        assert str(source_path) in content
        assert "test log" in content

    def test_writer_auto_flushes_on_buffer_full(self, tmp_path):
        """Test writer auto-flushes when buffer is full."""
        output_file = tmp_path / "output.log"

        with BufferedLogWriter(output_file, buffer_size=2) as writer:
            writer.write_text("line1\n")
            writer.write_text("line2\n")
            # Buffer should auto-flush here
            writer.write_text("line3\n")

        content = output_file.read_text()
        assert "line1" in content
        assert "line2" in content
        assert "line3" in content


class TestIntegrationPipeline:
    """Test complete file processing pipeline."""

    def test_end_to_end_pipeline(self, tmp_path):
        """Test complete pipeline: scan -> read -> parse -> write."""
        # Create test log file
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 INFO App started\n"
            "  Initialization complete\n"
            "2025-01-01 10:00:01.000+0000 ERROR Something failed\n"
            "  Error details here\n"
        )

        # Scan for files
        scanner = FileScanner(tmp_path, recursive=False)
        files = [f for f in scanner.scan() if not f.should_skip]
        assert len(files) == 1

        # Read and parse
        handler = LogFileHandler(files[0].path)
        lines = handler.read_lines()

        parser = StreamingRecordParser()
        records = list(parser.parse_lines(lines))
        assert len(records) == 2

        # Write results
        output_file = tmp_path / "output.log"
        with BufferedLogWriter(output_file) as writer:
            for record in records:
                writer.write_record(record, source_path=files[0].path)

        # Verify output
        output_content = output_file.read_text()
        assert "INFO App started" in output_content
        assert "ERROR Something failed" in output_content
        assert "app.log" in output_content
