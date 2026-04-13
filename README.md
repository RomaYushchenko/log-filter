# Log Filter (Skill Transfer Branch)

This branch is meant to be copied into another repo and used as a **Python library**: you call `run_filter(config_json)` from your own code. There is no CLI entrypoint.

## Layout

Runtime code lives under `scripts/` (`scripts/log_filter/` is the importable package). You must put **`scripts` on `sys.path`** (or set `PYTHONPATH`) before `from log_filter import run_filter`, unless you install the project as a package.

## One-time environment setup

### Windows (recommended for skills)

From the **repository root** (the folder that contains `scripts/` and `init.bat`):

```bat
init.bat
```

This creates **`venv`** next to `init.bat`, activates it, and runs `pip install -r scripts/requirements-log-filter.txt`. After that, use only:

```bat
.\venv\Scripts\python.exe ...
```

Manual equivalent:

```bat
python -m venv venv
.\venv\Scripts\activate.bat
python -m pip install -r scripts/requirements-log-filter.txt
```

### macOS / Linux

```bash
cd /path/to/log-filter
python3 -m venv venv
source venv/bin/activate
python -m pip install -r scripts/requirements-log-filter.txt
```

Use `venv/bin/python` for all commands.

## How to invoke the API

1. Working directory: stay at the **project root** (so paths like `./scripts/input-logs` in config match real folders).
2. Interpreter: **`venv\Scripts\python.exe`** (Windows) or **`venv/bin/python`** (Unix).
3. Import path: add **`scripts`** so Python finds the `log_filter` package.

Use a small script at the repo root, e.g. `run_example.py` (avoids painful quoting in `python -c`):

```python
import sys
sys.path.insert(0, "scripts")

from log_filter import run_filter

config_json = {
    "search": {"expression": "ERROR", "ignore_case": False},
    "files": {
        "path": "./scripts/input-logs",
        "include_patterns": ["*.log", "*.log.gz"],
        "exclude_patterns": [],
        "max_file_size": None,
        "max_record_size": None,
    },
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {
        "output_file": "./scripts/output/filter-result.log",
        "no_path": False,
        "highlight": False,
        "stats": True,
        "verbose": False,
        "quiet": False,
        "dry_run": False,
        "dry_run_details": False,
        "max_records_per_file": 500,
        "output_file_pattern": "{base}-{index:03d}{ext}",
        "sort_by_timestamp": True,
    },
    "processing": {
        "max_workers": 1,
        "debug": False,
        "normalize_log_levels": True,
        "sort_input_files": True,
    },
}

output_files = run_filter(config_json)
print(output_files)
```

Run from the same directory as the script:

```bat
.\venv\Scripts\python.exe run_example.py
```

If your skill lives elsewhere, set the **current directory** to this project root, or change `files.path` / `output.output_file` in `config_json` to absolute paths.

`run_filter` returns a **list of strings**: absolute paths to output files that were written. If there are no matches, or dry-run is enabled, the list may be **empty** (see `references/09-public-api-contract.md`).

## Included in this tree

- `scripts/log_filter/` — engine and **`run_filter`**
- `scripts/requirements-log-filter.txt` — runtime dependencies for `pip`
- `init.bat` — Windows venv + install (optional but convenient)
- `references/` — docs (`references/README.md`, API: `references/09-public-api-contract.md`)

## Copy into a target project

Typical bundle:

- `scripts/log_filter/`
- `scripts/requirements-log-filter.txt` (and other `scripts/requirements*.txt` if you need them)
- `init.bat` (Windows)
- `scripts/config.json` or `scripts/config.json.template`
- `references/`, `assets/`
- `scripts/tests/` (optional)
- `scripts/input-logs/` (optional sample logs)
