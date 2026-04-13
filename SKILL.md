---
name: log-filter
description: "Use this skill for ANY log-related task — searching, investigating errors, tracing entities, debugging incidents, or analyzing application behavior. Always trigger on: 'investigate error', 'find in logs', 'debug logs', 'check logs', 'what happened in logs', 'trace container/shipment/move/segment', 'service errors', 'why did X fail', 'find exception', 'search logs'. When in doubt — use this skill. Never generate PowerShell or shell scripts for log searching; always use run_filter() Python API instead"
allowed-tools: Read, Bash(python:*)
dependencies: pyyaml>=6.0, tqdm>=4.66.0
---

# Log Investigator Skill

This skill searches and analyzes logs using `run_filter()` from the `log_filter` Python package.

Key rule:
- Never generate PowerShell, CMD, or shell scripts for log searching.
- Always use `run_filter_runner.py` for investigations from chat sessions.
- Creating temporary Python files for investigation is prohibited (for example, `move_investigation.py`, `tmp_*.py`).
- Only existing skill files are allowed. Do not create helper scripts or ad-hoc runners.
- Never use `Get-ChildItem`, `Select-String`, `grep`, `findstr`, or direct file reads as a substitute for filtering.

## Configuration (fill once)

**IMPORTANT:** All Python commands must use the virtual environment.

Windows path rule (depends on current directory):
- If `cwd` is `REPO_ROOT/.github/skills/log-filter`, use `./venv/Scripts/python.exe`.
- If `cwd` is `REPO_ROOT`, use `./.github/skills/log-filter/venv/Scripts/python.exe`.
- Do not use `./venv/Scripts/python.exe` from `REPO_ROOT` (there is `./.venv` there, not skill `venv`).

PowerShell execution rule:
- For explicit executable paths in pipelines, use the call operator `&`.

Base paths:
- `REPO_ROOT`: repository root
- `SKILL_LOGS_PATH`: `REPO_ROOT/.github/skills/log-filter/scripts/input-logs`
- `REPO_LOGS_PATHS`: `REPO_ROOT/logs`, `REPO_ROOT/logs-dev`
- `OUTPUT_PATH`: `REPO_ROOT/.github/skills/log-filter/scripts/output`

Path resolution rule:
- Default: use relative paths (`./scripts/input-logs`, `./scripts/output`)
- Override: if the user provides an absolute path, use it as-is with no modification
- Never mix: do not convert a user-provided absolute path to relative

If these paths are not set in context, ask the user before the first run.

## Step 0 - Initialization (fill once)

 **Initialize virtual environment:**
   - If current folder is REPO_ROOT:
     ```bash
     Set-Location ./.github/skills/log-filter
     ./init.bat
     ```
   - If current folder is already REPO_ROOT/.github/skills/log-filter:
     ```bash
     ./init.bat
     ```
   This creates venv and installs dependencies (pyyaml, tqdm).

  **Do not duplicate path in Set-Location:**
  - Wrong from skill folder: `Set-Location ./.github/skills/log-filter` (creates non-existing nested path)
  - Correct from skill folder: keep current directory and run `./init.bat`

  **Stable launch templates (PowerShell):**
  - From REPO_ROOT:
    `'<EXPRESSION>' | & ./.github/skills/log-filter/venv/Scripts/python.exe ./.github/skills/log-filter/scripts/run_filter_runner.py --expression-stdin --output-file ./.github/skills/log-filter/scripts/output/custom-investigation.log`
  - From REPO_ROOT/.github/skills/log-filter:
		`'<EXPRESSION>' | & ./venv/Scripts/python.exe ./scripts/run_filter_runner.py --expression-stdin --output-file ./scripts/output/custom-investigation.log`

  **CWD hard-stop rule (mandatory before each run):**
	- If `cwd` is `REPO_ROOT`, use the REPO_ROOT template.
	- If `cwd` is `REPO_ROOT/.github/skills/log-filter`, use the skill-folder template.
	- Do not use `Set-Location ./.github/skills/log-filter` when already inside `REPO_ROOT/.github/skills/log-filter`.
	- If `Set-Location` throws any error, treat the step as failed and rerun with the correct template.
	- Do not continue investigation from partially failed commands.

Before the first filter run, always validate the logs path and do not run `run_filter` until the path is valid.

## Step 1 - Validate logs path and determine search scope

Preflight rules:
1. Determine `repo_root` (workspace root).
2. Start with the default relative logs path `./scripts/input-logs` (resolved from the skill folder); if the user provided an absolute logs path, validate that path instead.
3. If the folder exists, always run the first search only there.
4. If there are no matches there, move to repository logs: first `repo_root/logs`, then `repo_root/logs-dev`.
5. If no folder exists, ask one short clarifying question to the user about the actual path.

Goal: stable search priority without random directory selection.

Canonical execution rule:
- For investigations, run exactly one command first: `python ./.github/skills/log-filter/scripts/run_filter_runner.py ...`.
- Do not manually orchestrate fallback across `./logs` and `./logs-dev` in shell logic; the runner handles fallback order.
- Do not pass `--logs-path` unless the user explicitly requested an exact directory.
- In persistent terminal sessions, re-evaluate `cwd` before every runner invocation and select the matching template.
- Navigation errors are fatal for the current step; do not parse or summarize output from that failed invocation.

Long-running execution policy:
- For log filtering commands, always use one synchronous terminal execution that waits for completion.
- In VS Code tool terms: use `run_in_terminal` with `mode=sync` and `timeout=0` so the tool blocks until the script finishes.
- Do not implement tight polling loops with repeated `get_terminal_output` calls while waiting for normal completion.
- Use async + `get_terminal_output` only as a fallback when synchronous waiting is unavailable; in that case, poll with sparse cadence (for example every 30-60 seconds), not continuously.

## Step 2 - Understand the task

Always determine:
- What to search: keyword, phrase, error type, ID.
- Period: date or date range.
- Time: time window if needed.
- Log level: `ERROR`, `WARN`, `INFO`, etc.

If the context is clear from the request, do not ask unnecessary follow-up questions and proceed immediately.

## Step 3 - Build the search expression

The `search.expression` field supports `AND`, `OR`, `NOT`, parentheses, and quoted phrases. Use [filter-expression-language.md](./references/04-filter-expression-language.md) page as a reference for constructing expressions.

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

## Step 4 - Choose API level (3-tier hierarchy)

Use only the public API and choose by scenario:

1) Fast default for typical service failures:
- `from log_filter import run_filter_service_errors`
- `output_paths = run_filter_service_errors(logs_path=..., output_file=...)`

2) Default for most investigations (dates/time/level/expression):
- `from log_filter import search_logs`
- `output_paths = search_logs(logs_path=..., output_file=..., expression=..., date_from=..., date_to=..., time_from=..., time_to=..., level=[...], ignore_case=..., regex=..., word_boundary=..., strip_quotes=..., max_workers=None)`

3) Advanced only (custom config and full control):
- `from log_filter import run_filter`
- `output_paths = run_filter(config_json)`

Compatibility with VS Code + PowerShell:
- Use `run_filter_runner.py` as the default entrypoint.
- Do not rely on shell scripts or grep pipelines.
- Do not create new runner files for one-off searches; use the existing `run_filter_runner.py`.
- If the expression contains spaces/quotes/parentheses, do not use `--expression`; use `--expression-stdin` (preferred) or `--expression-file`.
- Avoid long `python -c` commands for filtering.
- If `--expression-file` is used in PowerShell, avoid BOM (recommended `Set-Content -Encoding utf8NoBOM` in PowerShell 7+).

Execution requirements:
- Add `scripts` to `sys.path` before import.
- Use relative paths by default: `./scripts/input-logs` for `files.path` and `./scripts/output/...` for `output.output_file`.
- If the user provided an absolute `logs_path` or `output_file`, use it as-is without converting it to relative.
- Unless the user explicitly asked for a different path, `output.output_file` must be only in `OUTPUT_PATH`.

## Search order & retry rules
1. Default command must omit `--logs-path` so the runner starts with `./scripts/input-logs`.
2. If default search returns `output_paths == []`, rely on the runner's built-in fallback to `./logs`, then `./logs-dev`.
3. Do not manually re-run stage-by-stage for fallback unless debugging runner behavior itself.
4. If user provided explicit logs path, pass `--logs-path` and, when required, `--strict-logs-path`; skip fallback.
5. If all stages return `[]`, report no matches and suggest minimal filter expansion.
6. If a provided path does not exist, correct the path once and retry.

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
		"path": "<LOGS_PATH>",  # default: ./scripts/input-logs; keep user-provided absolute path as-is
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
		"verbose": True,
		"quiet": True,
		"dry_run": False,
		"dry_run_details": False,
		"max_records_per_file": 500,
		"output_file_pattern": "{base}-{index:03d}{ext}",
		"sort_by_timestamp": True
	},
	"processing": {
		"max_workers": None,  # auto-detect based on CPU count
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

## Step 5 - Read results

Always read exactly the paths returned by `run_filter()`.

Reading rules:
- For large results, read in chunks (start with ~8000 characters).
- If `output_paths = []`, state that there are no matches and suggest a minimal filter expansion.

## Step 6 - Analyze and respond

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
- Container tracking: `(container OR "container number" OR "containerNumber" OR "intermidalUnitNumber" OR "IMUNumber" OR "intermodalUnit") AND "<ID>"`
- Move tracking: `(move OR "moveId" OR "move ID") AND "<ID>"`
- Segment tracking: `(segment OR "segment id" OR "segmentId") AND "<ID>"`
- Equipment tracking: `(equipment OR "equipment id" OR "equipmentNumber") AND "<ID>"`

## Paths And Output Rules

Apply the Path resolution rule from the Configuration section.

Default values:
- `files.path = ./scripts/input-logs`
- `output.output_file = ./scripts/output/filter-result.log`

Override priority:
1. If the user provided an absolute `logs` path, use it as `files.path` with no modification.
2. Otherwise use default `./scripts/input-logs`.
3. If the user provided an absolute `output` path, use it as `output.output_file` with no modification.
4. Otherwise use default `./scripts/output/filter-result.log`.
5. Never convert a user-provided absolute path to relative.
6. Do not independently choose other folders (for example `report/`) for `output.output_file` without an explicit user request.

File naming convention:
- Service errors -> `service-errors.log`
- Container, intermodalUnit -> `container-<ID>.log`
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

- Never generate PowerShell/CMD/bash for log searching — always use Python API.
- Never read log files directly without run_filter().
- Never use direct shell text search (`Select-String`, `grep`, `findstr`) for investigative filtering.
- Never use workspace text search (`grep_search`) as investigative fallback after a runner command; refine expression and rerun the runner instead.
- If a runner command emits `Set-Location`/path errors, stop and rerun with corrected `cwd` template before any analysis.
- Always quote specific log lines in conclusions.
- Always include output_paths at the end of the response.


## Output Format
```
##  Search Results
 
**Query**: {expression}
**Period**: {date.from} — {date.to}
**Result files**: {count from output_paths}
 
---
 
## 🔍 What Was Found
 
[Brief description — patterns, frequency, time of first/last error]
 
## 🚨 Critical Issues
 
[Most serious errors with specific log lines]
 
## 🔗 Root cause (possible cause)
 
[Hypothesis based on the sequence of events in the logs]
 
## ✅ Recommended Actions
 
1. ...
 
## 📁 Result Files
{list of paths from output_paths}
```
 
Always quote specific log lines — not just the overall summary.
 
---

## References

- [quick-start.md](./references/01-quick-start.md) — read on first run or env setup issues
- [public-api-contract.md](./references/09-public-api-contract.md) — read when run_filter() returns unexpected results
- [config-json-reference.md](./references/03-config-json-reference.md) — read when building advanced config_json
- [filter-expression-language.md](./references/04-filter-expression-language.md) — read when constructing complex AND/OR/NOT expressions
- [recipes-and-examples.md](./references/05-recipes-and-examples.md) — read when user needs a non-standard search scenario
- [troubleshooting.md](./references/06-troubleshooting.md) — read when run_filter() throws an error
- [performance-tuning.md](./references/07-performance-tuning.md) — read when processing is slow or result set is too large
