# Recipes and Examples

Before any example, ensure:

1. Dependencies: `scripts/requirements-log-filter.txt` (e.g. run **`init.bat`** on Windows from the repo root — see root **`README.md`**).
2. Import path: the package lives under **`scripts/`**:

```python
import sys
sys.path.insert(0, "scripts")

from log_filter import run_filter
```

Each recipe below assumes `run_filter` is already importable. Adjust `files.path` and `output.output_file` for your machine (paths are relative to the process **current working directory** unless you use absolute paths).

## 1) All errors

```python
cfg = {
    "search": {"expression": "ERROR"},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {
        "output_file": "./output/errors.log",
        "stats": True,
        "verbose": False,
        "quiet": False,
    },
    "processing": {"max_workers": None},
}
paths = run_filter(cfg)
```

## 2) Errors and criticals, excluding tests

```python
cfg = {
    "search": {"expression": '(ERROR OR CRITICAL) AND NOT test'},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {"output_file": "./output/result.log", "quiet": True},
    "processing": {},
}
paths = run_filter(cfg)
```

## 3) Date and time filtering

```python
cfg = {
    "search": {"expression": "ERROR"},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": "2026-04-01", "to": "2026-04-07"},
    "time": {"from": "09:00:00", "to": "18:00:00"},
    "output": {"output_file": "./output/result.log", "quiet": True},
    "processing": {},
}
paths = run_filter(cfg)
```

## 4) Regex search for error codes

```python
cfg = {
    "search": {"expression": r"ERR_[0-9]{4}", "regex": True},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {"output_file": "./output/result.log", "quiet": True},
    "processing": {},
}
paths = run_filter(cfg)
```

## 5) Exact word matching

Use `word_boundary` and `strip_quotes` (same effect as historical `--exact-match`):

```python
cfg = {
    "search": {"expression": "MOVE", "word_boundary": True, "strip_quotes": True},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {"output_file": "./output/result.log", "quiet": True},
    "processing": {},
}
paths = run_filter(cfg)
```

## 6) Large datasets with chunked output

```python
cfg = {
    "search": {"expression": "ERROR OR WARN"},
    "files": {"path": "./logs", "include_patterns": ["*.log", "*.log.gz"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {
        "output_file": "./output/result.log",
        "max_records_per_file": 1000,
        "output_file_pattern": "{base}-{index:03d}{ext}",
        "stats": True,
        "quiet": True,
    },
    "processing": {"max_workers": 8},
}
paths = run_filter(cfg)  # may return multiple paths
```

## 7) Dry-run before production run

```python
cfg = {
    "search": {"expression": "ERROR"},
    "files": {"path": "./logs", "include_patterns": ["*.log"], "exclude_patterns": []},
    "date": {"from": None, "to": None},
    "time": {"from": None, "to": None},
    "output": {"output_file": "./output/unused.log", "dry_run_details": True, "quiet": True},
    "processing": {},
}
assert run_filter(cfg) == []
```

## 8) Run from a JSON file on disk

```python
import json
from pathlib import Path

from log_filter import run_filter

config_json = json.loads(Path("scripts/config.json").read_text(encoding="utf-8"))
paths = run_filter(config_json)
```
