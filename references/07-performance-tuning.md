# Performance Tuning

All settings are fields in **`config_json`** passed to `run_filter` (see [Config JSON Reference](./03-config-json-reference.md)).

## Workers

- Start with `processing.max_workers` around `4`, then try `8` or `16` if CPU and I/O allow.
- Too many workers can hurt throughput (memory, disk contention).
- The engine caps worker count per platform; very high values are rejected at config validation time.

## Sorting

- `processing.sort_input_files`: `true` — pre-sort input files by date/index from filenames (chronological reading).
- `output.sort_by_timestamp`: `true` — sort matched records by timestamp before writing.
- For maximum throughput on huge runs where order matters less, you can set `sort_by_timestamp` or `sort_input_files` to `false` (trade clarity of ordering for speed).

## Chunked output

For large result sets, keep individual files smaller:

- `output.max_records_per_file` — e.g. `1000` (use `0` for unlimited records per file).
- `output.output_file_pattern` — e.g. `"{base}-{index:03d}{ext}"`.

`run_filter` may return **multiple** absolute paths when chunking creates several files.

## Regex vs plain terms

- `search.regex`: `true` — more expressive, usually more CPU cost.
- Prefer plain substring terms when regex is unnecessary.

## Recommended workflow

1. Set `output.dry_run_details`: `true` (or `output.dry_run`: `true`) for a preview — **no output files**; return value is `[]` (see [Public API contract](./09-public-api-contract.md)).
2. Narrow `date` / `time` and run on a small window.
3. Tune `processing.max_workers` and sorting flags.
4. Run the full filter with dry-run off and inspect returned paths.
