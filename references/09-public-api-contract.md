# Public API contract

This project is **library-first**: callers import a single entrypoint and pass a configuration object that matches `scripts/config.json.template`.

## Runtime layout

- Install dependencies from **`scripts/requirements-log-filter.txt`** (on Windows, **`init.bat`** in the repo root creates **`venv`** and installs them — see the root **`README.md`**).
- The importable package is **`scripts/log_filter`**. Add **`scripts`** to `sys.path` (or `PYTHONPATH`) before `from log_filter import run_filter`, unless the project is installed as a package.
- String paths inside `config_json` (`files.path`, `output.output_file`) are interpreted by the OS relative to the **current working directory** unless you pass absolute paths.

## Entrypoint

```python
import sys

sys.path.insert(0, "scripts")
from log_filter import run_filter

output_paths: list[str] = run_filter(config_json)
```

- **Module path** (when `scripts/` is on `sys.path`): `log_filter`
- **Function**: `run_filter`
- **Parameter**: `config_json` — a `dict` deserialized from JSON (same keys and nesting as the template).

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

- **`log_filter.core.exceptions.ConfigurationError`**: invalid `config_json` (missing `search.expression`, bad types, invalid date/time strings, non-dict root, etc.).
- **`ValueError`**: invalid combinations enforced by configuration models (for example `files.path` does not exist or is not a directory, invalid `SearchConfig` ranges).
- **Other exceptions**: processing failures (I/O, parser failures surfaced by the pipeline) are **not** wrapped; callers should handle or log them.

There is **no** CLI, no `sys.exit` codes, and no separate `main` entrypoint in this branch.

## Configuration shape

The authoritative schema is:

- [Config JSON Reference](./03-config-json-reference.md)
- Template file: `scripts/config.json.template`

Minimal example:

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
