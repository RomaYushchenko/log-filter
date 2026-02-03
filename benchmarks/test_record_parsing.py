"""Benchmarks for record parsing performance.

Tests pattern matching and record assembly operations.
"""

import re

from log_filter.processing.record_parser import StreamingRecordParser


class TestRecordParsing:
    """Benchmark record parsing operations."""

    def test_is_record_start_fast_path(self, benchmark, sample_log_lines: list[str]):
        """Benchmark is_record_start with fast-path optimization.

        This tests the critical optimization of checking first character
        before running expensive regex. Should be 20-40% faster than
        regex-only approach.

        Target: < 1ms for 100 lines
        """
        parser = StreamingRecordParser()

        def check_all_lines():
            count = 0
            for line in sample_log_lines:
                if parser.is_record_start(line):
                    count += 1
            return count

        record_count = benchmark(check_all_lines)
        assert record_count > 0  # Should find some record starts

    def test_is_record_start_worst_case(self, benchmark):
        """Benchmark is_record_start with lines that pass fast-path.

        All lines start with digits, so fast-path check passes and
        regex must be evaluated every time.

        Target: < 5ms for 1000 lines
        """
        parser = StreamingRecordParser()

        # Generate lines that all start with digits (worst case for fast-path)
        lines = [f"2026-02-03 10:30:45.123+0000 INFO Request {i}" for i in range(1000)]

        def check_all_lines():
            count = 0
            for line in lines:
                if parser.is_record_start(line):
                    count += 1
            return count

        record_count = benchmark(check_all_lines)
        assert record_count == 1000  # All should match

    def test_is_record_start_best_case(self, benchmark):
        """Benchmark is_record_start with non-matching lines.

        Lines don't start with digits, so fast-path immediately returns False.

        Target: < 0.5ms for 1000 lines (should be ~100x faster than regex)
        """
        parser = StreamingRecordParser()

        # Generate lines that don't start with digits (best case for fast-path)
        lines = ["    at com.example.Service.method(Service.java:42)" for _ in range(1000)]

        def check_all_lines():
            count = 0
            for line in lines:
                if parser.is_record_start(line):
                    count += 1
            return count

        record_count = benchmark(check_all_lines)
        assert record_count == 0  # None should match

    def test_pattern_compilation(self, benchmark):
        """Benchmark regex pattern compilation.

        Target: < 1ms for default pattern
        """
        pattern_str = (
            r"^(\d{4}-\d{2}-\d{2}) " r"(\d{2}:\d{2}:\d{2})" r"\.\d{3}[+-]\d{4}\s+" r"([A-Z]+)"
        )

        def compile_pattern():
            return re.compile(pattern_str)

        pattern = benchmark(compile_pattern)
        assert pattern is not None


class TestLevelNormalization:
    """Benchmark level normalization operations."""

    def test_normalize_level(self, benchmark):
        """Benchmark level normalization.

        Should be O(1) dictionary lookup.

        Target: < 0.1ms for 1000 operations
        """
        parser = StreamingRecordParser()

        levels = ["E", "W", "I", "D", "ERROR", "WARN", "INFO", "DEBUG"] * 125

        def normalize_all():
            return [parser._normalize_level(level) for level in levels]

        normalized = benchmark(normalize_all)
        assert len(normalized) == 1000
        assert "ERROR" in normalized
        assert "WARN" in normalized
