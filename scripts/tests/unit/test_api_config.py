"""Tests for JSON config validation and mapping (replaces former CLI config tests)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from log_filter import run_filter
from log_filter.core.exceptions import ConfigurationError


def _base_config(tmp_path: Path, logs_subdir: str = "logs") -> dict:
    logs = tmp_path / logs_subdir
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "app.log").write_text(
        "2025-01-01 10:00:00.000+0000 ERROR sample\n", encoding="utf-8"
    )
    out = tmp_path / "out" / "result.log"
    return {
        "search": {"expression": "ERROR", "ignore_case": False},
        "files": {
            "path": str(logs),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
            "max_file_size": None,
            "max_record_size": None,
        },
        "date": {"from": None, "to": None},
        "time": {"from": None, "to": None},
        "output": {
            "output_file": str(out),
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


def test_minimal_config_runs(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    paths = run_filter(cfg)
    assert paths
    assert Path(paths[0]).exists()


def test_full_search_and_output_options(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "app.log").write_text(
        "2025-01-01 10:00:00.000+0000 ERROR Something failed softly\n"
        "2025-01-01 10:00:01.000+0000 ERROR HARD FAILED\n",
        encoding="utf-8",
    )
    out = tmp_path / "all.log"
    cfg = {
        "search": {"expression": "failed", "ignore_case": True, "regex": False},
        "files": {
            "path": str(logs),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
        },
        "date": {"from": None, "to": None},
        "time": {"from": None, "to": None},
        "output": {
            "output_file": str(out),
            "no_path": True,
            "highlight": False,
            "stats": False,
            "verbose": False,
            "quiet": True,
            "dry_run": False,
            "dry_run_details": False,
            "max_records_per_file": None,
            "output_file_pattern": "{base}-{index:03d}{ext}",
            "sort_by_timestamp": True,
        },
        "processing": {"max_workers": 1, "debug": False},
    }
    paths = run_filter(cfg)
    text = Path(paths[0]).read_text(encoding="utf-8")
    assert "failed softly" in text and "HARD FAILED" in text
    assert str(logs) not in text


def test_date_filter_in_config(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "app.log").write_text(
        "2025-01-01 10:00:00.000+0000 ERROR early\n"
        "2025-01-02 10:00:00.000+0000 ERROR middle\n"
        "2025-01-03 10:00:00.000+0000 ERROR late\n",
        encoding="utf-8",
    )
    out = tmp_path / "out" / "result.log"
    cfg = {
        "search": {"expression": "ERROR", "ignore_case": False},
        "files": {
            "path": str(logs),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
            "max_file_size": None,
            "max_record_size": None,
        },
        "date": {"from": "2025-01-02", "to": "2025-01-02"},
        "time": {"from": None, "to": None},
        "output": {
            "output_file": str(out),
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
        "processing": {"max_workers": 1, "debug": False},
    }
    paths = run_filter(cfg)
    content = Path(paths[0]).read_text(encoding="utf-8")
    assert "middle" in content
    assert "early" not in content
    assert "late" not in content


def test_config_from_json_file_roundtrip(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    paths = run_filter(loaded)
    assert paths


def test_missing_expression_raises() -> None:
    with pytest.raises(ConfigurationError, match="search.expression"):
        run_filter({"files": {"path": "."}, "search": {}})


def test_invalid_date_raises() -> None:
    with pytest.raises(ConfigurationError, match="Invalid date"):
        run_filter(
            {
                "search": {"expression": "ERROR"},
                "files": {"path": "."},
                "date": {"from": "not-a-date", "to": None},
            }
        )


def test_invalid_time_raises() -> None:
    with pytest.raises(ConfigurationError, match="Invalid time"):
        run_filter(
            {
                "search": {"expression": "ERROR"},
                "files": {"path": "."},
                "time": {"from": "25:00:00", "to": None},
            }
        )


def test_include_patterns_must_be_list_of_strings(tmp_path: Path) -> None:
    cfg = _base_config(tmp_path)
    cfg["files"]["include_patterns"] = "*.log"  # type: ignore[assignment]
    with pytest.raises(ConfigurationError, match="include_patterns"):
        run_filter(cfg)


def test_non_dict_config_raises() -> None:
    with pytest.raises(ConfigurationError, match="dictionary"):
        run_filter("not-a-dict")  # type: ignore[arg-type]
