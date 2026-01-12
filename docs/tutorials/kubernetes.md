# Kubernetes Tutorial: Production-Scale Log Filtering

**Duration:** 20 minutes  
**Level:** Advanced  
**Prerequisites:** Kubernetes cluster access, kubectl installed  
**Last Updated:** January 8, 2026

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- ✅ Deploy Log Filter to Kubernetes
- ✅ Configure CronJobs for scheduled processing
- ✅ Manage configuration with ConfigMaps
- ✅ Store logs with PersistentVolumes
- ✅ Implement log aggregation patterns
- ✅ Scale horizontally with multiple pods
- ✅ Monitor with Prometheus
- ✅ Implement GitOps workflows

---

## Part 1: Basic Deployment (4 minutes)

### Step 1: Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: log-filter
  labels:
    name: log-filter
```

```bash
kubectl apply -f namespace.yaml
```

### Step 2: Create ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-filter-config
  namespace: log-filter
data:
  config.yaml: |
    search:
      expression: "ERROR OR CRITICAL"
      ignore_case: false
    
    files:
      path: /logs
      include_patterns:
        - "*.log"
    
    output:
      output_file: /output/filtered.txt
      show_stats: true
    
    processing:
      max_workers: 8
```

```bash
kubectl apply -f configmap.yaml
```

### Step 3: Create PersistentVolumeClaim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: log-storage
  namespace: log-filter
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: standard

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: filtered-output
  namespace: log-filter
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

```bash
kubectl apply -f pvc.yaml
```

### Step 4: Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-filter
  namespace: log-filter
  labels:
    app: log-filter
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
        image: log-filter:production
        args:
          - "--config"
          - "/config/config.yaml"
        
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
        - name: logs
          mountPath: /logs
          readOnly: true
        - name: output
          mountPath: /output
        
        # Liveness probe
        livenessProbe:
          exec:
            command:
              - test
              - -f
              - /output/.health
          initialDelaySeconds: 30
          periodSeconds: 60
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe
        readinessProbe:
          exec:
            command:
              - test
              - -f
              - /output/.health
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
      
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
```

```bash
kubectl apply -f deployment.yaml
```

### Step 5: Verify Deployment

```bash
# Check pod status
kubectl get pods -n log-filter

# View logs
kubectl logs -n log-filter -l app=log-filter -f

# Check resource usage
kubectl top pod -n log-filter
```

---

## Part 2: CronJob for Scheduled Processing (4 minutes)

### Daily Processing CronJob

```yaml
# cronjob-daily.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-filter-daily
  namespace: log-filter
spec:
  # Run daily at 1 AM
  schedule: "0 1 * * *"
  
  # Keep last 3 successful and failed jobs
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  
  # Job template
  jobTemplate:
    spec:
      # Retry failed jobs
      backoffLimit: 3
      
      # Clean up completed jobs after 1 hour
      ttlSecondsAfterFinished: 3600
      
      template:
        metadata:
          labels:
            app: log-filter
            type: cronjob
        spec:
          restartPolicy: OnFailure
          
          containers:
          - name: log-filter
            image: log-filter:production
            
            # Process yesterday's logs
            args:
              - "--config"
              - "/config/config.yaml"
              - "--start-date"
              - "$(date -d 'yesterday' +%Y-%m-%d)"
              - "--end-date"
              - "$(date -d 'yesterday' +%Y-%m-%d)"
              - "--output"
              - "/output/$(date -d 'yesterday' +%Y-%m-%d)-errors.txt"
            
            resources:
              requests:
                memory: "2Gi"
                cpu: "2"
              limits:
                memory: "4Gi"
                cpu: "4"
            
            volumeMounts:
            - name: config
              mountPath: /config
              readOnly: true
            - name: logs
              mountPath: /logs
              readOnly: true
            - name: output
              mountPath: /output
          
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
```

```bash
kubectl apply -f cronjob-daily.yaml
```

### Hourly Processing CronJob

```yaml
# cronjob-hourly.yaml
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
          restartPolicy: OnFailure
          containers:
          - name: log-filter
            image: log-filter:production
            args:
              - "--config"
              - "/config/config.yaml"
              - "--start-time"
              - "$(date -d '1 hour ago' +%H:00:00)"
              - "--end-time"
              - "$(date +%H:00:00)"
            
            resources:
              requests:
                memory: "1Gi"
                cpu: "1"
              limits:
                memory: "2Gi"
                cpu: "2"
            
            volumeMounts:
            - name: config
              mountPath: /config
            - name: logs
              mountPath: /logs
              readOnly: true
            - name: output
              mountPath: /output
          
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
```

### Manage CronJobs

```bash
# Apply CronJob
kubectl apply -f cronjob-daily.yaml

# List CronJobs
kubectl get cronjobs -n log-filter

# View recent jobs
kubectl get jobs -n log-filter

# Trigger manual run
kubectl create job --from=cronjob/log-filter-daily log-filter-manual -n log-filter

# Delete CronJob
kubectl delete cronjob log-filter-daily -n log-filter
```

---

## Part 3: Multi-Service Architecture (4 minutes)

### Separate Processing by Log Type

```yaml
# multi-service-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: error-filter-config
  namespace: log-filter
data:
  config.yaml: |
    search:
      expression: "ERROR OR CRITICAL"
    files:
      path: /logs
    output:
      output_file: /output/errors.txt

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: warning-filter-config
  namespace: log-filter
data:
  config.yaml: |
    search:
      expression: "WARNING"
    files:
      path: /logs
    output:
      output_file: /output/warnings.txt

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: error-filter
  namespace: log-filter
spec:
  replicas: 2
  selector:
    matchLabels:
      app: error-filter
  template:
    metadata:
      labels:
        app: error-filter
    spec:
      containers:
      - name: log-filter
        image: log-filter:production
        args: ["--config", "/config/config.yaml"]
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
        
        volumeMounts:
        - name: config
          mountPath: /config
        - name: logs
          mountPath: /logs
          readOnly: true
        - name: output
          mountPath: /output
      
      volumes:
      - name: config
        configMap:
          name: error-filter-config
      - name: logs
        persistentVolumeClaim:
          claimName: log-storage
      - name: output
        persistentVolumeClaim:
          claimName: filtered-output

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: warning-filter
  namespace: log-filter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: warning-filter
  template:
    metadata:
      labels:
        app: warning-filter
    spec:
      containers:
      - name: log-filter
        image: log-filter:production
        args: ["--config", "/config/config.yaml"]
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        
        volumeMounts:
        - name: config
          mountPath: /config
        - name: logs
          mountPath: /logs
          readOnly: true
        - name: output
          mountPath: /output
      
      volumes:
      - name: config
        configMap:
          name: warning-filter-config
      - name: logs
        persistentVolumeClaim:
          claimName: log-storage
      - name: output
        persistentVolumeClaim:
          claimName: filtered-output
```

```bash
kubectl apply -f multi-service-deployment.yaml
```

---

## Part 4: Monitoring with Prometheus (4 minutes)

### ServiceMonitor Configuration

```yaml
# servicemonitor.yaml
apiVersion: v1
kind: Service
metadata:
  name: log-filter-metrics
  namespace: log-filter
  labels:
    app: log-filter
spec:
  selector:
    app: log-filter
  ports:
  - name: metrics
    port: 8000
    targetPort: 8000

---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: log-filter
  namespace: log-filter
  labels:
    app: log-filter
spec:
  selector:
    matchLabels:
      app: log-filter
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboard

```yaml
# grafana-dashboard-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-filter-dashboard
  namespace: log-filter
  labels:
    grafana_dashboard: "1"
data:
  log-filter.json: |
    {
      "dashboard": {
        "title": "Log Filter Metrics",
        "panels": [
          {
            "title": "Records Processed",
            "targets": [
              {
                "expr": "rate(log_filter_records_total[5m])"
              }
            ]
          },
          {
            "title": "Processing Duration",
            "targets": [
              {
                "expr": "log_filter_duration_seconds"
              }
            ]
          },
          {
            "title": "Error Rate",
            "targets": [
              {
                "expr": "rate(log_filter_errors_total[5m])"
              }
            ]
          }
        ]
      }
    }
```

---

## Part 5: Log Aggregation Pipeline (4 minutes)

### Complete Pipeline Architecture

```yaml
# log-aggregation-pipeline.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aggregation-config
  namespace: log-filter
data:
  # Stage 1: Collect all errors
  collect-config.yaml: |
    search:
      expression: "ERROR OR CRITICAL"
    output:
      output_file: /pipeline/01-collected.txt
  
  # Stage 2: Deduplicate
  dedupe-config.yaml: |
    search:
      expression: ".*"  # All records
    files:
      path: /pipeline
      include_patterns: ["01-collected.txt"]
    output:
      output_file: /pipeline/02-deduped.txt
  
  # Stage 3: Categorize
  categorize-config.yaml: |
    search:
      expression: "(database OR sql) OR (payment OR transaction) OR (auth OR login)"
    files:
      path: /pipeline
      include_patterns: ["02-deduped.txt"]
    output:
      output_file: /pipeline/03-categorized.txt

---
apiVersion: batch/v1
kind: Job
metadata:
  name: log-aggregation-pipeline
  namespace: log-filter
spec:
  template:
    spec:
      restartPolicy: OnFailure
      
      # Init container: Stage 1 - Collect
      initContainers:
      - name: collect
        image: log-filter:production
        args: ["--config", "/config/collect-config.yaml"]
        volumeMounts:
        - name: config
          mountPath: /config
        - name: logs
          mountPath: /logs
          readOnly: true
        - name: pipeline
          mountPath: /pipeline
      
      # Stage 2: Deduplicate
      - name: dedupe
        image: log-filter:production
        args: ["--config", "/config/dedupe-config.yaml"]
        volumeMounts:
        - name: config
          mountPath: /config
        - name: pipeline
          mountPath: /pipeline
      
      # Main container: Stage 3 - Categorize
      containers:
      - name: categorize
        image: log-filter:production
        args: ["--config", "/config/categorize-config.yaml"]
        volumeMounts:
        - name: config
          mountPath: /config
        - name: pipeline
          mountPath: /pipeline
        - name: output
          mountPath: /output
      
      volumes:
      - name: config
        configMap:
          name: aggregation-config
      - name: logs
        persistentVolumeClaim:
          claimName: log-storage
      - name: pipeline
        emptyDir: {}
      - name: output
        persistentVolumeClaim:
          claimName: filtered-output
```

---

## Practice Exercises

### Exercise 1: Deploy to Kubernetes

Deploy Log Filter to your cluster and process sample logs.

<details>
<summary>Solution</summary>

```bash
# Create namespace
kubectl create namespace log-filter

# Create ConfigMap
kubectl create configmap log-filter-config \
  --from-file=config.yaml=./config.yaml \
  -n log-filter

# Create deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n log-filter
kubectl logs -n log-filter -l app=log-filter
```
</details>

### Exercise 2: Set Up Daily CronJob

Configure a CronJob to process logs daily at 2 AM.

<details>
<summary>Solution</summary>

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-log-processing
  namespace: log-filter
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: log-filter
            image: log-filter:production
            args:
              - "--config"
              - "/config/config.yaml"
            volumeMounts:
            - name: config
              mountPath: /config
            - name: logs
              mountPath: /logs
              readOnly: true
            - name: output
              mountPath: /output
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
```
</details>

### Exercise 3: Scale Deployment

Scale the deployment to 3 replicas.

<details>
<summary>Solution</summary>

```bash
# Scale deployment
kubectl scale deployment log-filter --replicas=3 -n log-filter

# Verify
kubectl get pods -n log-filter

# Auto-scale based on CPU
kubectl autoscale deployment log-filter \
  --min=2 --max=10 --cpu-percent=70 \
  -n log-filter
```
</details>

---

## Troubleshooting

### Problem: Pod Crashes (CrashLoopBackOff)

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n log-filter
kubectl logs <pod-name> -n log-filter --previous
```

**Common Solutions:**
1. Check ConfigMap is mounted correctly
2. Verify PVC is bound
3. Check resource limits
4. Review application logs

### Problem: CronJob Not Running

**Diagnosis:**
```bash
kubectl get cronjobs -n log-filter
kubectl describe cronjob <name> -n log-filter
kubectl get jobs -n log-filter
```

**Solutions:**
1. Verify schedule syntax
2. Check job history limits
3. Review pod logs for failed jobs

### Problem: High Memory Usage

**Solutions:**
```yaml
resources:
  limits:
    memory: "2Gi"  # Reduce limit
  requests:
    memory: "1Gi"
```

---

## Deployment Checklist

- [ ] Create namespace
- [ ] Configure ConfigMaps
- [ ] Set up PersistentVolumes
- [ ] Deploy application
- [ ] Configure CronJobs
- [ ] Set up monitoring
- [ ] Configure alerting
- [ ] Test with sample data
- [ ] Document deployment
- [ ] Set up backups

---

## What's Next?

You've mastered Kubernetes deployment! 🎉

### Next Steps:

1. **[Integration Guide](../integration_guide.md)** - CI/CD and GitOps
2. **[Advanced Tutorial](advanced.md)** - Production patterns
3. **[Examples](../examples/)** - Real-world deployments
4. **[Performance Guide](../performance.md)** - Optimization strategies

---

**Tutorial Version:** 1.0  
**Last Updated:** January 8, 2026  
**Feedback:** Report issues on GitHub
