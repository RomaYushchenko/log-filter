"""Performance benchmarks for log_filter components using pytest-benchmark."""

import gzip
import string
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    SearchConfig,
)
from src.log_filter.core.evaluator import ExpressionEvaluator
from src.log_filter.core.parser import ExpressionParser
from src.log_filter.core.tokenizer import Tokenizer
from src.log_filter.infrastructure.file_handlers.gzip_handler import GzipFileHandler
from src.log_filter.infrastructure.file_handlers.log_handler import LogFileHandler
from src.log_filter.infrastructure.file_scanner import FileScanner
from src.log_filter.processing.pipeline import ProcessingPipeline
from src.log_filter.processing.record_parser import StreamingRecordParser


class TestTokenizerBenchmarks:
    """Benchmark tokenizer performance."""

    def test_benchmark_simple_expression(self, benchmark):
        """Benchmark tokenizing a simple expression."""
        expression = "ERROR"
        result = benchmark(lambda: Tokenizer(expression).tokenize())
        assert len(result) > 0

    def test_benchmark_complex_expression(self, benchmark):
        """Benchmark tokenizing a complex boolean expression."""
        expression = "(ERROR OR WARN) AND NOT (timeout OR failed)"
        result = benchmark(lambda: Tokenizer(expression).tokenize())
        assert len(result) > 0

    def test_benchmark_deeply_nested_expression(self, benchmark):
        """Benchmark tokenizing deeply nested expression."""
        expression = "((((ERROR OR WARN) AND INFO) OR DEBUG) AND (critical OR fatal))"
        result = benchmark(lambda: Tokenizer(expression).tokenize())
        assert len(result) > 0


class TestParserBenchmarks:
    """Benchmark parser performance."""

    def test_benchmark_simple_parse(self, benchmark):
        """Benchmark parsing a simple expression."""
        tokens = Tokenizer("ERROR OR WARN").tokenize()
        result = benchmark(lambda: ExpressionParser(tokens).parse())
        assert result is not None

    def test_benchmark_complex_parse(self, benchmark):
        """Benchmark parsing a complex expression."""
        tokens = Tokenizer("(ERROR OR WARN) AND NOT timeout").tokenize()
        result = benchmark(lambda: ExpressionParser(tokens).parse())
        assert result is not None

    def test_benchmark_deeply_nested_parse(self, benchmark):
        """Benchmark parsing deeply nested expression."""
        tokens = Tokenizer("((ERROR OR WARN) AND (INFO OR DEBUG))").tokenize()
        result = benchmark(lambda: ExpressionParser(tokens).parse())
        assert result is not None


class TestEvaluatorBenchmarks:
    """Benchmark evaluator performance."""

    @pytest.fixture
    def sample_log_line(self):
        """Generate a sample log line."""
        return "2025-01-08 10:00:00.000+0000 ERROR Database connection failed after 30 seconds"

    @pytest.fixture
    def long_log_line(self):
        """Generate a long log line."""
        return "2025-01-08 10:00:00.000+0000 ERROR " + "x" * 1000

    def test_benchmark_simple_term_match(self, benchmark, sample_log_line):
        """Benchmark evaluating a simple term."""
        # Tokenize and parse once
        tokens = Tokenizer("ERROR").tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        result = benchmark(lambda: evaluator.evaluate(ast, sample_log_line))
        assert result is True

    def test_benchmark_boolean_expression(self, benchmark, sample_log_line):
        """Benchmark evaluating boolean expression."""
        tokens = Tokenizer("ERROR AND Database").tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        result = benchmark(lambda: evaluator.evaluate(ast, sample_log_line))
        assert result is True

    def test_benchmark_complex_expression(self, benchmark, sample_log_line):
        """Benchmark evaluating complex expression."""
        expression = "(ERROR OR WARN) AND (Database OR connection)"
        tokens = Tokenizer(expression).tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        result = benchmark(lambda: evaluator.evaluate(ast, sample_log_line))
        assert result is True

    def test_benchmark_regex_evaluation(self, benchmark, sample_log_line):
        """Benchmark regex evaluation."""
        tokens = Tokenizer(r"ERROR.*failed").tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=True)
        result = benchmark(lambda: evaluator.evaluate(ast, sample_log_line))
        assert result is True

    def test_benchmark_case_insensitive(self, benchmark, sample_log_line):
        """Benchmark case-insensitive evaluation."""
        tokens = Tokenizer("error").tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=True, use_regex=False)
        result = benchmark(lambda: evaluator.evaluate(ast, sample_log_line))
        assert result is True

    def test_benchmark_long_text(self, benchmark, long_log_line):
        """Benchmark evaluation on long text."""
        tokens = Tokenizer("ERROR").tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        result = benchmark(lambda: evaluator.evaluate(ast, long_log_line))
        assert result is True


class TestFileHandlerBenchmarks:
    """Benchmark file handler performance."""

    @pytest.fixture
    def small_log_file(self, tmp_path):
        """Create a small log file (100 lines)."""
        log_file = tmp_path / "small.log"
        lines = [f"2025-01-08 10:00:{i:02d}.000+0000 ERROR Test error {i}\n" for i in range(100)]
        log_file.write_text("".join(lines))
        return log_file

    @pytest.fixture
    def medium_log_file(self, tmp_path):
        """Create a medium log file (10,000 lines)."""
        log_file = tmp_path / "medium.log"
        lines = [f"2025-01-08 10:00:00.{i:06d}+0000 ERROR Test error {i}\n" for i in range(10000)]
        log_file.write_text("".join(lines))
        return log_file

    @pytest.fixture
    def compressed_log_file(self, tmp_path):
        """Create a compressed log file."""
        gz_file = tmp_path / "compressed.log.gz"
        lines = [f"2025-01-08 10:00:{i:02d}.000+0000 ERROR Test error {i}\n" for i in range(1000)]
        with gzip.open(gz_file, "wt") as f:
            f.writelines(lines)
        return gz_file

    def test_benchmark_read_small_file(self, benchmark, small_log_file):
        """Benchmark reading a small plain log file."""
        handler = LogFileHandler(small_log_file)

        def read_all():
            lines = []
            for line in handler.read_lines():
                lines.append(line)
            return lines

        result = benchmark(read_all)
        assert len(result) == 100

    def test_benchmark_read_medium_file(self, benchmark, medium_log_file):
        """Benchmark reading a medium plain log file."""
        handler = LogFileHandler(medium_log_file)

        def read_all():
            count = 0
            for _ in handler.read_lines():
                count += 1
            return count

        result = benchmark(read_all)
        assert result == 10000

    def test_benchmark_read_compressed_file(self, benchmark, compressed_log_file):
        """Benchmark reading a compressed log file."""
        handler = GzipFileHandler(compressed_log_file)

        def read_all():
            count = 0
            for _ in handler.read_lines():
                count += 1
            return count

        result = benchmark(read_all)
        assert result == 1000


class TestRecordParserBenchmarks:
    """Benchmark record parser performance."""

    @pytest.fixture
    def log_lines(self):
        """Generate sample log lines."""
        return [
            f"2025-01-08 10:{i//60:02d}:{i%60:02d}.000+0000 ERROR Test error {i}"
            for i in range(1000)
        ]

    def test_benchmark_parse_single_line_records(self, benchmark, log_lines):
        """Benchmark parsing single-line records."""
        parser = StreamingRecordParser(max_record_size_bytes=1024 * 1024)  # 1MB

        def parse_all():
            records = list(parser.parse_lines(iter(log_lines), file_path="benchmark.log"))
            return records

        result = benchmark(parse_all)
        assert len(result) == 1000


class TestFileScannerBenchmarks:
    """Benchmark file scanner performance."""

    @pytest.fixture
    def file_tree(self, tmp_path):
        """Create a directory tree with many files."""
        # Create 100 log files across 10 directories
        for i in range(10):
            dir_path = tmp_path / f"dir_{i}"
            dir_path.mkdir()
            for j in range(10):
                log_file = dir_path / f"app_{j}.log"
                log_file.write_text(f"2025-01-08 ERROR Test {i}-{j}\n")
        return tmp_path

    def test_benchmark_scan_directory(self, benchmark, file_tree):
        """Benchmark scanning a directory tree."""
        scanner = FileScanner(root_path=file_tree, allowed_extensions={".log"}, file_masks=[])

        result = benchmark(lambda: list(scanner.scan()))
        assert len(result) == 100


class TestEndToEndBenchmarks:
    """Benchmark end-to-end pipeline performance."""

    @pytest.fixture
    def benchmark_data(self, tmp_path):
        """Create benchmark data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create 10 log files with 1000 lines each
        for i in range(10):
            log_file = data_dir / f"app_{i}.log"
            lines = []
            for j in range(1000):
                level = ["INFO", "WARN", "ERROR", "DEBUG"][j % 4]
                lines.append(
                    f"2025-01-08 10:00:{j%60:02d}.{j:03d}+0000 {level} Message {j} in file {i}\n"
                )
            log_file.write_text("".join(lines))

        return data_dir

    def test_benchmark_simple_search(self, benchmark, benchmark_data, tmp_path):
        """Benchmark simple search across multiple files."""
        output = tmp_path / "output.log"

        def run_pipeline():
            config = ApplicationConfig(
                search=SearchConfig(expression="ERROR"),
                files=FileConfig(search_root=benchmark_data),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )
            pipeline = ProcessingPipeline(config)
            pipeline.run()

        benchmark(run_pipeline)
        assert output.exists()

    def test_benchmark_complex_search(self, benchmark, benchmark_data, tmp_path):
        """Benchmark complex boolean search."""
        output = tmp_path / "output.log"

        def run_pipeline():
            config = ApplicationConfig(
                search=SearchConfig(expression="(ERROR OR WARN) AND Message"),
                files=FileConfig(search_root=benchmark_data),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )
            pipeline = ProcessingPipeline(config)
            pipeline.run()
            # Clean up for next iteration
            if output.exists():
                output.unlink()

        benchmark(run_pipeline)


class TestScalabilityBenchmarks:
    """Benchmark scalability with different data sizes."""

    def create_log_file(self, path: Path, num_lines: int):
        """Helper to create log files of specific size."""
        lines = [
            f"2025-01-08 10:00:00.{i:06d}+0000 ERROR Test error message {i}\n"
            for i in range(num_lines)
        ]
        path.write_text("".join(lines))

    @pytest.mark.parametrize("num_lines", [100, 1000, 10000])
    def test_benchmark_file_size_scaling(self, benchmark, tmp_path, num_lines):
        """Benchmark how performance scales with file size."""
        log_file = tmp_path / f"test_{num_lines}.log"
        self.create_log_file(log_file, num_lines)

        output = tmp_path / "output.log"

        def run_pipeline():
            config = ApplicationConfig(
                search=SearchConfig(expression="ERROR"),
                files=FileConfig(search_root=tmp_path, file_masks=[f"test_{num_lines}.log"]),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )
            pipeline = ProcessingPipeline(config)
            pipeline.run()
            if output.exists():
                output.unlink()

        benchmark(run_pipeline)

    @pytest.mark.parametrize("num_files", [1, 10, 50])
    def test_benchmark_file_count_scaling(self, benchmark, tmp_path, num_files):
        """Benchmark how performance scales with number of files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        for i in range(num_files):
            log_file = data_dir / f"app_{i}.log"
            self.create_log_file(log_file, 1000)

        output = tmp_path / "output.log"

        def run_pipeline():
            config = ApplicationConfig(
                search=SearchConfig(expression="ERROR"),
                files=FileConfig(search_root=data_dir),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )
            pipeline = ProcessingPipeline(config)
            pipeline.run()
            if output.exists():
                output.unlink()

        benchmark(run_pipeline)


class TestMemoryEfficiencyBenchmarks:
    """Benchmark memory efficiency for large files."""

    @pytest.fixture
    def large_log_file(self, tmp_path):
        """Create a very large log file (100K lines)."""
        log_file = tmp_path / "large.log"
        # Write in chunks to avoid memory issues during test setup
        with open(log_file, "w") as f:
            for batch in range(100):
                lines = [
                    f"2025-01-08 10:00:00.{i:06d}+0000 ERROR Test error {batch * 1000 + i}\n"
                    for i in range(1000)
                ]
                f.writelines(lines)
        return log_file

    def test_benchmark_streaming_large_file(self, benchmark, large_log_file, tmp_path):
        """Benchmark streaming processing of large file."""
        output = tmp_path / "output.log"

        def run_pipeline():
            config = ApplicationConfig(
                search=SearchConfig(expression="ERROR"),
                files=FileConfig(search_root=tmp_path, file_masks=["large.log"]),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )
            pipeline = ProcessingPipeline(config)
            pipeline.run()
            if output.exists():
                output.unlink()

        benchmark(run_pipeline)
