"""Integration tests for the public run_filter API (chunking and edge cases)."""

from __future__ import annotations

from pathlib import Path

import pytest

from log_filter import run_filter
from log_filter.core.exceptions import ConfigurationError


def _quiet_config(
    tmp_path: Path,
    *,
    expression: str = "ERROR",
    log_lines: list[str] | None = None,
    output_name: str = "out.log",
    **output_overrides: object,
) -> dict:
    logs = tmp_path / "logs"
    logs.mkdir()
    lines = log_lines or ["2025-01-01 10:00:00.000+0000 ERROR one"]
    (logs / "app.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = tmp_path / output_name
    output = {
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
    }
    output.update(output_overrides)
    return {
        "search": {"expression": expression, "ignore_case": False},
        "files": {
            "path": str(logs),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
        },
        "date": {"from": None, "to": None},
        "time": {"from": None, "to": None},
        "output": output,
        "processing": {"max_workers": 1, "debug": False},
    }


def test_chunking_splits_into_multiple_files(tmp_path: Path) -> None:
    log_lines = [
        f"2025-01-01 10:00:0{i}.000+0000 ERROR hit {i}"
        for i in range(5)
    ]
    cfg = _quiet_config(
        tmp_path,
        log_lines=log_lines,
        max_records_per_file=2,
    )
    paths = run_filter(cfg)
    assert len(paths) >= 3
    for p in paths:
        assert Path(p).exists()


def test_max_records_per_file_zero_writes_single_unlimited_file(tmp_path: Path) -> None:
    log_lines = [
        "2025-01-01 10:00:00.000+0000 ERROR a",
        "2025-01-01 10:00:01.000+0000 ERROR b",
    ]
    cfg = _quiet_config(tmp_path, log_lines=log_lines, max_records_per_file=0)
    paths = run_filter(cfg)
    assert len(paths) == 1
    content = Path(paths[0]).read_text(encoding="utf-8")
    assert "a" in content and "b" in content


def test_no_matches_returns_empty_path_list(tmp_path: Path) -> None:
    cfg = _quiet_config(
        tmp_path,
        expression="CRITICAL",
        log_lines=["2025-01-01 10:00:00.000+0000 INFO ok"],
    )
    assert run_filter(cfg) == []


def test_dry_run_returns_no_output_files(tmp_path: Path) -> None:
    cfg = _quiet_config(tmp_path, dry_run=True)
    assert run_filter(cfg) == []


def test_missing_input_directory_raises(tmp_path: Path) -> None:
    cfg = _quiet_config(tmp_path)
    cfg["files"]["path"] = str(tmp_path / "does-not-exist")
    with pytest.raises(ValueError, match="does not exist"):
        run_filter(cfg)


def test_regex_mode_via_config(tmp_path: Path) -> None:
    cfg = _quiet_config(
        tmp_path,
        expression=r"ERR_[0-9]+",
        log_lines=["2025-01-01 10:00:00.000+0000 ERROR ERR_404 happened"],
    )
    cfg["search"]["regex"] = True
    paths = run_filter(cfg)
    assert paths
    assert "ERR_404" in Path(paths[0]).read_text(encoding="utf-8")


def test_worker_count_greater_than_one(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    for i in range(3):
        (logs / f"f{i}.log").write_text(
            f"2025-01-01 10:00:00.000+0000 ERROR x{i}\n", encoding="utf-8"
        )
    out = tmp_path / "multi.log"
    cfg = {
        "search": {"expression": "ERROR"},
        "files": {
            "path": str(logs),
            "include_patterns": ["*.log"],
            "exclude_patterns": [],
        },
        "date": {"from": None, "to": None},
        "time": {"from": None, "to": None},
        "output": {
            "output_file": str(out),
            "quiet": True,
            "stats": False,
            "verbose": False,
            "max_records_per_file": None,
            "output_file_pattern": "{base}-{index:03d}{ext}",
        },
        "processing": {"max_workers": 2},
    }
    paths = run_filter(cfg)
    assert paths
    body = Path(paths[0]).read_text(encoding="utf-8")
    assert "x0" in body and "x2" in body
