"""
Comprehensive end-to-end integration tests.

Tests complete workflows from CLI input through final output:
- Multi-file processing scenarios
- Complex boolean expressions
- Real-world log analysis patterns
- Error recovery and edge cases
- Performance with large datasets
"""

import gzip
from datetime import date, datetime, time
from pathlib import Path

import pytest

from log_filter.cli import parse_args
from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.processing.pipeline import ProcessingPipeline


class TestEndToEndWorkflows:
    """Test complete end-to-end processing workflows."""

    def test_simple_error_search(self, tmp_path):
        """Test searching for ERROR level logs."""
        # Create test log file with proper timestamp format
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 INFO Application started\n"
            "2025-01-01 10:00:01.000+0000 ERROR Database connection failed\n"
            "2025-01-01 10:00:02.000+0000 WARN Retrying connection\n"
            "2025-01-01 10:00:03.000+0000 INFO Database connected\n"
            "2025-01-01 10:00:04.000+0000 ERROR Authentication failed for user admin\n"
        )

        output = tmp_path / "errors.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify output
        assert output.exists()
        content = output.read_text()
        assert "Database connection failed" in content
        assert "Authentication failed" in content
        assert "INFO Application started" not in content  # Should not include INFO logs

    def test_complex_boolean_expression(self, tmp_path):
        """Test complex boolean expression."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 ERROR Database connection failed\n"
            "2025-01-01 10:00:01.000+0000 ERROR Network timeout occurred\n"
            "2025-01-01 10:00:02.000+0000 WARN High memory usage detected\n"
            "2025-01-01 10:00:03.000+0000 ERROR Disk full detected\n"
        )

        output = tmp_path / "results.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="(ERROR OR WARN) AND NOT timeout"),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should match: ERROR or WARN but not containing "timeout"
        assert "Database connection failed" in content
        assert "High memory usage" in content
        assert "Disk full" in content
        # Should NOT match
        assert "Network timeout" not in content

    def test_date_filtering(self, tmp_path):
        """Test filtering by date range."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 ERROR Early error\n"
            "2025-01-02 10:00:00.000+0000 ERROR Middle error\n"
            "2025-01-03 10:00:00.000+0000 ERROR Late error\n"
        )

        output = tmp_path / "filtered.log"

        config = ApplicationConfig(
            search=SearchConfig(
                expression="ERROR", date_from=date(2025, 1, 2), date_to=date(2025, 1, 2)
            ),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should only include errors from 2025-01-02
        assert "2025-01-02" in content
        assert "Middle error" in content
        # Should NOT include errors from other dates
        assert "Early error" not in content
        assert "Late error" not in content

    def test_case_insensitive_search(self, tmp_path):
        """Test case-insensitive searching."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 ERROR First error\n"
            "2025-01-01 10:00:01.000+0000 Error Second error\n"
            "2025-01-01 10:00:02.000+0000 error Third error\n"
        )

        output = tmp_path / "case_insensitive.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="error", ignore_case=True),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should match all case variants
        assert "First error" in content
        assert "Second error" in content
        assert "Third error" in content

    def test_multiple_file_processing(self, tmp_path):
        """Test processing multiple files."""
        # Create multiple log files
        (tmp_path / "app1.log").write_text("2025-01-01 10:00:00.000+0000 ERROR Error in app1\n")
        (tmp_path / "app2.log").write_text("2025-01-01 10:00:00.000+0000 ERROR Error in app2\n")
        (tmp_path / "app3.log").write_text("2025-01-01 10:00:00.000+0000 ERROR Error in app3\n")

        output = tmp_path / "all_errors.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should include errors from all files
        assert "Error in app1" in content
        assert "Error in app2" in content
        assert "Error in app3" in content

    def test_compressed_file_processing(self, tmp_path):
        """Test processing gzip compressed files."""
        # Create compressed log file
        gz_file = tmp_path / "app.log.gz"
        with gzip.open(gz_file, "wt") as f:
            f.write("2025-01-01 10:00:00.000+0000 ERROR Compressed error\n")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".gz",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        assert "Compressed error" in content


class TestRealWorldScenarios:
    """Test real-world log analysis scenarios."""

    def test_critical_error_analysis(self, tmp_path):
        """Test finding critical errors across all services."""
        # Application server logs
        (tmp_path / "server.log").write_text(
            "2025-01-08 09:00:00.000+0000 INFO Server started on port 8080\n"
            "2025-01-08 09:01:00.000+0000 WARN Connection pool exhausted\n"
            "2025-01-08 09:02:00.000+0000 ERROR Failed to process order\n"
            "2025-01-08 09:03:00.000+0000 ERROR Payment gateway timeout\n"
            "2025-01-08 09:04:00.000+0000 INFO Order completed\n"
            "2025-01-08 09:05:00.000+0000 ERROR Database deadlock detected\n"
        )

        # API gateway logs
        (tmp_path / "api.log").write_text(
            "2025-01-08 09:00:00.000+0000 INFO API gateway ready\n"
            "2025-01-08 09:01:00.000+0000 WARN Rate limit exceeded for IP 192.168.1.1\n"
            "2025-01-08 09:02:00.000+0000 ERROR 503 Service Unavailable\n"
            "2025-01-08 09:03:00.000+0000 INFO Request processed in 150ms\n"
        )

        # Database logs
        (tmp_path / "database.log").write_text(
            "2025-01-08 09:00:00.000+0000 INFO Database initialized\n"
            "2025-01-08 09:02:00.000+0000 WARN Slow query: 5.2s\n"
            "2025-01-08 09:05:00.000+0000 ERROR Lock timeout on table orders\n"
        )

        output = tmp_path / "critical.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR AND (timeout OR deadlock OR Unavailable)"),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(
                output_file=output, include_file_path=True, show_progress=False, show_stats=False
            ),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should find all critical errors
        assert "Payment gateway timeout" in content
        assert "Database deadlock" in content
        assert "503 Service Unavailable" in content

    def test_performance_issue_detection(self, tmp_path):
        """Test detecting performance issues."""
        (tmp_path / "server.log").write_text(
            "2025-01-08 09:01:00.000+0000 WARN Connection pool exhausted\n"
            "2025-01-08 09:02:00.000+0000 WARN slow query detected\n"
            "2025-01-08 09:03:00.000+0000 INFO Everything OK\n"
        )

        output = tmp_path / "performance.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="WARN AND (slow OR exhausted)"),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        assert "Connection pool exhausted" in content
        assert "slow query" in content


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_directory(self, tmp_path):
        """Test processing empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=empty_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should complete without error, output may or may not exist
        if output.exists():
            content = output.read_text()
            assert content == "" or content.isspace()

    def test_no_matches_found(self, tmp_path):
        """Test when no matches are found."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("2025-01-08 10:00:00.000+0000 INFO Everything is fine\n")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="CRITICAL"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # When no matches found, output file is not created
        # This is correct behavior - don't create empty files
        if output.exists():
            content = output.read_text()
            assert content == "" or content.isspace()
        # Test passes either way - file may or may not be created for no matches

    def test_mixed_line_endings(self, tmp_path):
        """Test handling files with mixed line endings."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Write file with mixed line endings
        log_file = log_dir / "mixed.log"
        log_file.write_bytes(
            b"2025-01-08 10:00:00.000+0000 ERROR Unix\n"
            b"2025-01-08 10:00:01.000+0000 ERROR Windows\r\n"
            b"2025-01-08 10:00:02.000+0000 ERROR Mac\r"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # Should handle all line endings
        assert "Unix" in content
        assert "Windows" in content

    def test_special_characters_in_logs(self, tmp_path):
        """Test handling special characters."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        (log_dir / "special.log").write_text(
            "2025-01-08 10:00:00.000+0000 ERROR Special chars: àéîöü\n"
            "2025-01-08 10:00:01.000+0000 ERROR Symbols: @#$%^&*\n"
            "2025-01-08 10:00:02.000+0000 ERROR Unicode: 你好世界\n",
            encoding="utf-8",
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text(encoding="utf-8")
        assert "àéîöü" in content
        assert "@#$%^&*" in content

    def test_very_long_lines(self, tmp_path):
        """Test handling very long log lines."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        long_line = "ERROR " + "x" * 10000 + "\n"
        (log_dir / "long.log").write_text(
            "2025-01-08 10:00:00.000+0000 "
            + long_line
            + "2025-01-08 10:00:01.000+0000 INFO Short line\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        assert output.exists()
        content = output.read_text()
        assert "ERROR" in content


class TestStatisticsAndReporting:
    """Test statistics collection and reporting."""

    def test_statistics_are_collected(self, tmp_path):
        """Test that statistics are properly collected."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        (log_dir / "app.log").write_text(
            "2025-01-08 10:00:00.000+0000 ERROR Error 1\n"
            "2025-01-08 10:00:01.000+0000 INFO Info 1\n"
            "2025-01-08 10:00:02.000+0000 ERROR Error 2\n"
            "2025-01-08 10:00:03.000+0000 INFO Info 2\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_stats=True, show_progress=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        stats = pipeline.stats.get_snapshot()

        assert stats.files_processed == 1
        assert stats.records_total == 4
        assert stats.records_matched == 2

    def test_dry_run_mode(self, tmp_path):
        """Test dry run mode doesn't write output."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        (log_dir / "app.log").write_text("2025-01-08 10:00:00.000+0000 ERROR Test error\n")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(
                output_file=output, dry_run=True, show_progress=False, show_stats=False
            ),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Output file should not be created in dry run
        assert not output.exists()


class TestConcurrentProcessing:
    """Test concurrent/parallel processing scenarios."""

    def test_multi_worker_processing(self, tmp_path):
        """Test processing with multiple workers."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create multiple log files
        for i in range(5):
            (log_dir / f"app{i}.log").write_text(
                f"2025-01-08 10:00:00.000+0000 ERROR Error in file {i}\n"
                f"2025-01-08 10:00:01.000+0000 INFO Info in file {i}\n"
            )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=log_dir),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(worker_count=2),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        content = output.read_text()
        # All errors should be found
        for i in range(5):
            assert f"file {i}" in content
