"""Stable runner for log_filter public API without long one-liners.

Edit constants below or pass CLI arguments to run investigations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_EXPRESSION = "ERROR"
DEFAULT_LOGS_PATH = "./scripts/input-logs"
DEFAULT_OUTPUT_FILE = "./scripts/output/custom-investigation.log"
DEFAULT_MODE = "expression"


def _detect_repo_root() -> Path:
    # scripts/run_filter_runner.py -> repo root is 5 levels above
    return Path(__file__).resolve().parents[4]


def _resolve_logs_path(raw_logs_path: str, repo_root: Path, *, allow_name_fallback: bool = True) -> Path:
    requested = Path(raw_logs_path)
    candidates: list[Path] = []

    if requested.is_absolute():
        candidates.append(requested)
    else:
        candidates.append((Path.cwd() / requested).resolve())
        candidates.append((Path(__file__).resolve().parent / requested).resolve())
        candidates.append((repo_root / requested).resolve())

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


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _detect_repo_root()
    resolved_logs_path = _resolve_logs_path(
        args.logs_path,
        repo_root,
        allow_name_fallback=not args.strict_logs_path,
    )

    from log_filter import run_filter, run_filter_service_errors

    if args.mode == "service-errors":
        output_paths = run_filter_service_errors(
            logs_path=str(resolved_logs_path),
            output_file=args.output_file,
        )
    else:
        expression = _load_expression(args)
        output_paths = run_filter(
            expression,
            logs_path=str(resolved_logs_path),
            output_file=args.output_file,
        )

    print(json.dumps(output_paths, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
