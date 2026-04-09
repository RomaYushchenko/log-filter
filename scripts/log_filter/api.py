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


def run_filter(config_json: dict[str, Any]) -> list[str]:
    """Run filtering and return output file paths.

    Args:
        config_json: JSON-like dict with the same shape as config.json.template.

    Returns:
        A list of output file paths created by the pipeline.
    """
    if not isinstance(config_json, dict):
        raise ConfigurationError("config_json must be a dictionary.")

    config = _to_config(config_json)
    if config.processing.debug:
        logging.basicConfig(level=logging.DEBUG)

    pipeline = ProcessingPipeline(config)
    pipeline.run()

    return [str(path.resolve()) for path in pipeline.created_output_files]
