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


def test_resolve_logs_path_skill_relative_default_input_logs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_logs_dir = repo_root / ".github" / "skills" / "log-filter" / "scripts" / "input-logs"
    input_logs_dir.mkdir(parents=True)

    resolved = run_filter_runner._resolve_logs_path("./scripts/input-logs", repo_root)

    assert resolved == input_logs_dir.resolve()


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
                "missing-parent/logs-dev",
                repo_root,
                allow_name_fallback=False,
            )
    finally:
        os.chdir(old_cwd)


def test_resolve_search_paths_prioritizes_input_logs_then_repo_logs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_logs_dir = repo_root / ".github" / "skills" / "log-filter" / "scripts" / "input-logs"
    logs_dir = repo_root / "logs"
    logs_dev_dir = repo_root / "logs-dev"
    input_logs_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)
    logs_dev_dir.mkdir(parents=True)

    resolved = run_filter_runner._resolve_search_paths("./scripts/input-logs", repo_root)

    assert resolved == [
        input_logs_dir.resolve(),
        logs_dir.resolve(),
        logs_dev_dir.resolve(),
    ]


def test_resolve_search_paths_keeps_explicit_path_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True)
    (repo_root / ".github" / "skills" / "log-filter" / "scripts" / "input-logs").mkdir(
        parents=True
    )

    resolved = run_filter_runner._resolve_search_paths("logs", repo_root)

    assert resolved == [logs_dir.resolve()]


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


def test_run_investigation_retries_repo_logs_when_input_logs_has_no_matches(tmp_path: Path) -> None:
    input_logs_dir = tmp_path / "input-logs"
    repo_logs_dir = tmp_path / "logs"
    input_logs_dir.mkdir()
    repo_logs_dir.mkdir()

    calls: list[tuple[str, str]] = []

    def fake_run_filter(expression: str, *, logs_path: str, output_file: str) -> list[str]:
        calls.append((expression, logs_path))
        if logs_path == str(input_logs_dir):
            return []
        return [output_file]

    output_paths = run_filter_runner._run_investigation(
        mode="expression",
        expression="ERROR",
        logs_paths=[input_logs_dir, repo_logs_dir],
        output_file=tmp_path / "out.log",
        run_filter_func=fake_run_filter,
        run_filter_service_errors_func=lambda **_: [],
    )

    assert output_paths == [str((tmp_path / "out.log").resolve())]
    assert calls == [
        ("ERROR", str(input_logs_dir)),
        ("ERROR", str(repo_logs_dir)),
    ]


def test_run_investigation_stops_after_first_success(tmp_path: Path) -> None:
    input_logs_dir = tmp_path / "input-logs"
    repo_logs_dir = tmp_path / "logs"
    input_logs_dir.mkdir()
    repo_logs_dir.mkdir()

    calls: list[str] = []

    def fake_run_filter(expression: str, *, logs_path: str, output_file: str) -> list[str]:
        calls.append(logs_path)
        return [output_file]

    output_paths = run_filter_runner._run_investigation(
        mode="expression",
        expression="ERROR",
        logs_paths=[input_logs_dir, repo_logs_dir],
        output_file=tmp_path / "out.log",
        run_filter_func=fake_run_filter,
        run_filter_service_errors_func=lambda **_: [],
    )

    assert output_paths == [str((tmp_path / "out.log").resolve())]
    assert calls == [str(input_logs_dir)]
