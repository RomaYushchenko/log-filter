# Skill Integration

## Recommended invocation pattern

Skills and automation should call the **public API** only. Use the project **virtual environment** (e.g. Windows: `.\venv\Scripts\python.exe` after `init.bat`).

```python
import sys

sys.path.insert(0, "scripts")  # repo root = cwd; adjust if your layout differs

from log_filter import run_filter

output_paths = run_filter(config_json)
```

Do not rely on a CLI entrypoint in this branch. Build `config_json` in code (or `json.loads` from a checked-in config), merge any Skill-specific overrides, then call `run_filter`.

If the skill directory is not the log-filter repo root, either **change the working directory** before running Python or use **absolute** `files.path` / `output.output_file` in `config_json`.

Authoritative contract: [Public API contract](./09-public-api-contract.md).

## Baseline presets for Skills

Translate historical one-liners into `config_json`:

- **Fast search**: `search.expression`: `"ERROR"`, set `files.path`, keep `processing.max_workers` default or `1`.
- **Exact search**: `search.word_boundary` and `search.strip_quotes` set to `true`, expression e.g. `"MOVE"`.
- **Deep search**: complex `search.expression`, set `output.output_file`, `output.stats`, `processing.max_workers` (e.g. `8`).

See [Recipes and Examples](./05-recipes-and-examples.md).

## Error handling in Skills

- **`ConfigurationError`**: invalid config dict; return a clear message listing missing/invalid fields (especially `search.expression` and `files.path`).
- **`ValueError`**: model validation (paths, ranges); surface the message to the user.
- **Other exceptions**: treat as processing failures (I/O, unexpected engine errors); log traceback in debug tooling.

There are **no process exit codes** — use Python exception handling.

## Recommended Skill response format

- what was searched (`search.expression`, `files.path`, date/time filters)
- how many output files were produced (`len(output_paths)`)
- absolute paths returned by `run_filter`
- whether dry-run was used (`output.dry_run` / `dry_run_details`)
