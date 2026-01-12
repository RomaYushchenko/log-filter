"""
Integration tests for log level abbreviation support.

Tests end-to-end filtering with abbreviated log levels (E, W, I, D)
versus full level names (ERROR, WARN, INFO, DEBUG).
"""

from pathlib import Path

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.processing.pipeline import ProcessingPipeline


class TestAbbreviatedLevelFiltering:
    """Test filtering logs with abbreviated levels."""

    def test_filter_abbreviated_error_logs(self, tmp_path):
        """Test searching for 'ERROR' matches logs with abbreviated 'E'."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Database connection failed\n"
            "2025-01-08 10:00:01.000+0000 I Application started\n"
            "2025-01-08 10:00:02.000+0000 E Timeout occurred\n"
            "2025-01-08 10:00:03.000+0000 W Connection slow\n"
        )

        output = tmp_path / "output.log"

        # Create config with normalization enabled (default)
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=True),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match 2 ERROR records (both with 'E')
        assert output.exists()
        content = output.read_text()
        assert "Database connection failed" in content
        assert "Timeout occurred" in content
        assert "Application started" not in content
        assert "Connection slow" not in content

    def test_boolean_expression_with_abbreviated_levels(self, tmp_path):
        """Test boolean expressions work with abbreviated levels."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Database error occurred\n"
            "2025-01-08 10:00:01.000+0000 W Database is slow\n"
            "2025-01-08 10:00:02.000+0000 I Normal operation\n"
            "2025-01-08 10:00:03.000+0000 E Network error\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR AND database", ignore_case=True),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=True),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match only 1 record: "E Database error occurred"
        assert output.exists()
        content = output.read_text()
        assert "Database error occurred" in content
        assert "Network error" not in content  # Doesn't contain "database"
        assert "Database is slow" not in content  # Not ERROR level

    def test_or_expression_with_levels(self, tmp_path):
        """Test OR expressions with log levels."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Database error\n"
            "2025-01-08 10:00:01.000+0000 W Connection slow\n"
            "2025-01-08 10:00:02.000+0000 I Normal operation\n"
            "2025-01-08 10:00:03.000+0000 D Debug message\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR OR WARN"),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=True),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match 2 records (E and W)
        assert output.exists()
        content = output.read_text()
        assert "Database error" in content
        assert "Connection slow" in content
        assert "Normal operation" not in content
        assert "Debug message" not in content

    def test_mixed_level_formats(self, tmp_path):
        """Test logs with mixed level formats (abbreviated and full)."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 ERROR Full level name\n"
            "2025-01-08 10:00:01.000+0000 E Abbreviated level\n"
            "2025-01-08 10:00:02.000+0000 WARN Another full name\n"
            "2025-01-08 10:00:03.000+0000 W Another abbreviation\n"
            "2025-01-08 10:00:04.000+0000 INFO Info message\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=True),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match both ERROR and E records
        assert output.exists()
        content = output.read_text()
        assert "Full level name" in content
        assert "Abbreviated level" in content
        assert "Another full name" not in content

    def test_content_search_unchanged(self, tmp_path):
        """Test content-based search works regardless of level format."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Database connection failed\n"
            "2025-01-08 10:00:01.000+0000 I Database query completed\n"
            "2025-01-08 10:00:02.000+0000 W Database is slow\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="database", ignore_case=True),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=True),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match all 3 records (content search)
        assert output.exists()
        content = output.read_text()
        assert "Database connection failed" in content
        assert "Database query completed" in content
        assert "Database is slow" in content

    def test_normalization_disabled(self, tmp_path):
        """Test filtering with normalization disabled."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Error with abbreviation\n"
            "2025-01-08 10:00:01.000+0000 ERROR Error with full name\n"
            "2025-01-08 10:00:02.000+0000 I Info message\n"
        )

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=tmp_path),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(normalize_log_levels=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should match only the full "ERROR" record, not "E"
        assert output.exists()
        content = output.read_text()
        assert "Error with full name" in content
        assert "Error with abbreviation" not in content


class TestAllLevelAbbreviations:
    """Test all supported level abbreviations."""

    def test_all_standard_abbreviations(self, tmp_path):
        """Test all standard log level abbreviations."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2025-01-08 10:00:00.000+0000 E Error message\n"
            "2025-01-08 10:00:01.000+0000 W Warning message\n"
            "2025-01-08 10:00:02.000+0000 I Info message\n"
            "2025-01-08 10:00:03.000+0000 D Debug message\n"
            "2025-01-08 10:00:04.000+0000 T Trace message\n"
            "2025-01-08 10:00:05.000+0000 F Fatal message\n"
        )

        # Test each level
        test_cases = [
            ("ERROR", "Error message"),
            ("WARN", "Warning message"),
            ("INFO", "Info message"),
            ("DEBUG", "Debug message"),
            ("TRACE", "Trace message"),
            ("FATAL", "Fatal message"),
        ]

        for expression, expected_text in test_cases:
            output = tmp_path / f"output_{expression.lower()}.log"

            config = ApplicationConfig(
                search=SearchConfig(expression=expression),
                files=FileConfig(path=tmp_path),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
                processing=ProcessingConfig(normalize_log_levels=True),
            )

            pipeline = ProcessingPipeline(config)
            pipeline.run()

            assert output.exists(), f"Output file not created for {expression}"
            content = output.read_text()
            assert (
                expected_text in content
            ), f"Expected text '{expected_text}' not found for {expression}"
