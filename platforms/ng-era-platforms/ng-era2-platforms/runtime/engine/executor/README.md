<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

<!--
@gl-layer ECO-90-META
@gl-module engine/executor/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Executor Stage - Stage 7

## Overview

The Executor Stage executes artifacts on local or remote systems, supporting commands, scripts, file operations, and service management with rollback capabilities.

## Components

### LocalExecutor
Local system executor.

**Features:**
- Execute shell commands
- Run scripts
- File operations (copy, mkdir, delete)
- Service management (systemctl)
- Dry-run mode
- Timeout handling

**Usage:**
```typescript
import { LocalExecutor } from './executor/local_executor';

const executor = new LocalExecutor({
  workingDir: '/workspace',
  dryRun: false
});
const result = await executor.execute(artifact, 'production');
```

### RemoteExecutor
Remote executor with SSH and API support.

**Features:**
- SSH command execution
- API endpoint execution
- Connection pooling
- Authentication handling
- Error recovery

**Usage:**
```typescript
import { RemoteExecutor } from './executor/remote_executor';

const executor = new RemoteExecutor({
  sshConfig: { host: 'remote-server', user: 'deploy' }
});
const result = await executor.execute(artifact, 'production');
```

### Rollback
Rollback manager with pre-execution backup.

**Features:**
- Pre-execution backup
- Restore capabilities
- Rollback history
- State verification

**Usage:**
```typescript
import { RollbackManager } from './executor/rollback';

const rollback = new RollbackManager();
await rollback.createBackup(artifact);
await rollback.execute(artifact, 'production');
if (failed) {
  await rollback.restore();
}
```

## Evidence Records

All executor operations generate evidence records with:
- Command/script details
- Execution output and errors
- Exit codes
- Performance metrics

## Output

**ExecutionResult:**
- `status`: 'success' | 'error' | 'warning'
- `output`: string - Command output
- `errors`: string[] - Any errors encountered
- `duration`: number - Execution time in ms
- `evidence`: EvidenceRecord[] - Complete evidence chain
