# Configuration Directory

This directory contains configuration files for log-filter.

## Files

- **local.yaml** - Local development configuration (ready to use)
- **config.yaml.template** - Template in project root (copy as needed)

## Usage with Docker

### Using local.yaml

```powershell
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  -v ${PWD}/config:/config:ro \
  log-filter:latest \
  --config /config/local.yaml
```

### Using Docker Compose

```powershell
docker-compose -f docker-compose.local.yml run --rm log-filter-config
```

## Creating Custom Configurations

Copy the template from project root:

```powershell
Copy-Item ../config.yaml.template ./my-config.yaml
```

Then customize as needed and use:

```powershell
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  -v ${PWD}/config:/config:ro \
  log-filter:latest \
  --config /config/my-config.yaml
```

## Configuration Options

See [Configuration Documentation](../docs/configuration.md) for all available options.
