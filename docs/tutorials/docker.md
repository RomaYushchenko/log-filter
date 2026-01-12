# Docker Tutorial: Containerized Log Filtering

**Duration:** 15 minutes  
**Level:** Intermediate  
**Prerequisites:** Docker installed, basic Docker knowledge  
**Last Updated:** January 8, 2026

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- ✅ Build Log Filter Docker images
- ✅ Run Log Filter in containers
- ✅ Mount volumes for logs and configuration
- ✅ Configure resource limits
- ✅ Use multi-stage builds for optimization
- ✅ Deploy with Docker Compose
- ✅ Troubleshoot container issues

---

## Part 1: Basic Docker Image (3 minutes)

### Step 1: Create Dockerfile

Create a simple Dockerfile:

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install log-filter
RUN pip install --no-cache-dir log-filter

# Set working directory
WORKDIR /app

# Run as non-root user
RUN useradd -m -u 1000 logfilter && \
    chown -R logfilter:logfilter /app
USER logfilter

# Default command
CMD ["log-filter", "--help"]
```

### Step 2: Build Image

```bash
docker build -t log-filter:latest .
```

**Output:**
```
[+] Building 15.2s (8/8) FINISHED
 => [1/4] FROM python:3.10-slim
 => [2/4] RUN pip install log-filter
 => [3/4] WORKDIR /app
 => [4/4] RUN useradd -m logfilter
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to docker.io/library/log-filter:latest
```

### Step 3: Test Image

```bash
docker run --rm log-filter:latest --version
```

---

## Part 2: Running with Volumes (4 minutes)

### Step 1: Create Directory Structure

```bash
mkdir -p demo-docker/{logs,output,config}
cd demo-docker
```

### Step 2: Create Sample Logs

```bash
cat > logs/app.log << 'EOF'
2026-01-08 10:00:00 INFO Application started
2026-01-08 10:01:00 ERROR Database connection failed
2026-01-08 10:02:00 WARNING Cache miss
2026-01-08 10:03:00 ERROR Payment timeout
2026-01-08 10:04:00 INFO Request processed
EOF
```

### Step 3: Create Configuration

```yaml
# config/config.yaml
search:
  expression: "ERROR"
  ignore_case: false

files:
  path: /logs
  include_patterns:
    - "*.log"

output:
  output_file: /output/errors.txt
  show_stats: true
```

### Step 4: Run Container with Volumes

```bash
docker run --rm \
  -v $(pwd)/logs:/logs:ro \
  -v $(pwd)/output:/output \
  -v $(pwd)/config:/config:ro \
  log-filter:latest \
  --config /config/config.yaml
```

**Output:**
```
Processing /logs/app.log...
Found 2 matches

Results written to: /output/errors.txt
================================================================================
Processing Statistics
================================================================================
Files:
  Processed:     1
  Matched:       1 (100.0%)

Records:
  Total:         5
  Matched:       2 (40.0%)
================================================================================
```

### Step 5: View Results

```bash
cat output/errors.txt
```

---

## Part 3: Production-Ready Dockerfile (3 minutes)

### Multi-Stage Build

Create an optimized Dockerfile with multi-stage build:

```dockerfile
# Dockerfile.production
# Stage 1: Build environment
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install log-filter and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir log-filter

# Stage 2: Runtime environment
FROM python:3.10-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create application user and directories
RUN useradd -m -u 1000 logfilter && \
    mkdir -p /logs /output /config && \
    chown -R logfilter:logfilter /logs /output /config

# Set working directory
WORKDIR /app

# Switch to non-root user
USER logfilter

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD test -f /output/.health || exit 1

# Default command
CMD ["log-filter", "--config", "/config/config.yaml"]
```

### Build Production Image

```bash
docker build -f Dockerfile.production -t log-filter:production .
```

**Benefits:**
- ✅ Smaller image size (~150 MB vs 250 MB)
- ✅ No build dependencies in final image
- ✅ Security: non-root user
- ✅ Health checks included

---

## Part 4: Docker Compose (3 minutes)

### Complete Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  log-filter:
    build:
      context: .
      dockerfile: Dockerfile.production
    image: log-filter:production
    container_name: log-filter
    
    # Volumes
    volumes:
      - ./logs:/logs:ro                    # Read-only log files
      - ./output:/output                    # Output directory
      - ./config/config.yaml:/config/config.yaml:ro  # Configuration
    
    # Environment variables
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_FILTER_CONFIG=/config/config.yaml
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
    
    # Restart policy
    restart: unless-stopped
    
    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    # Health check
    healthcheck:
      test: ["CMD", "test", "-f", "/output/.health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
```

### Run with Docker Compose

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop service
docker-compose down
```

---

## Part 5: Advanced Configurations (2 minutes)

### Scheduled Processing with Cron

```yaml
# docker-compose-cron.yml
version: '3.8'

services:
  log-filter-daily:
    image: log-filter:production
    container_name: log-filter-cron
    
    volumes:
      - ./logs:/logs:ro
      - ./output:/output
      - ./config/daily-config.yaml:/config/config.yaml:ro
      - ./scripts/cron-entry.sh:/app/run.sh:ro
    
    command: crond -f -d 8
    
    restart: unless-stopped
```

**Cron script:**
```bash
#!/bin/bash
# scripts/cron-entry.sh

# Add cron job
echo "0 1 * * * cd /app && log-filter --config /config/config.yaml" | crontab -

# Start cron
exec crond -f -d 8
```

### Multi-Container Setup

```yaml
# docker-compose-multiservice.yml
version: '3.8'

services:
  # Filter errors
  filter-errors:
    image: log-filter:production
    volumes:
      - logs:/logs:ro
      - errors:/output
    environment:
      - EXPRESSION=ERROR OR CRITICAL
    command: ["log-filter", "--expr", "${EXPRESSION}", "--input", "/logs", "--output", "/output/errors.txt"]
  
  # Filter warnings
  filter-warnings:
    image: log-filter:production
    volumes:
      - logs:/logs:ro
      - warnings:/output
    environment:
      - EXPRESSION=WARNING
    command: ["log-filter", "--expr", "${EXPRESSION}", "--input", "/logs", "--output", "/output/warnings.txt"]
  
  # Generate reports
  reporter:
    image: log-filter:production
    volumes:
      - logs:/logs:ro
      - reports:/output
    command: ["log-filter", "--input", "/logs", "--output", "/output/report.txt", "--stats"]
    depends_on:
      - filter-errors
      - filter-warnings

volumes:
  logs:
  errors:
  warnings:
  reports:
```

---

## Docker Best Practices

### Security

```dockerfile
# Use specific version tags
FROM python:3.10.8-slim

# Scan for vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Don't run as root
USER logfilter

# Use read-only filesystems where possible
```

```bash
# Scan image for vulnerabilities
docker scan log-filter:production
```

### Performance

```yaml
# docker-compose.yml
services:
  log-filter:
    # CPU pinning
    cpuset: "0-3"
    
    # Memory limits
    mem_limit: 4g
    mem_reservation: 2g
    
    # Use tmpfs for temporary files
    tmpfs:
      - /tmp
    
    # Optimize I/O
    storage_opt:
      size: '10G'
```

### Resource Monitoring

```bash
# Monitor container resources
docker stats log-filter

# Example output:
CONTAINER    CPU %     MEM USAGE / LIMIT     MEM %     NET I/O
log-filter   45.23%    1.5GiB / 4GiB        37.5%     1.2MB / 856kB
```

---

## Practice Exercises

### Exercise 1: Build and Run

Build a Docker image and process logs from `./logs` directory.

<details>
<summary>Solution</summary>

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.10-slim
RUN pip install log-filter
USER nobody
CMD ["log-filter"]
EOF

# Build
docker build -t my-log-filter .

# Run
docker run --rm \
  -v $(pwd)/logs:/logs:ro \
  -v $(pwd)/output:/output \
  my-log-filter \
  --expr "ERROR" \
  --input /logs \
  --output /output/errors.txt
```
</details>

### Exercise 2: Docker Compose with Multiple Services

Create a Docker Compose setup that filters ERROR and WARNING logs separately.

<details>
<summary>Solution</summary>

```yaml
# docker-compose.yml
version: '3.8'

services:
  errors:
    image: log-filter:latest
    volumes:
      - ./logs:/logs:ro
      - ./output:/output
    command: ["log-filter", "--expr", "ERROR", "--input", "/logs", "--output", "/output/errors.txt"]
  
  warnings:
    image: log-filter:latest
    volumes:
      - ./logs:/logs:ro
      - ./output:/output
    command: ["log-filter", "--expr", "WARNING", "--input", "/logs", "--output", "/output/warnings.txt"]
```

```bash
docker-compose up
```
</details>

### Exercise 3: Scheduled Processing

Set up a container that processes logs every hour.

<details>
<summary>Solution</summary>

```dockerfile
# Dockerfile.cron
FROM python:3.10-slim
RUN pip install log-filter && apt-get update && apt-get install -y cron
COPY crontab /etc/cron.d/logfilter-cron
RUN chmod 0644 /etc/cron.d/logfilter-cron && crontab /etc/cron.d/logfilter-cron
CMD ["cron", "-f"]
```

```
# crontab
0 * * * * log-filter --config /config/config.yaml >> /var/log/cron.log 2>&1
```
</details>

---

## Troubleshooting

### Problem: Permission Denied

**Error:**
```
Error: Permission denied: '/output/errors.txt'
```

**Solution:**
```bash
# Fix ownership
docker run --rm \
  -v $(pwd)/output:/output \
  --user $(id -u):$(id -g) \
  log-filter:latest \
  --expr "ERROR" --input /logs --output /output/errors.txt
```

### Problem: Volume Not Mounting

**Diagnosis:**
```bash
# Check volume mounts
docker inspect log-filter | grep -A 10 Mounts
```

**Solution:**
```bash
# Use absolute paths
docker run --rm \
  -v "$(pwd)/logs:/logs:ro" \
  -v "$(pwd)/output:/output" \
  log-filter:latest
```

### Problem: Container Exits Immediately

**Diagnosis:**
```bash
# Check logs
docker logs log-filter

# Run interactively
docker run --rm -it log-filter:latest /bin/bash
```

---

## Deployment Checklist

- [ ] Build optimized image with multi-stage build
- [ ] Scan image for vulnerabilities
- [ ] Configure resource limits
- [ ] Set up health checks
- [ ] Use non-root user
- [ ] Mount volumes correctly
- [ ] Configure logging
- [ ] Test with sample data
- [ ] Set up monitoring
- [ ] Document configuration

---

## What's Next?

You've mastered Docker deployment! 🎉

### Next Steps:

1. **[Kubernetes Tutorial](kubernetes.md)** - Scale to production
2. **[Integration Guide](../integration_guide.md)** - CI/CD pipelines
3. **[Advanced Tutorial](advanced.md)** - Production patterns
4. **[Examples](../examples/)** - Real-world use cases

---

**Tutorial Version:** 1.0  
**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
