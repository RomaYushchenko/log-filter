"""Public API for running log filtering from Python code."""

from __future__ import annotations

import logging
from datetime import date, time
from pathlib import Path
from typing import Any

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.exceptions import ConfigurationError
from log_filter.processing.pipeline import ProcessingPipeline

DEFAULT_LOGS_PATH = "./scripts/input-logs"
DEFAULT_OUTPUT_FILE = "./scripts/output/filter-result.log"
DEFAULT_INCLUDE_PATTERNS = ["*.log", "*.log.gz"]


def _ensure_logging(level: int) -> None:
    """Ensure root logging is configured at least to the requested level."""
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=level)
        return

    if root_logger.getEffectiveLevel() > level:
        root_logger.setLevel(level)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        year, month, day = (int(part) for part in value.split("-"))
        return date(year, month, day)
    except Exception as exc:  # noqa: BLE001
        raise ConfigurationError(f"Invalid date format '{value}'. Expected YYYY-MM-DD.") from exc


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None

    try:
        hour, minute, second = (int(part) for part in value.split(":"))
        return time(hour, minute, second)
    except Exception as exc:  # noqa: BLE001
        raise ConfigurationError(f"Invalid time format '{value}'. Expected HH:MM:SS.") from exc


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ConfigurationError(f"Expected boolean value, got: {type(value).__name__}")


def _to_config(config_json: dict[str, Any]) -> ApplicationConfig:
    search = config_json.get("search", {})
    files = config_json.get("files", {})
    output = config_json.get("output", {})
    processing = config_json.get("processing", {})
    date_cfg = config_json.get("date", {})
    time_cfg = config_json.get("time", {})

    expression = search.get("expression")
    if not expression or not isinstance(expression, str):
        raise ConfigurationError("search.expression is required and must be a string.")

    output_file_raw = output.get("output_file", "filter-result.log")
    output_file = Path(output_file_raw) if isinstance(output_file_raw, str) else output_file_raw
    if not isinstance(output_file, Path):
        raise ConfigurationError("output.output_file must be a string path.")

    path_raw = files.get("path", ".")
    files_path = Path(path_raw) if isinstance(path_raw, str) else path_raw
    if not isinstance(files_path, Path):
        raise ConfigurationError("files.path must be a string path.")

    include_patterns = files.get("include_patterns", [])
    exclude_patterns = files.get("exclude_patterns", [])

    if not isinstance(include_patterns, list) or not all(
        isinstance(item, str) for item in include_patterns
    ):
        raise ConfigurationError("files.include_patterns must be a list of strings.")
    if not isinstance(exclude_patterns, list) or not all(
        isinstance(item, str) for item in exclude_patterns
    ):
        raise ConfigurationError("files.exclude_patterns must be a list of strings.")

    search_config = SearchConfig(
        expression=expression,
        ignore_case=_to_bool(search.get("ignore_case"), default=False),
        use_regex=_to_bool(search.get("regex"), default=False),
        word_boundary=_to_bool(search.get("word_boundary"), default=False),
        strip_quotes=_to_bool(search.get("strip_quotes"), default=False),
        date_from=_parse_date(date_cfg.get("from")),
        date_to=_parse_date(date_cfg.get("to")),
        time_from=_parse_time(time_cfg.get("from")),
        time_to=_parse_time(time_cfg.get("to")),
    )

    file_config = FileConfig(
        path=files_path,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        max_file_size_mb=files.get("max_file_size"),
        max_record_size_kb=files.get("max_record_size"),
    )

    output_config = OutputConfig(
        output_file=output_file,
        include_file_path=not _to_bool(output.get("no_path"), default=False),
        highlight_matches=_to_bool(output.get("highlight"), default=False),
        show_progress=(
            False
            if _to_bool(output.get("quiet"), default=False)
            else _to_bool(output.get("verbose"), default=False)
        ),
        show_stats=_to_bool(output.get("stats"), default=False),
        dry_run=_to_bool(output.get("dry_run"), default=False),
        dry_run_details=_to_bool(output.get("dry_run_details"), default=False),
        max_records_per_file=output.get("max_records_per_file", 500),
        output_file_pattern=output.get("output_file_pattern", "{base}-{index:03d}{ext}"),
        sort_by_timestamp=_to_bool(output.get("sort_by_timestamp"), default=True),
    )

    processing_config = ProcessingConfig(
        worker_count=processing.get("max_workers"),
        debug=_to_bool(processing.get("debug"), default=False),
        normalize_log_levels=_to_bool(processing.get("normalize_log_levels"), default=True),
        sort_input_files=_to_bool(processing.get("sort_input_files"), default=True),
    )

    return ApplicationConfig(
        search=search_config,
        files=file_config,
        output=output_config,
        processing=processing_config,
    )


def _build_default_config(
    expression: str,
    logs_path: str | Path = DEFAULT_LOGS_PATH,
    output_file: str | Path = DEFAULT_OUTPUT_FILE,
) -> dict[str, Any]:
    if not expression or not isinstance(expression, str):
        raise ConfigurationError("expression is required and must be a string.")

    return {
        "search": {
            "expression": expression,
            "ignore_case": False,
            "regex": False,
            "word_boundary": False,
            "strip_quotes": True,
        },
        "files": {
            "path": str(logs_path),
            "include_patterns": DEFAULT_INCLUDE_PATTERNS,
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
            "stats": True,
            "verbose": True,
            "quiet": False,
            "dry_run": False,
            "dry_run_details": False,
            "max_records_per_file": 3000,
            "output_file_pattern": "{base}-{index:03d}{ext}",
            "sort_by_timestamp": True,
        },
        "processing": {
            "max_workers": None,
            "debug": False,
            "normalize_log_levels": True,
            "sort_input_files": True,
        },
    }


def run_filter_simple(
    expression: str,
    logs_path: str | Path = DEFAULT_LOGS_PATH,
    output_file: str | Path = DEFAULT_OUTPUT_FILE,
) -> list[str]:
    """Run filtering with a compact API.

    Args:
        expression: Boolean expression used for filtering.
        logs_path: Directory containing log files.
        output_file: Output log file path.

    Returns:
        A list of output file paths created by the pipeline.
    """
    return run_filter(_build_default_config(expression, logs_path, output_file))


def search_logs(
    logs_path: str,
    output_file: str,
    expression: str,
    date_from: str | None = None,
    date_to: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
    level: list[str] | None = None,
    ignore_case: bool = False,
    regex: bool = False,
    word_boundary: bool = False,
    strip_quotes: bool = False,
    max_workers: int | None = None,
) -> list[str]:
    """Run filtering with common search options.

    This helper builds a config payload internally and delegates execution to
    ``run_filter``.
    """
    if not expression or not isinstance(expression, str):
        raise ConfigurationError("expression is required and must be a string.")

    effective_expression = expression
    if level is not None:
        if not isinstance(level, list) or not all(isinstance(item, str) for item in level):
            raise ConfigurationError("level must be a list of strings.")

        normalized_levels = [item.strip().upper() for item in level if item and item.strip()]
        if normalized_levels:
            level_expression = " OR ".join(normalized_levels)
            effective_expression = f"({level_expression}) AND ({expression})"

    config_json = _build_default_config(
        expression=effective_expression,
        logs_path=logs_path,
        output_file=output_file,
    )
    config_json["search"]["ignore_case"] = ignore_case
    config_json["search"]["regex"] = regex
    config_json["search"]["word_boundary"] = word_boundary
    config_json["search"]["strip_quotes"] = strip_quotes
    config_json["date"]["from"] = date_from
    config_json["date"]["to"] = date_to
    config_json["time"]["from"] = time_from
    config_json["time"]["to"] = time_to
    config_json["processing"]["max_workers"] = max_workers

    return run_filter(config_json)


def run_filter_service_errors(
    logs_path: str | Path = DEFAULT_LOGS_PATH,
    output_file: str | Path = "./scripts/output/service-errors.log",
) -> list[str]:
    """Run a built-in service error investigation query."""
    return run_filter_simple(
        expression="(ERROR OR CRITICAL OR FATAL OR EXCEPTION) AND NOT test",
        logs_path=logs_path,
        output_file=output_file,
    )


def run_filter(
    config_json: dict[str, Any] | str,
    logs_path: str | Path = DEFAULT_LOGS_PATH,
    output_file: str | Path = DEFAULT_OUTPUT_FILE,
) -> list[str]:
    """Run filtering and return output file paths.

    Args:
        config_json: JSON-like dict with the same shape as config.json.template,
            or search expression string for compact API usage.
        logs_path: Logs directory when using expression mode.
        output_file: Output file path when using expression mode.

    Returns:
        A list of output file paths created by the pipeline.
    """
    if isinstance(config_json, str):
        config_payload = _build_default_config(config_json, logs_path, output_file)
    elif isinstance(config_json, dict):
        config_payload = config_json
    else:
        raise ConfigurationError(
            "config_json must be a dictionary or expression string."
        )

    config = _to_config(config_payload)
    if config.processing.debug:
        _ensure_logging(logging.DEBUG)
    elif config.output.show_progress or config.output.show_stats:
        _ensure_logging(logging.INFO)

    pipeline = ProcessingPipeline(config)
    pipeline.run()

    return [str(path.resolve()) for path in pipeline.created_output_files]
