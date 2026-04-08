# Skill Integration

## Recommended invocation pattern

The Skill should call only the entrypoint:

```bash
python scripts/log_filter_entry.py ...
```

Do not call internal modules directly.

## Baseline presets for Skill

- Fast search:
  - `python scripts/log_filter_entry.py --expression "ERROR" --path ./logs`
- Exact search:
  - `python scripts/log_filter_entry.py --expression "MOVE" --exact-match --path ./logs`
- Deep search:
  - `python scripts/log_filter_entry.py --expression "(ERROR OR CRITICAL) AND NOT test" --path ./logs --output ./output/result.log --stats --workers 8`

## Error handling in Skill

- if exit code is `2` - return a configuration error with guidance
- if exit code is `1` - return a processing error and suggest narrowing the filter
- if exit code is `130` - mark the task as user-interrupted

## Recommended Skill response format

- what was searched (expression, path, filters)
- number of matches found
- where results were saved (`output_file`, if set)
- which constraints were applied (date/time, size limits, dry-run)
