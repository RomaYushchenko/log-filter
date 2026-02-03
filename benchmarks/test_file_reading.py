"""Benchmarks for file reading performance.

Tests different file sizes and formats to measure I/O and decompression performance.
"""

from pathlib import Path

from log_filter.infrastructure.file_handlers.gzip_handler import GzipFileHandler
from log_filter.infrastructure.file_handlers.log_handler import LogFileHandler


class TestFileReading:
    """Benchmark file reading operations."""

    def test_read_small_file(self, benchmark, small_log_file: Path):
        """Benchmark reading a small log file (1MB).

        Target: < 50ms for 1MB file
        """
        handler = LogFileHandler(small_log_file)

        def read_all_lines():
            return list(handler.read_lines())

        lines = benchmark(read_all_lines)
        assert len(lines) > 5000  # Verify file was read

    def test_read_medium_file(self, benchmark, medium_log_file: Path):
        """Benchmark reading a medium log file (10MB).

        Target: < 500ms for 10MB file
        """
        handler = LogFileHandler(medium_log_file)

        def read_all_lines():
            return list(handler.read_lines())

        lines = benchmark(read_all_lines)
        assert len(lines) > 50000

    def test_read_large_file(self, benchmark, large_log_file: Path):
        """Benchmark reading a large log file (100MB).

        Target: < 5s for 100MB file
        """
        handler = LogFileHandler(large_log_file)

        def read_all_lines():
            return list(handler.read_lines())

        lines = benchmark(read_all_lines)
        assert len(lines) > 500000

    def test_read_compressed_file(self, benchmark, compressed_log_file: Path):
        """Benchmark reading a compressed log file (5-8MB compressed).

        Target: < 2s for 5MB compressed file (with pigz: < 1s)
        """
        handler = GzipFileHandler(compressed_log_file)

        def read_all_lines():
            return list(handler.read_lines())

        lines = benchmark(read_all_lines)
        assert len(lines) > 250000

    def test_read_many_small_files(self, benchmark, many_small_files: Path):
        """Benchmark reading many small log files (100 files × 100KB).

        Target: < 2s for 100 files
        """

        def read_all_files():
            total_lines = 0
            for file_path in many_small_files.glob("*.log"):
                handler = LogFileHandler(file_path)
                total_lines += len(list(handler.read_lines()))
            return total_lines

        total_lines = benchmark(read_all_files)
        assert total_lines > 50000  # 100 files × 500 lines


class TestFileValidation:
    """Benchmark file validation operations."""

    def test_validate_log_file(self, benchmark, medium_log_file: Path):
        """Benchmark log file validation.

        Target: < 10ms
        """
        handler = LogFileHandler(medium_log_file)

        def validate():
            return handler.validate()

        is_valid, error = benchmark(validate)
        assert is_valid

    def test_validate_gzip_file(self, benchmark, compressed_log_file: Path):
        """Benchmark gzip file validation.

        Target: < 50ms
        """
        handler = GzipFileHandler(compressed_log_file)

        def validate():
            return handler.validate()

        is_valid, error = benchmark(validate)
        assert is_valid
