# Log Filter (Skill Transfer Branch)

This branch is optimized for copying into another repository where the tool will
be used as a local script utility for Skills.

## Layout

All transferable project logic is stored under `scripts/`.
The project is intended to be run from `scripts/` only.

## Included

- Full runtime engine in `scripts/log_filter/`
- Skill-friendly entrypoint `scripts/log_filter_entry.py`
- Minimal runtime dependencies in `scripts/requirements-log-filter.txt`

## Quick start

```bash
python -m pip install -r scripts/requirements-log-filter.txt
python scripts/log_filter_entry.py --expression "ERROR" --path ./scripts/test-logs --stats
```

## Copy into target project

Copy the following files/directories:

- `scripts/log_filter/`
- `scripts/log_filter_entry.py`
- `scripts/requirements*.txt`
- `scripts/config.json`
- `references/`
- `assets/`
- `scripts/tests/`
- `scripts/test-logs/` (optional sample logs for local checks)
