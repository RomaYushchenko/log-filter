# Recipes and Examples

## 1) All errors

```bash
python scripts/log_filter_entry.py --expression "ERROR" --path ./logs --stats
```

## 2) Errors and criticals, excluding tests

```bash
python scripts/log_filter_entry.py \
  --expression "(ERROR OR CRITICAL) AND NOT test" \
  --path ./logs
```

## 3) Date and time filtering

```bash
python scripts/log_filter_entry.py \
  --expression "ERROR" \
  --path ./logs \
  --from 2026-04-01 --to 2026-04-07 \
  --from-time 09:00:00 --to-time 18:00:00
```

## 4) Regex search for error codes

```bash
python scripts/log_filter_entry.py \
  --expression "ERR_[0-9]{4}" \
  --regex \
  --path ./logs
```

## 5) Exact word matching

```bash
python scripts/log_filter_entry.py \
  --expression "MOVE" \
  --exact-match \
  --path ./logs
```

## 6) Large datasets with chunked output

```bash
python scripts/log_filter_entry.py \
  --expression "ERROR OR WARN" \
  --path ./logs \
  --output ./output/result.log \
  --max-records-per-file 1000 \
  --output-pattern "{base}-{index:03d}{ext}" \
  --workers 8 \
  --stats
```

## 7) Dry-run before production run

```bash
python scripts/log_filter_entry.py \
  --expression "ERROR" \
  --path ./logs \
  --dry-run-details
```

## 8) Run from config

```bash
python scripts/log_filter_entry.py --config ./scripts/config.json
```
