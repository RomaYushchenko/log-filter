"""
Integration tests for observability features.

Tests statistics reporting, progress tracking, performance metrics,
logging configuration, and summary report generation.
"""

import json
import logging
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest

from log_filter.statistics.collector import ProcessingStats, StatisticsCollector
from log_filter.statistics.performance import (
    FilePerformance,
    PerformanceMetrics,
    PerformanceTracker,
)
from log_filter.statistics.reporter import StatisticsReporter
from log_filter.statistics.summary import ProcessingSummary, SummaryReportGenerator
from log_filter.utils.logging import (
    LoggerAdapter,
    configure_component_logging,
    configure_logging,
    create_file_logger,
    get_logger,
)
from log_filter.utils.progress import ProgressCounter, ProgressTracker


class TestStatisticsReporter:
    """Test statistics reporter functionality."""

    def test_console_output_format(self):
        """Test console output formatting."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_scanned=100,
            files_processed=90,
            files_skipped=10,
            skip_reasons={"too_large": 5, "permission_denied": 5},
            records_total=10000,
            records_matched=1500,
            records_skipped=500,
            total_bytes_processed=50_000_000,
            total_lines_processed=15000,
            start_time=start,
            end_time=start + 300.0,
        )

        reporter = StatisticsReporter()
        output = StringIO()
        reporter.print_console(stats, file=output)

        result = output.getvalue()
        assert "LOG FILTER PROCESSING STATISTICS" in result
        assert "100" in result  # files scanned
        assert "1,500" in result  # records matched (with comma formatting)
        assert "47.68 MB" in result or "50.00 MB" in result  # megabytes
        assert "too_large" in result

    def test_json_export(self, tmp_path):
        """Test JSON export functionality."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_scanned=50,
            files_processed=45,
            records_total=5000,
            records_matched=500,
            total_bytes_processed=10_000_000,
            total_lines_processed=7500,
            start_time=start,
            end_time=start + 60.0,
        )

        output_file = tmp_path / "stats.json"
        reporter = StatisticsReporter()
        reporter.export_json(stats, output_file, pretty=True)

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["files"]["scanned"] == 50
        assert data["records"]["total"] == 5000
        assert data["records"]["matched"] == 500
        assert data["execution"]["duration_seconds"] == 60.0

    def test_csv_export(self, tmp_path):
        """Test CSV export functionality."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_scanned=25,
            files_processed=20,
            records_total=2500,
            records_matched=250,
            total_bytes_processed=5_000_000,
            total_lines_processed=3000,
            start_time=start,
            end_time=start + 30.0,
        )

        output_file = tmp_path / "stats.csv"
        reporter = StatisticsReporter()
        reporter.export_csv(stats, output_file)

        assert output_file.exists()

        content = output_file.read_text()
        assert "Files scanned,25" in content
        assert "Records total,2500" in content

    def test_format_summary(self):
        """Test one-line summary formatting."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_processed=10,
            records_total=1000,
            records_matched=100,
            start_time=start,
            end_time=start + 10.0,
        )

        reporter = StatisticsReporter()
        summary = reporter.format_summary(stats)

        assert "10 files" in summary
        assert "1,000 records" in summary
        assert "100 matches" in summary
        assert "10.00s" in summary


class TestProgressTracker:
    """Test progress tracking functionality."""

    def test_disabled_progress_passthrough(self):
        """Test that disabled progress tracker acts as passthrough."""
        tracker = ProgressTracker(enable=False)
        items = [1, 2, 3, 4, 5]

        result = list(tracker.track_generic(items, unit="item"))

        assert result == items

    def test_progress_counter_context_manager(self):
        """Test progress counter as context manager."""
        tracker = ProgressTracker(enable=False)

        with tracker.create_counter(total=10, unit="item") as counter:
            for i in range(10):
                counter.update(1)

        # Should complete without errors

    def test_progress_counter_methods(self):
        """Test progress counter update methods."""
        tracker = ProgressTracker(enable=False)

        counter = tracker.create_counter(total=100, unit="item")
        counter.__enter__()

        counter.update(10)
        counter.set_postfix_str("Processing...")
        counter.set_description("Updated")

        counter.__exit__(None, None, None)


class TestPerformanceTracker:
    """Test performance metrics tracking."""

    def test_file_timer_context_manager(self):
        """Test file timer context manager."""
        tracker = PerformanceTracker()
        tracker.start()

        with tracker.track_file(Path("test.log"), 1024) as timer:
            timer.set_records(100, 25)

        tracker.stop()
        metrics = tracker.get_metrics()

        assert metrics.total_files == 1
        assert metrics.total_records == 100
        assert metrics.total_bytes == 1024

    def test_multiple_file_tracking(self):
        """Test tracking multiple files."""
        tracker = PerformanceTracker()
        tracker.start()

        for i in range(5):
            with tracker.track_file(
                Path(f"file{i}.log"), 2048, worker_id=f"worker-{i % 2}"
            ) as timer:
                timer.set_records(50, 10)

        tracker.stop()
        metrics = tracker.get_metrics()

        assert metrics.total_files == 5
        assert metrics.total_records == 250
        assert metrics.total_bytes == 10240
        assert len(metrics.worker_times) == 2  # 2 workers

    def test_performance_metrics_properties(self):
        """Test performance metrics calculated properties."""
        metrics = PerformanceMetrics(
            total_files=10, total_records=1000, total_bytes=10_000_000, total_time_seconds=10.0
        )

        assert metrics.avg_records_per_sec == 100.0
        assert metrics.avg_file_time_seconds == 1.0
        assert abs(metrics.avg_mb_per_sec - 0.954) < 0.01
        assert abs(metrics.total_megabytes - 9.54) < 0.01

    def test_file_performance_properties(self):
        """Test file performance calculated properties."""
        perf = FilePerformance(
            file_path="test.log",
            file_size_bytes=1_000_000,
            records_processed=500,
            records_matched=100,
            processing_time_seconds=2.0,
        )

        assert perf.throughput_records_per_sec == 250.0
        assert abs(perf.throughput_mb_per_sec - 0.477) < 0.01
        assert perf.match_rate == 20.0

    def test_slowest_and_largest_files(self):
        """Test getting slowest and largest files."""
        metrics = PerformanceMetrics()

        # Add various file performances
        metrics.file_performances = [
            FilePerformance("fast.log", 1000, 10, 5, 0.1),
            FilePerformance("slow.log", 1000, 10, 5, 5.0),
            FilePerformance("medium.log", 1000, 10, 5, 1.0),
            FilePerformance("small.log", 500, 10, 5, 0.5),
            FilePerformance("large.log", 10000, 10, 5, 2.0),
        ]

        slowest = metrics.get_slowest_files(2)
        assert len(slowest) == 2
        assert slowest[0].file_path == "slow.log"
        assert slowest[1].file_path == "large.log"

        largest = metrics.get_largest_files(2)
        assert len(largest) == 2
        assert largest[0].file_path == "large.log"


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_configure_logging_console_only(self, capsys):
        """Test console-only logging configuration."""
        configure_logging(level="INFO", log_to_console=True)
        logger = get_logger("log_filter.test")

        logger.info("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_configure_logging_with_file(self, tmp_path):
        """Test logging configuration with file handler."""
        log_file = tmp_path / "test.log"
        configure_logging(level="DEBUG", log_file=log_file, log_to_console=False)

        logger = get_logger("log_filter.test")
        logger.info("Test message")
        logger.debug("Debug message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
        assert "Debug message" in content

    def test_configure_component_logging(self):
        """Test component-specific logging configuration."""
        configure_logging(level="INFO")
        configure_component_logging("log_filter.test", "DEBUG")

        logger = get_logger("log_filter.test")
        assert logger.level == logging.DEBUG

    def test_logger_adapter_context(self, capsys):
        """Test logger adapter with context."""
        configure_logging(level="INFO", log_to_console=True)
        base_logger = get_logger("log_filter.test")
        adapter = LoggerAdapter(base_logger, {"file": "test.log", "worker": "worker-1"})

        adapter.info("Processing")

        captured = capsys.readouterr()
        assert "Processing" in captured.out
        assert "file=test.log" in captured.out
        assert "worker=worker-1" in captured.out

    def test_create_file_logger(self, capsys):
        """Test file logger creation."""
        configure_logging(level="INFO", log_to_console=True)
        logger = create_file_logger(Path("/path/to/test.log"))

        logger.info("Processing file")

        captured = capsys.readouterr()
        assert "Processing file" in captured.out
        assert "test.log" in captured.out


class TestSummaryReportGenerator:
    """Test summary report generation."""

    def test_console_report_generation(self):
        """Test console report generation."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_scanned=100,
            files_processed=95,
            files_skipped=5,
            skip_reasons={"too_large": 3, "empty": 2},
            records_total=10000,
            records_matched=1000,
            records_skipped=200,
            total_bytes_processed=50_000_000,
            total_lines_processed=15000,
            start_time=start,
            end_time=start + 300.0,
        )

        performance = PerformanceMetrics(
            total_files=95,
            total_records=10000,
            total_bytes=50_000_000,
            total_time_seconds=300.0,
            file_performances=[
                FilePerformance("slow.log", 10_000_000, 5000, 500, 60.0),
                FilePerformance("fast.log", 1_000_000, 1000, 100, 5.0),
            ],
            worker_times={"worker-0": 150.0, "worker-1": 140.0},
        )

        summary = ProcessingSummary(
            statistics=stats,
            performance=performance,
            timestamp=datetime.now(),
            errors=["Error processing file X"],
            warnings=["Large file detected"],
        )

        generator = SummaryReportGenerator()
        output = StringIO()
        generator.generate_console_report(summary, file=output, show_top_files=2)

        result = output.getvalue()
        assert "PROCESSING SUMMARY REPORT" in result
        assert "100" in result  # files scanned
        assert "10,000" in result  # records
        assert "too_large" in result
        assert "slow.log" in result
        assert "Error processing file X" in result
        assert "Large file detected" in result

    def test_markdown_report_generation(self, tmp_path):
        """Test markdown report generation."""
        import time

        start = time.time()
        stats = ProcessingStats(
            files_scanned=50,
            files_processed=45,
            records_total=5000,
            records_matched=500,
            total_bytes_processed=10_000_000,
            total_lines_processed=7500,
            start_time=start,
            end_time=start + 60.0,
        )

        performance = PerformanceMetrics(
            total_files=45,
            total_records=5000,
            total_bytes=10_000_000,
            total_time_seconds=60.0,
            file_performances=[
                FilePerformance("file1.log", 5_000_000, 2500, 250, 30.0),
            ],
        )

        summary = ProcessingSummary(
            statistics=stats,
            performance=performance,
            timestamp=datetime.now(),
            errors=[],
            warnings=[],
        )

        output_file = tmp_path / "report.md"
        generator = SummaryReportGenerator()
        generator.generate_markdown_report(summary, output_file, show_top_files=5)

        assert output_file.exists()
        content = output_file.read_text()

        assert "# Log Processing Summary Report" in content
        assert "## Execution" in content
        assert "## Files" in content
        assert "## Records" in content
        assert "## Performance" in content

    def test_empty_summary(self):
        """Test report generation with empty data."""
        stats = ProcessingStats(
            files_scanned=0,
            files_processed=0,
            records_total=0,
            records_matched=0,
            total_bytes_processed=0,
            total_lines_processed=0,
            start_time=None,
            end_time=None,
        )

        performance = PerformanceMetrics()

        summary = ProcessingSummary(
            statistics=stats,
            performance=performance,
            timestamp=datetime.now(),
            errors=[],
            warnings=[],
        )

        generator = SummaryReportGenerator()
        output = StringIO()
        generator.generate_console_report(summary, file=output)

        result = output.getvalue()
        assert "PROCESSING SUMMARY REPORT" in result
        assert "0" in result  # Should show zeros


class TestIntegratedObservability:
    """Test integrated observability features."""

    def test_full_observability_workflow(self, tmp_path):
        """Test complete observability workflow."""
        # Configure logging
        log_file = tmp_path / "app.log"
        configure_logging(level="INFO", log_file=log_file, log_to_console=False)
        logger = get_logger("log_filter.test")

        # Create trackers
        stats_collector = StatisticsCollector()
        perf_tracker = PerformanceTracker()
        progress_tracker = ProgressTracker(enable=False)

        # Start tracking
        perf_tracker.start()
        logger.info("Processing started")

        # Simulate file processing
        files = [Path(f"file{i}.log") for i in range(3)]

        for file_path in progress_tracker.track_files(files, total=len(files)):
            stats_collector.increment_files_scanned()

            with perf_tracker.track_file(file_path, 1024) as timer:
                # Simulate processing
                records_count = 100
                matches_count = 10

                stats_collector.increment_files_processed()
                stats_collector.increment_records_total(records_count)
                stats_collector.increment_records_matched(matches_count)
                stats_collector.add_bytes_processed(1024)

                timer.set_records(records_count, matches_count)

            logger.info(f"Processed {file_path}")

        # Stop tracking
        perf_tracker.stop()
        logger.info("Processing completed")

        # Generate reports
        stats = stats_collector.get_snapshot()
        perf_metrics = perf_tracker.get_metrics()

        # Verify statistics
        assert stats.files_scanned == 3
        assert stats.files_processed == 3
        assert stats.records_total == 300
        assert stats.records_matched == 30

        # Verify performance
        assert perf_metrics.total_files == 3
        assert perf_metrics.total_records == 300

        # Verify logging
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Processing started" in log_content
        assert "Processing completed" in log_content

        # Generate summary
        summary = ProcessingSummary(
            statistics=stats,
            performance=perf_metrics,
            timestamp=datetime.now(),
            errors=[],
            warnings=[],
        )

        generator = SummaryReportGenerator()
        output = StringIO()
        generator.generate_console_report(summary, file=output)

        result = output.getvalue()
        assert "3" in result  # files processed
        assert "300" in result  # records
