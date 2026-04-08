# Performance Tuning

## Workers

- start with `--workers 4`, then increase to `8/16`
- too many workers can reduce throughput
- platforms enforce a maximum worker limit

## Sorting

- `sort_input_files=true` helps with chronological reading
- `sort_by_timestamp=true` helps with final analysis
- for maximum speed, you can disable:
  - `--no-sort-files`
  - `--no-sort-timestamps`

## Chunked output

For large outputs, use:

- `--max-records-per-file`
- `--output-pattern`

This keeps individual files smaller and simplifies post-processing.

## Regex vs plain terms

- `--regex` is more flexible, but usually slower
- for large runs, use plain terms when regex is unnecessary

## Recommended workflow

1. `--dry-run-details`
2. run on a small date range
3. tune workers and sorting
4. execute the full run
