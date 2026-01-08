"""
Integration tests for the processing pipeline.

Tests the complete pipeline including workers, filters, and statistics.
"""

import tempfile
from datetime import date, datetime, time
from pathlib import Path

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.domain.filters import DateRangeFilter, TimeRangeFilter
from log_filter.domain.models import LogRecord
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.processing.record_parser import StreamingRecordParser
from log_filter.statistics.collector import StatisticsCollector


class TestStatisticsCollector:
    """Test statistics collector."""
    
    def test_collector_initialization(self):
        """Test collector starts with zero stats."""
        collector = StatisticsCollector()
        
        assert collector.stats.files_scanned == 0
        assert collector.stats.files_processed == 0
        assert collector.stats.records_total == 0
    
    def test_collector_increments(self):
        """Test collector increments correctly."""
        collector = StatisticsCollector()
        
        collector.increment_files_scanned(5)
        collector.increment_files_processed(3)
        collector.increment_records_total(100)
        collector.increment_records_matched(25)
        
        assert collector.stats.files_scanned == 5
        assert collector.stats.files_processed == 3
        assert collector.stats.records_total == 100
        assert collector.stats.records_matched == 25
    
    def test_collector_skip_reasons(self):
        """Test collector tracks skip reasons."""
        collector = StatisticsCollector()
        
        collector.increment_files_skipped("size-limit", 2)
        collector.increment_files_skipped("name-filter", 3)
        collector.increment_files_skipped("size-limit", 1)
        
        assert collector.stats.files_skipped == 6
        assert collector.stats.skip_reasons["size-limit"] == 3
        assert collector.stats.skip_reasons["name-filter"] == 3
    
    def test_collector_duration(self):
        """Test collector tracks duration."""
        collector = StatisticsCollector()
        
        collector.start()
        collector.stop()
        
        assert collector.stats.duration_seconds >= 0
    
    def test_collector_snapshot(self):
        """Test collector provides immutable snapshot."""
        collector = StatisticsCollector()
        collector.increment_files_processed(5)
        
        snapshot1 = collector.get_snapshot()
        collector.increment_files_processed(3)
        snapshot2 = collector.get_snapshot()
        
        assert snapshot1.files_processed == 5
        assert snapshot2.files_processed == 8


class TestFilters:
    """Test record filters."""
    
    def test_date_filter_passes_in_range(self):
        """Test date filter passes records in range."""
        filter = DateRangeFilter(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 10)
        )
        
        record = LogRecord(
            content="test",
            first_line="2025-01-05 10:00:00 INFO test",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 5, 10, 0, 0),
            level="INFO",
            size_bytes=4
        )
        
        assert filter.matches(record) is True
    
    def test_date_filter_rejects_out_of_range(self):
        """Test date filter rejects records out of range."""
        filter = DateRangeFilter(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 10)
        )
        
        record = LogRecord(
            content="test",
            first_line="2025-01-15 10:00:00 INFO test",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            level="INFO",
            size_bytes=4
        )
        
        assert filter.matches(record) is False
    
    def test_time_filter_passes_in_range(self):
        """Test time filter passes records in range."""
        filter = TimeRangeFilter(
            time_from=time(9, 0, 0),
            time_to=time(17, 0, 0)
        )
        
        record = LogRecord(
            content="test",
            first_line="2025-01-05 12:00:00 INFO test",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 5, 12, 0, 0),
            level="INFO",
            size_bytes=4
        )
        
        assert filter.matches(record) is True
    
    def test_time_filter_rejects_out_of_range(self):
        """Test time filter rejects records out of range."""
        filter = TimeRangeFilter(
            time_from=time(9, 0, 0),
            time_to=time(17, 0, 0)
        )
        
        record = LogRecord(
            content="test",
            first_line="2025-01-05 20:00:00 INFO test",
            source_file=Path("test.log"),
            start_line=1,
            end_line=1,
            timestamp=datetime(2025, 1, 5, 20, 0, 0),
            level="INFO",
            size_bytes=4
        )
        
        assert filter.matches(record) is False


class TestFileHandlerFactory:
    """Test file handler factory."""
    
    def test_factory_creates_log_handler(self, tmp_path):
        """Test factory creates LogFileHandler for .log files."""
        log_file = tmp_path / "test.log"
        log_file.write_text("test")
        
        factory = FileHandlerFactory()
        handler = factory.create_handler(log_file)
        
        assert handler.__class__.__name__ == "LogFileHandler"
    
    def test_factory_creates_gzip_handler(self, tmp_path):
        """Test factory creates GzipFileHandler for .gz files."""
        import gzip
        
        gz_file = tmp_path / "test.log.gz"
        with gzip.open(gz_file, "wt") as f:
            f.write("test")
        
        factory = FileHandlerFactory()
        handler = factory.create_handler(gz_file)
        
        assert handler.__class__.__name__ == "GzipFileHandler"
    
    def test_factory_supports_file_check(self, tmp_path):
        """Test factory checks file support."""
        factory = FileHandlerFactory()
        
        assert factory.supports_file(Path("test.log")) is True
        assert factory.supports_file(Path("test.gz")) is True
        assert factory.supports_file(Path("test.txt")) is False


class TestProcessingPipeline:
    """Test processing pipeline integration."""
    
    def test_pipeline_processes_simple_file(self, tmp_path):
        """Test pipeline processes a simple log file."""
        # Create test log file
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 INFO App started\n"
            "2025-01-01 10:00:01.000+0000 ERROR Something failed\n"
            "2025-01-01 10:00:02.000+0000 INFO App stopped\n"
        )
        
        # Create configuration
        config = ApplicationConfig(
            search=SearchConfig(
                expression="ERROR",
                ignore_case=True,
                use_regex=False
            ),
            files=FileConfig(
                search_root=tmp_path,
                file_masks=[],
                extensions=(".log",)
            ),
            output=OutputConfig(
                output_file=tmp_path / "output.log",
                show_progress=False,
                show_stats=False
            ),
            processing=ProcessingConfig(worker_count=1)
        )
        
        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()
        
        # Check statistics
        stats = pipeline.stats.get_snapshot()
        assert stats.files_processed == 1
        assert stats.records_total == 3
        assert stats.records_matched == 1
    
    def test_pipeline_handles_date_filtering(self, tmp_path):
        """Test pipeline applies date filtering."""
        # Create test log file
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2025-01-01 10:00:00.000+0000 INFO Early\n"
            "2025-01-05 10:00:00.000+0000 INFO Middle\n"
            "2025-01-10 10:00:00.000+0000 INFO Late\n"
        )
        
        # Create configuration with date filter
        config = ApplicationConfig(
            search=SearchConfig(
                expression="INFO",
                ignore_case=True,
                date_from=date(2025, 1, 4),
                date_to=date(2025, 1, 6)
            ),
            files=FileConfig(
                search_root=tmp_path,
                extensions=(".log",)
            ),
            output=OutputConfig(
                output_file=tmp_path / "output.log",
                show_progress=False,
                show_stats=False
            ),
            processing=ProcessingConfig(worker_count=1)
        )
        
        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()
        
        # Check statistics
        stats = pipeline.stats.get_snapshot()
        assert stats.records_matched == 1  # Only middle record
    
    def test_pipeline_handles_dry_run(self, tmp_path):
        """Test pipeline handles dry-run mode."""
        # Create test log files
        (tmp_path / "test1.log").write_text("content1")
        (tmp_path / "test2.log").write_text("content2")
        
        # Create configuration with dry-run
        config = ApplicationConfig(
            search=SearchConfig(expression="test"),
            files=FileConfig(
                search_root=tmp_path,
                extensions=(".log",)
            ),
            output=OutputConfig(
                output_file=tmp_path / "output.log",
                dry_run=True,
                show_progress=False,
                show_stats=False
            ),
            processing=ProcessingConfig(worker_count=1)
        )
        
        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()
        
        # In dry-run, no records should be processed
        stats = pipeline.stats.get_snapshot()
        assert stats.records_total == 0
        assert not (tmp_path / "output.log").exists()
    
    def test_pipeline_handles_empty_directory(self, tmp_path):
        """Test pipeline handles directory with no matching files."""
        config = ApplicationConfig(
            search=SearchConfig(expression="test"),
            files=FileConfig(
                search_root=tmp_path,
                extensions=(".log",)
            ),
            output=OutputConfig(
                output_file=tmp_path / "output.log",
                show_progress=False,
                show_stats=False
            ),
            processing=ProcessingConfig(worker_count=1)
        )
        
        # Run pipeline
        pipeline = ProcessingPipeline(config)
        pipeline.run()
        
        # Should complete without error
        stats = pipeline.stats.get_snapshot()
        assert stats.files_processed == 0
