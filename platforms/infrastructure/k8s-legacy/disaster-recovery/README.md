# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Disaster Recovery - Enterprise Implementation

## Overview

This directory contains enterprise-grade disaster recovery configuration for the MachineNativeOps platform, providing comprehensive backup strategies, automated recovery procedures, and business continuity planning.

## Architecture

### Components
- **Backup System**: Velero for Kubernetes resource and persistent volume backups
- **Storage Backend**: S3-compatible storage for backup repositories
- **Schedule Jobs**: Automated backup jobs for databases, configurations, and critical data
- **Restore Jobs**: Automated restore procedures with validation
- **DR Plans**: Detailed disaster recovery runbooks and procedures

### Backup Strategy

#### Backup Types
1. **Full Backups**: Complete backup of all resources and volumes
2. **Incremental Backups**: Only changed data since last backup
3. **Differential Backups**: Changed data since last full backup
4. **Snapshot Backups**: Point-in-time snapshots of persistent volumes

#### Backup Schedule
| Resource Type | Full Backup | Incremental | Retention |
|--------------|-------------|-------------|-----------|
| etcd Cluster | Daily | Hourly | 30 days |
| PV Snapshots | Daily | N/A | 7 days |
| Redis | Hourly | N/A | 7 days |
| PostgreSQL | Hourly | N/A | 30 days |
| Application Config | On change | N/A | 90 days |

## Deployment

### Prerequisites
- Kubernetes cluster (v1.19+)
- S3-compatible storage (MinIO, AWS S3, GCS, Azure Blob)
- kubectl and helm installed
- Velero CLI installed

### Installation Steps

1. **Install Velero CLI:**
```bash
# Download Velero CLI
wget [EXTERNAL_URL_REMOVED]
tar -xvf velero-v1.12.0-linux-amd64.tar.gz
sudo mv velero-v1.12.0-linux-amd64/velero /usr/local/bin/
```

2. **Configure S3 Credentials:**
```bash
# Create credentials file
cat > /tmp/velero-credentials.txt <<EOF
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
EOF
```

3. **Install Velero:**
```bash
# Install Velero with S3 backend
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket machine-native-ops-backups \
  --secret-file /tmp/velero-credentials.txt \
  --use-volume-snapshots \
  --backup-location-config region=us-east-1,s3ForcePathStyle="true",s3Url=[EXTERNAL_URL_REMOVED] \
  --snapshot-location-config region=us-east-1
```

4. **Apply Backup Schedules:**
```bash
kubectl apply -f k8s/disaster-recovery/schedules/
```

5. **Deploy Backup Jobs:**
```bash
kubectl apply -f k8s/disaster-recovery/jobs/
```

## Backup Configuration

### Velero Backup Schedules

**Daily Full Backup:**
```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-full-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  template:
    includedNamespaces:
    - machine-native-ops
    - monitoring
    - logging
    storageLocation: aws-s3
    volumeSnapshotLocations:
    - aws-s3
    ttl: 720h  # 30 days
    hooks:
      resources:
      - name: pre-backup-hook
        includedNamespaces:
        - machine-native-ops
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: machine-native-ops
        pre:
        - exec:
            container: machine-native-ops
            command:
            - /bin/sh
            - -c
            - "pg_dumpall -U postgres > /tmp/backup.sql"
            onError: Continue
            timeout: 300s
```

**Hourly Incremental Backup:**
```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: hourly-incremental-backup
  namespace: velero
spec:
  schedule: "0 * * * *"  # Every hour
  template:
    includedNamespaces:
    - machine-native-ops
    storageLocation: aws-s3
    ttl: 168h  # 7 days
    snapshotVolumes: false
```

### Database Backup Jobs

**PostgreSQL Backup:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: platform-03
spec:
  schedule: "0 * * * *"  # Hourly
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -U postgres -h postgres machine_native_ops > /backup/backup_$(date +%Y%m%d_%H%M%S).sql
              aws s3 cp /backup/backup_*.sql s3://machine-native-ops-backups/postgres/
              find /backup -name "*.sql" -mtime +7 -delete
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            volumeMounts:
            - name: backup
              mountPath: /backup
            - name: aws-credentials
              mountPath: /root/.aws
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
          - name: aws-credentials
            secret:
              secretName: aws-credentials
          restartPolicy: OnFailure
```

**Redis Backup:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-backup
  namespace: platform-03
spec:
  schedule: "30 * * * *"  # Every 30 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: redis-backup
            image: redis:7
            command:
            - /bin/bash
            - -c
            - |
              redis-cli -h redis BGSAVE
              sleep 10
              redis-cli -h redis LASTSAVE
              cp /data/dump.rdb /backup/dump_$(date +%Y%m%d_%H%M%S).rdb
              aws s3 cp /backup/dump_*.rdb s3://machine-native-ops-backups/redis/
              find /backup -name "*.rdb" -mtime +7 -delete
            volumeMounts:
            - name: backup
              mountPath: /backup
            - name: aws-credentials
              mountPath: /root/.aws
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: redis-backup-pvc
          - name: aws-credentials
            secret:
              secretName: aws-credentials
          restartPolicy: OnFailure
```

## Restore Procedures

### Full Cluster Restore

**Restore from Velero Backup:**
```bash
# List available backups
velero backup get

# Restore specific backup
velero restore create --from-backup backup-20240127-020000

# Monitor restore progress
velero restore get
velero restore describe <restore-name> --details
```

**Restore with Selective Resources:**
```bash
# Restore only specific namespace
velero restore create \
  --from-backup backup-20240127-020000 \
  --include-namespaces machine-native-ops

# Restore specific resources
velero restore create \
  --from-backup backup-20240127-020000 \
  --include-resources deployments,configmaps,secrets

# Exclude specific resources
velero restore create \
  --from-backup backup-20240127-020000 \
  --exclude-resources persistentvolumes
```

### Database Restore

**PostgreSQL Restore:**
```bash
# Download backup from S3
aws s3 cp s3://machine-native-ops-backups/postgres/backup_20240127_020000.sql /tmp/backup.sql

# Restore to PostgreSQL
kubectl exec -it postgres-0 -n machine-native-ops -- psql -U postgres -d machine_native_ops < /tmp/backup.sql
```

**Redis Restore:**
```bash
# Download backup from S3
aws s3 cp s3://machine-native-ops-backups/redis/dump_20240127_020000.rdb /tmp/dump.rdb

# Copy to Redis pod
kubectl cp /tmp/dump.rdb redis-0:/tmp/dump.rdb -n machine-native-ops

# Restore in Redis pod
kubectl exec -it redis-0 -n machine-native-ops -- redis-cli SHUTDOWN NOSAVE
kubectl exec -it redis-0 -n machine-native-ops -- mv /tmp/dump.rdb /data/dump.rdb
kubectl exec -it redis-0 -n machine-native-ops -- redis-server
```

## Disaster Recovery Runbook

### Scenario 1: Pod Failure

**Detection:**
- Monitor alerts for pod crashes
- Check pod status: `kubectl get pods -n machine-native-ops`
- View pod logs: `kubectl logs <pod-name> -n machine-native-ops`

**Recovery:**
1. Identify root cause (OOMKilled, CrashLoopBackOff, etc.)
2. Fix underlying issue (resource limits, configuration, etc.)
3. Delete failed pod: `kubectl delete pod <pod-name> -n machine-native-ops`
4. Verify new pod starts: `kubectl get pods -n machine-native-ops`

**Time to Recovery:** < 5 minutes

### Scenario 2: Node Failure

**Detection:**
- Node becomes NotReady
- Pods on node are rescheduled
- Alerts trigger for node unavailability

**Recovery:**
1. Mark node as unschedulable: `kubectl cordon <node-name>`
2. Evict pods: `kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data`
3. Replace or repair failed node
4. Uncordon node: `kubectl uncordon <node-name>`
5. Verify pod placement: `kubectl get pods -o wide`

**Time to Recovery:** < 30 minutes

### Scenario 3: Persistent Volume Failure

**Detection:**
- Volume becomes unavailable
- Pods stuck in Pending state
- I/O errors in application logs

**Recovery:**
1. Identify failed PV: `kubectl get pv`
2. Check volume status and events
3. Restore from snapshot (if available)
4. Or create new PV and restore from backup
5. Update PVC to use restored/new PV
6. Restart affected pods

**Time to Recovery:** < 1 hour

### Scenario 4: Regional Failure

**Detection:**
- Multi-zone outage detected
- All nodes in region unreachable
- Complete service disruption

**Recovery:**
1. Activate disaster recovery site
2. Restore from latest backup in secondary region
3. Update DNS to point to secondary region
4. Verify all services operational
5. Monitor performance and connectivity

**Time to Recovery:** < 4 hours (RTO)
**Data Loss:** < 1 hour (RPO)

### Scenario 5: Data Corruption

**Detection:**
- Data inconsistency detected
- Application errors
- Integrity checks fail

**Recovery:**
1. Identify corruption scope and time
2. Locate last known good backup
3. Verify backup integrity
4. Restore affected data
5. Run validation checks
6. Resume normal operations

**Time to Recovery:** < 2 hours

## Backup Validation

### Automated Validation

**Backup Health Check:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-validation
  namespace: velero
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: validator
            image: velero/velero:v1.12.0
            command:
            - /bin/bash
            - -c
            - |
              # Check latest backup
              LATEST_BACKUP=$(velero backup get -o json | jq -r '.items | sort_by(.metadata.creationTimestamp) | reverse | .[0].metadata.name')
              
              # Verify backup status
              STATUS=$(velero backup get $LATEST_BACKUP -o json | jq -r '.status.phase')
              
              if [ "$STATUS" != "Completed" ]; then
                echo "Backup $LATEST_BACKUP failed with status: $STATUS"
                exit 1
              fi
              
              # Check backup age
              BACKUP_AGE=$(velero backup get $LATEST_BACKUP -o json | jq -r '.metadata.creationTimestamp')
              echo "Latest backup: $LATEST_BACKUP ($BACKUP_AGE)"
              
              echo "Backup validation passed"
          restartPolicy: OnFailure
```

### Manual Validation

**Test Restore:**
```bash
# Create test namespace
kubectl create namespace restore-test

# Restore backup to test namespace
velero restore create \
  --from-backup backup-20240127-020000 \
  --namespace-mappings machine-native-ops:restore-test

# Verify restored resources
kubectl get all -n restore-test

# Clean up test namespace
kubectl delete namespace restore-test
```

## Monitoring and Alerting

### Backup Monitoring

**Prometheus Queries:**
```promql
# Backup success rate
rate(velero_backup_total{phase="Completed"}[1h]) / rate(velero_backup_total[1h])

# Backup duration
velero_backup_duration_seconds{phase="Completed"}

# Backup age
time() - velero_backup_last_successful_timestamp_seconds

# Storage usage
velero_backup_storage_usage_bytes
```

**Alerting Rules:**
```yaml
groups:
- name: backup-alerts
  rules:
  - alert: BackupFailed
    expr: velero_backup_total{phase="Failed"} > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Backup {{ $labels.name }} failed"
      
  - alert: BackupTooOld
    expr: time() - velero_backup_last_successful_timestamp_seconds > 86400
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Last successful backup is more than 24 hours old"
      
  - alert: BackupStorageFull
    expr: velero_backup_storage_usage_bytes / velero_backup_storage_capacity_bytes > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Backup storage is 90% full"
```

## Best Practices

### 1. Backup Strategy
- Implement 3-2-1 rule: 3 copies, 2 different media, 1 offsite
- Use incremental backups to reduce storage and time
- Schedule backups during low-traffic periods
- Test backups regularly

### 2. Restore Testing
- Perform monthly restore tests
- Test restore of different resource types
- Validate data integrity after restore
- Document and update procedures based on tests

### 3. Security
- Encrypt backups at rest and in transit
- Use IAM roles for backup operations
- Rotate encryption keys regularly
- Audit backup and restore operations

### 4. Documentation
- Keep DR procedures up-to-date
- Document all backup and restore steps
- Include contact information for key personnel
- Store documentation in multiple locations

### 5. Performance
- Monitor backup performance metrics
- Optimize backup schedules based on load
- Use compression for large backups
- Consider parallel backups for large clusters

## Troubleshooting

### Backup Failures

**Check Velero Logs:**
```bash
kubectl logs -n velero deployment/velero
```

**Check Backup Status:**
```bash
velero backup get --details
velero backup describe <backup-name> --details
```

**Common Issues:**
- **S3 connectivity**: Check credentials and network
- **Snapshot failures**: Verify storage provider supports snapshots
- **Timeout**: Increase backup timeout duration
- **Insufficient resources**: Check pod resources

### Restore Failures

**Check Restore Logs:**
```bash
velero restore get --details
velero restore describe <restore-name> --details
```

**Common Issues:**
- **Resource conflicts**: Delete conflicting resources before restore
- **Namespace missing**: Create required namespaces
- **PVC binding**: Ensure PVs are available
- **Version mismatch**: Check Velero version compatibility

## References

- [Velero Documentation]([EXTERNAL_URL_REMOVED])
- [Kubernetes Backup Best Practices]([EXTERNAL_URL_REMOVED])
- [Disaster Recovery Planning]([EXTERNAL_URL_REMOVED])