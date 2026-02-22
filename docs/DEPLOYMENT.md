# IndestructibleEco Deployment Guide

URI: indestructibleeco://docs/DEPLOYMENT

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Python | 3.11+ | AI service, root gateway, tests |
| Node.js | 20.x+ | API gateway, frontend, IM adapters |
| pnpm | 8.x+ | Package management (workspaces) |
| Docker | 24+ | Container builds |
| Docker Compose | 2.20+ | Local full-stack development |
| Kubernetes | 1.28+ | Production deployment |
| Helm | 3.14+ | Kubernetes package management |
| Argo CD | 2.10+ | GitOps continuous delivery |
| kubectl | 1.28+ | Kubernetes CLI |

## Local Development

### Quick Start (Python only)

Run the core test suite without any infrastructure dependencies:

```bash
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Install Python dependencies
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy

# Run all 448 tests
PYTHONPATH=. pytest tests/ -v

# Run skill tests
pytest tools/skill-creator/skills/ -v

# Run CI validator
python3 tools/ci-validator/validate.py
```

### Full Stack (Docker Compose)

Start all 7 services with a single command:

```bash
# Copy environment template
cp .env.example .env.local

# Start all services
docker compose up -d

# Verify health
curl http://localhost:8001/health   # AI service
curl http://localhost:3000/health   # API gateway
curl http://localhost:8000/health   # Root gateway
open http://localhost:5173          # Web frontend
open http://localhost:9090          # Prometheus
open http://localhost:3001          # Grafana (admin/eco_grafana)
```

**Services started by Docker Compose:**

| Service | Port | Health Check |
|---------|------|-------------|
| PostgreSQL | 5432 | `pg_isready` |
| Redis | 6379 | `redis-cli ping` |
| AI Service | 8001 (HTTP), 8000 (gRPC) | `GET /health` |
| API Gateway | 3000 | `GET /health` |
| Web Frontend | 5173 | HTTP 200 |
| Prometheus | 9090 | HTTP 200 |
| Grafana | 3001 | HTTP 200 |

### Individual Service Development

**AI Service:**

```bash
cd backend/ai
pip install -r requirements.txt  # or use pyproject.toml
ECO_AI_HTTP_PORT=8001 ECO_AI_GRPC_PORT=8000 uvicorn src.app:app --reload --port 8001
```

**API Gateway:**

```bash
cd backend/api
npm install
ECO_API_PORT=3000 ECO_AI_SERVICE_HTTP=http://localhost:8001 npm run dev
```

**Web Frontend:**

```bash
cd platforms/web/app
npm install
npm run dev  # Vite dev server on port 5173
```

### Generate .qyaml Manifests

```bash
node tools/yaml-toolkit/bin/cli.js gen --input=module.json --output=out/
node tools/yaml-toolkit/bin/cli.js validate k8s/base/*.qyaml
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl apply -f k8s/base/namespace.qyaml
```

### 2. Deploy with Helm

**Production:**

```bash
helm install eco helm/ \
  --namespace indestructibleeco \
  --values helm/values.yaml \
  --set global.imageRegistry=ghcr.io/indestructibleorg \
  --set secrets.jwtSecret=$(openssl rand -hex 32) \
  --set secrets.postgresPassword=$(openssl rand -hex 16) \
  --set secrets.hfToken=$HF_TOKEN
```

**Staging:**

```bash
helm install eco-staging helm/ \
  --namespace indestructibleeco-staging \
  --values helm/values-staging.yaml
```

### 3. Verify Deployment

```bash
# Check rollout status
kubectl rollout status deployment/eco-ai -n indestructibleeco
kubectl rollout status deployment/eco-api -n indestructibleeco

# Check pods
kubectl get pods -n indestructibleeco

# Check services
kubectl get svc -n indestructibleeco

# Test health endpoints
kubectl port-forward svc/eco-ai-svc 8001:8001 -n indestructibleeco &
curl http://localhost:8001/health
```

### 4. Helm Chart Components

The Helm chart (`helm/`) includes 12 templates:

| Template | Description |
|----------|-------------|
| `deployment.yaml` | AI service deployment with probes, resources, env |
| `service.yaml` | ClusterIP service for HTTP and gRPC ports |
| `hpa.yaml` | Horizontal Pod Autoscaler (CPU 70%, Memory 80%, 2-10 replicas) |
| `pdb.yaml` | PodDisruptionBudget (maxUnavailable: 1) |
| `ingress.yaml` | Nginx ingress with TLS (cert-manager) |
| `configmap.yaml` | ECO_* environment configuration from values |
| `secrets.yaml` | Base64-encoded secrets (redis-url, supabase-url, jwt-secret, hf-token) |
| `serviceaccount.yaml` | GKE workload identity annotation |
| `networkpolicy.yaml` | Namespace isolation, ingress-nginx allow, DNS/HTTPS egress |
| `servicemonitor.yaml` | Prometheus ServiceMonitor with eco_* metric filtering |
| `NOTES.txt` | Post-install instructions |
| `_helpers.tpl` | Template helper functions |

### 5. Engine Deployment

Each inference engine is deployed as a separate StatefulSet with GPU resources:

```bash
# Deploy vLLM engine
kubectl apply -f k8s/base/vllm-engine.qyaml

# Deploy TGI engine
kubectl apply -f k8s/base/tgi-engine.qyaml

# Deploy SGLang engine
kubectl apply -f k8s/base/sglang-engine.qyaml

# Deploy Ollama (optional, CPU-capable)
kubectl apply -f k8s/base/ollama-engine.qyaml
```

**GPU Resource Requirements:**

| Engine | GPU Memory | CPU | RAM |
|--------|-----------|-----|-----|
| vLLM | 1x A100 80GB | 4-8 cores | 16-32 GB |
| TGI | 1x A100 80GB | 4-8 cores | 16-32 GB |
| SGLang | 1x A100 80GB | 4-8 cores | 16-32 GB |
| Ollama | 1x T4 16GB (optional) | 2-4 cores | 8-16 GB |

---

## Argo CD GitOps

### Install ApplicationSet

```bash
kubectl apply -f k8s/argocd/applicationset.yaml -n argocd
```

This creates two Argo CD Applications:

| Application | Branch | Namespace | Auto-Sync | Prune |
|-------------|--------|-----------|-----------|-------|
| `eco-staging` | `develop` | `indestructibleeco-staging` | Yes | Yes |
| `eco-production` | `main` | `indestructibleeco` | No (manual) | No |

### Verify Sync

```bash
argocd app list
argocd app get eco-staging
argocd app get eco-production

# Manual sync for production
argocd app sync eco-production
```

### Self-Healing

Staging has self-healing enabled. If a resource is manually modified in the cluster, Argo CD automatically reverts it to match the Git state. Production requires manual sync to prevent accidental changes.

### Notifications

Argo CD sends Slack notifications on sync events:

| Event | Channel |
|-------|---------|
| Sync succeeded | `#eco-deployments` |
| Sync failed | `#eco-alerts` |

See [Argo CD GitOps Guide](argocd-gitops-guide.md) for detailed configuration.

---

## CI/CD Pipeline

The 5-gate CI pipeline runs on every push to `main` and `develop`, and on all pull requests to `main`.

### Gate Details

**Gate 1: validate**

- CI Validator Engine with 8 validators
- .qyaml governance validation

**Gate 2: lint**

- Python `py_compile` on all `.py` files (including all services, engines, tests)
- JavaScript syntax check
- YAML governance validation
- Skill validation

**Gate 3: test**

- 448 tests total:
  - Unit tests: `tests/unit/` (30+ test files)
  - Integration tests: `tests/integration/`
  - E2E tests: `tests/e2e/`
  - Skill tests: `tools/skill-creator/skills/`

**Gate 4: build**

- Docker image build
- Repository structure verification (42+ directories, 24+ files)
- New test file presence verification

**Gate 5: auto-fix**

- Runs only on failure
- Executes `tools/ci-validator/auto-fix.py` in diagnostic mode
- Reports findings but does not auto-commit

### Running CI Locally

```bash
# Gate 1: Validate
python3 tools/ci-validator/validate.py

# Gate 2: Lint
python3 -m py_compile src/app.py
python3 -m py_compile backend/ai/src/app.py
# ... (all .py files)

# Gate 3: Test
PYTHONPATH=. pytest tests/ -v
pytest tools/skill-creator/skills/ -v

# Gate 4: Build
docker build -t eco-ai:test -f backend/ai/Dockerfile backend/ai/
```

---

## Monitoring

### Prometheus

Prometheus scrapes metrics from all services at `/metrics` endpoints.

**Configuration:** `ecosystem/monitoring/` contains Prometheus configuration and alert rules.

**Alert Rules** (`ecosystem/monitoring/alertmanager/alert-rules.yaml`):

16 alerts organized in 4 groups:

| Group | Alerts |
|-------|--------|
| Availability | ServiceDown, HighErrorRate, PodCrashLooping, PodNotReady |
| Performance | HighLatency, HighCPU, HighMemory, QueueBacklog |
| AI Service | EngineUnhealthy, AllEnginesDown, ModelLoadFailure, InferenceTimeout |
| Infrastructure | DiskPressure, CertificateExpiry, PVCNearFull, NodeNotReady |

### Grafana

**Dashboard:** `ecosystem/monitoring/dashboards/ai-service.json` (9-panel dashboard):

| Panel | Metric |
|-------|--------|
| Request Rate | `eco_total_requests` |
| Error Rate | `eco_total_errors / eco_total_requests` |
| Latency P50/P95/P99 | `eco_request_latency_seconds` |
| Active Engines | `eco_active_engines` |
| Queue Depth | `eco_queue_depth` |
| GPU Utilization | `eco_gpu_utilization` |
| Memory Usage | `eco_memory_used_bytes` |
| Model Registry | `eco_registry_models_gauge` |
| Circuit Breaker State | `eco_circuit_breaker_state` |

### Accessing Dashboards

```bash
# Local development
open http://localhost:9090   # Prometheus
open http://localhost:3001   # Grafana

# Kubernetes
kubectl port-forward svc/prometheus 9090:9090 -n indestructibleeco
kubectl port-forward svc/grafana 3001:3000 -n indestructibleeco
```

---

## Security

### Vulnerability Scanning

```bash
# Trivy filesystem scan
trivy fs . --severity HIGH,CRITICAL

# Trivy Kubernetes config scan
trivy config k8s/ --severity HIGH,CRITICAL

# SBOM is at sbom.json (CycloneDX format)
```

### OPA Policy Enforcement

```bash
# Test governance policies
conftest test -p policy/ k8s/base/*.qyaml

# Run OPA tests
opa test policy/
```

### Network Security

- **Network Policies**: Namespace isolation with explicit ingress/egress rules
- **mTLS**: Service-to-service encryption via `backend/k8s/security/mtls.qyaml`
- **RBAC**: Least-privilege Kubernetes RBAC via `backend/k8s/security/rbac.qyaml`
- **Sealed Secrets**: Encrypted secrets via `backend/k8s/secrets/sealed-secrets.qyaml`

---

## Troubleshooting

### Common Issues

**AI service returns 503 (all engines down):**

```bash
# Check engine pods
kubectl get pods -l app.kubernetes.io/component=engine -n indestructibleeco

# Check engine logs
kubectl logs -l app=eco-vllm -n indestructibleeco --tail=50

# Check health monitor
curl http://localhost:8001/health/monitor
```

**API gateway cannot reach AI service:**

```bash
# Check service DNS resolution
kubectl exec -it deploy/eco-api -- nslookup eco-ai-svc

# Check network policy
kubectl get networkpolicy -n indestructibleeco
```

**Tests failing locally:**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Install all test dependencies
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy

# Run with verbose output
pytest tests/ -v --tb=long
```

---

## Related Documentation

- [API Reference](API.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Environment Variables Reference](ENV_REFERENCE.md)
- [.qyaml Governance Specification](QYAML_GOVERNANCE.md)
- [Argo CD GitOps Guide](argocd-gitops-guide.md)
- [Auto-Repair Architecture](auto-repair-architecture.md)
