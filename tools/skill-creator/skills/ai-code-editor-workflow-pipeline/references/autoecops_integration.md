# AutoEcoOps Ecosystem Integration

## Architecture

The AI Code Editor Workflow Pipeline integrates with the AutoEcoOps shared kernel (control plane) for enterprise-grade capabilities across the remediation lifecycle.

```
┌─────────────────────────────────────────────────────────┐
│                Shared Kernel (Control Plane)             │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌─────────────┐ ┌────────────────────┐│
│ │ Auth Service  │ │ Memory Hub  │ │ Policy & Audit     ││
│ │ (Keycloak)   │ │ (pgvector)  │ │ (OPA/Kyverno)      ││
│ └──────────────┘ └─────────────┘ └────────────────────┘│
│ ┌──────────────┐ ┌─────────────┐                       │
│ │ Event Bus    │ │ Infra Mgr   │                       │
│ │ (Kafka)      │ │ (ArgoCD)    │                       │
│ └──────────────┘ └─────────────┘                       │
└─────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
    AI Code Editor Workflow Pipeline
    (Understand → Retrieve → Analyze → Reason →
     Remediate → Validate → Audit)
```

## 1. Auth Service Integration

### JWT Token Validation
Every pipeline action validates the actor's JWT token against the Auth Service before executing remediation operations.

### RBAC Permission Checks
Required permissions per phase:

- `remediation:read` — Understand, Retrieve, Analyze, Reason
- `remediation:write` — Consolidate, Integrate
- `remediation:deploy` — Validate (production), Audit
- `remediation:admin` — Override policies, force-push

### API Key Rotation
Service-to-service authentication uses API keys with 90-day rotation. Keys are stored in sealed secrets and referenced via `ECO_AUTH_API_KEY` environment variable.

## 2. Memory Hub Integration

### Vector Search (RAG)
The Retrieve phase queries Memory Hub for similar code patterns and past solutions using vector embeddings.

```
POST /api/v1/search
{
  "query": "memory leak in connection pool",
  "top_k": 10,
  "filters": { "type": ["incident", "fix", "runbook"] }
}
```

### Document Ingestion
After successful remediation, the pipeline ingests the fix details into Memory Hub for future retrieval:

- Root cause description
- Fix strategy and patch
- Validation results
- Audit trail reference

### Embedding Model
Default: `text-embedding-3-small` via `ECO_EMBEDDING_MODEL` environment variable. Dimension: 1024 (aligned with IndestructibleEco vector alignment model).

## 3. Event Bus Integration

### Published Events
The pipeline publishes events at each phase transition:

| Event Type | Phase | Payload |
|-----------|-------|---------|
| `remediation.started` | Understand | problem_id, target_path, actor |
| `remediation.analyzed` | Analyze | root_causes, severity |
| `remediation.fixed` | Integrate | commit_sha, patch_diff |
| `remediation.validated` | Validate | success_rate, layers |
| `remediation.completed` | Audit | trace_id, compliance_tags |

### Event Schema
```json
{
  "event_type": "remediation.completed",
  "source": "ai-code-editor-workflow-pipeline",
  "timestamp": "ISO 8601",
  "trace_id": "UUID v1",
  "data": { ... }
}
```

### Subscribers

- **Monitoring dashboards** — Real-time remediation status
- **Notification services** — Alert on failure or policy violation
- **Analytics pipeline** — Aggregate success rates and trends

## 4. Policy & Audit Integration

### OPA Policy Decisions
Before applying any fix, the pipeline queries OPA for policy approval:

```
POST /v1/data/remediation/allow
{
  "input": {
    "actor": "ai-code-editor-workflow-pipeline",
    "action": "apply-fix",
    "resource": "src/db/pool.py",
    "severity": "critical",
    "compliance_mode": "enterprise"
  }
}
```

### Kyverno Policies
For K8s-related fixes, Kyverno validates manifests before deployment:

- Resource limits enforcement
- Image registry restrictions
- Label requirements
- Network policy compliance

### Audit Write
Every phase writes to the immutable audit log:

- Actor, action, resource, result
- Policy version and decision
- Content hash and signature
- Governance stamp (URI/URN)

## 5. Infra Manager Integration

### Drift Detection
After deployment, Infra Manager monitors for configuration drift:

- Compare deployed state vs. GitOps source
- Alert on unauthorized changes
- Auto-remediate if policy allows

### Rollback Triggers
If post-deployment validation fails:

1. Infra Manager detects SLO violation
2. Triggers automatic rollback to last known good state
3. Publishes `remediation.rollback` event
4. Pipeline re-enters Analyze phase with new context

### GitOps Sync
All fixes are committed to Git and synced via ArgoCD:

- Declarative desired state in Git
- Automated sync with drift detection
- Multi-cluster support via ApplicationSets

## Integration Flow Example

```
1. Pipeline detects AI-generated code vulnerability
2. Queries Memory Hub for similar cases (RAG)
3. Calls Auth Service to verify RBAC permissions
4. Generates fix, publishes remediation.analyzed to Event Bus
5. Policy & Audit validates fix against OPA policies
6. Fix applied, committed, pushed via GitOps
7. Infra Manager monitors deployment for drift
8. Audit trail written to immutable storage
9. Fix details ingested into Memory Hub for future retrieval
```
