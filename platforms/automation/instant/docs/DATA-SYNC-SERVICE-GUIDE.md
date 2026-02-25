<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Data Synchronization Service Guide

## Overview

The Data Synchronization Service is a comprehensive solution for synchronizing data between two systems with advanced features including conflict resolution, incremental sync, retry logic, data validation, and monitoring.

## Features

### Core Capabilities

- **Multiple Sync Modes**: Real-time, scheduled, and manual synchronization
- **Conflict Resolution**: Multiple strategies (source-wins, target-wins, latest-timestamp, manual)
- **Change Tracking**: Detailed tracking of all data changes
- **Retry Logic**: Exponential backoff for failed operations
- **Data Validation**: Comprehensive validation rules
- **Monitoring**: Real-time metrics and alerting
- **Security**: Data encryption and masking
- **Audit Logging**: Complete audit trail

### Integration Points

#### Agent Orchestration Integration

The service integrates with the agent-orchestration.yml system:

```yaml
agents:
  - id: data-sync-agent
    name: "Data Synchronization Agent"
    type: "synchronization"
    priority: 1
    config:
      serviceConfig: "instant/configs/data-sync-config.yaml"
      pipelines:
        - "users-sync"
        - "orders-sync"
        - "inventory-sync"
```

#### File Organizer System Integration

The service works with the file-organizer-system for:

- Configuration file management
- Artifact storage
- Log file organization
- Backup management

#### AEP Engine Integration

The service leverages the AEP Engine for:

- Architecture validation
- Governance enforcement
- Semantic anchoring
- Evidence chain generation

## Quick Start

### Installation

```bash
cd instant
npm install
```

### Configuration

1. Copy the example configuration:
```bash
cp configs/data-sync-config.yaml configs/data-sync-config.local.yaml
```

2. Update the configuration with your settings:
```yaml
sourceSystem:
  connectionString: "your-source-url"
  auth:
    credentials:
      token: "your-token"

targetSystem:
  connectionString: "your-target-url"
  auth:
    credentials:
      username: "your-username"
      password: "your-password"
```

### Running the Service

#### Development Mode

```bash
npm run dev
```

#### Production Mode

```bash
npm run build
npm start
```

### Basic Usage

```typescript
import { 
  createDataSyncService, 
  exampleConfig 
} from './src/data-sync-service';

// Create and start service
const service = await createDataSyncService(exampleConfig);

// Trigger immediate sync
const status = await service.syncNow();
console.log('Sync Status:', status);

// Get conflicts
const conflicts = service.getConflicts();
console.log('Conflicts:', conflicts);

// Resolve a conflict
await service.resolveConflict('conflict-id', 'source');

// Stop service
await service.stop();
```

## Configuration

### Sync Modes

#### Real-Time Sync

```yaml
syncMode: "real-time"
```

Continuous synchronization using websockets or change data capture.

#### Scheduled Sync

```yaml
syncMode: "scheduled"
schedule:
  cron: "0 */5 * * * *"  # Every 5 minutes
  timezone: "UTC"
```

Synchronization based on a cron schedule.

#### Manual Sync

```yaml
syncMode: "manual"
```

Synchronization triggered manually via API or command.

### Conflict Resolution Strategies

#### Source Wins

Always use source data when conflicts occur:

```yaml
conflictResolution: "source-wins"
```

#### Target Wins

Always preserve target data when conflicts occur:

```yaml
conflictResolution: "target-wins"
```

#### Latest Timestamp

Use the record with the latest timestamp:

```yaml
conflictResolution: "latest-timestamp"
```

#### Manual Resolution

Require manual intervention for conflicts:

```yaml
conflictResolution: "manual"
```

### Validation Rules

Define validation rules for data quality:

```yaml
validationRules:
  - field: "id"
    type: "required"
    config:
      errorMessage: "ID field is required"
  
  - field: "email"
    type: "format"
    config:
      pattern: "^[^@]+@[^@]+\\.[^@]+$"
      errorMessage: "Invalid email format"
  
  - field: "age"
    type: "range"
    config:
      min: 0
      max: 150
      errorMessage: "Age must be between 0 and 150"
```

### Retry Policy

Configure retry behavior:

```yaml
retryPolicy:
  maxRetries: 3
  backoffMultiplier: 2
  initialDelayMs: 1000
  maxDelayMs: 30000
  jitter: true
```

### Monitoring

Enable monitoring and alerting:

```yaml
monitoring:
  enabled: true
  metricsPort: 9090
  healthCheckInterval: 30
  logLevel: "info"
  
  metrics:
    - "sync_throughput"
    - "sync_latency"
    - "sync_errors"
    - "sync_conflicts"
  
  alerting:
    enabled: true
    thresholds:
      failureRate: 0.1
      conflictRate: 0.05
      latencyMs: 5000
    
    channels:
      - type: "webhook"
        url: "${ALERT_WEBHOOK_URL}"
        severity: "high"
```

## Advanced Usage

### Custom Transformations

Define custom data transformations:

```yaml
transformations:
  - field: "createdAt"
    transform: "timestamp"
    config:
      inputFormat: "ISO8601"
      outputFormat: "unix"
  
  - field: "price"
    transform: "decimal"
    config:
      precision: 2
      scale: 2
```

### Change Tracking

Enable detailed change tracking:

```yaml
changeTracking:
  enabled: true
  retentionDays: 90
  maxHistoryRecords: 10000
  fields:
    - "id"
    - "timestamp"
    - "version"
    - "operation"
```

### Security Configuration

Configure data encryption and masking:

```yaml
security:
  encryptData: true
  encryptFields:
    - "password"
    - "token"
    - "ssn"
  encryptionKey: "${ENCRYPTION_KEY}"
  
  maskFields:
    - "password"
    - "token"
    - "apiKey"
```

## API Reference

### DataSyncService Interface

#### Methods

- `start(): Promise<void>` - Start the synchronization service
- `stop(): Promise<void>` - Stop the synchronization service
- `syncNow(): Promise<SyncStatus>` - Trigger immediate synchronization
- `getStatus(): SyncStatus` - Get current synchronization status
- `getConflicts(): SyncRecord[]` - Get list of conflicted records
- `resolveConflict(recordId: string, resolution: 'source' | 'target'): Promise<void>` - Resolve a conflict

### DataSyncEngine Interface

#### Methods

- `start(): Promise<void>` - Start the synchronization engine
- `stop(): Promise<void>` - Stop the synchronization engine
- `registerService(name: string, config: SyncConfig): void` - Register a synchronization service
- `registerPipeline(config: PipelineConfig): void` - Register a synchronization pipeline
- `createJob(pipelineName: string): Promise<string>` - Create and queue a job
- `getJobStatus(jobId: string): SyncJob | undefined` - Get job status
- `getMetrics(): EngineMetrics` - Get engine metrics

## Monitoring and Observability

### Metrics

The service exposes the following metrics:

- `sync_throughput` - Records synchronized per second
- `sync_latency` - Time to complete synchronization
- `sync_errors` - Number of synchronization errors
- `sync_conflicts` - Number of conflicts detected
- `queue_size` - Number of records in sync queue
- `retry_count` - Number of retry attempts

### Health Check

Health check endpoint at `/health`:

```bash
curl [EXTERNAL_URL_REMOVED]
```

Response:
```json
{
  "status": "healthy",
  "dependencies": {
    "source": "healthy",
    "target": "healthy"
  },
  "metrics": {
    "sync_throughput": 100,
    "sync_latency": 500,
    "sync_errors": 0,
    "sync_conflicts": 0
  }
}
```

### Logs

Logs are written to stdout and can be configured:

```yaml
monitoring:
  logLevel: "info"  # Options: debug, info, warn, error
```

## Troubleshooting

### Common Issues

#### High Failure Rate

**Symptom**: High failure rate in synchronization

**Solutions**:
1. Check network connectivity to source and target systems
2. Verify authentication credentials
3. Review validation rules for overly strict conditions
4. Check retry policy settings

#### Conflicts Not Resolving

**Symptom**: Conflicts accumulating without resolution

**Solutions**:
1. Review conflict resolution strategy
2. Ensure timestamp fields are properly synchronized
3. Implement manual resolution process
4. Consider adjusting conflict resolution to automatic mode

#### Performance Issues

**Symptom**: Slow synchronization performance

**Solutions**:
1. Increase batch size
2. Adjust max concurrent syncs
3. Optimize validation rules
4. Review network latency
5. Consider using scheduled mode instead of real-time

## Best Practices

1. **Start with Manual Mode**: Test configurations in manual mode before enabling real-time sync
2. **Monitor Closely**: Enable monitoring and alerts from the beginning
3. **Validate Early**: Implement comprehensive validation rules
4. **Plan for Conflicts**: Choose appropriate conflict resolution strategy
5. **Test Rollback**: Ensure you can rollback changes if needed
6. **Document Configurations**: Keep documentation updated with configuration changes
7. **Regular Backups**: Enable backup functionality
8. **Audit Regularly**: Review audit logs for anomalies

## Security Considerations

1. **Encrypt Credentials**: Never store credentials in plain text
2. **Use Environment Variables**: Store sensitive data in environment variables
3. **Enable Encryption**: Encrypt sensitive fields in transit and at rest
4. **Mask Sensitive Data**: Mask sensitive data in logs and metrics
5. **Implement RBAC**: Use role-based access control for API endpoints
6. **Regular Security Audits**: Perform regular security audits

## Support and Maintenance

### Version Updates

```bash
npm update @machinenativeops/data-sync
```

### Backup Configuration

```bash
cp configs/data-sync-config.yaml configs/backup/data-sync-config.yaml.$(date +%Y%m%d)
```

### View Logs

```bash
# View recent logs
tail -f logs/data-sync.log

# Search for errors
grep "ERROR" logs/data-sync.log
```

## License

This project is part of the MachineNativeOps ecosystem and follows the same license terms.

## Governance

This service is governed by the GL Unified Architecture Governance Framework and follows all governance layer requirements.

- **Governance Layer**: GL90-99
- **Charter Version**: 2.0.0
- **Semantic Anchor**: ../../engine/governance/GL_SEMANTIC_ANCHOR.json