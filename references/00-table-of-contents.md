# Log Filter References - Table of Contents

Single entrypoint for embedded documentation.

## Quick Links

- [Quick Start](./01-quick-start.md)
- [CLI Arguments Reference](./02-cli-arguments-reference.md)
- [Config JSON Reference](./03-config-json-reference.md)
- [Filter Expression Language](./04-filter-expression-language.md)
- [Recipes and Examples](./05-recipes-and-examples.md)
- [Troubleshooting](./06-troubleshooting.md)
- [Performance Tuning](./07-performance-tuning.md)
- [Skill Integration](./08-skill-integration.md)

## Recommended Reading Order

1. `01-quick-start.md`
2. `04-filter-expression-language.md`
3. `02-cli-arguments-reference.md`
4. `03-config-json-reference.md`
5. `05-recipes-and-examples.md`
6. `06-troubleshooting.md` and `07-performance-tuning.md`
7. `08-skill-integration.md`

## Short Use-Case Scenarios

### 1) Quick error search in local logs

Use when you need a fast error overview.

```bash
python scripts/log_filter_entry.py --expression "ERROR" --path ./logs --stats
```

Docs:
- `01-quick-start.md`
- `05-recipes-and-examples.md`

### 2) Find business events with multiple conditions

Use when you need precise event selection by term combinations.

```bash
python scripts/log_filter_entry.py \
  --expression "\"eventEntity\" AND (\"MOVE\" OR \"PLAN\") AND NOT test" \
  --path ./logs
```

Docs:
- `04-filter-expression-language.md`
- `05-recipes-and-examples.md`

### 3) Analyze a specific time window

Use when date/time constraints are required.

```bash
python scripts/log_filter_entry.py \
  --expression "ERROR" \
  --path ./logs \
  --from 2026-04-01 --to 2026-04-07 \
  --from-time 09:00:00 --to-time 18:00:00
```

Docs:
- `02-cli-arguments-reference.md`
- `03-config-json-reference.md`

### 4) Large logs with chunked output

Use when output volume is large and must stay manageable.

```bash
python scripts/log_filter_entry.py \
  --expression "(ERROR OR WARN) AND NOT healthcheck" \
  --path ./logs \
  --output ./output/result.log \
  --max-records-per-file 1000 \
  --workers 8 \
  --stats
```

Docs:
- `05-recipes-and-examples.md`
- `07-performance-tuning.md`

### 5) Validate configuration before full run

Use when you need a safe pre-check.

```bash
python scripts/log_filter_entry.py \
  --expression "ERROR" \
  --path ./logs \
  --dry-run-details
```

Docs:
- `01-quick-start.md`
- `06-troubleshooting.md`

### 6) Skill integration mode

Use when the tool is invoked by an agent/Skill as a backend command.

Recommendation:
- call only `python scripts/log_filter_entry.py ...`
- do not call internal modules directly

Docs:
- `08-skill-integration.md`

## Quick Pre-Run Checklist

- dependencies from `scripts/requirements-log-filter.txt` are installed
- logs path exists
- expression is provided (`--expression`) or configured in `scripts/config.json`
- for large datasets, tune `--workers` and chunking
