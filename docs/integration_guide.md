# Integration Guide

**Last Updated:** January 8, 2026  
**Version:** 2.0.0  
**Target Audience:** DevOps Engineers, Software Architects, Integration Specialists

---

## Table of Contents

- [Python API Usage](#python-api-usage)
- [CI/CD Integration](#cicd-integration)
- [Monitoring Integration](#monitoring-integration)
- [Log Aggregation Systems](#log-aggregation-systems)
- [Container Orchestration](#container-orchestration)
- [Event-Driven Integration](#event-driven-integration)
- [REST API Wrapper](#rest-api-wrapper)
- [Cloud Platform Integration](#cloud-platform-integration)

---

## Python API Usage

### Programmatic Usage

Log Filter can be embedded directly into Python applications:

#### Basic Integration

```python
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.config.models import (
    ApplicationConfig,
    SearchConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig
)
from pathlib import Path

def filter_logs(log_dir: str, expression: str, output_file: str):
    """Filter logs programmatically."""
    config = ApplicationConfig(
        search=SearchConfig(
            expression=expression,
            case_sensitive=False
        ),
        files=FileConfig(
            search_root=Path(log_dir),
            include_patterns=["*.log", "*.gz"]
        ),
        output=OutputConfig(
            output_file=Path(output_file),
            show_stats=True
        ),
        processing=ProcessingConfig(
            max_workers=4
        )
    )
    
    pipeline = ProcessingPipeline(config)
    result = pipeline.run()
    
    return {
        "files_processed": result.total_files,
        "records_processed": result.total_records,
        "matches_found": result.total_matches,
        "processing_time": result.total_time
    }

# Use in your application
if __name__ == "__main__":
    result = filter_logs(
        log_dir="/var/log/myapp",
        expression="ERROR AND database",
        output_file="errors.txt"
    )
    print(f"Found {result['matches_found']} matching records")
```

#### Advanced Integration with Callbacks

```python
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.domain.models import LogRecord
from typing import Callable, List

class LogFilterService:
    """Service for filtering logs with callbacks."""
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.pipeline = ProcessingPipeline(config)
        self.match_callbacks: List[Callable[[LogRecord], None]] = []
    
    def add_match_callback(self, callback: Callable[[LogRecord], None]):
        """Add callback for each matching record."""
        self.match_callbacks.append(callback)
    
    def process(self):
        """Process logs and trigger callbacks."""
        for record in self.pipeline.process_stream():
            for callback in self.match_callbacks:
                try:
                    callback(record)
                except Exception as e:
                    print(f"Callback error: {e}")

# Usage example
service = LogFilterService(config)

# Add callbacks
service.add_match_callback(lambda r: print(f"Match: {r.content}"))
service.add_match_callback(lambda r: send_to_elasticsearch(r))
service.add_match_callback(lambda r: trigger_alert(r))

# Process
service.process()
```

### Custom Pipeline Construction

Build a custom processing pipeline:

```python
from log_filter.core.parser import parse
from log_filter.core.evaluator import Evaluator
from log_filter.processing.record_parser import StreamingRecordParser
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
from log_filter.statistics.collector import StatisticsCollector
from pathlib import Path

class CustomLogPipeline:
    """Custom log processing pipeline."""
    
    def __init__(self, expression: str):
        # Parse expression
        self.ast = parse(expression)
        self.evaluator = Evaluator(self.ast, case_sensitive=False)
        
        # Set up components
        self.record_parser = StreamingRecordParser()
        self.file_handler = FileHandlerFactory()
        self.stats = StatisticsCollector()
    
    def process_file(self, file_path: Path):
        """Process a single file."""
        handler = self.file_handler.get_handler(file_path)
        matches = []
        
        for line in handler.read_lines(file_path):
            records = self.record_parser.feed_line(line, line_number=0)
            
            for record in records:
                if self.evaluator.evaluate(record.content):
                    matches.append(record)
        
        # Get final records
        final_records = self.record_parser.finalize()
        for record in final_records:
            if self.evaluator.evaluate(record.content):
                matches.append(record)
        
        return matches
    
    def process_multiple(self, files: List[Path]):
        """Process multiple files."""
        all_matches = []
        
        for file_path in files:
            try:
                matches = self.process_file(file_path)
                all_matches.extend(matches)
                
                self.stats.record_file_processed(
                    file_path=str(file_path),
                    records=len(matches),
                    matches=len(matches),
                    time_taken=0,
                    bytes_count=file_path.stat().st_size
                )
            except Exception as e:
                self.stats.record_error("processing_error", str(file_path))
        
        return all_matches

# Use custom pipeline
pipeline = CustomLogPipeline("ERROR OR WARNING")
matches = pipeline.process_multiple([Path("app.log"), Path("db.log")])
print(f"Found {len(matches)} matches")
```

### Event Hooks

Implement event hooks for custom processing:

```python
from typing import Protocol
from log_filter.domain.models import LogRecord

class ProcessingHooks(Protocol):
    """Protocol for processing hooks."""
    
    def on_file_start(self, file_path: Path) -> None:
        """Called when file processing starts."""
        ...
    
    def on_file_complete(self, file_path: Path, matches: int) -> None:
        """Called when file processing completes."""
        ...
    
    def on_match(self, record: LogRecord) -> None:
        """Called for each matching record."""
        ...
    
    def on_error(self, error: Exception, context: str) -> None:
        """Called when an error occurs."""
        ...

class MyHooks:
    """Custom hooks implementation."""
    
    def on_file_start(self, file_path: Path):
        print(f"Processing {file_path.name}...")
    
    def on_file_complete(self, file_path: Path, matches: int):
        print(f"Completed {file_path.name}: {matches} matches")
    
    def on_match(self, record: LogRecord):
        # Send to external system
        send_to_splunk(record)
    
    def on_error(self, error: Exception, context: str):
        print(f"Error in {context}: {error}")
        # Log to monitoring system
        send_error_to_sentry(error, context)

# Use hooks
hooks = MyHooks()
pipeline = ProcessingPipeline(config, hooks=hooks)
pipeline.run()
```

---

## CI/CD Integration

### GitHub Actions

Create a workflow to filter logs in your CI/CD pipeline:

```yaml
# .github/workflows/log-analysis.yml
name: Log Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM
    - cron: '0 2 * * *'

jobs:
  analyze-logs:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Log Filter
        run: |
          pip install log-filter
      
      - name: Download logs from artifact storage
        uses: actions/download-artifact@v3
        with:
          name: application-logs
          path: ./logs
      
      - name: Filter error logs
        run: |
          log-filter \
            --input ./logs \
            --expr "ERROR OR CRITICAL" \
            --output ./filtered-errors.txt \
            --stats
      
      - name: Check for critical errors
        run: |
          if grep -q "CRITICAL" ./filtered-errors.txt; then
            echo "::error::Critical errors found in logs!"
            exit 1
          fi
      
      - name: Upload filtered logs
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: filtered-logs
          path: ./filtered-errors.txt
      
      - name: Comment on PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const content = fs.readFileSync('./filtered-errors.txt', 'utf8');
            const lines = content.split('\n').length;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Log Analysis Results\n\n` +
                    `Found ${lines} error/critical messages.\n\n` +
                    `<details>\n<summary>View Errors</summary>\n\n` +
                    `\`\`\`\n${content.slice(0, 2000)}\n\`\`\`\n</details>`
            });
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - analyze

analyze_logs:
  stage: analyze
  image: python:3.10
  
  before_script:
    - pip install log-filter
  
  script:
    # Download logs from artifacts or external storage
    - aws s3 sync s3://my-logs-bucket/$(date +%Y-%m-%d) ./logs/
    
    # Filter logs
    - log-filter 
        --input ./logs
        --expr "ERROR OR WARNING"
        --output ./filtered.txt
        --config ./ci/log-filter-config.yaml
    
    # Generate statistics
    - log-filter 
        --input ./logs
        --expr "ERROR"
        --stats-only > error-stats.json
    
    # Check error threshold
    - |
      error_count=$(grep -c "ERROR" ./filtered.txt || echo 0)
      if [ $error_count -gt 100 ]; then
        echo "Too many errors: $error_count"
        exit 1
      fi
  
  artifacts:
    paths:
      - filtered.txt
      - error-stats.json
    reports:
      metrics: error-stats.json
    expire_in: 30 days
  
  only:
    - main
    - develop
  
  when: always
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        LOG_DIR = "${WORKSPACE}/logs"
        OUTPUT_DIR = "${WORKSPACE}/filtered-logs"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m pip install log-filter
                    mkdir -p ${OUTPUT_DIR}
                '''
            }
        }
        
        stage('Collect Logs') {
            steps {
                // Copy logs from deployment
                sh '''
                    scp -r deploy-server:/var/log/myapp/* ${LOG_DIR}/
                '''
            }
        }
        
        stage('Filter Logs') {
            steps {
                script {
                    def result = sh(
                        script: """
                            log-filter \
                                --input ${LOG_DIR} \
                                --expr "ERROR OR CRITICAL" \
                                --output ${OUTPUT_DIR}/errors.txt \
                                --stats
                        """,
                        returnStatus: true
                    )
                    
                    if (result != 0) {
                        error("Log filtering failed")
                    }
                }
            }
        }
        
        stage('Analyze Results') {
            steps {
                script {
                    def errorCount = sh(
                        script: "wc -l < ${OUTPUT_DIR}/errors.txt",
                        returnStdout: true
                    ).trim().toInteger()
                    
                    echo "Found ${errorCount} errors"
                    
                    if (errorCount > 50) {
                        unstable("High error count: ${errorCount}")
                    }
                    
                    if (errorCount > 100) {
                        error("Critical: too many errors")
                    }
                }
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'filtered-logs/**/*.txt'
                
                // Send to monitoring
                sh '''
                    python3 scripts/send_metrics.py \
                        --file ${OUTPUT_DIR}/errors.txt \
                        --prometheus http://prometheus:9090
                '''
            }
        }
    }
    
    post {
        failure {
            emailext(
                subject: "Log Analysis Failed: ${env.JOB_NAME}",
                body: "Log filtering or analysis failed. Check ${env.BUILD_URL}",
                to: "devops@company.com"
            )
        }
    }
}
```

### Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.10'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '$(pythonVersion)'
    displayName: 'Use Python $(pythonVersion)'
  
  - script: |
      python -m pip install --upgrade pip
      pip install log-filter
    displayName: 'Install Log Filter'
  
  - task: DownloadPipelineArtifact@2
    inputs:
      artifact: 'application-logs'
      path: $(Pipeline.Workspace)/logs
    displayName: 'Download logs'
  
  - script: |
      log-filter \
        --input $(Pipeline.Workspace)/logs \
        --expr "ERROR OR CRITICAL" \
        --output $(Build.ArtifactStagingDirectory)/filtered-errors.txt \
        --stats
    displayName: 'Filter error logs'
  
  - task: PublishPipelineArtifact@1
    inputs:
      targetPath: '$(Build.ArtifactStagingDirectory)/filtered-errors.txt'
      artifact: 'filtered-logs'
    displayName: 'Publish filtered logs'
  
  - script: |
      error_count=$(wc -l < $(Build.ArtifactStagingDirectory)/filtered-errors.txt)
      echo "##vso[task.setvariable variable=ErrorCount]$error_count"
      echo "Found $error_count errors"
      
      if [ $error_count -gt 100 ]; then
        echo "##vso[task.logissue type=error]Too many errors: $error_count"
        exit 1
      elif [ $error_count -gt 50 ]; then
        echo "##vso[task.logissue type=warning]High error count: $error_count"
      fi
    displayName: 'Validate error threshold'
```

---

## Monitoring Integration

### Prometheus Integration

Export metrics to Prometheus:

```python
# prometheus_exporter.py
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.statistics.collector import StatisticsCollector
import time

# Define metrics
files_processed = Counter(
    'log_filter_files_processed_total',
    'Total number of files processed'
)
records_processed = Counter(
    'log_filter_records_processed_total',
    'Total number of records processed'
)
matches_found = Counter(
    'log_filter_matches_found_total',
    'Total number of matches found'
)
processing_duration = Histogram(
    'log_filter_processing_duration_seconds',
    'Time spent processing logs'
)
active_workers = Gauge(
    'log_filter_active_workers',
    'Number of active worker threads'
)

def process_with_metrics(config):
    """Process logs and export metrics to Prometheus."""
    with processing_duration.time():
        collector = StatisticsCollector()
        pipeline = ProcessingPipeline(config, stats_collector=collector)
        
        result = pipeline.run()
        
        # Update metrics
        files_processed.inc(result.total_files)
        records_processed.inc(result.total_records)
        matches_found.inc(result.total_matches)
    
    stats = collector.get_stats()
    return stats

if __name__ == "__main__":
    # Start metrics server
    start_http_server(8000)
    print("Metrics available at http://localhost:8000/metrics")
    
    # Process logs periodically
    while True:
        try:
            stats = process_with_metrics(config)
            print(f"Processed {stats.files_processed} files")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(300)  # Every 5 minutes
```

### Grafana Dashboard

Create a Grafana dashboard with these queries:

```text
# Files processed rate
rate(log_filter_files_processed_total[5m])

# Records processed rate
rate(log_filter_records_processed_total[5m])

# Match rate
rate(log_filter_matches_found_total[5m]) / 
rate(log_filter_records_processed_total[5m])

# Processing duration (p95)
histogram_quantile(0.95, log_filter_processing_duration_seconds_bucket)

# Active workers
log_filter_active_workers
```

### Elasticsearch Integration

Send matching records to Elasticsearch:

```python
# elasticsearch_integration.py
from elasticsearch import Elasticsearch
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.domain.models import LogRecord
from datetime import datetime

class ElasticsearchExporter:
    """Export filtered logs to Elasticsearch."""
    
    def __init__(self, es_url: str, index_name: str):
        self.es = Elasticsearch([es_url])
        self.index_name = index_name
    
    def export_record(self, record: LogRecord):
        """Export a single record to Elasticsearch."""
        doc = {
            'timestamp': record.timestamp.isoformat(),
            'level': record.level,
            'content': record.content,
            'source_file': str(record.source_file),
            'line_number': record.line_number,
            '@timestamp': datetime.utcnow().isoformat()
        }
        
        self.es.index(
            index=self.index_name,
            document=doc
        )
    
    def export_batch(self, records: list[LogRecord]):
        """Export multiple records in batch."""
        from elasticsearch.helpers import bulk
        
        actions = [
            {
                '_index': self.index_name,
                '_source': {
                    'timestamp': record.timestamp.isoformat(),
                    'level': record.level,
                    'content': record.content,
                    'source_file': str(record.source_file),
                    'line_number': record.line_number,
                    '@timestamp': datetime.utcnow().isoformat()
                }
            }
            for record in records
        ]
        
        bulk(self.es, actions)

# Usage
exporter = ElasticsearchExporter(
    es_url="http://elasticsearch:9200",
    index_name="filtered-logs"
)

# Process and export
for record in pipeline.process_stream():
    exporter.export_record(record)
```

### Splunk Integration

```python
# splunk_integration.py
import requests
import json
from log_filter.domain.models import LogRecord

class SplunkExporter:
    """Export logs to Splunk HEC (HTTP Event Collector)."""
    
    def __init__(self, hec_url: str, hec_token: str, source: str = "log-filter"):
        self.hec_url = hec_url
        self.headers = {
            'Authorization': f'Splunk {hec_token}',
            'Content-Type': 'application/json'
        }
        self.source = source
    
    def send_event(self, record: LogRecord):
        """Send single event to Splunk."""
        event = {
            'event': {
                'timestamp': record.timestamp.isoformat(),
                'level': record.level,
                'content': record.content,
                'source_file': str(record.source_file),
                'line_number': record.line_number
            },
            'source': self.source,
            'sourcetype': 'filtered_logs'
        }
        
        response = requests.post(
            f'{self.hec_url}/services/collector/event',
            headers=self.headers,
            data=json.dumps(event),
            verify=False
        )
        
        return response.status_code == 200
    
    def send_batch(self, records: list[LogRecord]):
        """Send multiple events in batch."""
        events = '\n'.join([
            json.dumps({
                'event': {
                    'timestamp': record.timestamp.isoformat(),
                    'level': record.level,
                    'content': record.content,
                    'source_file': str(record.source_file)
                },
                'source': self.source
            })
            for record in records
        ])
        
        response = requests.post(
            f'{self.hec_url}/services/collector/event',
            headers=self.headers,
            data=events,
            verify=False
        )
        
        return response.status_code == 200

# Usage
splunk = SplunkExporter(
    hec_url="https://splunk:8088",
    hec_token="your-hec-token-here"
)

batch = []
for record in pipeline.process_stream():
    batch.append(record)
    
    if len(batch) >= 100:
        splunk.send_batch(batch)
        batch = []

# Send remaining
if batch:
    splunk.send_batch(batch)
```

---

## Log Aggregation Systems

### Fluentd Integration

Create a Fluentd plugin to use Log Filter:

```ruby
# fluent-plugin-log-filter.rb
require 'fluent/plugin/filter'
require 'open3'
require 'json'

module Fluent::Plugin
  class LogFilterFilter < Filter
    Fluent::Plugin.register_filter('log_filter', self)
    
    config_param :expression, :string
    config_param :case_sensitive, :bool, default: false
    
    def filter(tag, time, record)
      content = record['message'] || record['log'] || ''
      
      # Use log-filter CLI to evaluate expression
      cmd = ['log-filter', '--expr', @expression, '--stdin']
      
      stdout, stderr, status = Open3.capture3(*cmd, stdin_data: content)
      
      if status.success? && !stdout.empty?
        record['filtered'] = true
        record['filter_expression'] = @expression
        record
      else
        nil  # Drop record if not matched
      end
    end
  end
end
```

Configuration:

```xml
<filter app.**>
  @type log_filter
  expression "ERROR OR WARNING"
  case_sensitive false
</filter>

<match app.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name filtered-logs
</match>
```

### Logstash Integration

```ruby
# logstash-filter-log-filter.conf
filter {
  if [message] {
    ruby {
      code => '
        require "open3"
        
        expression = "ERROR OR WARNING"
        message = event.get("message")
        
        cmd = ["log-filter", "--expr", expression, "--stdin"]
        stdout, stderr, status = Open3.capture3(*cmd, stdin_data: message)
        
        if status.success? && !stdout.empty?
          event.set("matched", true)
          event.set("filter_expression", expression)
        else
          event.cancel
        end
      '
    }
  }
}

output {
  if [matched] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "filtered-logs-%{+YYYY.MM.dd}"
    }
  }
}
```

---

## Container Orchestration

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  log-filter:
    image: log-filter:2.0.0
    container_name: log-filter
    volumes:
      - ./logs:/logs:ro
      - ./config:/config:ro
      - ./output:/output
    command: ["--config", "/config/config.yaml"]
    environment:
      - MAX_WORKERS=8
      - BUFFER_SIZE=32768
    restart: unless-stopped
    mem_limit: 2g
    cpus: 4
  
  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  # Optional: Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Kubernetes Deployment

```yaml
# kubernetes-deployment-advanced.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-filter-config
data:
  config.yaml: |
    search:
      expression: "ERROR OR CRITICAL"
      case_sensitive: false
    
    files:
      search_root: /var/log
      include_patterns:
        - "*.log"
        - "*.gz"
    
    output:
      output_file: /output/filtered.txt
      show_stats: true
    
    processing:
      max_workers: 8
      buffer_size: 32768

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-filter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: log-filter
  template:
    metadata:
      labels:
        app: log-filter
    spec:
      containers:
        - name: log-filter
          image: log-filter:2.0.0
          args: ["--config", "/config/config.yaml"]
          
          resources:
            requests:
              memory: "1Gi"
              cpu: "2"
            limits:
              memory: "4Gi"
              cpu: "4"
          
          volumeMounts:
            - name: config
              mountPath: /config
            - name: logs
              mountPath: /var/log
              readOnly: true
            - name: output
              mountPath: /output
          
          # Health checks
          livenessProbe:
            exec:
              command: ["cat", "/output/filtered.txt"]
            initialDelaySeconds: 30
            periodSeconds: 60
          
          # Metrics endpoint
          ports:
            - name: metrics
              containerPort: 8000
              protocol: TCP
      
      volumes:
        - name: config
          configMap:
            name: log-filter-config
        - name: logs
          persistentVolumeClaim:
            claimName: log-storage
        - name: output
          persistentVolumeClaim:
            claimName: filtered-output

---
# Service for metrics
apiVersion: v1
kind: Service
metadata:
  name: log-filter-metrics
  labels:
    app: log-filter
spec:
  ports:
    - port: 8000
      name: metrics
  selector:
    app: log-filter

---
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: log-filter
  labels:
    app: log-filter
spec:
  selector:
    matchLabels:
      app: log-filter
  endpoints:
    - port: metrics
      interval: 30s
```

---

## Event-Driven Integration

### AWS Lambda

```python
# lambda_handler.py
import json
import boto3
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.config.models import ApplicationConfig
import tempfile
from pathlib import Path

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """Process logs triggered by S3 event."""
    
    # Get S3 object details from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Processing s3://{bucket}/{key}")
    
    # Download file to temp location
    with tempfile.TemporaryDirectory() as tmpdir:
        local_file = Path(tmpdir) / "input.log"
        s3.download_file(bucket, key, str(local_file))
        
        # Configure pipeline
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR OR CRITICAL"),
            files=FileConfig(search_root=local_file.parent),
            output=OutputConfig(output_file=Path(tmpdir) / "output.txt"),
            processing=ProcessingConfig(max_workers=2)
        )
        
        # Process
        pipeline = ProcessingPipeline(config)
        result = pipeline.run()
        
        # Upload results
        if result.total_matches > 0:
            output_key = f"filtered/{key}"
            s3.upload_file(
                str(config.output.output_file),
                bucket,
                output_key
            )
            
            print(f"Uploaded results to s3://{bucket}/{output_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'files_processed': result.total_files,
                'matches_found': result.total_matches,
                'output_location': f"s3://{bucket}/{output_key}"
            })
        }
```

### Azure Functions

```python
# __init__.py
import azure.functions as func
from log_filter.processing.pipeline import ProcessingPipeline
from pathlib import Path
import tempfile
import logging

def main(blobin: func.InputStream, blobout: func.Out[bytes]):
    """Azure Function triggered by blob storage."""
    
    logging.info(f"Processing blob: {blobin.name}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write input to temp file
        input_file = Path(tmpdir) / "input.log"
        input_file.write_bytes(blobin.read())
        
        # Configure and process
        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=input_file.parent),
            output=OutputConfig(output_file=Path(tmpdir) / "output.txt")
        )
        
        pipeline = ProcessingPipeline(config)
        result = pipeline.run()
        
        # Output results
        if result.total_matches > 0:
            output_content = config.output.output_file.read_bytes()
            blobout.set(output_content)
            
            logging.info(f"Found {result.total_matches} matches")
        else:
            logging.info("No matches found")
```

---

## REST API Wrapper

Create a REST API wrapper for Log Filter:

```python
# api_server.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from log_filter.processing.pipeline import ProcessingPipeline
from log_filter.config.models import ApplicationConfig
import tempfile
from pathlib import Path
import uuid

app = FastAPI(title="Log Filter API", version="2.0.0")

# Store for async job results
jobs = {}

class FilterRequest(BaseModel):
    expression: str
    case_sensitive: bool = False
    max_workers: int = 4

class FilterResponse(BaseModel):
    job_id: str
    status: str
    matches: int = 0
    results: list[str] = []

@app.post("/filter", response_model=FilterResponse)
async def filter_logs(
    file: UploadFile = File(...),
    request: FilterRequest = None
):
    """Filter uploaded log file."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded file
        input_path = Path(tmpdir) / file.filename
        content = await file.read()
        input_path.write_bytes(content)
        
        # Configure and process
        config = ApplicationConfig(
            search=SearchConfig(
                expression=request.expression,
                case_sensitive=request.case_sensitive
            ),
            files=FileConfig(search_root=input_path.parent),
            output=OutputConfig(output_file=Path(tmpdir) / "output.txt"),
            processing=ProcessingConfig(max_workers=request.max_workers)
        )
        
        pipeline = ProcessingPipeline(config)
        result = pipeline.run()
        
        # Read results
        results = []
        if result.total_matches > 0:
            results = config.output.output_file.read_text().splitlines()
        
        return FilterResponse(
            job_id=str(uuid.uuid4()),
            status="completed",
            matches=result.total_matches,
            results=results[:100]  # Limit to 100 results
        )

@app.post("/filter/async", response_model=dict)
async def filter_logs_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: FilterRequest = None
):
    """Filter logs asynchronously."""
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "matches": 0}
    
    # Process in background
    background_tasks.add_task(process_log_file, job_id, file, request)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/jobs/{job_id}", response_model=FilterResponse)
async def get_job_status(job_id: str):
    """Get job status and results."""
    
    if job_id not in jobs:
        return {"error": "Job not found"}, 404
    
    job = jobs[job_id]
    return FilterResponse(
        job_id=job_id,
        status=job["status"],
        matches=job.get("matches", 0),
        results=job.get("results", [])
    )

def process_log_file(job_id: str, file: UploadFile, request: FilterRequest):
    """Background task to process log file."""
    # Implementation similar to filter_logs
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Cloud Platform Integration

### AWS CloudWatch Logs

```python
# cloudwatch_integration.py
import boto3
from log_filter.processing.pipeline import ProcessingPipeline
from datetime import datetime, timedelta

cloudwatch = boto3.client('logs')

def filter_cloudwatch_logs(
    log_group: str,
    expression: str,
    start_time: datetime,
    end_time: datetime
):
    """Filter CloudWatch logs."""
    
    # Download logs from CloudWatch
    streams = cloudwatch.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True
    )
    
    for stream in streams['logStreams']:
        stream_name = stream['logStreamName']
        
        events = cloudwatch.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000)
        )
        
        # Process events with log-filter
        for event in events['events']:
            # Evaluate expression
            if evaluate_expression(event['message'], expression):
                print(f"[{stream_name}] {event['message']}")

# Usage
filter_cloudwatch_logs(
    log_group="/aws/lambda/my-function",
    expression="ERROR OR CRITICAL",
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now()
)
```

---

## Summary

This guide covered:

✅ **Python API** - Programmatic usage and custom pipelines  
✅ **CI/CD** - GitHub Actions, GitLab, Jenkins, Azure DevOps  
✅ **Monitoring** - Prometheus, Grafana, Elasticsearch, Splunk  
✅ **Log Aggregation** - Fluentd, Logstash integration  
✅ **Container Orchestration** - Docker, Kubernetes  
✅ **Event-Driven** - AWS Lambda, Azure Functions  
✅ **REST API** - API wrapper implementation  
✅ **Cloud Platforms** - AWS, Azure integration  

### Next Steps

- [Advanced Usage Guide](advanced_usage.md) - Optimize performance
- [Error Handling](error_handling.md) - Handle errors gracefully
- [API Reference](api/index.rst) - Complete API documentation

---

**Document Version:** 1.0  
**Last Review:** January 8, 2026
