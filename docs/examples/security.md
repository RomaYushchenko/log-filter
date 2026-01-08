# Security Analysis Examples

**Use Case:** Security Monitoring and Threat Detection  
**Difficulty:** Intermediate to Advanced  
**Time to Complete:** 20-25 minutes  
**Last Updated:** January 8, 2026

---

## Overview

These examples demonstrate how to use Log Filter for security monitoring, including intrusion detection, authentication failures, SQL injection attempts, and compliance auditing.

---

## Example 1: Failed Login Detection

### Scenario: Brute Force Attack Detection

Detect and alert on failed login attempts that may indicate brute force attacks.

#### Configuration

```yaml
# security/failed-logins.yaml
search:
  expression: |
    (
      (login OR authentication OR auth) AND
      (failed OR denied OR invalid OR incorrect)
    ) OR
    (password AND (wrong OR incorrect OR invalid))
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "auth.log"
    - "security.log"
    - "app.log"

output:
  output_file: /security/failed-logins-{timestamp}.txt
  show_stats: true
  format: json

processing:
  max_workers: 4
```

#### Brute Force Detection Script

```python
# security/detect_brute_force.py
import subprocess
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class LoginAttempt:
    """Represents a failed login attempt."""
    timestamp: datetime
    username: str
    ip_address: str
    source_file: str

class BruteForceDetector:
    """Detect brute force login attempts."""
    
    def __init__(self, config_file: str, threshold: int = 5, window_minutes: int = 10):
        self.config_file = config_file
        self.threshold = threshold
        self.window_minutes = window_minutes
    
    def detect(self) -> Dict[str, List[LoginAttempt]]:
        """Detect brute force attempts."""
        
        # Run log filter
        result = subprocess.run([
            'log-filter',
            '--config', self.config_file,
            '--format', 'json',
            '--since', f'{self.window_minutes}m'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running log-filter: {result.stderr}")
            return {}
        
        # Parse login attempts
        attempts = self.parse_attempts(result.stdout)
        
        # Group by IP and username
        by_ip = defaultdict(list)
        by_username = defaultdict(list)
        
        for attempt in attempts:
            by_ip[attempt.ip_address].append(attempt)
            by_username[attempt.username].append(attempt)
        
        # Find suspicious patterns
        suspicious_ips = {
            ip: attempts_list
            for ip, attempts_list in by_ip.items()
            if len(attempts_list) >= self.threshold
        }
        
        suspicious_usernames = {
            username: attempts_list
            for username, attempts_list in by_username.items()
            if len(attempts_list) >= self.threshold
        }
        
        # Report findings
        self.report_findings(suspicious_ips, suspicious_usernames)
        
        return suspicious_ips
    
    def parse_attempts(self, json_output: str) -> List[LoginAttempt]:
        """Parse login attempts from JSON output."""
        
        attempts = []
        
        for line in json_output.split('\n'):
            if not line.strip():
                continue
            
            try:
                event = json.loads(line)
                content = event.get('content', '')
                
                # Extract IP address
                ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
                ip_address = ip_match.group() if ip_match else 'unknown'
                
                # Extract username
                username_match = re.search(r'user(?:name)?[:\s=]+(\w+)', content, re.IGNORECASE)
                username = username_match.group(1) if username_match else 'unknown'
                
                # Extract timestamp
                timestamp_str = event.get('timestamp', '')
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    timestamp = datetime.now()
                
                attempts.append(LoginAttempt(
                    timestamp=timestamp,
                    username=username,
                    ip_address=ip_address,
                    source_file=event.get('file', '')
                ))
            
            except json.JSONDecodeError:
                continue
        
        return attempts
    
    def report_findings(self, suspicious_ips: Dict, suspicious_usernames: Dict):
        """Generate report of findings."""
        
        print("=" * 80)
        print("BRUTE FORCE DETECTION REPORT")
        print("=" * 80)
        print(f"Detection Window: Last {self.window_minutes} minutes")
        print(f"Threshold: {self.threshold} attempts")
        print("")
        
        if suspicious_ips:
            print("🚨 SUSPICIOUS IP ADDRESSES:")
            print("-" * 80)
            
            for ip, attempts in sorted(suspicious_ips.items(), 
                                      key=lambda x: len(x[1]), 
                                      reverse=True):
                print(f"\n  IP: {ip}")
                print(f"  Attempts: {len(attempts)}")
                print(f"  Usernames targeted: {', '.join(set(a.username for a in attempts))}")
                print(f"  First attempt: {min(a.timestamp for a in attempts)}")
                print(f"  Last attempt:  {max(a.timestamp for a in attempts)}")
                
                # Recommendation
                if len(attempts) > self.threshold * 2:
                    print(f"  ⚠️  CRITICAL: Block this IP immediately!")
        else:
            print("✅ No suspicious IP addresses detected")
        
        print("\n" + "=" * 80)
        
        if suspicious_usernames:
            print("🚨 TARGETED USERNAMES:")
            print("-" * 80)
            
            for username, attempts in sorted(suspicious_usernames.items(),
                                            key=lambda x: len(x[1]),
                                            reverse=True):
                print(f"\n  Username: {username}")
                print(f"  Attempts: {len(attempts)}")
                print(f"  Source IPs: {', '.join(set(a.ip_address for a in attempts))}")
                
                if len(attempts) > self.threshold * 3:
                    print(f"  ⚠️  WARNING: Account under heavy attack - consider temporary lockout")
        
        print("\n" + "=" * 80)
    
    def block_ip(self, ip_address: str):
        """Block IP address using iptables (requires root)."""
        import subprocess
        
        subprocess.run([
            'iptables', '-A', 'INPUT', '-s', ip_address, '-j', 'DROP'
        ])
        
        print(f"✅ Blocked IP: {ip_address}")

def main():
    detector = BruteForceDetector(
        config_file='failed-logins.yaml',
        threshold=5,
        window_minutes=10
    )
    
    suspicious_ips = detector.detect()
    
    # Auto-block critical threats
    for ip, attempts in suspicious_ips.items():
        if len(attempts) > 20:
            print(f"\n🚨 CRITICAL THREAT: {ip} - Auto-blocking...")
            # detector.block_ip(ip)  # Uncomment to enable auto-blocking

if __name__ == "__main__":
    main()
```

#### Usage

```bash
# Detect brute force attempts
python detect_brute_force.py

# Run continuously
watch -n 300 python detect_brute_force.py  # Every 5 minutes

# Cron job
*/5 * * * * /security/detect_brute_force.py >> /var/log/brute-force-detection.log
```

---

## Example 2: SQL Injection Detection

### Scenario: Detect SQL Injection Attempts

Monitor for SQL injection patterns in application logs.

#### Configuration

```yaml
# security/sql-injection.yaml
search:
  expression: |
    (sql OR query) AND
    (
      (injection OR malicious OR suspicious) OR
      (union AND select) OR
      (drop AND table) OR
      (exec OR execute) OR
      (' OR '1'='1) OR
      (-- OR /* OR */) OR
      (xp_cmdshell OR sp_executesql)
    )
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "app.log"
    - "web.log"
    - "security.log"

output:
  output_file: /security/sql-injection-{timestamp}.txt
  show_stats: true
  format: json
  include_context: 5  # Include 5 lines before/after
```

#### SQL Injection Analyzer

```python
# security/analyze_sql_injection.py
import re
import json
from typing import List, Dict
from dataclasses import dataclass
from collections import Counter

@dataclass
class InjectionAttempt:
    """SQL injection attempt."""
    timestamp: str
    ip_address: str
    endpoint: str
    payload: str
    attack_type: str

class SQLInjectionAnalyzer:
    """Analyze SQL injection attempts."""
    
    PATTERNS = {
        'union_based': r'union\s+select',
        'boolean_based': r"'\s*or\s*'1'\s*=\s*'1",
        'time_based': r'sleep\s*\(\s*\d+\s*\)',
        'error_based': r'convert\s*\(',
        'stacked_queries': r';\s*drop\s+table',
        'command_execution': r'xp_cmdshell|sp_executesql'
    }
    
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    def analyze(self) -> List[InjectionAttempt]:
        """Analyze SQL injection attempts."""
        
        attempts = []
        
        with open(self.log_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    content = event.get('content', '')
                    
                    # Extract details
                    ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
                    ip_address = ip_match.group() if ip_match else 'unknown'
                    
                    endpoint_match = re.search(r'(GET|POST|PUT|DELETE)\s+(\S+)', content)
                    endpoint = endpoint_match.group(2) if endpoint_match else 'unknown'
                    
                    # Detect attack type
                    attack_types = []
                    for attack_name, pattern in self.PATTERNS.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            attack_types.append(attack_name)
                    
                    if attack_types:
                        attempts.append(InjectionAttempt(
                            timestamp=event.get('timestamp', ''),
                            ip_address=ip_address,
                            endpoint=endpoint,
                            payload=content[:200],
                            attack_type=', '.join(attack_types)
                        ))
                
                except json.JSONDecodeError:
                    continue
        
        self.report(attempts)
        return attempts
    
    def report(self, attempts: List[InjectionAttempt]):
        """Generate analysis report."""
        
        print("=" * 80)
        print("SQL INJECTION ANALYSIS REPORT")
        print("=" * 80)
        
        if not attempts:
            print("\n✅ No SQL injection attempts detected")
            return
        
        print(f"\n🚨 Total Attempts: {len(attempts)}")
        
        # By IP
        by_ip = Counter(a.ip_address for a in attempts)
        print("\nTop Attacking IPs:")
        for ip, count in by_ip.most_common(10):
            print(f"  {ip}: {count} attempts")
        
        # By endpoint
        by_endpoint = Counter(a.endpoint for a in attempts)
        print("\nMost Targeted Endpoints:")
        for endpoint, count in by_endpoint.most_common(10):
            print(f"  {endpoint}: {count} attempts")
        
        # By attack type
        attack_types = []
        for attempt in attempts:
            attack_types.extend(attempt.attack_type.split(', '))
        by_type = Counter(attack_types)
        
        print("\nAttack Type Distribution:")
        for attack_type, count in by_type.most_common():
            print(f"  {attack_type.replace('_', ' ').title()}: {count}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        critical_ips = [ip for ip, count in by_ip.items() if count > 5]
        if critical_ips:
            print("\n⚠️  Block these IPs immediately:")
            for ip in critical_ips:
                print(f"    iptables -A INPUT -s {ip} -j DROP")
        
        vulnerable_endpoints = [ep for ep, count in by_endpoint.items() if count > 3]
        if vulnerable_endpoints:
            print("\n⚠️  Review security of these endpoints:")
            for endpoint in vulnerable_endpoints:
                print(f"    {endpoint}")
        
        print("\n⚠️  General recommendations:")
        print("    1. Use parameterized queries")
        print("    2. Implement input validation")
        print("    3. Use Web Application Firewall (WAF)")
        print("    4. Enable database query logging")
        print("    5. Regular security audits")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_sql_injection.py <log_file>")
        sys.exit(1)
    
    analyzer = SQLInjectionAnalyzer(sys.argv[1])
    analyzer.analyze()

if __name__ == "__main__":
    main()
```

---

## Example 3: Suspicious Access Patterns

### Scenario: Detect Anomalous Behavior

Identify unusual access patterns that may indicate security breaches.

#### Configuration

```yaml
# security/suspicious-access.yaml
search:
  expression: |
    (
      (access OR request) AND
      (suspicious OR unusual OR anomaly OR abnormal)
    ) OR
    (
      (404 OR 403 OR 401) AND
      (scan OR probe OR enumerate)
    ) OR
    (directory AND (traversal OR listing)) OR
    (path AND (../ OR ..\\)) OR
    (sensitive AND (file OR directory OR data))
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "access.log"
    - "web.log"

output:
  output_file: /security/suspicious-access-{timestamp}.txt
  format: json
```

#### Anomaly Detection

```python
# security/detect_anomalies.py
import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict

class AnomalyDetector:
    """Detect anomalous access patterns."""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.access_patterns = defaultdict(lambda: {
            'paths': Counter(),
            'times': [],
            'user_agents': Counter(),
            'status_codes': Counter()
        })
    
    def analyze(self):
        """Analyze access patterns."""
        
        # Parse logs
        with open(self.log_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    self.parse_event(event)
                except json.JSONDecodeError:
                    continue
        
        # Detect anomalies
        anomalies = self.detect_anomalies()
        
        # Report
        self.report(anomalies)
    
    def parse_event(self, event: Dict):
        """Parse access log event."""
        
        content = event.get('content', '')
        
        # Extract IP
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
        if not ip_match:
            return
        
        ip = ip_match.group()
        
        # Extract path
        path_match = re.search(r'(GET|POST|PUT|DELETE)\s+(\S+)', content)
        if path_match:
            self.access_patterns[ip]['paths'][path_match.group(2)] += 1
        
        # Extract timestamp
        try:
            timestamp = datetime.fromisoformat(event.get('timestamp', ''))
            self.access_patterns[ip]['times'].append(timestamp)
        except (ValueError, TypeError):
            pass
        
        # Extract status code
        status_match = re.search(r'\s(\d{3})\s', content)
        if status_match:
            self.access_patterns[ip]['status_codes'][status_match.group(1)] += 1
        
        # Extract user agent
        ua_match = re.search(r'"([^"]*)"$', content)
        if ua_match:
            self.access_patterns[ip]['user_agents'][ua_match.group(1)] += 1
    
    def detect_anomalies(self) -> Dict[str, List[str]]:
        """Detect various anomalies."""
        
        anomalies = defaultdict(list)
        
        for ip, patterns in self.access_patterns.items():
            # 1. High request rate
            if len(patterns['times']) > 100:
                anomalies['high_request_rate'].append(ip)
            
            # 2. Path scanning
            unique_paths = len(patterns['paths'])
            if unique_paths > 50:
                anomalies['path_scanning'].append(ip)
            
            # 3. High error rate
            total_requests = sum(patterns['status_codes'].values())
            error_requests = sum(
                count for status, count in patterns['status_codes'].items()
                if status.startswith('4') or status.startswith('5')
            )
            
            if total_requests > 0 and (error_requests / total_requests) > 0.5:
                anomalies['high_error_rate'].append(ip)
            
            # 4. Suspicious user agent
            for ua in patterns['user_agents']:
                if any(keyword in ua.lower() for keyword in ['bot', 'scanner', 'crawler', 'nikto', 'nmap']):
                    if ip not in anomalies['suspicious_user_agent']:
                        anomalies['suspicious_user_agent'].append(ip)
            
            # 5. Directory traversal attempts
            for path in patterns['paths']:
                if '../' in path or '..\\' in path:
                    if ip not in anomalies['directory_traversal']:
                        anomalies['directory_traversal'].append(ip)
        
        return anomalies
    
    def report(self, anomalies: Dict[str, List[str]]):
        """Generate anomaly report."""
        
        print("=" * 80)
        print("ANOMALY DETECTION REPORT")
        print("=" * 80)
        
        total_anomalies = sum(len(ips) for ips in anomalies.values())
        
        if total_anomalies == 0:
            print("\n✅ No anomalies detected")
            return
        
        print(f"\n🚨 Total IPs with anomalies: {total_anomalies}")
        
        # Report each anomaly type
        for anomaly_type, ips in sorted(anomalies.items()):
            if not ips:
                continue
            
            print(f"\n{anomaly_type.replace('_', ' ').title()}:")
            print(f"  Affected IPs: {len(ips)}")
            
            for ip in ips[:10]:  # Show top 10
                patterns = self.access_patterns[ip]
                
                print(f"\n  {ip}:")
                print(f"    Total requests: {len(patterns['times'])}")
                print(f"    Unique paths: {len(patterns['paths'])}")
                print(f"    Status codes: {dict(patterns['status_codes'].most_common(3))}")
                
                # Show most accessed paths
                top_paths = patterns['paths'].most_common(5)
                if top_paths:
                    print(f"    Top paths: {', '.join(p for p, _ in top_paths)}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if anomalies['high_request_rate']:
            print("\n⚠️  High Request Rate:")
            print("    - Implement rate limiting")
            print("    - Consider using CDN/WAF")
        
        if anomalies['path_scanning']:
            print("\n⚠️  Path Scanning:")
            print("    - Block scanning IPs")
            print("    - Disable directory listing")
        
        if anomalies['directory_traversal']:
            print("\n⚠️  Directory Traversal:")
            print("    - CRITICAL: Block these IPs immediately")
            print("    - Review path validation")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detect_anomalies.py <log_file>")
        sys.exit(1)
    
    detector = AnomalyDetector(sys.argv[1])
    detector.analyze()

if __name__ == "__main__":
    main()
```

---

## Example 4: Compliance Auditing

### Scenario: PCI-DSS Compliance Monitoring

Monitor for compliance violations.

#### Configuration

```yaml
# security/compliance-audit.yaml
search:
  expression: |
    (
      (credit-card OR card-number OR cvv OR pan) AND
      (logged OR stored OR displayed OR exposed)
    ) OR
    (
      (password OR secret OR key) AND
      (plain-text OR unencrypted OR cleartext)
    ) OR
    (pii AND (exposed OR leaked OR unauthorized))
  case_sensitive: false

files:
  search_root: /var/log
  include_patterns:
    - "*.log"

output:
  output_file: /security/compliance-violations-{timestamp}.txt
  format: json
```

#### Compliance Checker

```python
# security/compliance_checker.py
import json
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ComplianceViolation:
    """Compliance violation."""
    timestamp: str
    violation_type: str
    severity: str
    description: str
    source_file: str

class ComplianceChecker:
    """Check for compliance violations."""
    
    VIOLATIONS = {
        'credit_card_exposure': {
            'pattern': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'severity': 'CRITICAL',
            'description': 'Credit card number in logs'
        },
        'password_plaintext': {
            'pattern': r'password[:\s=]+[^\s]+',
            'severity': 'HIGH',
            'description': 'Plain text password'
        },
        'ssn_exposure': {
            'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
            'severity': 'CRITICAL',
            'description': 'Social Security Number in logs'
        },
        'api_key_exposure': {
            'pattern': r'(api[_-]?key|secret[_-]?key)[:\s=]+[^\s]+',
            'severity': 'HIGH',
            'description': 'API key in logs'
        }
    }
    
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    def check(self) -> List[ComplianceViolation]:
        """Check for compliance violations."""
        
        violations = []
        
        with open(self.log_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    content = event.get('content', '')
                    
                    # Check each violation type
                    for violation_type, config in self.VIOLATIONS.items():
                        if re.search(config['pattern'], content, re.IGNORECASE):
                            violations.append(ComplianceViolation(
                                timestamp=event.get('timestamp', ''),
                                violation_type=violation_type,
                                severity=config['severity'],
                                description=config['description'],
                                source_file=event.get('file', '')
                            ))
                
                except json.JSONDecodeError:
                    continue
        
        self.report(violations)
        return violations
    
    def report(self, violations: List[ComplianceViolation]):
        """Generate compliance report."""
        
        print("=" * 80)
        print("COMPLIANCE AUDIT REPORT")
        print("=" * 80)
        
        if not violations:
            print("\n✅ No compliance violations detected")
            return
        
        print(f"\n🚨 Total Violations: {len(violations)}")
        
        # Group by severity
        critical = [v for v in violations if v.severity == 'CRITICAL']
        high = [v for v in violations if v.severity == 'HIGH']
        
        print(f"\nBy Severity:")
        print(f"  CRITICAL: {len(critical)}")
        print(f"  HIGH: {len(high)}")
        
        # Group by type
        from collections import Counter
        by_type = Counter(v.violation_type for v in violations)
        
        print(f"\nBy Type:")
        for violation_type, count in by_type.most_common():
            print(f"  {violation_type.replace('_', ' ').title()}: {count}")
        
        # Critical violations details
        if critical:
            print("\n" + "=" * 80)
            print("CRITICAL VIOLATIONS")
            print("=" * 80)
            
            for v in critical[:10]:  # Show first 10
                print(f"\n  {v.timestamp}")
                print(f"  Type: {v.description}")
                print(f"  File: {v.source_file}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("IMMEDIATE ACTIONS REQUIRED")
        print("=" * 80)
        
        print("\n1. Review and redact sensitive data from logs")
        print("2. Update logging configuration to exclude sensitive fields")
        print("3. Implement log sanitization")
        print("4. Review access controls for log files")
        print("5. Report to compliance officer")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python compliance_checker.py <log_file>")
        sys.exit(1)
    
    checker = ComplianceChecker(sys.argv[1])
    violations = checker.check()
    
    # Exit with error if violations found
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()
```

---

## Automated Security Monitoring

### Continuous Monitoring Setup

```bash
#!/bin/bash
# security/continuous-monitoring.sh

LOG_DIR="/var/log"
SECURITY_DIR="/security/monitoring"
mkdir -p "$SECURITY_DIR"

while true; do
  echo "$(date): Running security checks..."
  
  # Check 1: Failed logins
  log-filter --config failed-logins.yaml
  python detect_brute_force.py
  
  # Check 2: SQL injection
  log-filter --config sql-injection.yaml
  if [ -f /security/sql-injection-*.txt ]; then
    python analyze_sql_injection.py /security/sql-injection-*.txt
  fi
  
  # Check 3: Anomalies
  log-filter --config suspicious-access.yaml
  if [ -f /security/suspicious-access-*.txt ]; then
    python detect_anomalies.py /security/suspicious-access-*.txt
  fi
  
  # Check 4: Compliance
  log-filter --config compliance-audit.yaml
  if [ -f /security/compliance-violations-*.txt ]; then
    python compliance_checker.py /security/compliance-violations-*.txt
  fi
  
  # Sleep for 5 minutes
  sleep 300
done
```

---

## Integration with SIEM

### Splunk Integration

```python
# security/splunk_integration.py
import subprocess
import json
import requests

def send_to_splunk(events: list, splunk_url: str, hec_token: str):
    """Send security events to Splunk."""
    
    headers = {
        'Authorization': f'Splunk {hec_token}',
        'Content-Type': 'application/json'
    }
    
    for event in events:
        payload = {
            'event': event,
            'sourcetype': 'log-filter:security',
            'index': 'security'
        }
        
        response = requests.post(
            f'{splunk_url}/services/collector/event',
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"Error sending to Splunk: {response.text}")
```

---

## Best Practices

1. **Automate monitoring** - Run security checks continuously
2. **Prioritize alerts** - Critical threats need immediate action
3. **Regular audits** - Review security logs daily
4. **Block threats** - Automatically block malicious IPs
5. **Document incidents** - Keep records for compliance
6. **Update signatures** - Keep attack patterns current
7. **Test detection** - Regularly test with known patterns

---

## What's Next?

- **[Monitoring Examples](monitoring.md)** - Application monitoring patterns
- **[DevOps Examples](devops.md)** - CI/CD integration
- **[Integration Guide](../integration_guide.md)** - Full integration patterns

---

**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
