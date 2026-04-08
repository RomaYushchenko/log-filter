# Troubleshooting

## Error: `Search expression is required`

Cause: `--expression` is missing and `search.expression` is not set in config.  
Fix: pass `--expression` or update config.

## Error: `Path does not exist`

Cause: `--path`/`files.path` points to a non-existing directory.  
Fix: verify path and permissions.

## Date/time format error

Cause: invalid format.  
Fix:

- date: `YYYY-MM-DD`
- time: `HH:MM:SS`

## Too many results

Fix:

- add more `AND` constraints
- use `NOT` to exclude noisy patterns
- add date/time filters
- write to file and enable chunking

## Unstable performance

Fix:

- tune `--workers` (usually `4..16`)
- enable/disable sorting based on your goal
- run `--dry-run-details` before the full run
