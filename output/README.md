# Output Directory

This directory is used by Docker containers to store filtered log results.

## Usage

When running log-filter with Docker:

```powershell
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  log-filter:latest \
  ERROR /logs -o /output/errors.txt
```

Results will appear in this directory.

## .gitignore

Add to your `.gitignore`:

```
output/*
!output/.gitkeep
!output/README.md
```
