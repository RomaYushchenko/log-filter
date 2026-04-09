# Quick Start

## 0) Where to run from

Use the **project root** (the directory that contains `scripts/`). Paths in `config_json` such as `./scripts/test-logs` are resolved relative to the **current working directory** of the process.

## 1) Environment and dependencies

### Windows (skills)

From the project root:

```bat
init.bat
```

This creates **`venv`**, installs `scripts/requirements-log-filter.txt`, and you should use:

```bat
.\venv\Scripts\python.exe ...
```

See the repository **`README.md`** at the project root for the full workflow.

### Any OS (manual)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Unix:     source venv/bin/activate
python -m pip install -r scripts/requirements-log-filter.txt
```

## 2) Python path

The package lives in **`scripts/log_filter`**. Before `from log_filter import run_filter`, add:

```python
import sys
sys.path.insert(0, "scripts")
```

(Or set `PYTHONPATH` to the `scripts` directory.) The snippets below assume this line ran first.

## 3) Call the public API

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from log_filter import run_filter

config_json = json.loads(
    Path("scripts/config.json.template").read_text(encoding="utf-8")
)
# Adjust files.path, output.output_file, and search.expression for your machine.

output_paths = run_filter(config_json)
print(output_paths)
```

See [Public API contract](./09-public-api-contract.md) for return values, dry-run behavior, and errors.

## 4) Minimal checklist

- `venv` (or your env) has packages from `scripts/requirements-log-filter.txt`
- `sys.path` includes `scripts` (or equivalent)
- `files.path` exists and is a directory
- `search.expression` is a non-empty string
- parent directory of `output.output_file` is writable (created automatically if needed)

## 5) Run tests (optional)

Developers typically use a separate env and `requirements-dev.txt`:

```bash
python -m venv venv
source venv/bin/activate   # or Windows: venv\Scripts\activate.bat
pip install -r scripts/requirements-dev.txt
pytest scripts/tests -q
```
