# indestructibleeco v1.0

> Enterprise cloud-native AI platform — mono-repository

## Quick Start

```bash
# Clone
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Install Python deps
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy

# Run tests
PYTHONPATH=. pytest tests/ -v
pytest tools/skill-creator/skills/ -v

# Run CI validator
python3 tools/ci-validator/validate.py

# Generate .qyaml
node tools/yaml-toolkit/bin/cli.js gen --input=module.json --output=out/

# Docker (full stack)
docker compose up -d

# Argo CD sync
argocd app sync eco-staging
```

## Architecture

```
indestructibleeco/
├── backend/
│   ├── ai/                          # AI inference service (FastAPI)
│   │   ├── src/
│   │   │   ├── app.py               # FastAPI entry + engine lifecycle
│   │   │   ├── config.py            # ECO_* env config (FAISS, ES, Neo4j)
│   │   │   ├── routes.py            # REST + OpenAI-compatible endpoints
│   │   │   ├── governance.py        # YAML-parse governance engine + audit
│   │   │   └── services/
│   │   │       ├── engine_manager.py # 7-engine orchestrator + failover
│   │   │       ├── circuit_breaker.py# 3-state circuit breaker
│   │   │       ├── connection_pool.py# Persistent httpx pools
│   │   │       ├── worker.py         # Async job queue + priority scheduling
│   │   │       ├── grpc_server.py    # gRPC inference server
│   │   │       ├── embedding.py      # Batch embedding + similarity
│   │   │       └── health_monitor.py # Engine health probing + recovery
│   │   └── engines/
│   │       ├── inference/            # 7 adapters + resilience layer
│   │       ├── compute/             # similarity, ranking, clustering, reasoning
│   │       ├── folding/             # vector (EmbeddingService), graph, hybrid, realtime (WAL)
│   │       └── index/               # FAISS, Elasticsearch, Neo4j, hybrid router
│   ├── api/                         # API gateway (Express/TypeScript)
│   │   └── src/
│   │       ├── routes/              # auth, platforms, ai, yaml, health, im-webhook
│   │       ├── services/            # supabase, ai-proxy, job-poller
│   │       ├── middleware/           # auth, rate-limiter, error-handler
│   │       └── types.ts             # Shared TypeScript types
│   ├── shared/
│   │   ├── db/                  # Supabase client wrapper + connection pool
│   │   ├── proto/generated/     # gRPC stubs (dataclass-based)
│   │   ├── models/              # Shared data models
│   │   └── utils/               # Shared utilities
│   ├── cloudflare/              # Edge webhook router (KV rate limiting)
│   ├── supabase/                # Database migrations
│   └── k8s/                     # Backend K8s manifests
├── src/                             # Root gateway (FastAPI)
│   ├── app.py                   # Application factory + proxy routing
│   ├── schemas/                 # Pydantic v2 schemas
│   ├── core/                    # Registry + queue
│   └── middleware/              # Auth middleware
├── packages/
│   ├── shared-types/            # TypeScript shared types
│   ├── api-client/              # Typed HTTP client (retry + interceptors)
│   └── ui-kit/                  # React components (Modal, Dropdown, Table, Toast)
├── platforms/
│   ├── web/                     # React + Vite (6 pages, dark theme)
│   ├── desktop/                 # Electron app
│   └── im-integration/          # 4 channel adapters (WhatsApp, Telegram, LINE, Messenger)
├── ecosystem/
│   ├── monitoring/              # Grafana dashboards + Prometheus alerts
│   ├── tracing/                 # Distributed tracing
│   ├── logging/                 # Centralized logging
│   └── service-discovery/       # Service mesh
├── k8s/                             # Platform K8s manifests + Argo CD
├── helm/                            # Helm chart (14 templates)
├── tools/
│   ├── ci-validator/            # 8-validator CI engine
│   ├── yaml-toolkit/            # .qyaml generator + validator
│   └── skill-creator/           # Skill scaffolding (70 tests)
├── policy/                          # OPA governance policies
├── docs/                            # API, Architecture, Deployment guides
└── tests/                           # 400+ tests (unit, integration, e2e)
```

## CI/CD

5-gate pipeline:
1. **validate** — CI Validator Engine
2. **lint** — Python compile + JS syntax + YAML governance
3. **test** — Core tests + skill tests
4. **build** — Docker build + structure verification
5. **auto-fix** — Diagnostic mode on failure

## Documentation

- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Argo CD GitOps Guide](docs/argocd-gitops-guide.md)
- [Auto-Repair Architecture](docs/auto-repair-architecture.md)

## License

Apache-2.0
