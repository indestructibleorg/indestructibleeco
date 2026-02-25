<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Data Synchronization Service

## Overview

This directory contains the Data Synchronization Service for the MachineNativeOps platform. The service provides comprehensive data synchronization capabilities between two systems with advanced features including conflict resolution, incremental sync, retry logic, data validation, and monitoring.

## GL Unified Architecture Governance Framework Activated

This service is governed by the GL (Governance Layers) Unified Architecture Governance Framework and follows all governance requirements:

- **Governance Layer**: GL90-99
- **Charter Version**: 2.0.0
- **Semantic Anchor**: ../../engine/governance/GL_SEMANTIC_ANCHOR.json

## Integration with Agent Orchestration

This service integrates with the `.github/agents/agent-orchestration.yml` system as a high-priority synchronization agent:

```yaml
agents:
  - id: data-sync-agent
    name: "Data Synchronization Agent"
    type: "synchronization"
    priority: 1
    enabled: true
    config:
      serviceConfig: "instant/configs/data-sync-config.yaml"
      pipelines:
        - "users-sync"
        - "orders-sync"
        - "inventory-sync"
    outputs:
      - "sync-status.json"
      - "sync-report.md"
```

## Integration with File Organizer System

The service works with the `file-organizer-system` for:
- Configuration file management
- Artifact storage and organization
- Log file management
- Backup and archive operations

## Integration with AEP Engine

The service leverages the `engine` (Architecture Execution Pipeline) for:
- Architecture validation and compliance
- Governance enforcement
- Semantic anchoring and evidence chain generation
- Pipeline orchestration

## Features

### Core Capabilities

1. **Multiple Sync Modes**
   - Real-time synchronization using websockets or change data capture
   - Scheduled synchronization with cron-based triggers
   - Manual synchronization triggered via API or CLI

2. **Conflict Resolution Strategies**
   - Source-wins: Always use source data
   - Target-wins: Always preserve target data
   - Latest-timestamp: Use record with latest timestamp
   - Manual resolution: Require human intervention

3. **Incremental Sync with Change Tracking**
   - Detailed tracking of all data changes
   - Configurable retention periods
   - History reconstruction capabilities

4. **Retry Logic**
   - Exponential backoff strategy
   - Configurable retry limits and delays
   - Jitter for preventing thundering herd

5. **Data Validation Layer**
   - Required field validation
   - Type validation
   - Format validation with regex patterns
   - Range validation
   - Custom validation functions

6. **Sync Status Monitoring**
   - Real-time metrics collection
   - Health check endpoints
   - Alerting and notifications
   - Performance dashboards

## Directory Structure

```
instant/
├── configs/
│   └── data-sync-config.yaml    # Main configuration file
├── docs/
│   └── DATA-SYNC-SERVICE-GUIDE.md # Comprehensive guide
├── scripts/
│   └── (deployment scripts)      # Deployment and management scripts
├── src/
│   ├── data-sync-service.ts      # Core synchronization service
│   ├── data-sync-engine.ts       # Orchestration engine
│   └── index.ts                  # Entry point
└── README.md                     # This file
```

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

2. Update the configuration with your environment settings:
```yaml
sourceSystem:
  connectionString: "your-source-url"
  auth:
    credentials:
      token: "your-source-token"

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

## Usage Examples

### Basic Synchronization

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

// Get current status
const currentStatus = service.getStatus();
console.log('Current Status:', currentStatus);

// Stop service
await service.stop();
```

### Using the Engine

```typescript
import { createSyncEngine } from './src/data-sync-engine';

// Create and start engine
const engine = await createSyncEngine();

// Create a synchronization job
const jobId = await engine.createJob('users-sync');

// Monitor progress
engine.on('jobCompleted', (job) => {
  console.log(`Job ${job.id} completed`);
});

// Get metrics
const metrics = engine.getMetrics();
console.log('Engine Metrics:', metrics);

// Stop engine
await engine.stop();
```

## Configuration

### Sync Modes

Configure the synchronization mode in `data-sync-config.yaml`:

```yaml
syncMode: "real-time"  # Options: real-time, scheduled, manual

# For scheduled mode:
schedule:
  cron: "0 */5 * * * *"  # Every 5 minutes
  timezone: "UTC"
```

### Conflict Resolution

Choose your conflict resolution strategy:

```yaml
conflictResolution: "latest-timestamp"  # Options: source-wins, target-wins, latest-timestamp, manual
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
```

### Monitoring and Alerting

Enable monitoring and configure alerts:

```yaml
monitoring:
  enabled: true
  metricsPort: 9090
  alertThreshold: 0.1  # 10% failure rate
  
  alerting:
    enabled: true
    thresholds:
      failureRate: 0.1
      conflictRate: 0.05
      latencyMs: 5000
```

## API Reference

### DataSyncService Interface

```typescript
interface DataSyncService {
  start(): Promise<void>;
  stop(): Promise<void>;
  syncNow(): Promise<SyncStatus>;
  getStatus(): SyncStatus;
  getConflicts(): SyncRecord[];
  resolveConflict(recordId: string, resolution: 'source' | 'target'): Promise<void>;
}
```

### DataSyncEngine Interface

```typescript
interface DataSyncEngine {
  start(): Promise<void>;
  stop(): Promise<void>;
  registerService(name: string, config: SyncConfig): void;
  registerPipeline(config: PipelineConfig): void;
  createJob(pipelineName: string): Promise<string>;
  getJobStatus(jobId: string): SyncJob | undefined;
  getMetrics(): EngineMetrics;
}
```

## Monitoring

### Metrics

The service exposes metrics on port 9090:

- `sync_throughput` - Records per second
- `sync_latency` - Synchronization latency in ms
- `sync_errors` - Number of errors
- `sync_conflicts` - Number of conflicts
- `queue_size` - Queue size

### Health Check

Health check endpoint at `/health`:

```bash
curl [EXTERNAL_URL_REMOVED]
```

## Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:coverage
```

## Troubleshooting

### Common Issues

1. **High Failure Rate**
   - Check network connectivity
   - Verify authentication credentials
   - Review validation rules

2. **Conflicts Not Resolving**
   - Review conflict resolution strategy
   - Ensure timestamps are synchronized
   - Implement manual resolution process

3. **Performance Issues**
   - Increase batch size
   - Adjust max concurrent syncs
   - Optimize validation rules

For detailed troubleshooting, see the [Data Synchronization Service Guide](docs/DATA-SYNC-SERVICE-GUIDE.md).

## Best Practices

1. **Start with Manual Mode**: Test configurations before enabling real-time sync
2. **Monitor Closely**: Enable monitoring and alerts from the beginning
3. **Validate Early**: Implement comprehensive validation rules
4. **Plan for Conflicts**: Choose appropriate conflict resolution strategy
5. **Test Rollback**: Ensure you can rollback changes if needed
6. **Document Configurations**: Keep documentation updated
7. **Regular Backups**: Enable backup functionality
8. **Audit Regularly**: Review audit logs for anomalies

## Security

- All credentials should be stored in environment variables
- Enable encryption for sensitive fields
- Mask sensitive data in logs
- Implement RBAC for API endpoints
- Perform regular security audits

## Governance and Compliance

This service is fully compliant with GL governance requirements:

- All files include GL governance markers
- Semantic anchoring with GL_SEMANTIC_ANCHOR.json
- Evidence chain generation for all operations
- Audit logging with configurable retention
- Compliance with GDPR, HIPAA, SOC2 standards

## Support and Maintenance

### Version Information

- **Version**: 1.0.0
- **Build Date**: 2026-01-28
- **Governance Layer**: GL90-99
- **Charter Version**: 2.0.0

### Backup and Recovery

```bash
# Backup configuration
cp configs/data-sync-config.yaml configs/backup/data-sync-config.yaml.$(date +%Y%m%d)

# View logs
tail -f logs/data-sync.log

# Check status
curl [EXTERNAL_URL_REMOVED]
```

## Contributing

When contributing to this service:

1. Follow GL governance standards
2. Include governance markers in all files
3. Update semantic anchors when necessary
4. Generate evidence chains for changes
5. Follow the coding standards defined in the repository

## License

This project is part of the MachineNativeOps ecosystem and follows the same license terms.

## Related Documentation

- [Data Synchronization Service Guide](docs/DATA-SYNC-SERVICE-GUIDE.md)
- [Agent Orchestration Configuration](../.github/agents/agent-orchestration.yml)
- [AEP Engine Documentation](../engine/README.md)
- [File Organizer System](../file-organizer-system/README.md)