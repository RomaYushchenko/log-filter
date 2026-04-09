# Troubleshooting

## `ModuleNotFoundError: No module named 'log_filter'`

Cause: Python cannot see the package under `scripts/log_filter`.  
Fix: before importing, run `sys.path.insert(0, "scripts")` (from the repo root), or set `PYTHONPATH` to the `scripts` directory. See [Quick Start](./01-quick-start.md).

## Error: `search.expression is required`

Cause: `search.expression` is missing, empty, or not a string in `config_json`.  
Fix: set `search.expression` before calling `run_filter`.

## Error: `Path does not exist`

Cause: `files.path` points to a non-existing directory.  
Fix: verify path and permissions.

## Date/time format error

Cause: invalid format.  
Fix:

- date: `YYYY-MM-DD` in `date.from` / `date.to`
- time: `HH:MM:SS` in `time.from` / `time.to`

## Empty result list `[]` but you expected output files

Possible causes:

- **No matches** for the expression or filters.
- **Dry-run** enabled (`output.dry_run` or `output.dry_run_details`) — by design, no files are written and the API returns `[]`.

See [Public API contract](./09-public-api-contract.md).

## Too many results

Fix:

- add more `AND` constraints
- use `NOT` to exclude noisy patterns
- add date/time filters
- enable `output.max_records_per_file` chunking

## Unstable performance

Fix:

- tune `processing.max_workers` (often `4..16`)
- enable/disable `output.sort_by_timestamp` and `processing.sort_input_files` based on your goal
- use `output.dry_run_details` for a lightweight preview (empty path list; no output files)
