"""Unit tests for robust logs path resolution in run_filter_runner."""

import argparse
from pathlib import Path

import pytest

import run_filter_runner


def test_resolve_logs_path_repo_relative(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    logs_dir = repo_root / "logs-dev"
    logs_dir.mkdir(parents=True)

    resolved = run_filter_runner._resolve_logs_path("logs-dev", repo_root)

    assert resolved == logs_dir.resolve()


def test_resolve_logs_path_recovers_from_parent_traversal(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    scripts_dir = repo_root / ".github" / "skills" / "log-filter" / "scripts"
    scripts_dir.mkdir(parents=True)
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True)

    old_cwd = Path.cwd()
    try:
        # Simulate runner execution from scripts directory where ../../../logs is wrong depth.
        import os

        os.chdir(scripts_dir)
        resolved = run_filter_runner._resolve_logs_path("../../../logs", repo_root)
    finally:
        os.chdir(old_cwd)

    assert resolved == logs_dir.resolve()


def test_resolve_logs_path_raises_for_missing_directory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)

    with pytest.raises(ValueError, match="Path does not exist"):
        run_filter_runner._resolve_logs_path("missing-logs-dir", repo_root)


def test_resolve_logs_path_strict_mode_disables_name_fallback(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    scripts_dir = repo_root / ".github" / "skills" / "log-filter" / "scripts"
    scripts_dir.mkdir(parents=True)
    (repo_root / "logs-dev").mkdir(parents=True)

    old_cwd = Path.cwd()
    try:
        import os

        os.chdir(scripts_dir)
        with pytest.raises(ValueError, match="Path does not exist"):
            run_filter_runner._resolve_logs_path(
                "../../../logs-dev",
                repo_root,
                allow_name_fallback=False,
            )
    finally:
        os.chdir(old_cwd)


def test_load_expression_from_file_preserves_quotes(tmp_path: Path) -> None:
    expression_file = tmp_path / "expression.txt"
    expression_file.write_text(
        '(move OR "move id" OR "moveId") AND "a1184211-5b0d-4d45-b3d7-f4517bc26da4"',
        encoding="utf-8",
    )

    args = argparse.Namespace(
        expression=None,
        expression_file=str(expression_file),
        expression_stdin=False,
    )

    expression = run_filter_runner._load_expression(args)

    assert expression == '(move OR "move id" OR "moveId") AND "a1184211-5b0d-4d45-b3d7-f4517bc26da4"'


def test_load_expression_from_file_strips_utf8_bom(tmp_path: Path) -> None:
    expression_file = tmp_path / "expression-bom.txt"
    expression_file.write_text(
        '\ufeff(move OR "moveId") AND "a1184211-5b0d-4d45-b3d7-f4517bc26da4"',
        encoding="utf-8",
    )

    args = argparse.Namespace(
        expression=None,
        expression_file=str(expression_file),
        expression_stdin=False,
    )

    expression = run_filter_runner._load_expression(args)

    assert expression.startswith("(move OR")


def test_load_expression_fails_for_empty_stdin() -> None:
    args = argparse.Namespace(
        expression=None,
        expression_file=None,
        expression_stdin=True,
    )

    import io

    original_stdin = run_filter_runner.sys.stdin
    try:
        run_filter_runner.sys.stdin = io.StringIO("\n\n")
        with pytest.raises(ValueError, match="Expression is empty"):
            run_filter_runner._load_expression(args)
    finally:
        run_filter_runner.sys.stdin = original_stdin
