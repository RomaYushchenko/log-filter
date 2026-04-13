"""Unit tests for the public API entrypoint."""

from pathlib import Path

import pytest

from log_filter import run_filter, run_filter_service_errors, run_filter_simple, search_logs
from log_filter.core.exceptions import ConfigurationError


def test_run_filter_returns_output_paths(tmp_path: Path) -> None:
    """run_filter should return created output file paths."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    input_log = logs_dir / "app.log"
    input_log.write_text(
        "\n".join(
            [
                "2025-01-07 10:00:00.000+0000 ERROR Database connection failed",
                "stack trace line",
                "2025-01-07 10:00:01.000+0000 INFO Retry successful",
            ]
        ),
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "filter-result.log"
    config_json = {
        "search": {"expression": "ERROR", "ignore_case": False},
        "files": {
            "path": str(logs_dir),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
            "max_file_size": None,
            "max_record_size": None,
        },
        "date": {"from": None, "to": None},
        "time": {"from": None, "to": None},
        "output": {
            "output_file": str(output_file),
            "no_path": False,
            "highlight": False,
            "stats": False,
            "verbose": False,
            "quiet": True,
            "dry_run": False,
            "dry_run_details": False,
            "max_records_per_file": 500,
            "output_file_pattern": "{base}-{index:03d}{ext}",
            "sort_by_timestamp": True,
        },
        "processing": {
            "max_workers": 1,
            "debug": False,
            "normalize_log_levels": True,
            "sort_input_files": True,
        },
    }

    output_paths = run_filter(config_json)

    assert output_paths
    for created_path in output_paths:
        path = Path(created_path)
        assert path.exists()


def test_run_filter_rejects_missing_expression(tmp_path: Path) -> None:
    """run_filter should raise on missing required search.expression."""
    config_json = {
        "files": {"path": str(tmp_path)},
        "output": {"output_file": str(tmp_path / "out.log")},
    }

    with pytest.raises(ConfigurationError):
        run_filter(config_json)


def test_run_filter_supports_expression_mode(tmp_path: Path) -> None:
    """run_filter should accept expression + logs path without JSON config."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "app.log").write_text(
        "2025-01-07 10:00:00.000+0000 ERROR API unavailable\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "expression-mode.log"
    output_paths = run_filter(
        "ERROR",
        logs_path=str(logs_dir),
        output_file=str(output_file),
    )

    assert output_paths
    assert Path(output_paths[0]).exists()


def test_run_filter_simple_rejects_empty_expression() -> None:
    """run_filter_simple should fail fast for empty expression."""
    with pytest.raises(ConfigurationError, match="expression"):
        run_filter_simple("")


def test_run_filter_service_errors_finds_critical(tmp_path: Path) -> None:
    """run_filter_service_errors should match built-in critical expression."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "app.log").write_text(
        "2025-01-07 10:00:00.000+0000 INFO heartbeat\n"
        "2025-01-07 10:00:01.000+0000 CRITICAL database unavailable\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "service-errors.log"
    paths = run_filter_service_errors(
        logs_path=str(logs_dir),
        output_file=str(output_file),
    )

    assert paths
    content = Path(paths[0]).read_text(encoding="utf-8")
    assert "CRITICAL" in content


def test_search_logs_filters_by_level_and_expression(tmp_path: Path) -> None:
    """search_logs should apply level + expression constraints."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "app.log").write_text(
        "2025-01-07 10:00:00.000+0000 INFO timeout happened\n"
        "2025-01-07 10:00:01.000+0000 ERROR timeout happened\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "search-logs.log"
    paths = search_logs(
        logs_path=str(logs_dir),
        output_file=str(output_file),
        expression="timeout",
        level=["ERROR"],
    )

    assert paths
    content = Path(paths[0]).read_text(encoding="utf-8")
    assert "ERROR timeout happened" in content
    assert "INFO timeout happened" not in content


def test_search_logs_with_empty_level_list_keeps_expression_only(tmp_path: Path) -> None:
    """An empty level list should not alter expression behavior."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "app.log").write_text(
        "2025-01-07 10:00:00.000+0000 INFO request completed\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "out" / "search-empty-level.log"
    paths = search_logs(
        logs_path=str(logs_dir),
        output_file=str(output_file),
        expression="request",
        level=[],
    )

    assert paths
    content = Path(paths[0]).read_text(encoding="utf-8")
    assert "request completed" in content


def test_search_logs_rejects_invalid_level_type(tmp_path: Path) -> None:
    """search_logs should validate level values."""
    with pytest.raises(ConfigurationError, match="level"):
        search_logs(
            logs_path=str(tmp_path),
            output_file=str(tmp_path / "out.log"),
            expression="ERROR",
            level=["ERROR", 1],  # type: ignore[list-item]
        )
