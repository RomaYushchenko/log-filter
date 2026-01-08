# DevOps Workflow Examples

**Use Case:** CI/CD and Deployment Workflows  
**Difficulty:** Intermediate  
**Time to Complete:** 20-25 minutes  
**Last Updated:** January 8, 2026

---

## Overview

These examples demonstrate how to integrate Log Filter into DevOps workflows, including CI/CD pipelines, post-deployment validation, incident investigation, and log aggregation.

---

## Example 1: Post-Deployment Health Check

### Scenario: Validate Deployment Success

Check for errors immediately after deployment to catch issues early.

#### CI/CD Pipeline Script

```bash
#!/bin/bash
# scripts/post-deployment-check.sh

set -e

DEPLOYMENT_TIME=$(date +%Y-%m-%d_%H:%M:%S)
LOG_DIR="/var/log/app"
OUTPUT_DIR="/tmp/deployment-checks"

mkdir -p "$OUTPUT_DIR"

echo "🔍 Running post-deployment health check..."

# Check for critical errors in last 5 minutes
log-filter \
  --expr "CRITICAL OR FATAL" \
  --input "$LOG_DIR" \
  --since "5m" \
  --output "$OUTPUT_DIR/critical-errors.txt"

# Check for startup errors
log-filter \
  --expr "(startup OR initialization) AND (error OR failed)" \
  --input "$LOG_DIR" \
  --since "5m" \
  --output "$OUTPUT_DIR/startup-errors.txt"

# Check for configuration errors
log-filter \
  --expr "configuration AND (invalid OR missing OR error)" \
  --input "$LOG_DIR" \
  --since "5m" \
  --output "$OUTPUT_DIR/config-errors.txt"

# Analyze results
CRITICAL_COUNT=$(wc -l < "$OUTPUT_DIR/critical-errors.txt" || echo 0)
STARTUP_COUNT=$(wc -l < "$OUTPUT_DIR/startup-errors.txt" || echo 0)
CONFIG_COUNT=$(wc -l < "$OUTPUT_DIR/config-errors.txt" || echo 0)

echo ""
echo "Results:"
echo "  Critical Errors: $CRITICAL_COUNT"
echo "  Startup Errors: $STARTUP_COUNT"
echo "  Config Errors: $CONFIG_COUNT"

# Determine deployment status
if [ "$CRITICAL_COUNT" -gt 0 ]; then
  echo "❌ DEPLOYMENT FAILED: Critical errors detected"
  cat "$OUTPUT_DIR/critical-errors.txt"
  exit 1
fi

if [ "$STARTUP_COUNT" -gt 0 ]; then
  echo "⚠️  WARNING: Startup errors detected"
  cat "$OUTPUT_DIR/startup-errors.txt"
fi

if [ "$CONFIG_COUNT" -gt 0 ]; then
  echo "⚠️  WARNING: Configuration errors detected"
  cat "$OUTPUT_DIR/config-errors.txt"
fi

if [ "$STARTUP_COUNT" -eq 0 ] && [ "$CONFIG_COUNT" -eq 0 ]; then
  echo "✅ DEPLOYMENT SUCCESSFUL: No errors detected"
  exit 0
else
  echo "⚠️  DEPLOYMENT COMPLETED WITH WARNINGS"
  exit 0
fi
```

#### GitHub Actions Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy and Validate

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy Application
      run: |
        # Your deployment commands
        ./scripts/deploy.sh
    
    - name: Install Log Filter
      run: |
        pip install log-filter
    
    - name: Wait for Application Startup
      run: sleep 30
    
    - name: Run Post-Deployment Checks
      id: health_check
      run: |
        ./scripts/post-deployment-check.sh
      continue-on-error: true
    
    - name: Upload Check Results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: deployment-checks
        path: /tmp/deployment-checks/
    
    - name: Notify on Failure
      if: steps.health_check.outcome == 'failure'
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        text: 'Deployment validation failed - critical errors detected'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    
    - name: Rollback on Critical Failure
      if: steps.health_check.outcome == 'failure'
      run: |
        echo "Rolling back deployment..."
        ./scripts/rollback.sh
```

---

## Example 2: Incident Investigation

### Scenario: Production Incident Response

Quickly analyze logs during an incident to identify root cause.

#### Investigation Script

```python
# scripts/investigate_incident.py
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

class IncidentInvestigator:
    """Tool for rapid incident investigation."""
    
    def __init__(self, log_dir: str, output_dir: str):
        self.log_dir = Path(log_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def investigate(self, incident_time: datetime, window_minutes: int = 30):
        """Investigate incident within time window."""
        
        start_time = incident_time - timedelta(minutes=window_minutes//2)
        end_time = incident_time + timedelta(minutes=window_minutes//2)
        
        print(f"🔍 Investigating incident around {incident_time}")
        print(f"   Time window: {start_time} to {end_time}")
        print("")
        
        # Step 1: Find all errors
        print("Step 1: Collecting all errors...")
        self.collect_errors(start_time, end_time)
        
        # Step 2: Find critical events
        print("Step 2: Finding critical events...")
        self.find_critical_events(start_time, end_time)
        
        # Step 3: Analyze patterns
        print("Step 3: Analyzing patterns...")
        self.analyze_patterns()
        
        # Step 4: Generate timeline
        print("Step 4: Generating timeline...")
        self.generate_timeline()
        
        print("")
        print(f"✅ Investigation complete. Results in: {self.output_dir}")
    
    def collect_errors(self, start_time: datetime, end_time: datetime):
        """Collect all errors in time window."""
        
        result = subprocess.run([
            'log-filter',
            '--expr', 'ERROR OR WARNING OR CRITICAL',
            '--input', str(self.log_dir),
            '--start-date', start_time.strftime('%Y-%m-%d'),
            '--start-time', start_time.strftime('%H:%M:%S'),
            '--end-date', end_time.strftime('%Y-%m-%d'),
            '--end-time', end_time.strftime('%H:%M:%S'),
            '--output', str(self.output_dir / 'all-errors.txt'),
            '--format', 'json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            error_count = len(result.stdout.strip().split('\n'))
            print(f"   Found {error_count} error messages")
    
    def find_critical_events(self, start_time: datetime, end_time: datetime):
        """Find critical events that might be root cause."""
        
        queries = {
            'database': 'database AND (connection OR timeout OR deadlock)',
            'memory': 'memory AND (leak OR exhausted OR oom)',
            'network': 'network AND (timeout OR refused OR unreachable)',
            'disk': 'disk AND (full OR space OR io)',
            'service': 'service AND (crashed OR stopped OR failed)'
        }
        
        for name, expr in queries.items():
            output_file = self.output_dir / f'critical-{name}.txt'
            
            subprocess.run([
                'log-filter',
                '--expr', expr,
                '--input', str(self.log_dir),
                '--start-date', start_time.strftime('%Y-%m-%d'),
                '--start-time', start_time.strftime('%H:%M:%S'),
                '--end-date', end_time.strftime('%Y-%m-%d'),
                '--end-time', end_time.strftime('%H:%M:%S'),
                '--output', str(output_file)
            ], capture_output=True)
            
            if output_file.exists():
                line_count = len(output_file.read_text().strip().split('\n'))
                if line_count > 0:
                    print(f"   {name.capitalize()}: {line_count} events")
    
    def analyze_patterns(self):
        """Analyze error patterns."""
        
        # Count error types
        errors_file = self.output_dir / 'all-errors.txt'
        if not errors_file.exists():
            return
        
        error_types = {}
        with open(errors_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    content = event.get('content', '')
                    
                    # Extract error type
                    if 'ERROR' in content:
                        error_type = 'ERROR'
                    elif 'WARNING' in content:
                        error_type = 'WARNING'
                    elif 'CRITICAL' in content:
                        error_type = 'CRITICAL'
                    else:
                        continue
                    
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                except json.JSONDecodeError:
                    pass
        
        # Write summary
        summary_file = self.output_dir / 'summary.txt'
        with open(summary_file, 'w') as f:
            f.write("INCIDENT INVESTIGATION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write("Error Breakdown:\n")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {error_type}: {count}\n")
        
        print(f"   Summary written to {summary_file}")
    
    def generate_timeline(self):
        """Generate incident timeline."""
        
        # Parse timestamps from all errors
        errors_file = self.output_dir / 'all-errors.txt'
        if not errors_file.exists():
            return
        
        events = []
        with open(errors_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    pass
        
        # Sort by timestamp
        events.sort(key=lambda e: e.get('timestamp', ''))
        
        # Write timeline
        timeline_file = self.output_dir / 'timeline.txt'
        with open(timeline_file, 'w') as f:
            f.write("INCIDENT TIMELINE\n")
            f.write("=" * 80 + "\n\n")
            
            for event in events:
                timestamp = event.get('timestamp', 'N/A')
                content = event.get('content', '').strip()
                f.write(f"{timestamp} | {content[:100]}\n")
        
        print(f"   Timeline written to {timeline_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python investigate_incident.py <incident_time> [window_minutes]")
        print("Example: python investigate_incident.py '2026-01-08 14:30:00' 30")
        sys.exit(1)
    
    incident_time_str = sys.argv[1]
    window_minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    incident_time = datetime.strptime(incident_time_str, '%Y-%m-%d %H:%M:%S')
    
    investigator = IncidentInvestigator(
        log_dir='/var/log/app',
        output_dir='/tmp/incident-investigation'
    )
    
    investigator.investigate(incident_time, window_minutes)

if __name__ == "__main__":
    main()
```

#### Usage

```bash
# Investigate incident that occurred at 2:30 PM
python investigate_incident.py "2026-01-08 14:30:00" 30

# Review results
cd /tmp/incident-investigation
ls -la
# all-errors.txt
# critical-database.txt
# critical-memory.txt
# summary.txt
# timeline.txt
```

---

## Example 3: Performance Regression Detection

### Scenario: Detect Performance Degradation

Monitor for performance issues after deployments.

#### Configuration

```yaml
# devops/performance-regression.yaml
search:
  expression: |
    (
      (slow OR latency OR timeout) AND
      (request OR query OR response)
    ) OR
    (duration AND (exceeded OR high)) OR
    (performance AND degradation)
  case_sensitive: false

files:
  search_root: /var/log/app
  include_patterns:
    - "performance.log"
    - "access.log"

output:
  output_file: /devops/performance-issues-{timestamp}.txt
  show_stats: true
  format: json
```

#### Regression Detection Script

```python
# scripts/detect_regression.py
import subprocess
import json
import statistics
from datetime import datetime, timedelta

class RegressionDetector:
    """Detect performance regressions."""
    
    def __init__(self, baseline_file: str, current_file: str):
        self.baseline_metrics = self.parse_metrics(baseline_file)
        self.current_metrics = self.parse_metrics(current_file)
    
    def parse_metrics(self, log_file: str) -> dict:
        """Parse performance metrics from logs."""
        
        metrics = {
            'response_times': [],
            'query_times': [],
            'error_count': 0
        }
        
        with open(log_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    content = event.get('content', '')
                    
                    # Extract response time
                    if 'response' in content and 'ms' in content:
                        import re
                        match = re.search(r'(\d+)ms', content)
                        if match:
                            metrics['response_times'].append(int(match.group(1)))
                    
                    # Count errors
                    if 'ERROR' in content or 'timeout' in content:
                        metrics['error_count'] += 1
                
                except json.JSONDecodeError:
                    pass
        
        return metrics
    
    def detect_regression(self) -> bool:
        """Compare metrics and detect regression."""
        
        print("=" * 80)
        print("PERFORMANCE REGRESSION ANALYSIS")
        print("=" * 80)
        
        has_regression = False
        
        # Compare response times
        if self.baseline_metrics['response_times'] and self.current_metrics['response_times']:
            baseline_avg = statistics.mean(self.baseline_metrics['response_times'])
            current_avg = statistics.mean(self.current_metrics['response_times'])
            
            baseline_p95 = sorted(self.baseline_metrics['response_times'])[int(len(self.baseline_metrics['response_times']) * 0.95)]
            current_p95 = sorted(self.current_metrics['response_times'])[int(len(self.current_metrics['response_times']) * 0.95)]
            
            print(f"\nResponse Time Comparison:")
            print(f"  Baseline Avg:  {baseline_avg:.1f}ms")
            print(f"  Current Avg:   {current_avg:.1f}ms")
            print(f"  Change:        {((current_avg - baseline_avg) / baseline_avg * 100):+.1f}%")
            print(f"\n  Baseline P95:  {baseline_p95:.1f}ms")
            print(f"  Current P95:   {current_p95:.1f}ms")
            print(f"  Change:        {((current_p95 - baseline_p95) / baseline_p95 * 100):+.1f}%")
            
            # Regression if > 20% slower
            if current_avg > baseline_avg * 1.2:
                print(f"\n  ❌ REGRESSION DETECTED: Average response time increased by > 20%")
                has_regression = True
            
            if current_p95 > baseline_p95 * 1.2:
                print(f"\n  ❌ REGRESSION DETECTED: P95 response time increased by > 20%")
                has_regression = True
        
        # Compare error rates
        baseline_errors = self.baseline_metrics['error_count']
        current_errors = self.current_metrics['error_count']
        
        print(f"\nError Rate Comparison:")
        print(f"  Baseline:      {baseline_errors}")
        print(f"  Current:       {current_errors}")
        
        if current_errors > baseline_errors * 1.5:
            print(f"\n  ❌ REGRESSION DETECTED: Error rate increased by > 50%")
            has_regression = True
        
        print("\n" + "=" * 80)
        
        if has_regression:
            print("⚠️  PERFORMANCE REGRESSION DETECTED")
            return True
        else:
            print("✅ No performance regression detected")
            return False

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python detect_regression.py <baseline_file> <current_file>")
        sys.exit(1)
    
    detector = RegressionDetector(sys.argv[1], sys.argv[2])
    
    if detector.detect_regression():
        sys.exit(1)  # Fail CI/CD pipeline
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
```

#### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - deploy
  - validate
  - rollback

deploy_production:
  stage: deploy
  script:
    - ./scripts/deploy.sh production
  only:
    - main

performance_check:
  stage: validate
  needs: [deploy_production]
  script:
    # Capture baseline metrics (before deployment)
    - log-filter --config performance-regression.yaml --output baseline.json --since "1h"
    
    # Wait for new deployment to settle
    - sleep 60
    
    # Capture current metrics
    - log-filter --config performance-regression.yaml --output current.json --since "5m"
    
    # Compare and detect regression
    - python scripts/detect_regression.py baseline.json current.json
  artifacts:
    when: always
    paths:
      - baseline.json
      - current.json
  only:
    - main

rollback_on_regression:
  stage: rollback
  when: on_failure
  needs: [performance_check]
  script:
    - echo "Performance regression detected, rolling back..."
    - ./scripts/rollback.sh
  only:
    - main
```

---

## Example 4: Log Aggregation Pipeline

### Scenario: Centralized Log Processing

Aggregate and process logs from multiple services.

#### Pipeline Script

```bash
#!/bin/bash
# scripts/log-aggregation-pipeline.sh

set -e

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="/data/aggregated-logs/$DATE"
mkdir -p "$OUTPUT_DIR"

echo "📊 Starting log aggregation pipeline for $DATE"

# Stage 1: Collect logs from all services
echo "Stage 1: Collecting logs..."

for service in api web worker database; do
  echo "  Processing $service..."
  
  log-filter \
    --input "/var/log/$service" \
    --output "$OUTPUT_DIR/$service-all.txt" \
    --stats
done

# Stage 2: Extract errors
echo "Stage 2: Extracting errors..."

for service in api web worker database; do
  log-filter \
    --expr "ERROR OR CRITICAL" \
    --input "$OUTPUT_DIR/$service-all.txt" \
    --output "$OUTPUT_DIR/$service-errors.txt"
done

# Stage 3: Consolidate errors
echo "Stage 3: Consolidating errors..."

cat "$OUTPUT_DIR"/*-errors.txt > "$OUTPUT_DIR/all-errors.txt"

# Stage 4: Categorize
echo "Stage 4: Categorizing issues..."

# Database issues
log-filter \
  --expr "database OR sql OR connection" \
  --input "$OUTPUT_DIR/all-errors.txt" \
  --output "$OUTPUT_DIR/category-database.txt"

# API issues
log-filter \
  --expr "api OR endpoint OR http" \
  --input "$OUTPUT_DIR/all-errors.txt" \
  --output "$OUTPUT_DIR/category-api.txt"

# Payment issues
log-filter \
  --expr "payment OR transaction OR billing" \
  --input "$OUTPUT_DIR/all-errors.txt" \
  --output "$OUTPUT_DIR/category-payment.txt"

# Stage 5: Generate summary
echo "Stage 5: Generating summary..."

cat > "$OUTPUT_DIR/summary.txt" << EOF
LOG AGGREGATION SUMMARY - $DATE
$(echo "=" | head -c 80)

Service Log Counts:
  API:      $(wc -l < "$OUTPUT_DIR/api-all.txt")
  Web:      $(wc -l < "$OUTPUT_DIR/web-all.txt")
  Worker:   $(wc -l < "$OUTPUT_DIR/worker-all.txt")
  Database: $(wc -l < "$OUTPUT_DIR/database-all.txt")

Error Counts:
  API:      $(wc -l < "$OUTPUT_DIR/api-errors.txt")
  Web:      $(wc -l < "$OUTPUT_DIR/web-errors.txt")
  Worker:   $(wc -l < "$OUTPUT_DIR/worker-errors.txt")
  Database: $(wc -l < "$OUTPUT_DIR/database-errors.txt")

Category Breakdown:
  Database: $(wc -l < "$OUTPUT_DIR/category-database.txt")
  API:      $(wc -l < "$OUTPUT_DIR/category-api.txt")
  Payment:  $(wc -l < "$OUTPUT_DIR/category-payment.txt")
EOF

cat "$OUTPUT_DIR/summary.txt"

# Stage 6: Upload to S3
echo "Stage 6: Uploading to S3..."
aws s3 sync "$OUTPUT_DIR" "s3://logs-archive/$DATE/" --quiet

echo "✅ Pipeline complete!"
```

#### Automated Pipeline with Airflow

```python
# airflow/dags/log_aggregation_dag.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'devops',
    'depends_on_past': False,
    'email': ['devops@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'log_aggregation',
    default_args=default_args,
    description='Daily log aggregation and analysis',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['logs', 'monitoring'],
)

# Task 1: Collect logs
collect_logs = BashOperator(
    task_id='collect_logs',
    bash_command='/scripts/collect-logs.sh',
    dag=dag,
)

# Task 2: Filter errors
filter_errors = BashOperator(
    task_id='filter_errors',
    bash_command='''
        log-filter --expr "ERROR OR CRITICAL" \
          --input /data/collected-logs \
          --output /data/filtered-errors.txt
    ''',
    dag=dag,
)

# Task 3: Analyze patterns
analyze_patterns = PythonOperator(
    task_id='analyze_patterns',
    python_callable=analyze_log_patterns,
    dag=dag,
)

# Task 4: Generate report
generate_report = BashOperator(
    task_id='generate_report',
    bash_command='/scripts/generate-report.sh',
    dag=dag,
)

# Task 5: Send notifications
send_notifications = PythonOperator(
    task_id='send_notifications',
    python_callable=send_daily_report,
    dag=dag,
)

# Define task dependencies
collect_logs >> filter_errors >> analyze_patterns >> generate_report >> send_notifications

def analyze_log_patterns():
    """Analyze log patterns."""
    # Implementation
    pass

def send_daily_report():
    """Send daily report."""
    # Implementation
    pass
```

---

## Jenkins Pipeline Integration

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Deploy') {
            steps {
                sh './scripts/deploy.sh'
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    // Install log-filter
                    sh 'pip install log-filter'
                    
                    // Wait for startup
                    sleep(time: 30, unit: 'SECONDS')
                    
                    // Check for errors
                    def exitCode = sh(
                        script: './scripts/post-deployment-check.sh',
                        returnStatus: true
                    )
                    
                    if (exitCode != 0) {
                        error("Deployment validation failed")
                    }
                }
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: '/tmp/deployment-checks/**'
            }
        }
    }
    
    post {
        failure {
            emailext(
                subject: "Deployment Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Check console output at ${env.BUILD_URL}",
                to: 'devops@example.com'
            )
            
            // Rollback
            sh './scripts/rollback.sh'
        }
    }
}
```

---

## Best Practices

### 1. Automate Everything

```bash
# Create automation scripts
/devops/
  ├── post-deploy-check.sh
  ├── incident-investigation.sh
  ├── performance-regression.sh
  └── log-aggregation.sh
```

### 2. Use Version Control

```bash
# Store configurations in Git
/configs/
  ├── production/
  │   ├── error-monitoring.yaml
  │   └── performance-monitoring.yaml
  └── staging/
      ├── error-monitoring.yaml
      └── performance-monitoring.yaml
```

### 3. Monitor Continuously

```bash
# Set up continuous monitoring
*/5 * * * * /devops/check-errors.sh
```

### 4. Document Runbooks

Create runbooks for common scenarios:
- Deployment validation
- Incident response
- Performance investigation
- Log aggregation

---

## What's Next?

- **[Security Examples](security.md)** - Security analysis patterns
- **[Monitoring Examples](monitoring.md)** - Application monitoring
- **[Integration Guide](../integration_guide.md)** - Full integration patterns

---

**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
