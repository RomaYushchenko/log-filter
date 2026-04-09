# Configuration reference (JSON) and legacy CLI mapping

The supported interface is **`run_filter(config_json)`** with a dict matching `scripts/config.json.template`.

The list below maps **historical CLI flags** (removed in this branch) to the **JSON fields** you should set instead. For full field descriptions see [Config JSON Reference](./03-config-json-reference.md).

## Search

| Legacy CLI | JSON |
| --- | --- |
| `--expression` / `--expr` | `search.expression` |
| `--ignore-case` | `search.ignore_case`: `true` |
| `--regex` | `search.regex`: `true` |
| `--word-boundary` | `search.word_boundary`: `true` |
| `--strip-quotes` | `search.strip_quotes`: `true` |
| `--exact-match` | `search.word_boundary` and `search.strip_quotes`: `true` |

## Files

| Legacy CLI | JSON |
| --- | --- |
| `--path` | `files.path` |
| `--file-name` | Not a direct field; use `files.include_patterns` / naming conventions, or pre-filter files |
| `--max-file-size` | `files.max_file_size` (MB) |
| `--max-record-size` | `files.max_record_size` (KB) |

## Date and time

| Legacy CLI | JSON |
| --- | --- |
| `--from` | `date.from` (`YYYY-MM-DD`) |
| `--to` | `date.to` |
| `--from-time` | `time.from` (`HH:MM:SS`) |
| `--to-time` | `time.to` |

## Output and UX

| Legacy CLI | JSON |
| --- | --- |
| `--output` | `output.output_file` |
| `--no-path` | `output.no_path`: `true` |
| `--highlight` | `output.highlight`: `true` |
| `--stats` | `output.stats`: `true` |
| `--progress` | `output.verbose`: `true` |
| `--quiet` / `-q` | `output.quiet`: `true` |

## Dry-run

| Legacy CLI | JSON |
| --- | --- |
| `--dry-run` | `output.dry_run`: `true` |
| `--dry-run-details` | `output.dry_run_details`: `true` |

## Chunking and sorting

| Legacy CLI | JSON |
| --- | --- |
| `--max-records-per-file` | `output.max_records_per_file` (`0` = unlimited) |
| `--output-pattern` | `output.output_file_pattern` |
| `--no-sort-timestamps` | `output.sort_by_timestamp`: `false` |
| `--no-sort-files` | `processing.sort_input_files`: `false` |

## Processing

| Legacy CLI | JSON |
| --- | --- |
| `--workers` | `processing.max_workers` |
| `--debug` | `processing.debug`: `true` |
| `--normalize-levels` / `--no-normalize-levels` | `processing.normalize_log_levels` |

## Precedence

Previously, CLI flags could override a file loaded via `--config`. With the API-only model, **only the dict passed to `run_filter`** applies. Merge overrides in your own code before calling `run_filter`.

## See also

- [Public API contract](./09-public-api-contract.md)
- [Config JSON Reference](./03-config-json-reference.md)
- Repository root **`README.md`** — `init.bat`, `venv`, and how to run `run_filter`
