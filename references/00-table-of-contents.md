# Log Filter References - Table of Contents

Single entrypoint for embedded documentation.

## Quick Links

- [Quick Start](./01-quick-start.md)
- [Public API contract](./09-public-api-contract.md)
- [Configuration reference (JSON) & legacy CLI mapping](./02-cli-arguments-reference.md)
- [Config JSON Reference](./03-config-json-reference.md)
- [Filter Expression Language](./04-filter-expression-language.md)
- [Recipes and Examples](./05-recipes-and-examples.md)
- [Troubleshooting](./06-troubleshooting.md)
- [Performance Tuning](./07-performance-tuning.md)
- [Skill Integration](./08-skill-integration.md)

## Recommended Reading Order

1. `01-quick-start.md`
2. `09-public-api-contract.md`
3. `04-filter-expression-language.md`
4. `03-config-json-reference.md`
5. `02-cli-arguments-reference.md` (if migrating from old CLI docs)
6. `05-recipes-and-examples.md`
7. `06-troubleshooting.md` and `07-performance-tuning.md`
8. `08-skill-integration.md`

## Short Use-Case Scenarios

### 1) Quick error search in local logs

Use when you need a fast error overview from Python (same idea as the old one-liner CLI).

Docs:

- `09-public-api-contract.md`
- `05-recipes-and-examples.md`

### 2) Find business events with multiple conditions

Use when you need precise event selection by term combinations.

Docs:

- `04-filter-expression-language.md`
- `05-recipes-and-examples.md`

### 3) Analyze a specific time window

Use when date/time constraints are required (`date` / `time` sections in config JSON).

Docs:

- `03-config-json-reference.md`
- `02-cli-arguments-reference.md`

### 4) Large logs with chunked output

Use when output volume is large and must stay manageable.

Set `output.max_records_per_file`, optionally `output.output_file_pattern`, and tune `processing.max_workers`.

Docs:

- `05-recipes-and-examples.md`
- `07-performance-tuning.md`

### 5) Validate configuration before full run

Use when you need a safe pre-check.

Set `output.dry_run` or `output.dry_run_details` to `true`. The API returns an empty path list and does not write results.

Docs:

- `09-public-api-contract.md`
- `06-troubleshooting.md`

### 6) Skill integration mode

Use when the tool is invoked by an agent/Skill.

Recommendation:

- import `run_filter` and pass a merged `config_json` dict.

Docs:

- `08-skill-integration.md`

## Quick Pre-Run Checklist

- virtual environment is ready (Windows: run **`init.bat`**, then use **`.\venv\Scripts\python.exe`**)
- dependencies from `scripts/requirements-log-filter.txt` are installed in that environment
- **`scripts`** is on `sys.path` (or `PYTHONPATH`) so `import log_filter` works
- current working directory matches what you assume for relative `files.path` / `output.output_file`
- `files.path` exists
- `search.expression` is set in `config_json`
- for large datasets, tune `processing.max_workers` and `output.max_records_per_file`

Project overview and copy-paste examples: root **`README.md`**.
