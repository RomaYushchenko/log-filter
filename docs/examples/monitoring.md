# Application Monitoring Examples

**Use Case:** Application Health Monitoring  
**Difficulty:** Intermediate  
**Time to Complete:** 15-20 minutes  
**Last Updated:** January 8, 2026

---

## Overview

These examples demonstrate how to use Log Filter for real-time application monitoring, including error tracking, performance monitoring, and anomaly detection.

---

## Example 1: Web Application Error Tracking

### Scenario: E-commerce Platform

Monitor a web application for critical errors that impact users.

#### Configuration

```yaml
# monitoring/webapp-errors.yaml
search:
  expression: |
    (status:(500 OR 502 OR 503 OR 504)) OR
    (ERROR AND (payment OR checkout OR cart)) OR
    (CRITICAL AND NOT health-check)
  case_sensitive: false

files:
  search_root: /var/log/webapp
  include_patterns:
    - "app-*.log"
    - "error.log"
  exclude_patterns:
    - "*debug.log"
    - "*test.log"

output:
  output_file: /monitoring/webapp-errors-{date}.txt
  show_stats: true
  format: json  # For downstream processing

processing:
  max_workers: 4

logging:
  level: WARNING
```

#### Usage

```bash
# Real-time monitoring
log-filter --config webapp-errors.yaml --follow

# Daily report
log-filter --config webapp-errors.yaml \
  --start-date $(date -d 'yesterday' +%Y-%m-%d) \
  --end-date $(date -d 'yesterday' +%Y-%m-%d)

# Alert on critical errors
log-filter --config webapp-errors.yaml \
  --expr "CRITICAL" \
  --output /tmp/critical.txt && \
  if [ -s /tmp/critical.txt ]; then
    send-alert --priority high --file /tmp/critical.txt
  fi
```

#### Integration with Alerting

```python
# monitoring/webapp_monitor.py
import subprocess
import json
from datetime import datetime

def monitor_webapp_errors():
    """Monitor web app errors and send alerts."""
    
    # Run log filter
    result = subprocess.run([
        'log-filter',
        '--config', 'webapp-errors.yaml',
        '--format', 'json',
        '--since', '5m'  # Last 5 minutes
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running log-filter: {result.stderr}")
        return
    
    # Parse results
    errors = []
    for line in result.stdout.split('\n'):
        if line.strip():
            try:
                errors.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    # Categorize errors
    critical_errors = [e for e in errors if 'CRITICAL' in e.get('content', '')]
    payment_errors = [e for e in errors if 'payment' in e.get('content', '').lower()]
    
    # Send alerts
    if critical_errors:
        send_pagerduty_alert(
            summary=f"{len(critical_errors)} critical errors detected",
            severity="critical",
            details=critical_errors[:5]
        )
    
    if len(payment_errors) > 10:
        send_slack_alert(
            channel="#payments",
            message=f"⚠️ High payment error rate: {len(payment_errors)} errors in 5 minutes",
            details=payment_errors[:3]
        )

def send_pagerduty_alert(summary, severity, details):
    """Send alert to PagerDuty."""
    # Implementation
    pass

def send_slack_alert(channel, message, details):
    """Send alert to Slack."""
    # Implementation
    pass

if __name__ == "__main__":
    monitor_webapp_errors()
```

---

## Example 2: Database Connection Issues

### Scenario: Connection Pool Monitoring

Detect and diagnose database connection problems.

#### Configuration

```yaml
# monitoring/database-connections.yaml
search:
  expression: |
    (database OR db OR sql) AND
    (
      (connection AND (timeout OR refused OR failed OR closed)) OR
      (pool AND (exhausted OR full OR limit)) OR
      (deadlock OR lock-wait-timeout) OR
      (too many connections)
    )
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "app.log"
    - "database.log"

output:
  output_file: /monitoring/db-issues-{timestamp}.txt
  show_stats: true
  include_context: 3  # Include 3 lines before/after

processing:
  max_workers: 2
```

#### Analysis Script

```python
# monitoring/analyze_db_issues.py
from collections import Counter
from datetime import datetime, timedelta
import re

def analyze_db_issues(log_file):
    """Analyze database issues from filtered logs."""
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Categorize issues
    issues = {
        'connection_timeout': 0,
        'connection_refused': 0,
        'pool_exhausted': 0,
        'deadlock': 0,
        'too_many_connections': 0
    }
    
    # Track timestamps
    timestamps = []
    
    for line in lines:
        # Extract timestamp
        match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
        if match:
            timestamps.append(datetime.strptime(match.group(), '%Y-%m-%d %H:%M:%S'))
        
        # Categorize
        if 'timeout' in line.lower():
            issues['connection_timeout'] += 1
        elif 'refused' in line.lower():
            issues['connection_refused'] += 1
        elif 'pool' in line.lower() and 'exhaust' in line.lower():
            issues['pool_exhausted'] += 1
        elif 'deadlock' in line.lower():
            issues['deadlock'] += 1
        elif 'too many connections' in line.lower():
            issues['too_many_connections'] += 1
    
    # Generate report
    print("=" * 80)
    print("DATABASE ISSUES ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Issues: {len(lines)}")
    print(f"\nBreakdown:")
    for issue_type, count in issues.items():
        print(f"  {issue_type.replace('_', ' ').title()}: {count}")
    
    # Time-based analysis
    if timestamps:
        print(f"\nTime Range:")
        print(f"  First: {min(timestamps)}")
        print(f"  Last:  {max(timestamps)}")
        print(f"  Duration: {max(timestamps) - min(timestamps)}")
        
        # Incidents per hour
        hours = Counter(ts.hour for ts in timestamps)
        print(f"\nIncidents by Hour:")
        for hour in sorted(hours.keys()):
            print(f"  {hour:02d}:00 - {hours[hour]} incidents")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if issues['pool_exhausted'] > 10:
        print("⚠️  High pool exhaustion rate - consider increasing pool size")
    
    if issues['connection_timeout'] > 20:
        print("⚠️  Frequent timeouts - check network latency and database load")
    
    if issues['deadlock'] > 0:
        print("⚠️  Deadlocks detected - review transaction isolation levels")
    
    if issues['too_many_connections'] > 0:
        print("⚠️  Connection limit reached - check for connection leaks")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_db_issues.py <log_file>")
        sys.exit(1)
    
    analyze_db_issues(sys.argv[1])
```

#### Usage

```bash
# Filter database issues
log-filter --config database-connections.yaml

# Analyze results
python analyze_db_issues.py /monitoring/db-issues-*.txt
```

---

## Example 3: API Performance Monitoring

### Scenario: Slow API Endpoints

Identify and track slow API responses.

#### Configuration

```yaml
# monitoring/api-performance.yaml
search:
  expression: |
    (
      (slow OR latency OR duration) AND
      (api OR endpoint OR request OR response)
    ) OR
    (response-time AND (> OR exceeded OR high))
  case_sensitive: false

files:
  search_root: /var/log/api
  include_patterns:
    - "access.log"
    - "performance.log"

output:
  output_file: /monitoring/slow-apis-{date}.txt
  show_stats: true
```

#### Performance Analysis

```python
# monitoring/api_performance_analyzer.py
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class APICall:
    """Represents an API call with performance metrics."""
    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: str

def parse_api_logs(log_file: str) -> List[APICall]:
    """Parse API logs and extract performance data."""
    
    api_calls = []
    
    # Example log format:
    # 2026-01-08 10:15:23 GET /api/users 200 1250ms
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (\S+) (\d{3}) (\d+)ms'
    
    with open(log_file, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                api_calls.append(APICall(
                    timestamp=match.group(1),
                    method=match.group(2),
                    endpoint=match.group(3),
                    status_code=int(match.group(4)),
                    duration_ms=float(match.group(5))
                ))
    
    return api_calls

def analyze_performance(api_calls: List[APICall]):
    """Analyze API performance metrics."""
    
    # Group by endpoint
    endpoint_metrics = defaultdict(list)
    for call in api_calls:
        endpoint_metrics[call.endpoint].append(call.duration_ms)
    
    print("=" * 80)
    print("API PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    print(f"\nTotal API Calls: {len(api_calls)}")
    print(f"Unique Endpoints: {len(endpoint_metrics)}")
    
    # Calculate statistics per endpoint
    print("\n" + "-" * 80)
    print(f"{'Endpoint':<40} {'Calls':>8} {'Avg (ms)':>10} {'P95 (ms)':>10} {'Max (ms)':>10}")
    print("-" * 80)
    
    for endpoint, durations in sorted(endpoint_metrics.items(), 
                                      key=lambda x: statistics.mean(x[1]), 
                                      reverse=True):
        avg_duration = statistics.mean(durations)
        p95_duration = sorted(durations)[int(len(durations) * 0.95)]
        max_duration = max(durations)
        
        print(f"{endpoint:<40} {len(durations):>8} {avg_duration:>10.1f} {p95_duration:>10.1f} {max_duration:>10.1f}")
    
    # Identify slow endpoints
    print("\n" + "=" * 80)
    print("SLOW ENDPOINTS (Avg > 1000ms)")
    print("=" * 80)
    
    slow_endpoints = [(endpoint, durations) for endpoint, durations in endpoint_metrics.items()
                      if statistics.mean(durations) > 1000]
    
    for endpoint, durations in sorted(slow_endpoints, 
                                      key=lambda x: statistics.mean(x[1]), 
                                      reverse=True):
        avg_duration = statistics.mean(durations)
        print(f"\n🐌 {endpoint}")
        print(f"   Calls: {len(durations)}")
        print(f"   Average: {avg_duration:.1f}ms")
        print(f"   P95: {sorted(durations)[int(len(durations) * 0.95)]:.1f}ms")
        print(f"   Max: {max(durations):.1f}ms")
        
        # Suggest action
        if avg_duration > 5000:
            print("   ⚠️  CRITICAL: Consider caching, indexing, or query optimization")
        elif avg_duration > 2000:
            print("   ⚠️  WARNING: Review database queries and external API calls")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python api_performance_analyzer.py <log_file>")
        sys.exit(1)
    
    api_calls = parse_api_logs(sys.argv[1])
    analyze_performance(api_calls)
```

---

## Example 4: Security Monitoring

### Scenario: Detect Security Threats

Monitor for suspicious activities and security events.

#### Configuration

```yaml
# monitoring/security-monitoring.yaml
search:
  expression: |
    (
      (authentication OR auth OR login) AND
      (failed OR denied OR unauthorized OR invalid)
    ) OR
    (
      (authorization OR access) AND
      (forbidden OR denied OR blocked)
    ) OR
    (sql AND (injection OR malicious)) OR
    (xss OR csrf OR rce OR lfi OR rfi) OR
    (suspicious OR anomaly OR unusual) OR
    (brute-force OR dos OR ddos)
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "security.log"
    - "auth.log"
    - "access.log"

output:
  output_file: /monitoring/security-alerts-{timestamp}.txt
  show_stats: true
  format: json

processing:
  max_workers: 4
```

#### Real-time Security Alerting

```python
# monitoring/security_monitor.py
import subprocess
import json
from collections import Counter
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

class SecurityMonitor:
    """Monitor security logs and send alerts."""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.alert_thresholds = {
            'failed_login': 5,
            'sql_injection': 1,
            'xss': 1,
            'unauthorized_access': 10
        }
    
    def monitor(self, duration_minutes: int = 5):
        """Monitor logs for the specified duration."""
        
        # Run log filter
        result = subprocess.run([
            'log-filter',
            '--config', self.config_file,
            '--format', 'json',
            '--since', f'{duration_minutes}m'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
        
        # Parse events
        events = []
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Analyze and alert
        self.analyze_events(events)
    
    def analyze_events(self, events: list):
        """Analyze security events and trigger alerts."""
        
        # Categorize events
        failed_logins = Counter()
        sql_injections = []
        xss_attempts = []
        unauthorized_access = []
        
        for event in events:
            content = event.get('content', '').lower()
            source_ip = self.extract_ip(content)
            
            if 'failed' in content and 'login' in content:
                failed_logins[source_ip] += 1
            
            if 'sql' in content and 'injection' in content:
                sql_injections.append(event)
            
            if 'xss' in content:
                xss_attempts.append(event)
            
            if 'unauthorized' in content or 'forbidden' in content:
                unauthorized_access.append(event)
        
        # Check thresholds and alert
        if sql_injections:
            self.send_critical_alert(
                "SQL Injection Attempts Detected",
                f"{len(sql_injections)} SQL injection attempts detected:\n" +
                '\n'.join(e['content'] for e in sql_injections[:3])
            )
        
        if xss_attempts:
            self.send_critical_alert(
                "XSS Attempts Detected",
                f"{len(xss_attempts)} XSS attempts detected"
            )
        
        # Brute force detection
        for ip, count in failed_logins.items():
            if count >= self.alert_thresholds['failed_login']:
                self.send_warning_alert(
                    f"Brute Force Attack from {ip}",
                    f"{count} failed login attempts from {ip}"
                )
        
        # Generate report
        self.generate_report(failed_logins, sql_injections, xss_attempts, unauthorized_access)
    
    def extract_ip(self, content: str) -> str:
        """Extract IP address from log entry."""
        import re
        match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
        return match.group() if match else 'unknown'
    
    def send_critical_alert(self, subject: str, message: str):
        """Send critical security alert."""
        print(f"🚨 CRITICAL: {subject}")
        print(f"   {message}")
        # Implement email/Slack/PagerDuty notification
    
    def send_warning_alert(self, subject: str, message: str):
        """Send warning security alert."""
        print(f"⚠️  WARNING: {subject}")
        print(f"   {message}")
    
    def generate_report(self, failed_logins, sql_injections, xss_attempts, unauthorized_access):
        """Generate security monitoring report."""
        
        print("\n" + "=" * 80)
        print("SECURITY MONITORING REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now()}")
        
        print(f"\nFailed Logins: {sum(failed_logins.values())}")
        if failed_logins:
            print("  Top Sources:")
            for ip, count in failed_logins.most_common(5):
                print(f"    {ip}: {count} attempts")
        
        print(f"\nSQL Injection Attempts: {len(sql_injections)}")
        print(f"XSS Attempts: {len(xss_attempts)}")
        print(f"Unauthorized Access Attempts: {len(unauthorized_access)}")

if __name__ == "__main__":
    monitor = SecurityMonitor('security-monitoring.yaml')
    monitor.monitor(duration_minutes=5)
```

---

## Cron Job Integration

### Automated Monitoring

```bash
# /etc/cron.d/log-monitoring

# Web app errors - every 5 minutes
*/5 * * * * /usr/local/bin/python3 /monitoring/webapp_monitor.py

# Database issues - every 15 minutes
*/15 * * * * /monitoring/check_db_issues.sh

# API performance - hourly
0 * * * * /usr/local/bin/python3 /monitoring/api_performance_analyzer.py /var/log/api/access.log

# Security monitoring - every 5 minutes
*/5 * * * * /usr/local/bin/python3 /monitoring/security_monitor.py

# Daily summary report - every day at 8 AM
0 8 * * * /monitoring/generate_daily_report.sh
```

---

## Integration with Monitoring Systems

### Prometheus Exporter

```python
# monitoring/prometheus_exporter.py
from prometheus_client import start_http_server, Gauge, Counter
import time
import subprocess
import json

# Define metrics
error_count = Counter('app_errors_total', 'Total application errors', ['severity'])
api_latency = Gauge('api_latency_seconds', 'API latency', ['endpoint'])
db_connections = Gauge('db_connection_issues', 'Database connection issues')

def collect_metrics():
    """Collect metrics from log filter."""
    
    # Run log filter
    result = subprocess.run([
        'log-filter',
        '--config', 'webapp-errors.yaml',
        '--format', 'json',
        '--since', '1m'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    event = json.loads(line)
                    content = event.get('content', '')
                    
                    if 'CRITICAL' in content:
                        error_count.labels(severity='critical').inc()
                    elif 'ERROR' in content:
                        error_count.labels(severity='error').inc()
                    
                except json.JSONDecodeError:
                    pass

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)
    print("Prometheus metrics available at http://localhost:8000")
    
    while True:
        collect_metrics()
        time.sleep(60)  # Collect every minute
```

---

## What's Next?

- **[DevOps Examples](devops.md)** - CI/CD and deployment workflows
- **[Security Examples](security.md)** - Security analysis patterns
- **[Integration Guide](../integration_guide.md)** - Full integration patterns

---

**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
