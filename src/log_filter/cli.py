"""
Command-line interface for the log filter application.

This module provides argument parsing and configuration building
from command-line arguments and configuration files.
"""

import argparse
import json
import logging
import sys
from datetime import date, time
from pathlib import Path
from typing import Any, List, Optional, cast

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from log_filter import __version__
from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.exceptions import ConfigurationError

# Initialize logger
logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="log-filter",
        description="Filter log records by boolean expression",
        epilog="""
Examples:
  log-filter --config searchConfig.json
  log-filter --expression "ERROR AND Kafka"
  log-filter --expression "ERROR" --from 2025-01-01 --to 2025-01-10
  log-filter --expression "ERROR [0-9]{3}" --regex
  log-filter --expression "ERROR" --path /var/log/myapp --workers 8
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Configuration file
    parser.add_argument("--config", type=Path, help="Load parameters from YAML/JSON config file")

    # Search expression
    parser.add_argument(
        "--expression", "--expr", help="Boolean search expression (e.g., 'ERROR AND Kafka')"
    )

    # File filtering
    parser.add_argument("--file-name", help="Substring to filter input files")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Root directory for log file search (default: current directory)",
    )

    # Search modes
    parser.add_argument("--ignore-case", action="store_true", help="Case-insensitive search")
    parser.add_argument(
        "--regex", action="store_true", help="Interpret search terms as regular expressions"
    )
    parser.add_argument(
        "--word-boundary",
        action="store_true",
        help="Match whole words only (not substrings). Example: 'MOVE' won't match 'MOVE_SNAPSHOT'",
    )
    parser.add_argument(
        "--strip-quotes",
        action="store_true",
        help="Strip quote characters before matching (useful for JSON/CSV logs)",
    )
    parser.add_argument(
        "--exact-match",
        action="store_true",
        help="Enable both --word-boundary and --strip-quotes for exact word matching",
    )

    # Date/time filtering
    parser.add_argument("--from", dest="date_from", help="Start date (YYYY-MM-DD, inclusive)")
    parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD, inclusive)")
    parser.add_argument("--from-time", dest="from_time", help="Start time (HH:MM:SS, inclusive)")
    parser.add_argument("--to-time", dest="to_time", help="End time (HH:MM:SS, inclusive)")

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: filter-result.log or from config file)",
    )
    parser.add_argument(
        "--no-path", action="store_true", help="Do not include source file path in output"
    )
    parser.add_argument(
        "--highlight", action="store_true", help="Highlight matches with <<< >>> markers"
    )

    # Display options
    parser.add_argument(
        "--progress", action="store_true", help="Show progress messages during processing"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress messages (quiet mode)"
    )
    parser.add_argument("--stats", action="store_true", help="Show final processing statistics")

    # Dry-run modes
    parser.add_argument(
        "--dry-run", action="store_true", help="Show files that would be processed and exit"
    )
    parser.add_argument(
        "--dry-run-details", action="store_true", help="Show detailed file statistics and exit"
    )

    # Size limits
    parser.add_argument(
        "--max-file-size", type=int, metavar="MB", help="Skip files larger than N megabytes"
    )
    parser.add_argument(
        "--max-record-size", type=int, metavar="KB", help="Skip log records larger than N kilobytes"
    )

    # Processing options
    parser.add_argument(
        "--workers", type=int, help="Number of parallel worker threads (default: CPU cores)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Level normalization
    normalize_group = parser.add_mutually_exclusive_group()
    normalize_group.add_argument(
        "--normalize-levels",
        dest="normalize_log_levels",
        action="store_true",
        default=None,
        help="Normalize abbreviated log levels (E->ERROR, W->WARN, etc.) [default: enabled]",
    )
    normalize_group.add_argument(
        "--no-normalize-levels",
        dest="normalize_log_levels",
        action="store_false",
        help="Disable log level normalization (use raw levels from logs)",
    )

    return parser


def load_config_file(config_path: Path) -> dict:
    """Load configuration from JSON or YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigurationError: If file cannot be loaded or parsed
    """
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    if not config_path.is_file():
        raise ConfigurationError(f"Configuration path is not a file: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try JSON first
        if config_path.suffix.lower() == ".json":
            return cast(dict[Any, Any], json.loads(content))

        # Try YAML
        if config_path.suffix.lower() in (".yaml", ".yml"):
            if not YAML_AVAILABLE:
                raise ConfigurationError(
                    "YAML support not available. Install PyYAML: pip install pyyaml"
                )
            return cast(dict[Any, Any], yaml.safe_load(content))

        # Try to auto-detect
        try:
            return cast(dict[Any, Any], json.loads(content))
        except json.JSONDecodeError as exc:
            if YAML_AVAILABLE:
                return cast(dict[Any, Any], yaml.safe_load(content))
            raise ConfigurationError(
                "Could not parse configuration file. "
                "Install PyYAML for YAML support: pip install pyyaml"
            ) from exc

    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config file: {e}") from e
    except Exception as e:
        if YAML_AVAILABLE and isinstance(e, yaml.YAMLError):
            raise ConfigurationError(f"Invalid YAML in config file: {e}") from e
        raise ConfigurationError(f"Error loading config file: {e}") from e


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string or None

    Returns:
        Parsed date or None

    Raises:
        ConfigurationError: If date format is invalid
    """
    if not date_str:
        return None

    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError("Expected format: YYYY-MM-DD")

        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)

    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"Invalid date format '{date_str}': {e}") from e


def parse_time(time_str: Optional[str]) -> Optional[time]:
    """Parse time string in HH:MM:SS format.

    Args:
        time_str: Time string or None

    Returns:
        Parsed time or None

    Raises:
        ConfigurationError: If time format is invalid
    """
    if not time_str:
        return None

    try:
        parts = time_str.split(":")
        if len(parts) != 3:
            raise ValueError("Expected format: HH:MM:SS")

        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
        return time(hour, minute, second)

    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"Invalid time format '{time_str}': {e}") from e


def build_config_from_args(
    args: argparse.Namespace,
) -> ApplicationConfig:  # pylint: disable=too-many-locals
    """Build ApplicationConfig from parsed command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Complete application configuration

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Load config file if specified
    config_dict = {}
    if args.config:
        config_dict = load_config_file(args.config)

    # Support both flat and nested config structures
    search_section = config_dict.get("search", {})
    files_section = config_dict.get("files", {})
    output_section = config_dict.get("output", {})
    processing_section = config_dict.get("processing", {})
    date_section = config_dict.get("date", {})
    time_section = config_dict.get("time", {})

    # Build search config
    # Try nested structure first, then flat
    expression = args.expression or search_section.get("expression") or config_dict.get("expr")
    if not expression:
        raise ConfigurationError(
            "Search expression is required. Use --expression or provide in config file."
        )

    # Get ignore_case from CLI args or config
    ignore_case_value = args.ignore_case
    if not ignore_case_value:
        ignore_case_value = search_section.get("ignore_case", config_dict.get("ignore_case", False))

    # Handle --exact-match shorthand: enables both word_boundary and strip_quotes
    word_boundary_value = args.word_boundary or args.exact_match
    strip_quotes_value = args.strip_quotes or args.exact_match

    # Get from config if not set by CLI
    if not word_boundary_value:
        word_boundary_value = search_section.get(
            "word_boundary", config_dict.get("word_boundary", False)
        )
    if not strip_quotes_value:
        strip_quotes_value = search_section.get(
            "strip_quotes", config_dict.get("strip_quotes", False)
        )

    search_config = SearchConfig(
        expression=expression,
        ignore_case=ignore_case_value,
        # Note: Config files use "regex" (recommended: search.regex), but model uses "use_regex"
        # Supports both "search.regex" (nested, recommended) and "use_regex" (root level, legacy)
        use_regex=args.regex or search_section.get("regex") or config_dict.get("use_regex", False),
        word_boundary=word_boundary_value,
        strip_quotes=strip_quotes_value,
        date_from=parse_date(
            args.date_from or date_section.get("from") or config_dict.get("date_from")
        ),
        date_to=parse_date(args.date_to or date_section.get("to") or config_dict.get("date_to")),
        time_from=parse_time(
            args.from_time or time_section.get("from") or config_dict.get("from_time")
        ),
        time_to=parse_time(args.to_time or time_section.get("to") or config_dict.get("to_time")),
    )

    # Build file config
    file_masks: List[str] = []
    if args.file_name:
        file_masks = [args.file_name]
    elif "file_name" in config_dict:
        fn = config_dict["file_name"]
        file_masks = fn if isinstance(fn, list) else [fn]

    # Handle path - nested vs flat
    path_value = args.path
    if path_value == Path("."):
        # User didn't specify --path, check config file
        if "path" in files_section:
            path_value = Path(files_section["path"])
        elif "search_root" in files_section:
            # Backward compatibility - deprecated
            logger.warning(
                "Config key 'search_root' is deprecated and will be removed in v3.0. "
                "Please use 'path' instead."
            )
            path_value = Path(files_section["search_root"])
        elif "path" in config_dict:
            path_value = Path(config_dict["path"])

    # Get include/exclude patterns from nested structure
    include_patterns = files_section.get("include_patterns", [])
    exclude_patterns = files_section.get("exclude_patterns", [])

    file_config = FileConfig(
        path=path_value,
        file_masks=file_masks,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        extensions=(".log", ".gz"),
        max_file_size_mb=args.max_file_size
        or files_section.get("max_file_size")
        or config_dict.get("max_file_size"),
        max_record_size_kb=args.max_record_size
        or files_section.get("max_record_size")
        or config_dict.get("max_record_size"),
    )

    # Build output config
    output_file = (
        args.output
        or output_section.get("output_file")
        or config_dict.get("output", Path("filter-result.log"))
    )
    if isinstance(output_file, str):
        output_file = Path(output_file)

    # Handle quiet flag - CLI takes precedence over config
    # Priority: CLI --quiet > Config quiet > CLI --progress > Config verbose
    is_quiet = args.quiet or output_section.get("quiet", False) or config_dict.get("quiet", False)
    show_progress_value = (
        False
        if is_quiet
        else (args.progress or output_section.get("verbose") or config_dict.get("progress", False))
    )

    output_config = OutputConfig(
        output_file=output_file,
        include_file_path=not (args.no_path or output_section.get("no_path", False)),
        highlight_matches=args.highlight
        or output_section.get("highlight")
        or config_dict.get("highlight", False),
        show_progress=show_progress_value,
        show_stats=args.stats or output_section.get("stats") or config_dict.get("stats", False),
        dry_run=args.dry_run or config_dict.get("dry_run", False),
        dry_run_details=args.dry_run_details or config_dict.get("dry_run_details", False),
    )

    # Build processing config
    worker_count = (
        args.workers or processing_section.get("max_workers") or config_dict.get("workers")
    )

    # Normalize log levels: CLI arg > config file > default (True)
    normalize_log_levels = True  # default
    if args.normalize_log_levels is not None:
        normalize_log_levels = args.normalize_log_levels
    elif "normalize_log_levels" in processing_section:
        normalize_log_levels = processing_section.get("normalize_log_levels", True)
    elif "normalize_log_levels" in config_dict:
        normalize_log_levels = config_dict.get("normalize_log_levels", True)

    processing_config = ProcessingConfig(
        worker_count=worker_count,
        debug=args.debug or processing_section.get("debug") or config_dict.get("debug", False),
        normalize_log_levels=normalize_log_levels,
    )

    # Build complete application config
    return ApplicationConfig(
        search=search_config, files=file_config, output=output_config, processing=processing_config
    )


def parse_args(argv: Optional[List[str]] = None) -> ApplicationConfig:
    """Parse command-line arguments and build configuration.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Complete application configuration

    Raises:
        ConfigurationError: If arguments are invalid
        SystemExit: If --help is requested or arguments are invalid
    """
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    try:
        return build_config_from_args(args)
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Error building configuration: {e}") from e


def main() -> None:
    """CLI entry point for testing."""
    try:
        config = parse_args()
        # CLI testing output - print() is appropriate for user-facing CLI feedback
        print("Configuration loaded successfully:")  # noqa: T201
        print(f"  Expression: {config.search.expression}")  # noqa: T201
        print(f"  Path: {config.files.path}")  # noqa: T201
        print(f"  Output: {config.output.output_file}")  # noqa: T201
    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
