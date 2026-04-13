"""Stable runner for log_filter public API without long one-liners.

Edit constants below or pass CLI arguments to run investigations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable


DEFAULT_EXPRESSION = "ERROR"
DEFAULT_LOGS_PATH = "./scripts/input-logs"
DEFAULT_OUTPUT_FILE = "./scripts/output/custom-investigation.log"
DEFAULT_MODE = "expression"
DEFAULT_FALLBACK_LOGS_PATHS = (DEFAULT_LOGS_PATH, "logs", "logs-dev")


def _detect_repo_root() -> Path:
    # scripts/run_filter_runner.py -> repo root is 5 levels above
    return Path(__file__).resolve().parents[4]


def _skill_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root / ".github" / "skills" / "log-filter"
    return Path(__file__).resolve().parent.parent


def _normalize_path_token(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _uses_default_search_order(raw_logs_path: str) -> bool:
    normalized = _normalize_path_token(raw_logs_path)
    return normalized in {"", "input-logs", "scripts/input-logs"}


def _resolve_logs_path(raw_logs_path: str, repo_root: Path, *, allow_name_fallback: bool = True) -> Path:
    requested = Path(raw_logs_path)
    candidates: list[Path] = []

    if requested.is_absolute():
        candidates.append(requested)
    else:
        # Resolve relative paths against the requested repo first to avoid leaking
        # into similarly named directories from the current workspace cwd.
        candidates.append((_skill_root(repo_root) / requested).resolve())
        candidates.append((Path(__file__).resolve().parent / requested).resolve())
        candidates.append((repo_root / requested).resolve())
        candidates.append((Path.cwd() / requested).resolve())

        # Guardrail: when caller passes ../../../logs or ../../../logs-dev from scripts,
        # try canonical workspace roots directly to avoid brittle path math.
        name_only = requested.name
        if allow_name_fallback and name_only:
            candidates.append((repo_root / name_only).resolve())

    unique_candidates: list[Path] = []
    seen = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(path)

    for candidate in unique_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    attempted = "\n".join(str(path) for path in unique_candidates)
    raise ValueError(
        "Path does not exist or is not a directory."
        f"\nRequested: {raw_logs_path}"
        f"\nAttempted:\n{attempted}"
        "\nTip: pass absolute path or repo-root-relative path (for example 'logs', 'logs-dev')."
    )


def _resolve_search_paths(
    raw_logs_path: str,
    repo_root: Path,
    *,
    allow_name_fallback: bool = True,
) -> list[Path]:
    candidate_inputs = (
        list(DEFAULT_FALLBACK_LOGS_PATHS)
        if _uses_default_search_order(raw_logs_path)
        else [raw_logs_path]
    )

    resolved_paths: list[Path] = []
    seen: set[str] = set()
    last_error: ValueError | None = None

    for candidate_input in candidate_inputs:
        try:
            resolved_path = _resolve_logs_path(
                candidate_input,
                repo_root,
                allow_name_fallback=allow_name_fallback,
            )
        except ValueError as exc:
            last_error = exc
            continue

        key = str(resolved_path)
        if key in seen:
            continue
        seen.add(key)
        resolved_paths.append(resolved_path)

    if resolved_paths:
        return resolved_paths

    if last_error is not None:
        raise last_error

    raise ValueError(f"No valid log directories found for: {raw_logs_path}")


def _resolve_output_file(raw_output_file: str, repo_root: Path) -> Path:
    requested = Path(raw_output_file)
    if requested.is_absolute():
        return requested

    normalized = _normalize_path_token(raw_output_file)
    if normalized.startswith("scripts/"):
        return (_skill_root(repo_root) / normalized).resolve()

    return (Path.cwd() / requested).resolve()


def _load_expression(args: argparse.Namespace) -> str:
    if args.expression_file:
        expression = Path(args.expression_file).read_text(encoding="utf-8")
    elif args.expression_stdin:
        expression = sys.stdin.read()
    elif args.expression is not None:
        expression = args.expression
    else:
        expression = DEFAULT_EXPRESSION

    # PowerShell Set-Content -Encoding UTF8 may prepend BOM; strip it defensively.
    expression = expression.lstrip("\ufeff").strip()
    if not expression:
        raise ValueError("Expression is empty. Provide --expression, --expression-file, or --expression-stdin.")
    return expression


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run log filtering with stable Python runner")
    parser.add_argument(
        "--mode",
        choices=["expression", "service-errors"],
        default=DEFAULT_MODE,
        help="Investigation mode",
    )
    expression_group = parser.add_mutually_exclusive_group()
    expression_group.add_argument(
        "--expression",
        default=None,
        help="Search expression for expression mode",
    )
    expression_group.add_argument(
        "--expression-file",
        default=None,
        help="Path to UTF-8 text file with expression for expression mode",
    )
    expression_group.add_argument(
        "--expression-stdin",
        action="store_true",
        help="Read expression from STDIN for expression mode",
    )
    parser.add_argument(
        "--logs-path",
        default=DEFAULT_LOGS_PATH,
        help="Directory with logs",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help="Output file for filtered results",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repository root used for robust relative path resolution",
    )
    parser.add_argument(
        "--strict-logs-path",
        action="store_true",
        help="Disable basename fallback when resolving --logs-path",
    )
    return parser


def _run_investigation(
    *,
    mode: str,
    expression: str | None,
    logs_paths: list[Path],
    output_file: Path,
    run_filter_func: Callable[..., list[str]],
    run_filter_service_errors_func: Callable[..., list[str]],
) -> list[str]:
    for logs_path in logs_paths:
        if mode == "service-errors":
            output_paths = run_filter_service_errors_func(
                logs_path=str(logs_path),
                output_file=str(output_file),
            )
        else:
            if expression is None:
                raise ValueError("Expression mode requires a non-empty expression.")

            output_paths = run_filter_func(
                expression,
                logs_path=str(logs_path),
                output_file=str(output_file),
            )

        if output_paths:
            return output_paths

    return []


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _detect_repo_root()
    resolved_logs_paths = _resolve_search_paths(
        args.logs_path,
        repo_root,
        allow_name_fallback=not args.strict_logs_path,
    )
    resolved_output_file = _resolve_output_file(args.output_file, repo_root)

    from log_filter import run_filter, run_filter_service_errors

    expression = None if args.mode == "service-errors" else _load_expression(args)
    output_paths = _run_investigation(
        mode=args.mode,
        expression=expression,
        logs_paths=resolved_logs_paths,
        output_file=resolved_output_file,
        run_filter_func=run_filter,
        run_filter_service_errors_func=run_filter_service_errors,
    )

    print(json.dumps(output_paths, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
