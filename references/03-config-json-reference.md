# Config JSON Reference

Example: `scripts/config.json` or `scripts/config.json.template`.

## Public API

This structure is passed **verbatim** (as a Python `dict`, usually from `json.loads`) to:

```python
import sys

sys.path.insert(0, "scripts")
from log_filter import run_filter

paths = run_filter(config_json)
```

Contract details: [Public API contract](./09-public-api-contract.md).

## Overall structure

- `search` - expression and matching mode
- `files` - where and which logs to read
- `date` / `time` - filtering ranges
- `output` - output format and behavior
- `processing` - performance and debug settings

## `search`

- `expression` (`string`) - boolean search expression
- `ignore_case` (`bool`) - case-insensitive mode
- `regex` (`bool`) - regex mode for terms
- `word_boundary` (`bool`) - whole-word matching only
- `strip_quotes` (`bool`) - strip quotes before matching

## `files`

- `path` (`string`) - root logs directory
- `include_patterns` (`string[]`) - include patterns (glob)
- `exclude_patterns` (`string[]`) - exclude patterns
- `max_file_size` (`int|null`) - file size limit in MB
- `max_record_size` (`int|null`) - record size limit in KB

Use **`files.path`** as the root directory to scan. Older docs mentioned `search_root`; the current **`run_filter` JSON mapping** only reads **`files.path`** (and optional `include_patterns` / `exclude_patterns`).

## `date` and `time`

- `date.from` / `date.to` - `YYYY-MM-DD`
- `time.from` / `time.to` - `HH:MM:SS`

## `output`

- `output_file` (`string`) - output file path
- `no_path` (`bool`) - do not include source file path
- `highlight` (`bool`) - highlight matches
- `stats` (`bool`) - final statistics
- `verbose` (`bool`) - processing progress
- `quiet` (`bool`) - quiet mode
- `dry_run` (`bool`) - preview run without filtering
- `dry_run_details` (`bool`) - extended dry-run details
- `max_records_per_file` (`int`) - output chunking (`0` = unlimited)
- `output_file_pattern` (`string`) - chunk filename template
- `sort_by_timestamp` (`bool`) - sort results by timestamp

## `processing`

- `max_workers` (`int|null`) - number of workers
- `debug` (`bool`) - debug logging
- `normalize_log_levels` (`bool`) - normalize short log levels
- `sort_input_files` (`bool`) - pre-sort input files

## Important compatibility notes

- Prefer `search.ignore_case` over ad-hoc `case_sensitive` keys in older configs.
- For migrating from the removed CLI, see [Configuration reference](./02-cli-arguments-reference.md).
