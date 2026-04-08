# CLI Arguments Reference

Arguments supported by `python scripts/log_filter_entry.py`.

## General

- `--help` - show help
- `--version` - tool version
- `--config <path>` - load parameters from a JSON/YAML file

## Search

- `--expression`, `--expr` - boolean search expression
- `--ignore-case` - case-insensitive search
- `--regex` - treat terms as regex patterns
- `--word-boundary` - match whole words only
- `--strip-quotes` - strip quotes before matching
- `--exact-match` - shortcut: `--word-boundary + --strip-quotes`

## Files

- `--path <dir>` - root log directory (default: current directory)
- `--file-name <substr>` - filter input files by filename substring
- `--max-file-size <MB>` - skip files larger than the limit
- `--max-record-size <KB>` - skip records larger than the limit

## Date and time

- `--from YYYY-MM-DD` - start date (inclusive)
- `--to YYYY-MM-DD` - end date (inclusive)
- `--from-time HH:MM:SS` - start time (inclusive)
- `--to-time HH:MM:SS` - end time (inclusive)

## Output

- `--output <file>` - output file
- `--no-path` - omit source file path in output
- `--highlight` - highlight matches with `<<< >>>`
- `--stats` - print final stats
- `--progress` - show progress
- `--quiet`, `-q` - quiet mode (hide progress)

## Dry-run

- `--dry-run` - show files that would be processed and exit
- `--dry-run-details` - show detailed dry-run stats and exit

## Chunking and sorting

- `--max-records-per-file <N>` - max records per output file (`0` = unlimited)
- `--output-pattern <template>` - chunk naming template (`{base}`, `{index}`, `{ext}`, `{timestamp}`)
- `--no-sort-timestamps` - disable timestamp sorting of output records
- `--no-sort-files` - disable pre-sorting of input files

## Performance and debugging

- `--workers <N>` - number of workers (default: auto)
- `--debug` - enable debug logging
- `--normalize-levels` - normalize levels (`E->ERROR`, `W->WARN`, ...)
- `--no-normalize-levels` - disable level normalization

## Argument precedence

When both CLI flags and `config` are provided, CLI values usually take precedence.
