# indestructibleeco v1.0

> Enterprise cloud-native platform — mono-repository

## Quick Start

```bash
# Prerequisites: Node 20+, pnpm 9+, Docker, kubectl

## Core Policies

| Policy | Standard | Weight |
|--------|----------|--------|
| UUID | v1 (time-based, sortable, traceable) | 1.0 |
| URI | `indestructibleeco://{domain}/{kind}/{name}` | 1.0 |
| URN | `urn:indestructibleeco:{domain}:{kind}:{name}:{uuid}` | 1.0 |
| Schema Version | v1 | 1.0 |
| YAML Toolkit | v1 | 1.0 |
| Manifests | `.qyaml` extension, 4 mandatory governance blocks | 1.0 |
| Vector Alignment | quantum-bert-xxl-v1, dim 1024–4096, tol 0.0001–0.005 | 1.0 |
| Security | Zero-trust, mTLS, Sealed Secrets, RBAC, RLS, NetworkPolicy | 1.0 |
| Env Vars | `ECO_*` prefix for all configuration variables | 1.0 |
| Namespace | `indestructibleeco` (K8s, Docker, Helm) | 1.0 |
| Container Naming | `eco-*` prefix for all containers | 1.0 |
| Registry | `ghcr.io/indestructibleorg/*` | 1.0 |
| GitHub Actions | Actions from `indestructibleorg` (SHA-pinned), plus local `./.github/actions/*` and digest-pinned `docker://` actions | 1.0 |

## Environment Variables (ECO_* Prefix)

# 2. Start local infrastructure
pnpm local:up          # postgres + redis + api + ai via Docker Compose

# 3. Start observability stack (optional)
pnpm ecosystem:up      # Prometheus + Grafana + Jaeger + Consul

# 4. Start web platform in dev mode
pnpm --filter @indestructibleeco/web dev

# 5. Open Grafana at http://localhost:3030 (admin/admin)
#    Open Jaeger at http://localhost:16686
#    Open Consul at http://localhost:8500
```

## Workspace Structure

```
├── packages/              # Shared: ui-kit, api-client, shared-types
├── backend/
│   ├── api/               # Express + Socket.IO REST/WS API
│   ├── ai/                # FastAPI + gRPC AI inference service
│   │   └── engines/       # Multi-engine inference (vLLM, TGI, Ollama, etc.)
│   ├── k8s/               # Kubernetes manifests (.qyaml governance)
│   ├── shared/            # Proto definitions, shared models/utils
│   ├── supabase/          # Database migrations & RLS policies
│   └── cloudflare/        # Edge workers (webhook routing)
├── platforms/
│   ├── web/               # React SPA (Vite + TailwindCSS)
│   ├── desktop/           # Electron desktop app
│   ├── im-integration/    # WhatsApp, Telegram, LINE, Messenger bots
│   └── platform-template/ # Scaffold for new platforms
├── ecosystem/             # Prometheus, Grafana, Jaeger, Consul
├── tools/
│   ├── yaml-toolkit/      # YAML Toolkit v8 — .qyaml generator & validator
│   ├── skill-creator/     # Skill authoring & validation framework
│   └── ci-validator/      # Centralized CI validation engine (7 validators) + auto-fix
├── k8s/                   # Infrastructure-level K8s manifests
│   ├── base/              # Core services (api-gateway, redis, postgres, engines)
│   ├── ingress/           # Ingress rules
│   ├── monitoring/        # Grafana + Prometheus
│   └── argocd/            # Argo CD GitOps applications & config
├── src/                   # API Gateway entry point (root-level)
├── docs/                  # Architecture guides & operational docs
├── helm/                  # Helm chart for platform deployment
├── docker/                # Docker build files (standard + GPU)
├── scripts/               # Build, deploy & Argo CD automation
├── tests/                 # Unit, integration, e2e test suites
└── .github/workflows/     # CI/CD pipelines (validate → lint → test → build → auto-fix)
```

## CI/CD Pipeline

The unified CI pipeline (`.github/workflows/ci.yaml`) enforces a 5-gate quality system:

| Gate | Purpose |
|------|---------|
| **validate** | Centralized CI Validator Engine (7 validators) |
| **lint** | Python compile, JS syntax, YAML governance, skill manifests |
| **test** | Config, governance, shared utils, YAML toolkit, skill tests |
| **build** | Docker image build + repository structure verification |
| **auto-fix** | Runs on failure — diagnoses issues, identifies auto-fixable patterns |

An additional `auto-repair.yaml` workflow triggers on CI failure via `workflow_run`, performing deep diagnostics and generating consolidated repair reports.

| Validator | Scope | Auto-fixable |
|-----------|-------|-------------|
| YAML Syntax | `*.yaml`, `*.yml`, `*.qyaml` | %YAML directives, tabs, inline python |
| Governance Blocks | `*.qyaml` | Missing blocks/fields |
| Identity Consistency | All source files | Stale `superai`/`SUPERAI_` references |
| Dockerfile Paths | `Dockerfile*` | COPY path mismatches |
| Schema Compliance | `skill.json` | Structure violations |
| Workflow Syntax | `.github/workflows/*.yaml` | Inline `python -c`, `continue-on-error` |
| Cross-References | `kustomization.yaml` | Missing file references |
| Actions Policy | `.github/workflows/*.yaml` | GitHub Actions ownership and SHA pinning violations |

The platform uses Argo CD for fully automated Kubernetes deployment via GitOps. Every push to `main` triggers automatic synchronization of all `.qyaml` manifests to the cluster.

| Feature | Description |
|---------|-------------|
| **Self-Heal** | Cluster drift automatically corrected to Git state |
| **Prune** | Resources removed from Git are deleted from cluster |
| **Webhook** | Push-triggered sync (no polling delay) |
| **Notifications** | Slack + webhook alerts for sync events |
| **Dual Environment** | Production (`indestructibleeco`) + Staging (`ecosystem-staging`) |

```bash
# Install Argo CD + deploy applications
./scripts/argocd-install.sh

# Setup GitHub webhook for push-triggered sync
./scripts/argocd-setup-webhook.sh

# Full guide: docs/argocd-gitops-guide.md
```

## Auto-Repair Engine

The CI Auto-Fix Engine (`tools/ci-validator/auto-fix.py`) provides automated repair for known issue patterns:

| Strategy | Scope | Risk |
|----------|-------|------|
| `path-correction` | Dockerfile COPY paths | Low |
| `identity-replace` | Stale identity references | Medium |
| `yaml-syntax` | Tabs, trailing whitespace | Low |
| `governance-block` | Missing .qyaml governance blocks | Medium |
| `schema-field` | Missing skill.json fields | Low |

```bash
# Detect issues
python3 tools/ci-validator/validate.py

# Preview fixes (dry-run)
python3 tools/ci-validator/auto-fix.py --dry-run

# Apply fixes
python3 tools/ci-validator/auto-fix.py

# Full architecture: docs/auto-repair-architecture.md
```

## YAML Governance

All deployment manifests are auto-generated by the indestructibleeco YAML Toolkit v8.
**No hand-crafted .qyaml files in production.**

```bash
# Generate a K8s manifest from module descriptor
pnpm yaml:gen --name my-service --target k8s

# Validate an existing .qyaml file
pnpm yaml:validate --input backend/k8s/deployments/api.qyaml
```

## Environment Variables

All environment variables use the `ECO_*` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_AI_HTTP_PORT` | 8001 | AI service HTTP port |
| `ECO_AI_GRPC_PORT` | 8000 | AI service gRPC port |
| `ECO_REDIS_URL` | redis://localhost:6379 | Redis connection |
| `ECO_VECTOR_DIM` | 1024 | Vector alignment dimension |
| `ECO_ALIGNMENT_MODEL` | quantum-bert-xxl-v1 | Default alignment model |

## Adding a new platform

```bash
cp -r platforms/platform-template platforms/platform-XX
# Edit package.json, add CI workflow, generate K8s manifest
```

## License

Internal use only — CONFIDENTIAL