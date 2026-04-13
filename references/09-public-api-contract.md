# Public API contract

This project is **library-first** with two public usage styles:

- compact API: pass only search expression (+ optional logs/output paths)
- full API: pass full configuration object matching `scripts/config.json.template`

## Runtime layout

- Install dependencies from **`scripts/requirements-log-filter.txt`** (on Windows, **`init.bat`** in the repo root creates **`venv`** and installs them — see the root **`README.md`**).
- The importable package is **`scripts/log_filter`**. Add **`scripts`** to `sys.path` (or `PYTHONPATH`) before `from log_filter import run_filter`, unless the project is installed as a package.
- String paths inside `config_json` (`files.path`, `output.output_file`) are interpreted by the OS relative to the **current working directory** unless you pass absolute paths.

## Entrypoint

```python
import sys

sys.path.insert(0, "scripts")
from log_filter import run_filter

output_paths: list[str] = run_filter("ERROR", logs_path="./scripts/input-logs")
```

- **Module path** (when `scripts/` is on `sys.path`): `log_filter`
- **Primary function**: `run_filter`
- **Compact mode**:
    - `run_filter(expression: str, logs_path: str|Path = DEFAULT_LOGS_PATH, output_file: str|Path = DEFAULT_OUTPUT_FILE)`
- **Full mode (backward compatible)**:
    - `run_filter(config_json: dict)`
- **Convenience functions**:
    - `run_filter_simple(expression, logs_path=..., output_file=...)`
    - `run_filter_service_errors(logs_path=..., output_file=...)`

## Return value

- **Type**: `list[str]`
- **Content**: absolute, resolved paths of **output files created** by this run.

Semantics:

| Situation | Return value |
| --- | --- |
| Matches found and written | One or more paths (chunking may produce multiple files). |
| No matches | `[]` — no output files are created. |
| `output.dry_run` or `output.dry_run_details` is `true` | `[]` — no output files are written (preview-only mode). |

## Errors

- **`log_filter.core.exceptions.ConfigurationError`**:
    - invalid `config_json` (missing `search.expression`, bad types, invalid date/time strings, etc.)
    - invalid compact call (`expression` is empty or wrong type)
- **`ValueError`**: invalid combinations enforced by configuration models (for example `files.path` does not exist or is not a directory, invalid `SearchConfig` ranges).
- **Other exceptions**: processing failures (I/O, parser failures surfaced by the pipeline) are **not** wrapped; callers should handle or log them.

There is **no** CLI, no `sys.exit` codes, and no separate `main` entrypoint in this branch.

## Configuration shape

The authoritative schema is:

- [Config JSON Reference](./03-config-json-reference.md)
- Template file: `scripts/config.json.template`

Minimal compact example:

```python
import sys

sys.path.insert(0, "scripts")
from log_filter import run_filter

paths = run_filter(
    "(ERROR OR CRITICAL OR EXCEPTION) AND NOT test",
    logs_path="./scripts/input-logs",
    output_file="./scripts/output/custom-investigation.log",
)
```

Full config example:

```python
import sys

sys.path.insert(0, "scripts")
from log_filter import run_filter

config_json = {
    "search": {"expression": "ERROR", "ignore_case": False},
    "files": {
        "path": "./logs",
        "include_patterns": ["*.log", "*.log.gz"],
        "exclude_patterns": [],
        "max_file_size": None,
        "max_record_size": None,
    },
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {
        "output_file": "./output/result.log",
        "no_path": False,
        "highlight": False,
        "stats": False,
        "verbose": False,
        "quiet": True,
        "dry_run": False,
        "dry_run_details": False,
        "max_records_per_file": 500,
        "output_file_pattern": "{base}-{index:03d}{ext}",
        "sort_by_timestamp": True,
    },
    "processing": {
        "max_workers": None,
        "debug": False,
        "normalize_log_levels": True,
        "sort_input_files": True,
    },
}

paths = run_filter(config_json)
```

(Remember `sys.path.insert(0, "scripts")` before importing `log_filter` when running from a normal script.)

## Stable runner script

Use `scripts/run_filter_runner.py` to avoid long inline terminal commands.

Supported modes:
- `--mode expression --expression "..." --logs-path "..." --output-file "..."`
- `--mode expression --expression-file "..." --logs-path "..." --output-file "..."`
- `--mode expression --expression-stdin --logs-path "..." --output-file "..."`
- `--mode service-errors --logs-path "..." --output-file "..."`

Path guardrails:
- `--strict-logs-path` disables basename fallback for `--logs-path` resolution.
- Use it when the caller must stay on an exact folder and should not auto-switch to similarly named directories.

The runner prints `output_paths` as JSON.

## Loading JSON from disk

The API does not read files; the caller loads JSON and passes a dict:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from log_filter import run_filter

config_json = json.loads(Path("scripts/config.json").read_text(encoding="utf-8"))
paths = run_filter(config_json)
```

## Versioning

- Behavior changes to `run_filter` signatures or return semantics should be treated as **breaking API changes**.
- The JSON config shape should remain backward compatible where possible; document additions in `03-config-json-reference.md`.

## Related docs

- [Quick Start](./01-quick-start.md)
- Root **`README.md`** (Windows `init.bat`, `venv`, example script)
- [Skill Integration](./08-skill-integration.md)
- [Configuration reference](./02-cli-arguments-reference.md) (JSON fields and legacy CLI mapping)
