"""Unit tests for the public API entrypoint."""

from pathlib import Path

import pytest

from log_filter import run_filter
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
