# Test Logs Directory

This directory is used for storing test log files when running log-filter locally with Docker.

## Quick Setup

### Create Sample Log Files

```powershell
# Create a sample application log
@"
2026-01-13 10:00:00 INFO Application started
2026-01-13 10:01:23 ERROR Database connection failed: Connection timeout
2026-01-13 10:02:15 WARNING Cache miss for key: user_123
2026-01-13 10:03:45 ERROR Failed to process request: timeout after 30s
2026-01-13 10:04:12 INFO Request processed successfully
2026-01-13 10:05:33 CRITICAL System overload detected - CPU at 98%
2026-01-13 10:06:00 ERROR Database query failed: syntax error near 'SELECT'
2026-01-13 10:07:15 INFO Background job completed
"@ | Out-File -FilePath "test-logs\app.log" -Encoding UTF8

# Create a system log
@"
2026-01-13 09:00:00 INFO System boot complete
2026-01-13 09:30:00 WARNING High memory usage: 85%
2026-01-13 10:00:00 ERROR Failed to start service: nginx
2026-01-13 10:15:00 INFO Service nginx started successfully
2026-01-13 11:00:00 CRITICAL Disk space critically low: 95% used
"@ | Out-File -FilePath "test-logs\system.log" -Encoding UTF8
```

### Add Your Own Logs

Simply copy your log files to this directory:

```powershell
# Copy logs from another location
Copy-Item "C:\MyApp\logs\*.log" test-logs\

# Or move them
Move-Item "C:\MyApp\logs\error.log" test-logs\
```

## Usage with Docker

Once you have log files in this directory:

```powershell
# Search for errors
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  log-filter:latest \
  ERROR /logs -o /output/errors.txt --stats

# Using Docker Compose
docker-compose -f docker-compose.local.yml run --rm log-filter-local
```

## Supported Formats

- Plain text log files (*.log, *.txt)
- Compressed logs (*.log.gz) - if enabled
- Any text-based log format

## Git Ignore

This directory is in .gitignore, so your test logs won't be committed. Only this README is tracked.

## Cleanup

To remove all test logs:

```powershell
# Remove all log files but keep the directory
Get-ChildItem test-logs\*.log | Remove-Item
```
