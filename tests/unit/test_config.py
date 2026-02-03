"""Unit tests for configuration models."""

from datetime import date, time
from pathlib import Path

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)


class TestSearchConfig:
    """Tests for SearchConfig."""

    def test_valid_config(self) -> None:
        """Test creating valid search config."""
        config = SearchConfig(expression="ERROR")
        assert config.expression == "ERROR"
        assert config.ignore_case is False
        assert config.use_regex is False

    def test_with_all_options(self) -> None:
        """Test config with all options."""
        config = SearchConfig(
            expression="ERROR",
            ignore_case=True,
            use_regex=True,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 7),
            time_from=time(10, 0, 0),
            time_to=time(18, 0, 0),
        )
        assert config.ignore_case is True
        assert config.use_regex is True
        assert config.date_from == date(2025, 1, 1)
        assert config.date_to == date(2025, 1, 7)

    def test_empty_expression_raises_error(self) -> None:
        """Test that empty expression raises error."""
        with pytest.raises(ValueError, match="Search expression cannot be empty"):
            SearchConfig(expression="")

    def test_whitespace_only_expression_raises_error(self) -> None:
        """Test that whitespace-only expression raises error."""
        with pytest.raises(ValueError, match="Search expression cannot be empty"):
            SearchConfig(expression="   \t\n   ")

    def test_invalid_date_range(self) -> None:
        """Test that invalid date range raises error."""
        with pytest.raises(ValueError, match="date_from.*must be.*date_to"):
            SearchConfig(
                expression="ERROR",
                date_from=date(2025, 1, 7),
                date_to=date(2025, 1, 1),
            )

    def test_invalid_time_range(self) -> None:
        """Test that invalid time range raises error."""
        with pytest.raises(ValueError, match="time_from.*must be.*time_to"):
            SearchConfig(
                expression="ERROR",
                time_from=time(18, 0, 0),
                time_to=time(10, 0, 0),
            )

    def test_equal_dates_allowed(self) -> None:
        """Test that equal dates are allowed."""
        config = SearchConfig(
            expression="ERROR",
            date_from=date(2025, 1, 7),
            date_to=date(2025, 1, 7),
        )
        assert config.date_from == config.date_to

    def test_equal_times_allowed(self) -> None:
        """Test that equal times are allowed."""
        config = SearchConfig(
            expression="ERROR",
            time_from=time(10, 0, 0),
            time_to=time(10, 0, 0),
        )
        assert config.time_from == config.time_to


class TestFileConfig:
    """Tests for FileConfig."""

    def test_default_config(self) -> None:
        """Test default file config."""
        config = FileConfig()
        assert config.path == Path(".")
        assert config.file_masks == []
        assert config.max_file_size_mb is None
        assert config.max_record_size_kb is None
        assert config.extensions == (".log", ".gz")

    def test_custom_path(self, tmp_path: Path) -> None:
        """Test custom path."""
        config = FileConfig(path=tmp_path)
        assert config.path == tmp_path

    def test_nonexistent_path(self) -> None:
        """Test nonexistent path raises error."""
        with pytest.raises(ValueError, match="Path does not exist"):
            FileConfig(path=Path("/nonexistent/path"))

    def test_path_not_directory(self, tmp_path: Path) -> None:
        """Test path that's not a directory raises error."""
        file_path = tmp_path / "test.log"
        file_path.touch()

        with pytest.raises(ValueError, match="Path is not a directory"):
            FileConfig(path=file_path)

    def test_with_file_masks(self) -> None:
        """Test config with file masks."""
        config = FileConfig(file_masks=["error", "warn"])
        assert config.file_masks == ["error", "warn"]

    def test_with_size_limits(self) -> None:
        """Test config with size limits."""
        config = FileConfig(max_file_size_mb=100, max_record_size_kb=1024)
        assert config.max_file_size_mb == 100
        assert config.max_record_size_kb == 1024

    def test_negative_file_size_raises_error(self) -> None:
        """Test negative max file size raises error."""
        with pytest.raises(ValueError, match="max_file_size_mb must be positive"):
            FileConfig(max_file_size_mb=-1)

    def test_zero_file_size_raises_error(self) -> None:
        """Test zero max file size raises error."""
        with pytest.raises(ValueError, match="max_file_size_mb must be positive"):
            FileConfig(max_file_size_mb=0)

    def test_negative_record_size_raises_error(self) -> None:
        """Test negative max record size raises error."""
        with pytest.raises(ValueError, match="max_record_size_kb must be positive"):
            FileConfig(max_record_size_kb=-1)

    def test_matches_file_mask_no_masks(self) -> None:
        """Test file mask matching with no masks configured."""
        config = FileConfig()
        assert config.matches_file_mask("any_file.log") is True
        assert config.matches_file_mask("another.log") is True

    def test_matches_file_mask_with_masks(self) -> None:
        """Test file mask matching with masks configured."""
        config = FileConfig(file_masks=["error", "warn"])
        assert config.matches_file_mask("error.log") is True
        assert config.matches_file_mask("server_error.log") is True
        assert config.matches_file_mask("warn_messages.log") is True
        assert config.matches_file_mask("info.log") is False

    def test_has_allowed_extension(self) -> None:
        """Test extension checking."""
        config = FileConfig()
        assert config.has_allowed_extension("test.log") is True
        assert config.has_allowed_extension("test.gz") is True
        assert config.has_allowed_extension("test.txt") is False

    def test_custom_extensions(self) -> None:
        """Test custom extensions."""
        config = FileConfig(extensions=(".txt", ".log"))
        assert config.has_allowed_extension("test.txt") is True
        assert config.has_allowed_extension("test.log") is True
        assert config.has_allowed_extension("test.gz") is False


class TestOutputConfig:
    """Tests for OutputConfig."""

    def test_default_config(self) -> None:
        """Test default output config."""
        config = OutputConfig()
        assert config.output_file == Path("filter-result.log")
        assert config.include_file_path is True
        assert config.highlight_matches is False
        assert config.show_progress is False
        assert config.show_stats is False
        assert config.dry_run is False
        assert config.dry_run_details is False

    def test_custom_output_file(self) -> None:
        """Test custom output file."""
        config = OutputConfig(output_file=Path("results.txt"))
        assert config.output_file == Path("results.txt")

    def test_all_flags_enabled(self) -> None:
        """Test with all flags enabled."""
        config = OutputConfig(
            include_file_path=False,
            highlight_matches=True,
            show_progress=True,
            show_stats=True,
            dry_run=True,
            dry_run_details=True,
        )
        assert config.include_file_path is False
        assert config.highlight_matches is True
        assert config.show_progress is True
        assert config.show_stats is True
        assert config.dry_run is True
        assert config.dry_run_details is True

    def test_chunked_output_defaults(self) -> None:
        """Test chunked output default values."""
        config = OutputConfig()
        assert config.max_records_per_file == 500
        assert config.output_file_pattern == "{base}-{index:03d}{ext}"
        assert config.sort_by_timestamp is True

    def test_chunked_output_custom(self) -> None:
        """Test chunked output custom values."""
        config = OutputConfig(
            max_records_per_file=1000,
            output_file_pattern="{base}_{index:05d}{ext}",
            sort_by_timestamp=False,
        )
        assert config.max_records_per_file == 1000
        assert config.output_file_pattern == "{base}_{index:05d}{ext}"
        assert config.sort_by_timestamp is False

    def test_unlimited_records_per_file(self) -> None:
        """Test unlimited records (None or 0)."""
        config1 = OutputConfig(max_records_per_file=None)
        assert config1.max_records_per_file is None

        config2 = OutputConfig(max_records_per_file=0)
        assert config2.max_records_per_file == 0


class TestProcessingConfig:
    """Tests for ProcessingConfig."""

    def test_default_config(self) -> None:
        """Test default processing config."""
        config = ProcessingConfig()
        assert config.worker_count is None
        assert config.debug is False

    def test_custom_worker_count(self) -> None:
        """Test custom worker count."""
        config = ProcessingConfig(worker_count=8)
        assert config.worker_count == 8

    def test_negative_worker_count_raises_error(self) -> None:
        """Test negative worker count raises error."""
        with pytest.raises(ValueError, match="worker_count must be positive"):
            ProcessingConfig(worker_count=-1)

    def test_zero_worker_count_raises_error(self) -> None:
        """Test zero worker count raises error."""
        with pytest.raises(ValueError, match="worker_count must be positive"):
            ProcessingConfig(worker_count=0)

    def test_debug_enabled(self) -> None:
        """Test debug mode enabled."""
        config = ProcessingConfig(debug=True)
        assert config.debug is True

    def test_sort_input_files_default(self) -> None:
        """Test sort_input_files default value."""
        config = ProcessingConfig()
        assert config.sort_input_files is True

    def test_sort_input_files_disabled(self) -> None:
        """Test disabling input file sorting."""
        config = ProcessingConfig(sort_input_files=False)
        assert config.sort_input_files is False

    def test_normalize_log_levels_default(self) -> None:
        """Test normalize_log_levels default value."""
        config = ProcessingConfig()
        assert config.normalize_log_levels is True

    def test_normalize_log_levels_disabled(self) -> None:
        """Test disabling log level normalization."""
        config = ProcessingConfig(normalize_log_levels=False)
        assert config.normalize_log_levels is False

    def test_worker_count_exceeds_platform_maximum(self) -> None:
        """Test that excessive worker count raises error."""
        import sys

        from log_filter.config.models import (
            MAX_WORKERS_DEFAULT,
            MAX_WORKERS_LINUX,
            MAX_WORKERS_MACOS,
            MAX_WORKERS_WINDOWS,
        )

        # Determine expected maximum for current platform
        if sys.platform == "win32":
            max_workers = MAX_WORKERS_WINDOWS
        elif sys.platform == "darwin":
            max_workers = MAX_WORKERS_MACOS
        elif sys.platform.startswith("linux"):
            max_workers = MAX_WORKERS_LINUX
        else:
            max_workers = MAX_WORKERS_DEFAULT

        # Should reject worker count above platform maximum
        with pytest.raises(ValueError, match="exceeds platform maximum"):
            ProcessingConfig(worker_count=max_workers + 1)

    def test_worker_count_at_platform_maximum(self) -> None:
        """Test that worker count at maximum is accepted."""
        import sys

        from log_filter.config.models import (
            MAX_WORKERS_DEFAULT,
            MAX_WORKERS_LINUX,
            MAX_WORKERS_MACOS,
            MAX_WORKERS_WINDOWS,
        )

        # Determine expected maximum for current platform
        if sys.platform == "win32":
            max_workers = MAX_WORKERS_WINDOWS
        elif sys.platform == "darwin":
            max_workers = MAX_WORKERS_MACOS
        elif sys.platform.startswith("linux"):
            max_workers = MAX_WORKERS_LINUX
        else:
            max_workers = MAX_WORKERS_DEFAULT

        # Should accept worker count at platform maximum
        config = ProcessingConfig(worker_count=max_workers)
        assert config.worker_count == max_workers


class TestApplicationConfig:
    """Tests for ApplicationConfig."""

    def test_minimal_config(self) -> None:
        """Test minimal application config."""
        search = SearchConfig(expression="ERROR")
        config = ApplicationConfig(search=search)

        assert config.search == search
        assert isinstance(config.files, FileConfig)
        assert isinstance(config.output, OutputConfig)
        assert isinstance(config.processing, ProcessingConfig)

    def test_full_config(self, tmp_path: Path) -> None:
        """Test full application config."""
        search = SearchConfig(
            expression="ERROR",
            ignore_case=True,
            date_from=date(2025, 1, 1),
        )
        files = FileConfig(
            path=tmp_path,
            file_masks=["error"],
            max_file_size_mb=100,
        )
        output = OutputConfig(
            output_file=Path("results.log"),
            show_stats=True,
        )
        processing = ProcessingConfig(
            worker_count=4,
            debug=True,
        )

        config = ApplicationConfig(
            search=search,
            files=files,
            output=output,
            processing=processing,
        )

        assert config.search == search
        assert config.files == files
        assert config.output == output
        assert config.processing == processing


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_real_world_config(self, tmp_path: Path) -> None:
        """Test realistic configuration."""
        config = ApplicationConfig(
            search=SearchConfig(
                expression="(ERROR OR WARN) AND NOT Heartbeat",
                ignore_case=True,
                date_from=date(2025, 1, 1),
                date_to=date(2025, 1, 7),
            ),
            files=FileConfig(
                path=tmp_path,
                file_masks=["app", "server"],
                max_file_size_mb=500,
                max_record_size_kb=100,
            ),
            output=OutputConfig(
                output_file=Path("filtered.log"),
                include_file_path=True,
                highlight_matches=True,
                show_progress=True,
                show_stats=True,
            ),
            processing=ProcessingConfig(
                worker_count=8,
                debug=False,
            ),
        )

        # Verify all settings
        assert config.search.expression == "(ERROR OR WARN) AND NOT Heartbeat"
        assert config.files.max_file_size_mb == 500
        assert config.output.show_stats is True
        assert config.processing.worker_count == 8

    def test_dry_run_config(self) -> None:
        """Test configuration for dry run mode."""
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            output=OutputConfig(dry_run=True, dry_run_details=True),
        )

        assert config.output.dry_run is True
        assert config.output.dry_run_details is True
