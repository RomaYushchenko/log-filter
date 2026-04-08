# Quick Start

## 1) Install dependencies

```bash
python -m pip install -r scripts/requirements-log-filter.txt
```

## 2) Basic run

```bash
python scripts/log_filter_entry.py --expression "ERROR" --path ./logs --stats
```

## 3) Run using config

```bash
python scripts/log_filter_entry.py --config ./scripts/config.json
```

## 4) Exit codes

- `0` - success
- `1` - processing error
- `2` - configuration/argument error
- `130` - interrupted by user (`Ctrl+C`)

## 5) Minimal checklist

- `--path` exists and is a directory
- expression is provided (`--expression`) or present in `scripts/config.json`
- dependencies are installed (`pyyaml`, `tqdm`)
