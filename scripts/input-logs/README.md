# Input Logs Directory

This directory is the default location for investigation input logs.

## Purpose

- Put logs to be searched by `run_filter(config_json)` in this folder.
- Default config path: `./scripts/input-logs`.
- You can override the path per investigation by setting `files.path`.

## Quick usage

```powershell
# Run from .github/skills/log-filter
Copy-Item "C:\MyApp\logs\*.log" .\scripts\input-logs\

# Prefer the stable runner over long python -c or here-string snippets
"ERROR" | ..\..\..\.venv\Scripts\python.exe .\scripts\run_filter_runner.py --mode expression --expression-stdin --output-file .\scripts\output\filter-result.log

# For complex expressions with quotes/parentheses use a file instead of inline code
Set-Content -Path .\scripts\output\expression.txt -Value '(ERROR OR WARN) AND "timeout"'
..\..\..\.venv\Scripts\python.exe .\scripts\run_filter_runner.py --mode expression --expression-file .\scripts\output\expression.txt --output-file .\scripts\output\filter-result.log
```
