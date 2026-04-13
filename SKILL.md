---
name: log-filter
description: "Use this skill whenever the user asks to investigate logs, find errors/events, or trace entities in logs. Trigger on phrases like: 'investigate error', 'find in logs', 'debug logs'. Always use Python API run_filter() from log_filter. Never generate PowerShell/CMD/shell scripts for log searching."
allowed-tools: Read, Bash(python:*)
dependencies: pyyaml>=6.0, tqdm>=4.66.0
---

# Log Investigator Skill

This skill searches and analyzes logs using `run_filter()` from the `log_filter` Python package.

Key rule:
- Never generate PowerShell, CMD, or shell scripts for log searching.
- Always use the Python call `run_filter(...)` or `run_filter_service_errors(...)`.
- Creating temporary Python files for investigation is prohibited (for example, `move_investigation.py`, `tmp_*.py`).
- Only existing skill files are allowed: `run_filter_runner.py` or a direct short Python API call without creating new files.

## Configuration (fill once)

Base paths:
- `REPO_ROOT`: repository root
- `SKILL_LOGS_PATH`: `REPO_ROOT/.github/skills/log-filter/scripts/input-logs`
- `REPO_LOGS_PATHS`: `REPO_ROOT/logs`, `REPO_ROOT/logs-dev`
- `OUTPUT_PATH`: `REPO_ROOT/.github/skills/log-filter/scripts/output`

If these paths are not set in context, ask the user before the first run.

## Step 0 - Path Preflight (required)

Before the first filter run, always validate the logs path and do not run `run_filter` until the path is valid.

Preflight rules:
1. Determine `repo_root` (workspace root).
2. Check `repo_root/.github/skills/log-filter/scripts/input-logs`.
3. If the folder exists, always run the first search only there.
4. If there are no matches there, move to repository logs: first `repo_root/logs`, then `repo_root/logs-dev`.
5. If no folder exists, ask one short clarifying question to the user about the actual path.

Goal: stable search priority without random directory selection.

## Step 1 - Understand the task

Always determine:
- What to search: keyword, phrase, error type, ID.
- Period: date or date range.
- Time: time window if needed.
- Log level: `ERROR`, `WARN`, `INFO`, etc.

If the context is clear from the request, do not ask unnecessary follow-up questions and proceed immediately.

## Step 2 - Build the search expression

The `search.expression` field supports `AND`, `OR`, `NOT`, parentheses, and quoted phrases.

Typical expressions:
- Single word: `ERROR`
- Phrase: `"database connection failed"`
- Either/or: `ERROR OR WARN`
- Both: `ERROR AND timeout`
- Exclude noise: `ERROR AND NOT Heartbeat`
- Complex: `(ERROR OR CRITICAL) AND (database OR payment)`

Additional modes:
- Exact match in JSON: enable `word_boundary: true` and `strip_quotes: true`.
- Regex: enable `regex: true`, example `ERR_[0-9]{3}`.

Level normalization:
- Processing must run with `processing.normalize_log_levels = true`.
- `E/W/I/D` are normalized to `ERROR/WARN/INFO/DEBUG`.

## Step 3 - Call run_filter()

Use only the public API:
- `from log_filter import run_filter`
- `output_paths = run_filter(expression, logs_path=..., output_file=...)`
- For the standard service-errors case: `run_filter_service_errors(logs_path=..., output_file=...)`

Compatibility with VS Code + PowerShell:
- Use a direct Python API call `run_filter(...)`.
- Do not rely on shell scripts or grep pipelines.
- Do not create new runner files for one-off searches; use the existing `run_filter_runner.py`.
- If running through `run_filter_runner.py` and the expression contains spaces/quotes/parentheses, do not use `--expression`; use `--expression-file` or `--expression-stdin`.
- For `--expression-file` in PowerShell, avoid BOM (recommended `Set-Content -Encoding utf8NoBOM` in PowerShell 7+).

Execution requirements:
- Add `scripts` to `sys.path` before import.
- Use absolute paths for `files.path` and `output.output_file`.
- Unless the user explicitly asked for a different path, `output.output_file` must be only in `OUTPUT_PATH`.

Search execution order:
1. Run `run_filter(...)` on `SKILL_LOGS_PATH` (`input-logs` in the skill folder).
2. If `output_paths` is empty, run `run_filter(...)` on `REPO_ROOT/logs`.
3. If still empty, run `run_filter(...)` on `REPO_ROOT/logs-dev`.
4. Merge results into one conclusion and include all `output_paths`.

Anti-retry rules:
- If `files.path` does not exist, fix the path and rerun only once for this stage.
- Do not run repeated retries with random relative paths.
- If the user specified a concrete `logs-path`, do not change it to other folders without explicit permission.
- If `argparse` returns `unrecognized arguments`, switch immediately to `--expression-file` (without extra `--expression` attempts).
- If execution fails, first adjust parameters of the existing `run_filter_runner.py`; do not switch to creating a new temporary script.

Minimal `config_json` template:

```python
{
	"search": {
		"expression": "ERROR AND database",
		"ignore_case": False,
		"regex": False,
		"word_boundary": False,
		"strip_quotes": False
	},
	"files": {
		"path": "<LOGS_PATH>",
		"include_patterns": ["*.log", "*.log.gz"],
		"exclude_patterns": [],
		"max_file_size": None,
		"max_record_size": None
	},
	"date": {"from": None, "to": None},
	"time": {"from": None, "to": None},
	"output": {
		"output_file": "<OUTPUT_PATH>/filter-result.log",
		"no_path": False,
		"highlight": False,
		"stats": True,
		"verbose": False,
		"quiet": True,
		"dry_run": False,
		"dry_run_details": False,
		"max_records_per_file": 500,
		"output_file_pattern": "{base}-{index:03d}{ext}",
		"sort_by_timestamp": True
	},
	"processing": {
		"max_workers": 8,
		"debug": False,
		"normalize_log_levels": True,
		"sort_input_files": True
	}
}
```

What `run_filter()` returns:
- `list[str]`: absolute paths to result files.
- `[]`: if there are no matches or if `dry_run`/`dry_run_details` is enabled.
- May return multiple files if chunking was triggered.

## Step 4 - Read results

Always read exactly the paths returned by `run_filter()`.

Reading rules:
- For large results, read in chunks (start with ~8000 characters).
- If `output_paths = []`, state that there are no matches and suggest a minimal filter expansion.

## Step 5 - Analyze and respond

Response structure:
- Search results: expression, period, number of result files.
- What was found: key patterns, frequency, first/last event.
- Critical issues: specific log lines with evidence.
- Possible cause (hypothesis): based only on events in logs.
- Recommended actions.
- List of `output_paths`.

Never state a cause without evidence in logs.

## Intent Mapping

- Service errors: `(ERROR OR CRITICAL OR FATAL OR EXCEPTION) AND NOT test`
- Container tracking: `(container OR "container number" OR "containerNumber") AND "<ID>"`
- Shipment tracking: `(shipment OR "shipment number" OR "shipmentNumber") AND "<ID>"`
- Move tracking: `(move OR "move number" OR "moveNumber" OR "moveId") AND "<ID>"`
- Segment tracking: `(segment OR "segment id" OR "segmentId") AND "<ID>"`
- Equipment tracking: `(equipment OR "equipment id" OR "equipmentNumber") AND "<ID>"`

## Paths And Output Rules

Default values:
- `files.path = ./scripts/input-logs`
- `output.output_file = ./scripts/output/filter-result.log`

Override priority:
1. If the user provided a `logs` path, use it as `files.path`.
2. Otherwise use default `./scripts/input-logs`.
3. If the user provided an `output` path, use it as `output.output_file`.
4. Otherwise use default `./scripts/output/filter-result.log`.
5. Do not independently choose other folders (for example `report/`) for `output.output_file` without an explicit user request.

File naming convention:
- Service errors -> `service-errors.log`
- Container -> `container-<ID>.log`
- Shipment -> `shipment-<ID>.log`
- Move -> `move-<ID>.log`
- Segment -> `segment-<ID>.log`
- Equipment -> `equipment-<ID>.log`
- Custom expression -> `custom-investigation.log`

ID sanitization: replace spaces and special characters with `-`.

## Error Handling

- `ConfigurationError`: invalid/incomplete config (often `search.expression`, `files.path`).
- `ValueError`: invalid values (paths, range formats, date/time).
- Other exceptions: processing execution error; return diagnostics without inventing causes.

## Response Contract

Always return:
1. Scope: `search.expression`, `files.path`, `date/time` bounds.
2. Number of output files and the output directory.
3. Absolute `output_paths` from `run_filter()`.
4. Dry-run flags: `output.dry_run` and `output.dry_run_details`.
5. Key findings with quotes of specific log lines.
6. Confidence level and gaps (if evidence is limited).

## Analysis Quality Checks

- Do not claim root cause without direct evidence in logs.
- Prioritize timestamps and exact log lines.
- If events are conflicting, present both and mark uncertainty.
- If the result is empty, suggest the smallest filter expansion.

## Rules

- Prohibited: generating PowerShell/CMD/bash scripts for log search.
- Prohibited: creating any temporary Python scripts for log search (for example `move_investigation.py`).
- Prohibited: reading raw logs directly without `run_filter()`.
- Required: use Python + public API `run_filter(...)`.
- Required: use the short API (`run_filter(expression, logs_path, output_file)`) or `run_filter_service_errors(...)`.
- Required: use the existing `run_filter_runner.py` (or a direct short API call without creating new files).
- Required: search first in the skill's `input-logs` folder, then in repository `logs`, then `logs-dev` (if the previous step is empty).
- Required: if the user did not specify another `output` path, store results only in `.github/skills/log-filter/scripts/output`.
- Prohibited: changing output folder to `report` or any other folder outside `scripts/output` without explicit user instruction.
- Required: include quoted log lines in conclusions.
- Required: include `output_paths` at the end of the response.

## References

- [references/00-table-of-contents.md](./references/00-table-of-contents.md) - unified navigation and quick use cases
- [references/01-quick-start.md](./references/01-quick-start.md) - venv / init.bat, sys.path, first run_filter call
- [references/09-public-api-contract.md](./references/09-public-api-contract.md) - authoritative API: run_filter, return values, errors
- [references/02-cli-arguments-reference.md](./references/02-cli-arguments-reference.md) - JSON configuration fields and legacy CLI mapping
- [references/03-config-json-reference.md](./references/03-config-json-reference.md) - config.json structure and fields
- [references/04-filter-expression-language.md](./references/04-filter-expression-language.md) - expression language (AND, OR, NOT, parentheses)
- [references/05-recipes-and-examples.md](./references/05-recipes-and-examples.md) - practical filtering examples (Python)
- [references/06-troubleshooting.md](./references/06-troubleshooting.md) - common issues and fixes
- [references/07-performance-tuning.md](./references/07-performance-tuning.md) - performance optimization guidance
- [references/08-skill-integration.md](./references/08-skill-integration.md) - skill integration guide (API)
