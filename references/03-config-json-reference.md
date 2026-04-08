# Config JSON Reference

Example: `scripts/config.json`.

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

Note:
- `search_root` is supported for backward compatibility, but `path` is preferred.

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
- `max_records_per_file` (`int`) - output chunking
- `output_file_pattern` (`string`) - chunk filename template
- `sort_by_timestamp` (`bool`) - sort results by timestamp

## `processing`

- `max_workers` (`int|null`) - number of workers
- `debug` (`bool`) - debug logging
- `normalize_log_levels` (`bool`) - normalize short log levels
- `sort_input_files` (`bool`) - pre-sort input files

## Important compatibility notes

- Your current `scripts/config.json` uses `search.case_sensitive`.
  - The current CLI/model field is `ignore_case`.
  - Recommendation: replace `case_sensitive` with `ignore_case`.
- Some old keys (`search_root` and root-level keys) are read as legacy.
  For new configs, prefer the nested sections described here.
