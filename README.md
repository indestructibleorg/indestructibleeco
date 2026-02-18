# IndestructibleEco v1.0

Enterprise cloud-native AI platform built on a mono-repository architecture with YAML-governed Kubernetes manifests, multi-engine inference routing, and quantum-bert vector alignment.

## Architecture

```
indestructibleeco/
├── packages/                # Shared libraries
│   ├── ui-kit/              # React component library (Tailwind + Radix UI)
│   ├── api-client/          # Auto-generated API SDK (fetch + socket.io)
│   └── shared-types/        # TypeScript interfaces (zero runtime cost)
├── backend/                 # Server services
│   ├── api/                 # REST + WebSocket API (Node.js Express 5)
│   ├── ai/                  # AI inference service (Python FastAPI)
│   ├── shared/              # Proto definitions, DB models, utilities
│   │   ├── proto/           # gRPC service definitions
│   │   ├── models/          # Shared data models (UUID v1)
│   │   └── utils/           # URI/URN builders, governance stamps
│   ├── k8s/                 # YAML-governed Kubernetes manifests (.qyaml)
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress/
│   │   ├── configmaps/
│   │   ├── secrets/
│   │   ├── security/        # NetworkPolicies, RBAC, mTLS
│   │   └── kustomization.yaml
│   └── supabase/            # DB migrations + RLS policies
├── platforms/               # User-facing applications
│   ├── web/                 # React 18 + Vite + React Router 6
│   ├── desktop/             # Electron 29 + Vite renderer
│   └── im-integration/     # WhatsApp / Telegram / LINE / Messenger
├── k8s/                     # Infrastructure K8s manifests (.qyaml)
│   ├── base/                # Core services (api-gateway, engines, redis, postgres)
│   ├── ingress/             # Ingress + NetworkPolicy
│   └── monitoring/          # Prometheus + Grafana
├── docker/                  # Docker images & production compose
│   ├── Dockerfile           # API Gateway image
│   ├── Dockerfile.gpu       # GPU engine images (vLLM, SGLang, TGI)
│   ├── docker-compose.yml   # Full production stack
│   └── prometheus.yml       # Prometheus scrape config
├── ecosystem/               # Cross-platform observability
│   ├── monitoring/          # Prometheus + Grafana + Alertmanager
│   ├── tracing/             # Jaeger + OpenTelemetry
│   ├── service-discovery/   # Consul
│   └── docker-compose.ecosystem.yml
├── helm/                    # Helm chart for K8s deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── tools/                   # Internal tooling
│   ├── yaml-toolkit/        # YAML Governance Toolkit v1
│   ├── ci-validator/        # Centralized CI Validation Engine (7 validators)
│   │   ├── validate.py      # Main engine — YAML, governance, identity, Dockerfile, schema, workflow, cross-ref
│   │   ├── schemas/         # JSON schemas for artifact validation
│   │   └── rules/           # Rule definitions (identity, governance, workflow)
│   └── skill-creator/       # Skill authoring & lifecycle management
│       ├── SKILL.md         # Skill definition spec
│       ├── scripts/         # init_skill.py, quick_validate.py, validate.js
│       ├── references/      # Workflow, output, and disclosure patterns
│       └── skills/          # Skill manifests (github-actions-repair-pro)
├── scripts/                 # Build & deploy scripts
│   ├── build.sh             # Docker image build (with pre-build validation)
│   └── deploy.sh            # K8s deployment (with pre-deploy validation)
├── tests/                   # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .github/workflows/       # CI/CD pipelines
│   ├── ci.yaml              # Unified 4-gate pipeline (validate → lint → test → build)
│   └── auto-repair.yaml     # Self-healing automation (triggered on CI failure)
├── .circleci/config.yml     # Secondary CI pipeline (validate → lint → test)
├── docker-compose.yml       # Local dev stack
└── package.json             # Workspace root
```

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

## Environment Variables (ECO_* Prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_ENVIRONMENT` | `development` | Runtime environment |
| `ECO_LOG_LEVEL` | `INFO` | Log verbosity |
| `ECO_AI_HTTP_PORT` | `8001` | AI service HTTP port |
| `ECO_AI_GRPC_PORT` | `8000` | AI service gRPC port |
| `ECO_AI_MODELS` | `vllm,ollama,tgi,sglang` | Enabled inference engines |
| `ECO_REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `ECO_VECTOR_DIM` | `1024` | Vector alignment dimension |
| `ECO_ALIGNMENT_MODEL` | `quantum-bert-xxl-v1` | Alignment model identifier |
| `ECO_CONSUL_ENDPOINT` | `http://localhost:8500` | Service discovery |
| `ECO_JAEGER_ENDPOINT` | `http://localhost:14268/api/traces` | Distributed tracing |

See `.env.example` for the complete variable reference.

## .qyaml Governance Blocks

Every `.qyaml` manifest must contain these 4 mandatory blocks:

1. **document_metadata** — unique_id (UUID v1), uri, urn, target_system, cross_layer_binding, schema_version, generated_by, created_at
2. **governance_info** — owner, approval_chain, compliance_tags, lifecycle_policy
3. **registry_binding** — service_endpoint, discovery_protocol, health_check_path, registry_ttl
4. **vector_alignment_map** — alignment_model, coherence_vector_dim, function_keyword, contextual_binding

## CI/CD Architecture

### Unified 4-Gate Pipeline (`.github/workflows/ci.yaml`)

| Gate | Job | Description |
|------|-----|-------------|
| 1 | `validate` | CI Validator Engine — 7 validators with JSON report |
| 2 | `lint` | Python compile, JS syntax, YAML governance, skill manifests |
| 3 | `test` | Config, governance engine, shared utils, YAML toolkit, skill tests |
| 4 | `build` | Docker image build + repository structure verification |

### CI Validator Engine (`tools/ci-validator/validate.py`)

| Validator | Scope | Auto-fixable |
|-----------|-------|-------------|
| YAML Syntax | `*.yaml`, `*.yml`, `*.qyaml` | %YAML directives, tabs, inline python |
| Governance Blocks | `*.qyaml` | Missing blocks/fields |
| Identity Consistency | All source files | Stale `superai`/`SUPERAI_` references |
| Dockerfile Paths | `Dockerfile*` | COPY path mismatches |
| Schema Compliance | `skill.json` | Structure violations |
| Workflow Syntax | `.github/workflows/*.yaml` | Inline `python -c`, `continue-on-error` |
| Cross-References | `kustomization.yaml` | Missing file references |

### Self-Healing Automation (`.github/workflows/auto-repair.yaml`)

Triggered automatically on CI failure. Runs diagnosis via CI Validator Engine, fetches failure logs, and generates structured repair reports.

### Secondary Pipeline (`.circleci/config.yml`)

Mirrors GitHub Actions logic: validate → lint → test.

## Quick Start

```bash
# Validate repository (run CI Validator Engine locally)
python3 tools/ci-validator/validate.py

# Start backend + dependencies (local dev)
docker compose up

# Start full production stack
cd docker && docker compose up

# Start ecosystem (monitoring, tracing, discovery)
npm run ecosystem:up

# Start web dev server
npm run dev:web

# Validate all .qyaml manifests
npm run yaml:lint

# Validate skill manifests
npm run skill:validate

# Build all Docker images
./scripts/build.sh 1.0.0

# Deploy to K8s
./scripts/deploy.sh
```

## API Endpoints

### Authentication
- `POST /auth/signup` — Register
- `POST /auth/login` — Login → JWT
- `POST /auth/refresh` — Refresh token
- `POST /auth/logout` — Invalidate session
- `GET /auth/me` — Current user

### Platforms
- `GET /api/v1/platforms` — List platforms
- `POST /api/v1/platforms` — Register platform (admin)
- `GET /api/v1/platforms/:id` — Platform detail
- `PATCH /api/v1/platforms/:id` — Update (admin)
- `DELETE /api/v1/platforms/:id` — Deregister (admin)

### YAML Governance
- `POST /api/v1/yaml/generate` — Generate .qyaml
- `POST /api/v1/yaml/validate` — Validate .qyaml
- `GET /api/v1/yaml/registry` — Service registry
- `GET /api/v1/yaml/vector/:id` — Vector alignment

### AI Generation
- `POST /api/v1/ai/generate` — Submit job (async)
- `GET /api/v1/ai/jobs/:jobId` — Poll status
- `POST /api/v1/ai/vector/align` — Vector alignment
- `GET /api/v1/ai/models` — List models

## Version Matrix

| Component | Version | Image |
|-----------|---------|-------|
| API Gateway | 1.0.0 | `ghcr.io/indestructibleorg/api:v1.0.0` |
| AI Service | 1.0.0 | `ghcr.io/indestructibleorg/ai:v1.0.0` |
| vLLM | 0.6.6 | `vllm/vllm-openai:v0.6.6` |
| SGLang | 0.3.6 | `lmsysorg/sglang:v0.3.6-cu124` |
| TGI | 2.4.1 | `ghcr.io/huggingface/text-generation-inference:2.4.1` |
| Ollama | latest | `ollama/ollama:latest` |
| Redis | 7 | `redis:7-alpine` |
| PostgreSQL | 16 | `postgres:16-alpine` |
| Prometheus | 2.54.0 | `prom/prometheus:v2.54.0` |
| Grafana | 11.2.0 | `grafana/grafana:11.2.0` |
| Node.js | ≥20.x | — |
| Python | ≥3.11 | — |

---

**IndestructibleEco v1.0 · Architecture Blueprint · CONFIDENTIAL · INTERNAL USE ONLY**