# indestructibleeco v1.0

> Enterprise cloud-native AI platform — mono-repository

## Quick Start

```bash
# Clone
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Install Python deps
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema

# Run tests (136 core + 70 skill = 206 total)
PYTHONPATH=. pytest tests/ -v
pytest tools/skill-creator/skills/ -v

# Run CI validator
python3 tools/ci-validator/validate.py

# Generate .qyaml
node tools/yaml-toolkit/bin/cli.js gen --input=module.json --output=out/

# Docker build
docker build -t eco-ai:dev -f backend/ai/Dockerfile backend/ai/

# Argo CD sync
argocd app sync eco-ai-service
```

## Architecture

```
indestructibleeco/
├── backend/
│   ├── ai/                          # AI inference service (FastAPI)
│   │   ├── src/
│   │   │   ├── app.py               # FastAPI entry + engine lifecycle
│   │   │   ├── config.py            # ECO_* env config
│   │   │   ├── routes.py            # /generate, /vector/align, /models
│   │   │   ├── governance.py        # Governance engine
│   │   │   └── services/
│   │   │       ├── engine_manager.py # 7-engine orchestrator + failover
│   │   │       ├── circuit_breaker.py# 3-state circuit breaker
│   │   │       └── connection_pool.py# Persistent httpx pools
│   │   ├── engines/
│   │   │   ├── inference/            # 7 adapters (vLLM, TGI, Ollama, SGLang, TensorRT, DeepSpeed, LMDeploy)
│   │   │   ├── compute/             # similarity, ranking, clustering, reasoning
│   │   │   ├── folding/             # vector, graph, hybrid, realtime
│   │   │   └── index/               # FAISS, Elasticsearch, Neo4j, hybrid router
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── api/                          # API gateway (Express + TypeScript)
│   │   ├── src/
│   │   │   ├── server.ts             # Express entry
│   │   │   ├── config.ts             # ECO_* config
│   │   │   ├── middleware/            # auth, error-handler, rate-limiter
│   │   │   ├── routes/               # auth, ai, yaml, platforms, health
│   │   │   └── ws/handler.ts         # WebSocket handler
│   │   ├── openapi.yaml              # OpenAPI 3.0 spec
│   │   └── Dockerfile
│   ├── shared/
│   │   ├── models/                   # Python dataclasses
│   │   ├── utils/                    # UUID v1, URI/URN, governance stamps
│   │   └── proto/                    # gRPC definitions
│   ├── cloudflare/
│   │   └── workers/webhook-router.ts # HMAC-verified webhook forwarding
│   ├── supabase/
│   │   └── migrations/               # 6-table schema + RLS
│   └── k8s/                          # 12 .qyaml manifests + kustomization
├── packages/
│   ├── shared-types/                 # TypeScript entities + API contracts
│   ├── api-client/                   # HTTP client + WebSocket with reconnect
│   └── ui-kit/                       # React components (Button, Card, Badge, Input, Spinner, StatusIndicator)
├── platforms/
│   ├── web/app/                      # React + Vite
│   │   └── src/
│   │       ├── pages/                # Dashboard, Login
│   │       ├── components/           # Layout, ProtectedRoute, AIChat, ModelSelector
│   │       ├── store/                # Zustand (auth, ai, platform)
│   │       ├── hooks/                # useAuth, useAI, useWebSocket
│   │       └── lib/                  # api client, ws client
│   ├── desktop/                      # Electron (main, preload, IPC, tray, auto-updater)
│   │   └── resources/icon.png
│   └── im-integration/              # 4 channel adapters
│       ├── telegram/                 # Telegraf polling + webhook
│       ├── whatsapp/                 # Cloud API webhook
│       ├── line/                     # Messaging API + HMAC
│       ├── messenger/                # Graph API + HMAC
│       └── shared/                   # normalizer, router, server
├── tools/
│   ├── ci-validator/                 # 8 validators + auto-fix engine
│   ├── skill-creator/                # 2 skills (70 tests)
│   │   └── skills/
│   │       ├── github-actions-repair-pro/
│   │       └── ai-code-editor-workflow-pipeline/
│   └── yaml-toolkit/                 # .qyaml gen/validate/validate-schema
├── k8s/
│   ├── base/                         # 8 .qyaml manifests
│   ├── ingress/                      # Ingress .qyaml
│   ├── monitoring/                   # ServiceMonitor .qyaml
│   └── argocd/                       # Argo CD apps (prod + staging)
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/                    # deployment, service, ingress, hpa, pdb
├── ecosystem/
│   ├── monitoring/                   # Prometheus, Alertmanager, Grafana
│   ├── logging/                      # Loki, Promtail
│   ├── tracing/                      # Tempo, OTel Collector
│   ├── service-discovery/            # Consul
│   └── gateway/                      # Nginx dev config
├── docker/                           # Production Dockerfiles + compose
├── scripts/                          # build.sh, deploy.sh, argocd-install.sh
├── src/                              # Core gateway (FastAPI)
│   ├── app.py                        # create_app() factory
│   ├── schemas/                      # Pydantic v2 (auth, inference, models)
│   ├── middleware/                    # AuthMiddleware (API key + JWT)
│   └── core/                         # RequestQueue, ModelRegistry
├── tests/
│   ├── unit/                         # 38 tests (schemas, auth, queue, registry)
│   ├── integration/                  # 7 tests (API endpoints)
│   └── e2e/                          # 15 tests (full flow + circuit breaker)
├── docs/
│   ├── argocd-gitops-guide.md
│   └── auto-repair-architecture.md
├── .github/workflows/
│   ├── ci.yaml                       # 5-gate pipeline (validate→lint→test→build→auto-fix)
│   └── auto-repair.yaml              # Self-healing on CI failure
└── .circleci/config.yml              # 3-stage mirror pipeline
```

## CI/CD Pipeline

| Gate | Purpose | Duration |
|------|---------|----------|
| validate | CI Validator Engine (8 validators) | ~3s |
| lint | Python compile, JS syntax, .qyaml governance, skill manifests | ~5s |
| test | Core tests (66), skill tests (70), config, governance, utils, YAML toolkit | ~11s |
| build | Docker image + repository structure verification | ~35s |
| auto-fix | Diagnostic mode on failure | skipped if green |

## Environment Variables

All variables use `ECO_*` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| ECO_AI_HTTP_PORT | 8001 | AI service HTTP port |
| ECO_AI_GRPC_PORT | 8000 | AI service gRPC port |
| ECO_REDIS_URL | redis://localhost:6379 | Redis connection |
| ECO_SUPABASE_URL | — | Supabase project URL |
| ECO_VLLM_URL | http://localhost:8100 | vLLM engine endpoint |
| ECO_OLLAMA_URL | http://localhost:11434 | Ollama engine endpoint |
| ECO_TGI_URL | http://localhost:8101 | TGI engine endpoint |
| ECO_SGLANG_URL | http://localhost:8102 | SGLang engine endpoint |
| ECO_TENSORRT_URL | http://localhost:8103 | TensorRT engine endpoint |
| ECO_DEEPSPEED_URL | http://localhost:8104 | DeepSpeed engine endpoint |
| ECO_LMDEPLOY_URL | http://localhost:8105 | LMDeploy engine endpoint |

## Test Summary

| Suite | Count | Coverage |
|-------|-------|----------|
| Unit (schemas, auth, queue, registry) | 38 | Core business logic |
| Integration (API endpoints) | 7 | HTTP contract validation |
| E2E (full flow + circuit breaker) | 15 | End-to-end + resilience |
| Skill tests (2 skills) | 70 | Skill manifests + governance |
| **Total** | **130+** | |

## Deployment

```bash
# Kubernetes
kubectl apply -k k8s/base/

# Argo CD
argocd app create eco-ai --repo https://github.com/indestructibleorg/indestructibleeco \
  --path k8s/base --dest-server https://kubernetes.default.svc \
  --dest-namespace indestructibleeco --sync-policy automated

# Helm
helm install eco helm/ -n indestructibleeco --create-namespace

# Docker Compose (development)
docker-compose up -d
```
