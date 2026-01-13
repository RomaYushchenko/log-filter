# Deployment Guide

Deploy log-filter in production environments.

## Deployment Options

- **[Standalone](#standalone-deployment)** - Direct installation on servers
- **[Docker](#docker-deployment)** - Containerized deployment
- **[Kubernetes](#kubernetes-deployment)** - Orchestrated deployment
- **[Cron Jobs](#scheduled-execution)** - Scheduled monitoring
- **[Systemd](#systemd-service)** - Background service

## Standalone Deployment

### System Requirements

**Minimum:**
- Python 3.10+
- 1 GB RAM
- 1 CPU core
- 100 MB disk space

**Recommended:**
- Python 3.12+
- 2 GB RAM
- 4 CPU cores
- 1 GB disk space

### Installation

```bash
# Install via pip
pip install log-filter

# Verify installation
log-filter --version
python -c "import log_filter; print(log_filter.__version__)"
```

### Production Configuration

Create `/etc/log-filter/config.yaml`:

```yaml
search:
  expression: "ERROR OR CRITICAL"
  ignore_case: false

files:
  search_root: "/var/log"
  include_patterns:
    - "*.log"
  exclude_patterns:
    - "*.gz"
    - "*.zip"
  max_depth: 3

output:
  output_file: "/var/log-filter/errors.txt"
  overwrite: true
  stats: true
  quiet: false

processing:
  max_workers: 8
  buffer_size: 32768
  encoding: "utf-8"
  errors: "replace"
```

Set permissions:

```bash
sudo mkdir -p /etc/log-filter /var/log-filter
sudo chown -R logfilter:logfilter /var/log-filter
sudo chmod 755 /etc/log-filter
sudo chmod 644 /etc/log-filter/config.yaml
```

## Docker Deployment

### Building Image

**From source:**

```bash
# Clone repository
git clone https://github.com/your-org/log-filter.git
cd log-filter

# Build image
docker build -t log-filter:2.0.0 .

# Tag for registry
docker tag log-filter:2.0.0 your-registry/log-filter:2.0.0
```

**From Docker Hub:**

```bash
# Pull official image
docker pull log-filter/log-filter:2.0.0

# Or pull latest
docker pull log-filter/log-filter:latest
```

### Running Container

**Basic usage:**

```bash
docker run --rm \
  -v /var/log:/logs:ro \
  -v $(pwd)/output:/output \
  log-filter:2.0.0 \
  "ERROR" "/logs" "-o" "/output/errors.txt"
```

**With configuration file:**

```bash
docker run --rm \
  -v /var/log:/logs:ro \
  -v $(pwd)/output:/output \
  -v $(pwd)/config:/config:ro \
  log-filter:2.0.0 \
  --config /config/config.yaml
```

**With environment variables:**

```bash
docker run --rm \
  -v /var/log:/logs:ro \
  -v $(pwd)/output:/output \
  -e LOG_FILTER_WORKERS=8 \
  -e LOG_FILTER_BUFFER_SIZE=32768 \
  -e LOG_FILTER_VERBOSE=true \
  log-filter:2.0.0 \
  "ERROR" "/logs" "-o" "/output/errors.txt"
```

**Interactive mode:**

```bash
docker run --rm -it \
  -v /var/log:/logs:ro \
  log-filter:2.0.0 \
  "ERROR" "/logs"
```

### Local Machine Setup (Windows/Mac/Linux)

**For local development and testing:**

#### Step 1: Prepare Environment

```powershell
# Create directories
New-Item -ItemType Directory -Force -Path "output", "config", "test-logs"

# Copy template config (if needed)
Copy-Item config.yaml.template config/local.yaml
```

#### Step 2: Add Test Logs

Place your log files in the `test-logs/` directory or create sample logs:

```powershell
# Example: Create sample log file
@"
2026-01-13 10:00:00 INFO Application started
2026-01-13 10:01:23 ERROR Database connection failed
2026-01-13 10:02:15 WARNING Cache miss for key: user_123
2026-01-13 10:03:45 ERROR Failed to process request: timeout
2026-01-13 10:05:33 CRITICAL System overload detected
"@ | Out-File -FilePath "test-logs\app.log" -Encoding UTF8
```

#### Step 3: Run with Local Configuration

```powershell
# Option A: Using docker-compose.local.yml (recommended)
docker-compose -f docker-compose.local.yml run --rm log-filter-local

# Option B: Using docker run
docker run --rm \
  -v ${PWD}/test-logs:/logs:ro \
  -v ${PWD}/output:/output \
  log-filter:latest \
  ERROR /logs -o /output/errors.txt --stats
```

#### Development Mode

For live code editing:

```powershell
# Build dev image
docker-compose -f docker-compose.dev.yml build

# Run with mounted source code
docker-compose -f docker-compose.dev.yml run --rm log-filter-dev \
  ERROR /logs -o /output/errors.txt --stats
```

**Windows Users**: Use PowerShell and `${PWD}` for current directory paths.  
**Linux/Mac Users**: Use `$(pwd)` instead of `${PWD}`.

**Complete Guide**: See [Docker Local Setup Analysis](../.github/docs/analize/docker-local-setup-analysis.md) for comprehensive instructions, troubleshooting, and best practices.

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  log-filter:
    image: log-filter:2.0.0
    volumes:
      - /var/log:/logs:ro
      - ./output:/output
      - ./config:/config:ro
    environment:
      - LOG_FILTER_WORKERS=8
      - LOG_FILTER_BUFFER_SIZE=32768
    command: ["--config", "/config/config.yaml"]
```

Run:

```bash
# One-time execution
docker-compose run --rm log-filter

# Background service
docker-compose up -d log-filter

# View logs
docker-compose logs -f log-filter

# Stop
docker-compose down
```

### Resource Limits

```bash
docker run --rm \
  --memory="1g" \
  --cpus="2.0" \
  -v /var/log:/logs:ro \
  log-filter:2.0.0 \
  "ERROR" "/logs"
```

Or in `docker-compose.yml`:

```yaml
services:
  log-filter:
    image: log-filter:2.0.0
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
```

## Kubernetes Deployment

### Prerequisites

```bash
# Create namespace
kubectl create namespace log-filter

# Create config map
kubectl create configmap log-filter-config \
  --from-file=config.yaml \
  -n log-filter
```

### CronJob Deployment

Create `cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-filter-hourly
  namespace: log-filter
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: log-filter
            image: log-filter:2.0.0
            args: ["--config", "/config/config.yaml"]
            volumeMounts:
              - name: logs
                mountPath: /logs
                readOnly: true
              - name: output
                mountPath: /output
              - name: config
                mountPath: /config
            resources:
              requests:
                memory: "256Mi"
                cpu: "500m"
              limits:
                memory: "1Gi"
                cpu: "2000m"
          volumes:
            - name: logs
              hostPath:
                path: /var/log
            - name: output
              persistentVolumeClaim:
                claimName: log-filter-output
            - name: config
              configMap:
                name: log-filter-config
          restartPolicy: OnFailure
```

Deploy:

```bash
kubectl apply -f cronjob.yaml

# Verify
kubectl get cronjobs -n log-filter
kubectl get jobs -n log-filter

# View logs
kubectl logs -n log-filter job/log-filter-hourly-<timestamp>
```

### One-Shot Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: log-filter-oneshot
  namespace: log-filter
spec:
  template:
    spec:
      containers:
      - name: log-filter
        image: log-filter:2.0.0
        args: ["ERROR", "/logs", "-o", "/output/errors.txt", "--stats"]
        volumeMounts:
          - name: logs
            mountPath: /logs
            readOnly: true
          - name: output
            mountPath: /output
      volumes:
        - name: logs
          hostPath:
            path: /var/log
        - name: output
          persistentVolumeClaim:
            claimName: log-filter-output
      restartPolicy: Never
```

Deploy:

```bash
kubectl apply -f job.yaml

# Monitor
kubectl get jobs -n log-filter
kubectl logs -n log-filter job/log-filter-oneshot
```

## Scheduled Execution

### Cron Jobs (Linux)

**Edit crontab:**

```bash
crontab -e
```

**Hourly error monitoring:**

```text
# Run every hour at minute 0
0 * * * * /usr/local/bin/log-filter "ERROR" /var/log -o /var/log-filter/errors-$(date +\%Y\%m\%d-\%H).txt --stats >> /var/log/log-filter.log 2>&1
```

**Daily full scan:**

```text
# Run daily at 2 AM
0 2 * * * /usr/local/bin/log-filter "(ERROR OR CRITICAL)" /var/log -o /var/log-filter/daily-$(date +\%Y\%m\%d).txt --stats >> /var/log/log-filter.log 2>&1
```

**Business hours monitoring:**

```text
# Run every 15 minutes during business hours (9 AM - 5 PM, Mon-Fri)
*/15 9-17 * * 1-5 /usr/local/bin/log-filter "ERROR" /var/log/app -o /var/log-filter/errors.txt --overwrite --stats
```

**With configuration file:**

```text
0 * * * * /usr/local/bin/log-filter --config /etc/log-filter/config.yaml >> /var/log/log-filter.log 2>&1
```

### Task Scheduler (Windows)

**Create scheduled task:**

```powershell
# Create basic task
$action = New-ScheduledTaskAction -Execute "log-filter" `
  -Argument '"ERROR" "C:\Logs" "-o" "C:\Output\errors.txt" "--stats"'

$trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
  -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "LogFilter-Daily" `
  -Action $action -Trigger $trigger -Principal $principal
```

**Run hourly:**

```powershell
$trigger = New-ScheduledTaskTrigger -Once -At "00:00" `
  -RepetitionInterval (New-TimeSpan -Hours 1) `
  -RepetitionDuration (New-TimeSpan -Days 365)

Register-ScheduledTask -TaskName "LogFilter-Hourly" `
  -Action $action -Trigger $trigger -Principal $principal
```

## Systemd Service

### Service Configuration

Create `/etc/systemd/system/log-filter.service`:

```ini
[Unit]
Description=Log Filter Monitoring Service
After=network.target

[Service]
Type=oneshot
User=logfilter
Group=logfilter
WorkingDirectory=/var/log-filter

# Use configuration file
ExecStart=/usr/local/bin/log-filter --config /etc/log-filter/config.yaml

# Environment
Environment="LOG_FILTER_WORKERS=8"
Environment="PYTHONUNBUFFERED=1"

# Logging
StandardOutput=append:/var/log/log-filter.log
StandardError=append:/var/log/log-filter.error.log

# Security
PrivateTmp=yes
NoNewPrivileges=yes
ReadOnlyPaths=/var/log
ReadWritePaths=/var/log-filter

[Install]
WantedBy=multi-user.target
```

### Timer Configuration

Create `/etc/systemd/system/log-filter.timer`:

```ini
[Unit]
Description=Log Filter Hourly Timer
Requires=log-filter.service

[Timer]
# Run hourly
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timer
sudo systemctl enable log-filter.timer

# Start timer
sudo systemctl start log-filter.timer

# Check status
sudo systemctl status log-filter.timer
sudo systemctl list-timers log-filter.timer

# View logs
sudo journalctl -u log-filter.service -f
```

### Manual Execution

```bash
# Run service manually
sudo systemctl start log-filter.service

# View logs
sudo journalctl -u log-filter.service
```

## Production Best Practices

### Security

**1. Run as non-root user:**

```bash
# Create dedicated user
sudo useradd -r -s /bin/false logfilter

# Set permissions
sudo chown -R logfilter:logfilter /var/log-filter
```

**2. Restrict file access:**

```bash
# Read-only log access
sudo chmod 755 /var/log
sudo setfacl -m u:logfilter:rx /var/log
```

**3. Secure configuration:**

```bash
# Protect config file
sudo chmod 600 /etc/log-filter/config.yaml
sudo chown logfilter:logfilter /etc/log-filter/config.yaml
```

### Monitoring

**1. Track execution:**

```bash
# Log all executions
log-filter "ERROR" /var/log --stats >> /var/log/log-filter-execution.log
```

**2. Monitor resource usage:**

```bash
# Check memory
ps aux | grep log-filter

# Check disk space
df -h /var/log-filter
```

**3. Alert on failures:**

```bash
# Wrap in script with error handling
#!/bin/bash
if ! log-filter --config /etc/log-filter/config.yaml; then
  echo "Log filter failed" | mail -s "Alert: Log Filter Failed" admin@example.com
fi
```

### Log Rotation

**Configure logrotate** (`/etc/logrotate.d/log-filter`):

```
/var/log-filter/*.txt {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 logfilter logfilter
}

/var/log/log-filter.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
}
```

### Performance Tuning

**1. Adjust workers based on load:**

```yaml
# /etc/log-filter/config.yaml
processing:
  max_workers: 8  # 2x CPU cores for I/O bound
```

**2. Optimize buffer size:**

```yaml
processing:
  buffer_size: 65536  # 64 KB for fast SSD
```

**3. Limit scope:**

```yaml
files:
  search_root: "/var/log"
  include_patterns:
    - "app*.log"    # Only app logs
  max_depth: 2       # Don't traverse deep
```

### Backup and Recovery

**1. Backup configuration:**

```bash
# Regular backup
sudo cp /etc/log-filter/config.yaml /etc/log-filter/config.yaml.bak

# Version control
cd /etc/log-filter
git init
git add config.yaml
git commit -m "Initial configuration"
```

**2. Backup results:**

```bash
# Daily backup to remote storage
rsync -avz /var/log-filter/ backup-server:/backups/log-filter/
```

## Cloud Deployments

### AWS

**EC2 Instance:**

```bash
# User data script
#!/bin/bash
pip install log-filter
mkdir -p /var/log-filter

# Configure
cat > /etc/log-filter/config.yaml << 'EOF'
search:
  expression: "ERROR"
files:
  search_root: "/var/log"
output:
  output_file: "/var/log-filter/errors.txt"
  stats: true
EOF

# Schedule with cron
echo "0 * * * * /usr/local/bin/log-filter --config /etc/log-filter/config.yaml" | crontab -
```

**Lambda Function:**

```python
import boto3
import subprocess

def lambda_handler(event, context):
    # Run log-filter
    result = subprocess.run([
        'log-filter',
        'ERROR',
        '/tmp/logs',
        '-o', '/tmp/errors.txt'
    ], capture_output=True, text=True)
    
    # Upload results to S3
    s3 = boto3.client('s3')
    s3.upload_file('/tmp/errors.txt', 'my-bucket', 'errors.txt')
    
    return {'statusCode': 200}
```

### Azure

**Container Instances:**

```bash
az container create \
  --resource-group log-filter-rg \
  --name log-filter \
  --image log-filter:2.0.0 \
  --cpu 2 \
  --memory 2 \
  --restart-policy Never \
  --environment-variables \
    LOG_FILTER_WORKERS=8 \
  --azure-file-volume-account-name mystorageaccount \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name logs \
  --azure-file-volume-mount-path /logs
```

### Google Cloud

**Cloud Run Job:**

```bash
gcloud run jobs create log-filter \
  --image gcr.io/project/log-filter:2.0.0 \
  --tasks 1 \
  --max-retries 3 \
  --cpu 2 \
  --memory 2Gi \
  --set-env-vars LOG_FILTER_WORKERS=8 \
  --region us-central1
```

## Troubleshooting

### Container Issues

**Permission denied:**

```bash
# Run as root (not recommended for production)
docker run --rm --user root \
  -v /var/log:/logs:ro \
  log-filter:2.0.0 "ERROR" "/logs"

# Or fix host permissions
sudo chmod -R +r /var/log
```

**Out of memory:**

```bash
# Increase container memory
docker run --rm --memory="2g" \
  -v /var/log:/logs:ro \
  log-filter:2.0.0 "ERROR" "/logs" -w 2
```

**Slow performance:**

```bash
# Check I/O
docker stats log-filter

# Increase workers
docker run --rm \
  -e LOG_FILTER_WORKERS=16 \
  log-filter:2.0.0 "ERROR" "/logs"
```

### Kubernetes Issues

**Pod not starting:**

```bash
# Check events
kubectl describe pod -n log-filter

# Check logs
kubectl logs -n log-filter <pod-name>

# Check config
kubectl get configmap log-filter-config -n log-filter -o yaml
```

**Job failed:**

```bash
# Check job status
kubectl get jobs -n log-filter

# View pod logs
kubectl logs -n log-filter job/log-filter-<name>

# Delete and retry
kubectl delete job log-filter-<name> -n log-filter
kubectl apply -f job.yaml
```

## Next Steps

- **[Configuration Guide](configuration.md)** - Configure for your environment
- **[Performance Tuning](performance.md)** - Optimize deployment
- **[Troubleshooting](troubleshooting.md)** - Solve common issues
- **[Migration Guide](migration.md)** - Upgrade from v1.x
