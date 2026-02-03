"""
Integration tests for sorted chunked output feature.

Tests the complete pipeline with file sorting, timestamp sorting, and chunked output.
"""

import tempfile
from datetime import datetime
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


class TestSortedChunkedOutput:
    """Integration tests for sorted chunked output."""

    def create_test_log_file(self, path: Path, records: list[str]) -> None:
        """Helper to create a test log file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(records))

    def test_basic_chunking(self, tmp_path: Path) -> None:
        """Test basic chunking splits output into multiple files."""
        # Create input log file
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        # Use proper log format: YYYY-MM-DD HH:MM:SS.mmm±ZZZZ LEVEL
        records = [f"2026-02-03 10:00:{i:02d}.000+0000 ERROR Test message {i}" for i in range(15)]
        self.create_test_log_file(log_file, records)

        # Configure pipeline with chunking
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=5,  # Split into files of 5 records
                sort_by_timestamp=False,  # Don't sort for this test
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify output files were created
        output_dir = output_file.parent
        output_files = sorted(output_dir.glob("result-*.log"))

        assert len(output_files) == 3  # 15 records / 5 per file = 3 files
        assert output_files[0].name == "result-001.log"
        assert output_files[1].name == "result-002.log"
        assert output_files[2].name == "result-003.log"

        # Verify each file has correct number of records
        records_file1 = output_files[0].read_text().strip().split("\n")
        records_file2 = output_files[1].read_text().strip().split("\n")
        records_file3 = output_files[2].read_text().strip().split("\n")

        assert len(records_file1) == 5
        assert len(records_file2) == 5
        assert len(records_file3) == 5

    def test_timestamp_sorting(self, tmp_path: Path) -> None:
        """Test that records are sorted by timestamp."""
        # Create input with unsorted timestamps
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            "2026-02-03 10:00:30.000+0000 ERROR Third message",
            "2026-02-03 10:00:10.000+0000 ERROR First message",
            "2026-02-03 10:00:20.000+0000 ERROR Second message",
            "2026-02-03 10:00:50.000+0000 ERROR Fifth message",
            "2026-02-03 10:00:40.000+0000 ERROR Fourth message",
        ]
        self.create_test_log_file(log_file, records)

        # Configure pipeline with sorting
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=0,  # Unlimited
                sort_by_timestamp=True,
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Read output and verify sorting
        output_content = output_file.read_text().strip().split("\n")

        assert len(output_content) == 5
        assert "First message" in output_content[0]
        assert "Second message" in output_content[1]
        assert "Third message" in output_content[2]
        assert "Fourth message" in output_content[3]
        assert "Fifth message" in output_content[4]

    def test_file_pre_sorting(self, tmp_path: Path) -> None:
        """Test that input files are pre-sorted by date/index."""
        # Create multiple input files with different dates
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create files in non-chronological order
        file3 = input_dir / "app-02-03-2026-1.log"
        file1 = input_dir / "app-02-01-2026-1.log"
        file2 = input_dir / "app-02-02-2026-1.log"

        self.create_test_log_file(file3, ["2026-02-03 10:00:00.000+0000 ERROR Message from day 3"])
        self.create_test_log_file(file1, ["2026-02-01 10:00:00.000+0000 ERROR Message from day 1"])
        self.create_test_log_file(file2, ["2026-02-02 10:00:00.000+0000 ERROR Message from day 2"])

        # Configure pipeline with file sorting enabled
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=None,
                sort_by_timestamp=True,
            ),
            processing=ProcessingConfig(
                worker_count=1,  # Single worker for deterministic order
                sort_input_files=True,
            ),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify output is sorted by date
        output_content = output_file.read_text().strip().split("\n")

        assert len(output_content) == 3
        assert "day 1" in output_content[0]
        assert "day 2" in output_content[1]
        assert "day 3" in output_content[2]

    def test_combined_sorting_and_chunking(self, tmp_path: Path) -> None:
        """Test combined timestamp sorting and chunking."""
        # Create input with mixed timestamps
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            "2026-02-03 10:00:50.000+0000 ERROR Message 5",
            "2026-02-03 10:00:20.000+0000 ERROR Message 2",
            "2026-02-03 10:00:40.000+0000 ERROR Message 4",
            "2026-02-03 10:00:10.000+0000 ERROR Message 1",
            "2026-02-03 10:00:30.000+0000 ERROR Message 3",
            "2026-02-03 10:01:10.000+0000 ERROR Message 7",
            "2026-02-03 10:01:00.000+0000 ERROR Message 6",
        ]
        self.create_test_log_file(log_file, records)

        # Configure with both sorting and chunking
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=3,  # 3 records per file
                sort_by_timestamp=True,
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify files are created
        output_dir = output_file.parent
        output_files = sorted(output_dir.glob("result-*.log"))

        assert len(output_files) == 3  # 7 records: 3 + 3 + 1

        # Verify first file has oldest records (sorted)
        file1_content = output_files[0].read_text().strip().split("\n")
        assert len(file1_content) == 3
        assert "Message 1" in file1_content[0]
        assert "Message 2" in file1_content[1]
        assert "Message 3" in file1_content[2]

        # Verify second file
        file2_content = output_files[1].read_text().strip().split("\n")
        assert len(file2_content) == 3
        assert "Message 4" in file2_content[0]
        assert "Message 5" in file2_content[1]
        assert "Message 6" in file2_content[2]

        # Verify third file has remaining records
        file3_content = output_files[2].read_text().strip().split("\n")
        assert len(file3_content) == 1
        assert "Message 7" in file3_content[0]

    def test_unlimited_output(self, tmp_path: Path) -> None:
        """Test that max_records_per_file=0 creates single file."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            f"2026-02-03 10:{i//60:02d}:{i%60:02d}.000+0000 ERROR Test {i}" for i in range(100)
        ]
        self.create_test_log_file(log_file, records)

        # Configure with unlimited records per file
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=0,  # Unlimited
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify only one file created at base path
        assert output_file.exists()

        # Verify no chunked files created
        output_dir = output_file.parent
        chunked_files = list(output_dir.glob("result-*.log"))
        assert len(chunked_files) == 0

        # Verify all records in single file
        content = output_file.read_text().strip().split("\n")
        assert len(content) == 100

    def test_custom_output_pattern(self, tmp_path: Path) -> None:
        """Test custom filename pattern for chunks."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [f"2026-02-03 10:00:{i:02d}.000+0000 ERROR Test {i}" for i in range(12)]
        self.create_test_log_file(log_file, records)

        # Configure with custom pattern
        output_file = tmp_path / "output" / "results.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=5,
                output_file_pattern="{base}_part{index:02d}{ext}",
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify custom filenames
        output_dir = output_file.parent
        output_files = sorted(output_dir.glob("results_part*.log"))

        assert len(output_files) == 3
        assert output_files[0].name == "results_part01.log"
        assert output_files[1].name == "results_part02.log"
        assert output_files[2].name == "results_part03.log"

    def test_sorting_with_source_path(self, tmp_path: Path) -> None:
        """Test sorting works with include_file_path option."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            "2026-02-03 10:00:30.000+0000 ERROR Third",
            "2026-02-03 10:00:10.000+0000 ERROR First",
            "2026-02-03 10:00:20.000+0000 ERROR Second",
        ]
        self.create_test_log_file(log_file, records)

        # Configure with file path inclusion
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                include_file_path=True,
                sort_by_timestamp=True,
                max_records_per_file=0,  # Unlimited - single file
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify output has file paths and is sorted
        output_content = output_file.read_text().strip().split("\n")

        assert len(output_content) == 3

        # Each line should have file path
        for line in output_content:
            assert "app.log:" in line

        # Verify sorting
        assert "First" in output_content[0]
        assert "Second" in output_content[1]
        assert "Third" in output_content[2]

    def test_disable_timestamp_sorting(self, tmp_path: Path) -> None:
        """Test that sorting can be disabled."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            "2026-02-03 10:00:30.000+0000 ERROR Third",
            "2026-02-03 10:00:10.000+0000 ERROR First",
            "2026-02-03 10:00:20.000+0000 ERROR Second",
        ]
        self.create_test_log_file(log_file, records)

        # Disable sorting
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                sort_by_timestamp=False,  # Disabled
                max_records_per_file=0,  # Unlimited - single file
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify output is NOT sorted (original order)
        output_content = output_file.read_text().strip().split("\n")

        assert len(output_content) == 3
        assert "Third" in output_content[0]
        assert "First" in output_content[1]
        assert "Second" in output_content[2]

    def test_disable_file_sorting(self, tmp_path: Path) -> None:
        """Test that file pre-sorting can be disabled."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create files with different dates (would normally be sorted)
        file3 = input_dir / "zzz-02-03-2026-1.log"  # Z prefix to be last alphabetically
        file1 = input_dir / "aaa-02-01-2026-1.log"  # A prefix to be first alphabetically

        self.create_test_log_file(file3, ["2026-02-03 10:00:00.000+0000 ERROR From Z file"])
        self.create_test_log_file(file1, ["2026-02-01 10:00:00.000+0000 ERROR From A file"])

        # Disable file sorting
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                sort_by_timestamp=False,
                max_records_per_file=0,  # Unlimited - single file
            ),
            processing=ProcessingConfig(
                worker_count=1,
                sort_input_files=False,  # Disabled
            ),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Output depends on file discovery order (alphabetical by default)
        # With sorting disabled, we can't guarantee order, just verify both records exist
        output_content = output_file.read_text()

        assert "From Z file" in output_content
        assert "From A file" in output_content

    def test_empty_results(self, tmp_path: Path) -> None:
        """Test behavior when no records match."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        records = [
            "2026-02-03 10:00:00.000+0000 INFO Information message",
            "2026-02-03 10:00:01.000+0000 DEBUG Debug message",
        ]
        self.create_test_log_file(log_file, records)

        # Search for ERROR (won't match)
        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                max_records_per_file=5,
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify no output files created
        output_dir = output_file.parent
        if output_dir.exists():
            output_files = list(output_dir.glob("*.log"))
            assert len(output_files) == 0

    def test_multiline_records_sorting(self, tmp_path: Path) -> None:
        """Test that multiline records are sorted correctly."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        log_file = input_dir / "app.log"
        # Multiline with timestamps on first line
        records = [
            "2026-02-03 10:00:30.000+0000 ERROR Third message",
            "  Stack trace line 1",
            "  Stack trace line 2",
            "2026-02-03 10:00:10.000+0000 ERROR First message",
            "  Another trace",
            "2026-02-03 10:00:20.000+0000 ERROR Second message",
        ]
        self.create_test_log_file(log_file, records)

        output_file = tmp_path / "output" / "result.log"
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(path=input_dir),
            output=OutputConfig(
                output_file=output_file,
                sort_by_timestamp=True,
                max_records_per_file=0,  # Unlimited - single file
            ),
            processing=ProcessingConfig(worker_count=1),
        )

        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Verify sorted output
        output_lines = output_file.read_text().strip().split("\n")

        # Should have all ERROR lines (multiline parts depend on parser)
        error_lines = [line for line in output_lines if "ERROR" in line]
        assert len(error_lines) == 3
        assert "First message" in error_lines[0]
        assert "Second message" in error_lines[1]
        assert "Third message" in error_lines[2]
