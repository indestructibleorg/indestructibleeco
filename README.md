# IndestructibleEco v1.0

Enterprise cloud-native platform built on a mono-repository architecture.

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
│   ├── supabase/            # DB migrations + RLS policies
│   └── cloudflare/          # Workers + Pages routing
├── platforms/               # User-facing applications
│   ├── web/                 # React 18 + Vite + React Router 6
│   ├── desktop/             # Electron 29 + Vite renderer
│   ├── im-integration/      # WhatsApp / Telegram / LINE / Messenger
│   └── chrome-extension/    # Browser extension
├── ecosystem/               # Cross-platform observability
│   ├── monitoring/          # Prometheus + Grafana + Alertmanager
│   ├── tracing/             # Jaeger + OpenTelemetry
│   ├── service-discovery/   # Consul
│   └── docker-compose.ecosystem.yml
├── tools/                   # Internal tooling
│   ├── yaml-toolkit/        # YAML Governance Toolkit v1
│   └── skill-creator/       # Skill authoring tool
├── .github/workflows/       # Per-platform CI/CD pipelines
├── docker-compose.yml       # Local dev stack
└── package.json             # Workspace root
```

## Core Policies

| Policy | Standard |
|--------|----------|
| UUID | v1 (time-based, sortable, traceable) |
| URI | `indestructibleeco://{domain}/{kind}/{name}` |
| URN | `urn:indestructibleeco:{domain}:{kind}:{name}:{uuid}` |
| Schema Version | v1 |
| YAML Toolkit | v1 |
| Manifests | `.qyaml` extension, 4 mandatory governance blocks |
| Vector Alignment | quantum-bert-xxl-v1, dim 1024–4096 |
| Security | Zero-trust, mTLS, Sealed Secrets, RBAC, RLS |

## .qyaml Governance Blocks

Every `.qyaml` manifest must contain:

1. **document_metadata** — unique_id (UUID v1), uri, urn, target_system, cross_layer_binding, schema_version, generated_by, created_at
2. **governance_info** — owner, approval_chain, compliance_tags, lifecycle_policy
3. **registry_binding** — service_endpoint, discovery_protocol, health_check_path, registry_ttl
4. **vector_alignment_map** — alignment_model, coherence_vector_dim, function_keyword, contextual_binding

## Quick Start

```bash
# Start backend + dependencies
docker compose up

# Start ecosystem (monitoring, tracing, discovery)
npm run ecosystem:up

# Start web dev server
npm run dev:web

# Validate all .qyaml manifests
npm run yaml:lint
```

## CI/CD Pipelines

| Workflow | Trigger | Target |
|----------|---------|--------|
| ci.yaml | push/PR to main | Lint + Test + Build |
| deploy-backend.yml | push main — backend/** | GKE via kubectl |
| deploy-web.yml | push main — platforms/web/** | Cloudflare Pages |
| deploy-desktop.yml | tag v*.*.* | GitHub Releases |
| deploy-im-integration.yml | push main — platforms/im-integration/** | Cloudflare Workers + K8s |
| yaml-lint.yml | PR — **.qyaml | Governance validation |

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

---

**indestructibleeco v1.0 · Architecture Blueprint · CONFIDENTIAL · INTERNAL USE ONLY**