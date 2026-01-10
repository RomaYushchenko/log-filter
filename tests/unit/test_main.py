"""
Unit tests for main entry point module.

Tests the main() function and setup_logging():
- Command-line argument parsing
- Configuration error handling
- Pipeline execution
- Exit code handling
- Logging configuration
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.exceptions import ConfigurationError
from log_filter.main import main, setup_logging


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging()

            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.WARNING

    def test_setup_logging_with_debug(self):
        """Test logging setup with debug enabled."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging(debug=True)

            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_with_progress(self):
        """Test logging setup with progress enabled."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging(show_progress=True)

            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO

    def test_setup_logging_debug_overrides_progress(self):
        """Test that debug takes precedence over progress."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging(debug=True, show_progress=True)

            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_setup_logging_format(self):
        """Test logging format configuration."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging()

            call_kwargs = mock_config.call_args[1]
            assert "format" in call_kwargs
            assert "%(levelname)s" in call_kwargs["format"]
            assert "%(message)s" in call_kwargs["format"]

    def test_setup_logging_date_format(self):
        """Test logging date format configuration."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging()

            call_kwargs = mock_config.call_args[1]
            assert "datefmt" in call_kwargs
            assert call_kwargs["datefmt"] == "%Y-%m-%d %H:%M:%S"


class TestMainFunction:
    """Test main entry point function."""

    @pytest.fixture
    def sample_config(self, tmp_path):
        """Create sample application configuration."""
        return ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            output=OutputConfig(output_file=tmp_path / "output.log"),
            processing=ProcessingConfig(),
        )

    def test_main_success(self, sample_config):
        """Test successful execution of main."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline_class.return_value = mock_pipeline

                exit_code = main()

                assert exit_code == 0
                mock_pipeline_class.assert_called_once_with(sample_config)
                mock_pipeline.run.assert_called_once()

    def test_main_configuration_error(self):
        """Test main with configuration error."""
        error_msg = "Invalid configuration"

        with patch("log_filter.main.parse_args", side_effect=ConfigurationError(error_msg)):
            with patch("sys.stderr") as mock_stderr:
                exit_code = main()

                assert exit_code == 2

    def test_main_system_exit_with_help(self):
        """Test main with --help flag (SystemExit)."""
        with patch("log_filter.main.parse_args", side_effect=SystemExit(0)):
            exit_code = main()

            assert exit_code == 0

    def test_main_system_exit_with_error(self):
        """Test main with invalid arguments (SystemExit)."""
        with patch("log_filter.main.parse_args", side_effect=SystemExit(2)):
            exit_code = main()

            assert exit_code == 2

    def test_main_system_exit_without_code(self):
        """Test main with SystemExit without integer code."""
        with patch("log_filter.main.parse_args", side_effect=SystemExit("error")):
            exit_code = main()

            assert exit_code == 1

    def test_main_keyboard_interrupt(self, sample_config):
        """Test main with keyboard interrupt."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.run.side_effect = KeyboardInterrupt()
                mock_pipeline_class.return_value = mock_pipeline

                exit_code = main()

                assert exit_code == 130

    def test_main_unexpected_exception(self, sample_config):
        """Test main with unexpected exception."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.run.side_effect = RuntimeError("Unexpected error")
                mock_pipeline_class.return_value = mock_pipeline

                exit_code = main()

                assert exit_code == 1

    def test_main_calls_setup_logging(self, sample_config):
        """Test that main calls setup_logging with correct parameters."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline"):
                with patch("log_filter.main.setup_logging") as mock_setup:
                    main()

                    mock_setup.assert_called_once_with(
                        debug=sample_config.processing.debug,
                        show_progress=sample_config.output.show_progress,
                    )

    def test_main_with_debug_config(self, tmp_path):
        """Test main with debug configuration."""
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            output=OutputConfig(output_file=tmp_path / "output.log"),
            processing=ProcessingConfig(debug=True),
        )

        with patch("log_filter.main.parse_args", return_value=config):
            with patch("log_filter.main.ProcessingPipeline"):
                with patch("log_filter.main.setup_logging") as mock_setup:
                    main()

                    mock_setup.assert_called_once_with(debug=True, show_progress=False)

    def test_main_with_progress_config(self, tmp_path):
        """Test main with progress display configuration."""
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            output=OutputConfig(output_file=tmp_path / "output.log", show_progress=True),
            processing=ProcessingConfig(),
        )

        with patch("log_filter.main.parse_args", return_value=config):
            with patch("log_filter.main.ProcessingPipeline"):
                with patch("log_filter.main.setup_logging") as mock_setup:
                    main()

                    mock_setup.assert_called_once_with(debug=False, show_progress=True)

    def test_main_logs_success_message(self, sample_config):
        """Test that main logs success message."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline"):
                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = Mock()
                    mock_get_logger.return_value = mock_logger

                    main()

                    mock_logger.info.assert_called_with("Processing completed successfully")

    def test_main_logs_keyboard_interrupt(self, sample_config):
        """Test that main logs keyboard interrupt warning."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.run.side_effect = KeyboardInterrupt()
                mock_pipeline_class.return_value = mock_pipeline

                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = Mock()
                    mock_get_logger.return_value = mock_logger

                    main()

                    mock_logger.warning.assert_called_with("Processing interrupted by user")

    def test_main_logs_exception_with_traceback(self, sample_config):
        """Test that main logs exceptions with traceback."""
        with patch("log_filter.main.parse_args", return_value=sample_config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                error = RuntimeError("Test error")
                mock_pipeline.run.side_effect = error
                mock_pipeline_class.return_value = mock_pipeline

                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = Mock()
                    mock_get_logger.return_value = mock_logger

                    main()

                    # Check that error was logged with exc_info
                    assert mock_logger.error.called
                    call_args = mock_logger.error.call_args
                    assert "exc_info" in call_args[1]
                    assert call_args[1]["exc_info"] is True


class TestMainIntegration:
    """Integration tests for main function."""

    def test_main_return_codes(self):
        """Test that main returns appropriate exit codes."""
        # Test configuration error
        with patch("log_filter.main.parse_args", side_effect=ConfigurationError("error")):
            assert main() == 2

        # Test keyboard interrupt
        config = Mock()
        with patch("log_filter.main.parse_args", return_value=config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.run.side_effect = KeyboardInterrupt()
                mock_pipeline_class.return_value = mock_pipeline

                assert main() == 130

        # Test unexpected error
        with patch("log_filter.main.parse_args", return_value=config):
            with patch("log_filter.main.ProcessingPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.run.side_effect = RuntimeError()
                mock_pipeline_class.return_value = mock_pipeline

                assert main() == 1
