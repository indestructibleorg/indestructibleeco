# .qyaml Governance Specification

URI: indestructibleeco://docs/QYAML_GOVERNANCE

## Overview

`.qyaml` is the IndestructibleEco governance-enhanced YAML format for Kubernetes manifests. Every `.qyaml` file extends standard Kubernetes YAML with four mandatory governance blocks that enable traceability, compliance enforcement, service discovery integration, and vector space alignment.

## File Extension

All governance-enhanced Kubernetes manifests use the `.qyaml` extension instead of `.yaml` or `.yml`. This enables:

- Automated governance validation in CI pipelines
- Distinct tooling via `yaml-toolkit`
- Clear separation from non-governed YAML files

## Required Governance Blocks

Every `.qyaml` manifest must contain these four top-level blocks:

### 1. document_metadata

Identity and traceability information for the manifest document.

```yaml
document_metadata:
  unique_id: "550e8400-e29b-41d4-a716-446655440000"   # UUID v1 (required)
  uri: "indestructibleeco://k8s/deployment/eco-ai"      # URI (required)
  urn: "urn:indestructibleeco:k8s:deployment:eco-ai"    # URN (required)
  target_system: "k8s"                                   # Target platform (required)
  schema_version: "v8"                                   # Schema version (required)
  generated_by: "yaml-toolkit-v8"                        # Generator tool (required)
  created_at: "2026-02-20T10:00:00.000Z"                # ISO 8601 timestamp (required)
  cross_layer_binding: ["eco-redis", "eco-postgres"]     # Dependencies (optional)
```

**Validation Rules:**
- `unique_id` must be a valid UUID v1 (time-based)
- `uri` must start with `indestructibleeco://`
- `urn` must start with `urn:indestructibleeco:`
- `schema_version` must match pattern `v\d+`

### 2. governance_info

Ownership, compliance, and lifecycle policy.

```yaml
governance_info:
  owner: "platform-team"                    # Owning team (required)
  approval_chain: ["tech-lead", "sre"]      # Approval chain (optional)
  compliance_tags: ["soc2", "gdpr"]         # Compliance tags (required)
  lifecycle_policy: "standard"              # Lifecycle policy (required)
```

**Lifecycle Policies:**
- `standard` - Normal lifecycle with manual retirement
- `ephemeral` - Auto-cleanup after TTL
- `critical` - Requires approval chain for any changes

### 3. registry_binding

Service discovery and health check integration.

```yaml
registry_binding:
  service_endpoint: "http://eco-ai-svc:8001"   # Service endpoint (required)
  discovery_protocol: "consul"                   # Discovery protocol (optional)
  health_check_path: "/health"                   # Health check path (required)
  registry_ttl: 30                               # TTL in seconds (optional)
  k8s_namespace: "indestructibleeco"             # Kubernetes namespace (optional)
```

### 4. vector_alignment_map

Vector space alignment configuration for semantic search and embedding coherence.

```yaml
vector_alignment_map:
  alignment_model: "quantum-bert-xxl-v1"     # Alignment model (required)
  coherence_vector_dim: 1024                  # Vector dimension (required)
  coherence_vector: []                        # Pre-computed vector (optional)
  function_keyword: ["ai-service"]            # Function keywords (optional)
  contextual_binding: "eco-ai -> [redis]"     # Dependency context (optional)
```

## Complete Example

```yaml
# k8s/base/api-gateway.qyaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eco-api-gateway
  namespace: indestructibleeco
  labels:
    app.kubernetes.io/name: eco-api-gateway
    app.kubernetes.io/part-of: indestructibleeco

document_metadata:
  unique_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  uri: "indestructibleeco://k8s/deployment/eco-api-gateway"
  urn: "urn:indestructibleeco:k8s:deployment:eco-api-gateway"
  target_system: "k8s"
  schema_version: "v8"
  generated_by: "yaml-toolkit-v8"
  created_at: "2026-02-20T10:00:00.000Z"
  cross_layer_binding:
    - eco-ai-service
    - eco-redis
    - eco-postgres

governance_info:
  owner: "platform-team"
  approval_chain:
    - tech-lead
    - sre-oncall
  compliance_tags:
    - soc2
    - internal
  lifecycle_policy: "standard"

registry_binding:
  service_endpoint: "http://eco-api-gateway:8000"
  discovery_protocol: "consul"
  health_check_path: "/health"
  registry_ttl: 30
  k8s_namespace: "indestructibleeco"

vector_alignment_map:
  alignment_model: "quantum-bert-xxl-v1"
  coherence_vector_dim: 1024
  coherence_vector: []
  function_keyword:
    - api-gateway
    - routing
    - authentication
  contextual_binding: "eco-api-gateway -> [eco-ai-service, eco-redis]"

spec:
  replicas: 3
  selector:
    matchLabels:
      app: eco-api-gateway
  template:
    metadata:
      labels:
        app: eco-api-gateway
    spec:
      containers:
        - name: eco-api-gateway
          image: ghcr.io/indestructibleorg/api:1.0.0
          ports:
            - containerPort: 8000
          env:
            - name: ECO_ENVIRONMENT
              value: production
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

## Validation

### GovernanceEngine (Runtime)

The `GovernanceEngine` class (`backend/ai/src/governance.py`) performs 5-phase validation:

1. **YAML Parse**: `yaml.safe_load_all()` to parse multi-document YAML
2. **Block Check**: Verify all 4 governance blocks are present
3. **Field Check**: Verify required fields within each block
4. **GKE Compatibility**: Validate Kubernetes-specific constraints
5. **Semantic Validation**: URI/URN format, UUID v1 version check, schema_version pattern

### CI Pipeline

The CI validator (`tools/ci-validator/validate.py`) runs governance validation as Gate 1 of the 5-gate pipeline.

### OPA Policies

Rego-based policies in `policy/qyaml_governance.rego` enforce governance rules via `conftest`:

```bash
conftest test -p policy/ k8s/base/*.qyaml
```

### YAML Toolkit CLI

```bash
# Validate a single file
node tools/yaml-toolkit/bin/cli.js validate k8s/base/api-gateway.qyaml

# Validate all .qyaml files
node tools/yaml-toolkit/bin/cli.js validate k8s/base/*.qyaml

# Generate a new .qyaml manifest
node tools/yaml-toolkit/bin/cli.js gen --input=module.json --output=out/
```

### API Endpoints

```bash
# Generate .qyaml via API
curl -X POST http://localhost:3000/api/v1/yaml/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module": {"name": "eco-new-service", "ports": [8080]}, "target": "k8s"}'

# Validate .qyaml via API
curl -X POST http://localhost:3000/api/v1/yaml/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "..."}'
```

## Converting to Standard Kubernetes YAML

The `convert` command strips governance blocks from `.qyaml` files, producing standard Kubernetes `.yaml` files compatible with any tool (kubectl, kustomize, Helm, etc.):

```bash
# Convert a single file
node tools/yaml-toolkit/bin/cli.js convert k8s/base/api-gateway.qyaml --output=out/

# The output file (out/api-gateway.yaml) contains only standard K8s manifests
# with all governance blocks removed.
kubectl apply -f out/api-gateway.yaml
```

This enables interoperability with standard Kubernetes tooling while maintaining governance in the source `.qyaml` files. The governance blocks are preserved in the repository and enforced by CI, but stripped at deployment time if needed.

## Audit Trail

Every governance validation produces an audit entry persisted to the append-only JSONL audit log:

```json
{
  "timestamp": "2026-02-20T10:00:00.000000+00:00",
  "action": "validate_qyaml",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "uri": "indestructibleeco://k8s/deployment/eco-ai",
  "result": "pass",
  "phases_passed": 5,
  "warnings": []
}
```

Audit logs are stored in the directory specified by `ECO_AUDIT_LOG_DIR` (default: `.eco-audit/`). Files rotate at 10 MB.

## Existing .qyaml Files

The repository contains 24 `.qyaml` files:

**Backend K8s** (`backend/k8s/`):
- `configmaps/api-config.qyaml`
- `deployments/ai.qyaml`, `deployments/api.qyaml`
- `ingress/main-ingress.qyaml`
- `namespaces/platform.qyaml`
- `secrets/sealed-secrets.qyaml`
- `security/mtls.qyaml`, `security/network-policies.qyaml`, `security/rbac.qyaml`
- `services/ai-svc.qyaml`, `services/api-svc.qyaml`

**Platform K8s** (`k8s/`):
- `argocd/namespace.qyaml`
- `base/api-gateway.qyaml`, `base/configmap.qyaml`, `base/namespace.qyaml`
- `base/ollama-engine.qyaml`, `base/postgres.qyaml`, `base/redis.qyaml`
- `base/sglang-engine.qyaml`, `base/tgi-engine.qyaml`, `base/vllm-engine.qyaml`
- `ingress/ingress.qyaml`
- `monitoring/grafana.qyaml`, `monitoring/prometheus.qyaml`

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Environment Variables Reference](ENV_REFERENCE.md)
