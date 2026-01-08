"""
Integration tests for CLI module.

Tests argument parsing, configuration building, and error handling.
"""

import json
import tempfile
from datetime import date, time
from pathlib import Path
from typing import Dict

import pytest

from log_filter.cli import (
    build_config_from_args,
    create_argument_parser,
    load_config_file,
    parse_args,
    parse_date,
    parse_time,
)
from log_filter.config.models import ApplicationConfig
from log_filter.core.exceptions import ConfigurationError


class TestArgumentParser:
    """Test argument parser creation and basic parsing."""
    
    def test_create_parser(self) -> None:
        """Test parser creation."""
        parser = create_argument_parser()
        assert parser is not None
        assert parser.prog == "log-filter"
    
    def test_parse_minimal_args(self) -> None:
        """Test parsing minimal required arguments."""
        parser = create_argument_parser()
        args = parser.parse_args(["--expr", "ERROR"])
        assert args.expr == "ERROR"
        assert args.ignore_case is False
        assert args.regex is False
    
    def test_parse_all_search_args(self) -> None:
        """Test parsing all search-related arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR AND Kafka",
            "--ignore-case",
            "--regex"
        ])
        assert args.expr == "ERROR AND Kafka"
        assert args.ignore_case is True
        assert args.regex is True
    
    def test_parse_file_args(self) -> None:
        """Test parsing file-related arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--path", "/var/log",
            "--file-name", "app.log"
        ])
        assert args.path == Path("/var/log")
        assert args.file_name == "app.log"
    
    def test_parse_date_time_args(self) -> None:
        """Test parsing date/time arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--from", "2025-01-01",
            "--to", "2025-01-31",
            "--from-time", "09:00:00",
            "--to-time", "17:00:00"
        ])
        assert args.date_from == "2025-01-01"
        assert args.date_to == "2025-01-31"
        assert args.from_time == "09:00:00"
        assert args.to_time == "17:00:00"
    
    def test_parse_output_args(self) -> None:
        """Test parsing output arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--output", "results.log",
            "--no-path",
            "--highlight"
        ])
        assert args.output == Path("results.log")
        assert args.no_path is True
        assert args.highlight is True
    
    def test_parse_display_args(self) -> None:
        """Test parsing display arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--progress",
            "--stats"
        ])
        assert args.progress is True
        assert args.stats is True
    
    def test_parse_dry_run_args(self) -> None:
        """Test parsing dry-run arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--dry-run"
        ])
        assert args.dry_run is True
        
        args = parser.parse_args([
            "--expr", "ERROR",
            "--dry-run-details"
        ])
        assert args.dry_run_details is True
    
    def test_parse_size_limit_args(self) -> None:
        """Test parsing size limit arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--max-file-size", "100",
            "--max-record-size", "64"
        ])
        assert args.max_file_size == 100
        assert args.max_record_size == 64
    
    def test_parse_processing_args(self) -> None:
        """Test parsing processing arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR",
            "--workers", "8",
            "--debug"
        ])
        assert args.workers == 8
        assert args.debug is True


class TestConfigFileLoading:
    """Test configuration file loading."""
    
    def test_load_json_config(self, tmp_path: Path) -> None:
        """Test loading JSON configuration file."""
        config_data = {
            "expr": "ERROR AND Kafka",
            "ignore_case": True,
            "path": "/var/log"
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        loaded = load_config_file(config_file)
        assert loaded == config_data
    
    def test_load_yaml_config(self, tmp_path: Path) -> None:
        """Test loading YAML configuration file."""
        pytest.importorskip("yaml")
        
        config_data = """
expr: ERROR AND Kafka
ignore_case: true
path: /var/log
"""
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_data)
        
        loaded = load_config_file(config_file)
        assert loaded["expr"] == "ERROR AND Kafka"
        assert loaded["ignore_case"] is True
        assert loaded["path"] == "/var/log"
    
    def test_load_nonexistent_file(self) -> None:
        """Test loading nonexistent config file."""
        with pytest.raises(ConfigurationError, match="not found"):
            load_config_file(Path("/nonexistent/config.json"))
    
    def test_load_directory_instead_of_file(self, tmp_path: Path) -> None:
        """Test loading directory instead of file."""
        with pytest.raises(ConfigurationError, match="not a file"):
            load_config_file(tmp_path)
    
    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{invalid json")
        
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            load_config_file(config_file)


class TestDateTimeParsing:
    """Test date and time parsing functions."""
    
    def test_parse_valid_date(self) -> None:
        """Test parsing valid date."""
        result = parse_date("2025-01-15")
        assert result == date(2025, 1, 15)
    
    def test_parse_none_date(self) -> None:
        """Test parsing None date."""
        result = parse_date(None)
        assert result is None
    
    def test_parse_invalid_date_format(self) -> None:
        """Test parsing invalid date format."""
        with pytest.raises(ConfigurationError, match="Invalid date format"):
            parse_date("2025/01/15")
    
    def test_parse_invalid_date_values(self) -> None:
        """Test parsing invalid date values."""
        with pytest.raises(ConfigurationError, match="Invalid date format"):
            parse_date("2025-13-01")  # Invalid month
    
    def test_parse_valid_time(self) -> None:
        """Test parsing valid time."""
        result = parse_time("14:30:45")
        assert result == time(14, 30, 45)
    
    def test_parse_none_time(self) -> None:
        """Test parsing None time."""
        result = parse_time(None)
        assert result is None
    
    def test_parse_invalid_time_format(self) -> None:
        """Test parsing invalid time format."""
        with pytest.raises(ConfigurationError, match="Invalid time format"):
            parse_time("14:30")
    
    def test_parse_invalid_time_values(self) -> None:
        """Test parsing invalid time values."""
        with pytest.raises(ConfigurationError, match="Invalid time format"):
            parse_time("25:00:00")  # Invalid hour


class TestConfigurationBuilding:
    """Test building ApplicationConfig from arguments."""
    
    def test_build_minimal_config(self) -> None:
        """Test building minimal configuration."""
        parser = create_argument_parser()
        args = parser.parse_args(["--expr", "ERROR"])
        
        config = build_config_from_args(args)
        
        assert isinstance(config, ApplicationConfig)
        assert config.search.expression == "ERROR"
        assert config.search.ignore_case is False
        assert config.search.use_regex is False
        assert config.files.search_root == Path(".")
        assert config.output.output_file == Path("filter-result.log")
    
    def test_build_full_config(self, tmp_path: Path) -> None:
        """Test building full configuration with all options."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "--expr", "ERROR AND Kafka",
            "--ignore-case",
            "--regex",
            "--path", str(tmp_path),  # Use tmp_path so validation passes
            "--file-name", "app.log",
            "--from", "2025-01-01",
            "--to", "2025-01-31",
            "--from-time", "09:00:00",
            "--to-time", "17:00:00",
            "--output", "results.log",
            "--no-path",
            "--highlight",
            "--progress",
            "--stats",
            "--max-file-size", "100",
            "--max-record-size", "64",
            "--workers", "8",
            "--debug"
        ])
        
        config = build_config_from_args(args)
        
        # Search config
        assert config.search.expression == "ERROR AND Kafka"
        assert config.search.ignore_case is True
        assert config.search.use_regex is True
        assert config.search.date_from == date(2025, 1, 1)
        assert config.search.date_to == date(2025, 1, 31)
        assert config.search.time_from == time(9, 0, 0)
        assert config.search.time_to == time(17, 0, 0)
        
        # File config
        assert config.files.search_root == tmp_path
        assert config.files.file_masks == ["app.log"]
        assert config.files.max_file_size_mb == 100
        assert config.files.max_record_size_kb == 64
        
        # Output config
        assert config.output.output_file == Path("results.log")
        assert config.output.include_file_path is False  # --no-path inverts this
        assert config.output.highlight_matches is True
        assert config.output.show_progress is True
        assert config.output.show_stats is True
        
        # Processing config
        assert config.processing.worker_count == 8
        assert config.processing.debug is True
    
    def test_build_config_missing_expression(self) -> None:
        """Test building config without required expression."""
        parser = create_argument_parser()
        args = parser.parse_args([])
        
        with pytest.raises(ConfigurationError, match="expression is required"):
            build_config_from_args(args)
    
    def test_build_config_from_file(self, tmp_path: Path) -> None:
        """Test building config from configuration file."""
        config_data = {
            "expr": "ERROR AND Kafka",
            "ignore_case": True,
            "use_regex": False,
            "path": str(tmp_path),
            "progress": True
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        parser = create_argument_parser()
        args = parser.parse_args(["--config", str(config_file)])
        
        config = build_config_from_args(args)
        
        assert config.search.expression == "ERROR AND Kafka"
        assert config.search.ignore_case is True
        assert config.files.search_root == tmp_path
        assert config.output.show_progress is True
    
    def test_build_config_cli_overrides_file(self, tmp_path: Path) -> None:
        """Test that CLI arguments override config file values."""
        config_data = {
            "expr": "ERROR",
            "ignore_case": False,
            "progress": False
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        parser = create_argument_parser()
        args = parser.parse_args([
            "--config", str(config_file),
            "--expr", "WARNING",
            "--ignore-case",
            "--progress"
        ])
        
        config = build_config_from_args(args)
        
        # CLI args should override file values
        assert config.search.expression == "WARNING"
        assert config.search.ignore_case is True
        assert config.output.show_progress is True


class TestParseArgsFunction:
    """Test the main parse_args function."""
    
    def test_parse_args_success(self) -> None:
        """Test successful argument parsing."""
        config = parse_args(["--expr", "ERROR"])
        
        assert isinstance(config, ApplicationConfig)
        assert config.search.expression == "ERROR"
    
    def test_parse_args_with_all_options(self) -> None:
        """Test parsing all options."""
        config = parse_args([
            "--expr", "ERROR",
            "--ignore-case",
            "--progress",
            "--stats"
        ])
        
        assert config.search.expression == "ERROR"
        assert config.search.ignore_case is True
        assert config.output.show_progress is True
        assert config.output.show_stats is True
    
    def test_parse_args_missing_expression(self) -> None:
        """Test parsing without required expression."""
        with pytest.raises(ConfigurationError, match="expression is required"):
            parse_args([])
    
    def test_parse_args_invalid_date(self) -> None:
        """Test parsing with invalid date."""
        with pytest.raises(ConfigurationError, match="Invalid date format"):
            parse_args(["--expr", "ERROR", "--from", "invalid-date"])


class TestIntegration:
    """Integration tests for complete CLI workflow."""
    
    def test_complete_workflow_cli_only(self, tmp_path: Path) -> None:
        """Test complete workflow with CLI arguments only."""
        config = parse_args([
            "--expr", "ERROR OR WARNING",
            "--path", str(tmp_path),  # Use tmp_path so validation passes
            "--ignore-case",
            "--progress",
            "--stats",
            "--workers", "4"
        ])
        
        assert config.search.expression == "ERROR OR WARNING"
        assert config.search.ignore_case is True
        assert config.files.search_root == tmp_path
        assert config.output.show_progress is True
        assert config.output.show_stats is True
        assert config.processing.worker_count == 4
    
    def test_complete_workflow_with_config_file(self, tmp_path: Path) -> None:
        """Test complete workflow with config file and CLI overrides."""
        config_data = {
            "expr": "ERROR",
            "path": str(tmp_path),  # Use tmp_path so validation passes
            "ignore_case": False,
            "workers": 2
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        config = parse_args([
            "--config", str(config_file),
            "--ignore-case",  # Override
            "--progress",      # Additional option
            "--workers", "8"   # Override
        ])
        
        assert config.search.expression == "ERROR"
        assert config.search.ignore_case is True  # Overridden
        assert config.files.search_root == tmp_path
        assert config.output.show_progress is True  # Added
        assert config.processing.worker_count == 8  # Overridden
    
    def test_dry_run_workflow(self, tmp_path: Path) -> None:
        """Test dry-run workflow."""
        config = parse_args([
            "--expr", "ERROR",
            "--path", str(tmp_path),  # Use tmp_path so validation passes
            "--dry-run"
        ])
        
        assert config.output.dry_run is True
        assert config.output.dry_run_details is False
    
    def test_dry_run_details_workflow(self, tmp_path: Path) -> None:
        """Test dry-run with details workflow."""
        config = parse_args([
            "--expr", "ERROR",
            "--path", str(tmp_path),  # Use tmp_path so validation passes
            "--dry-run-details"
        ])
        
        assert config.output.dry_run_details is True
