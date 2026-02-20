# IndestructibleEco v1.0

> Enterprise cloud-native AI platform -- mono-repository

[![CI](https://github.com/indestructibleorg/indestructibleeco/actions/workflows/ci.yaml/badge.svg)](https://github.com/indestructibleorg/indestructibleeco/actions/workflows/ci.yaml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-500%20passing-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![TypeScript](https://img.shields.io/badge/typescript-5.x-blue.svg)]()

## Overview

IndestructibleEco is a production-grade AI inference platform that routes requests across 7 engine backends (vLLM, TGI, Ollama, SGLang, TensorRT-LLM, DeepSpeed, LMDeploy) with automatic failover, circuit breaking, and connection pooling. It provides OpenAI-compatible endpoints, .qyaml governance enforcement, and Argo CD GitOps deployment.

**Key capabilities:**

- **Multi-engine inference** with automatic failover across 7 backends
- **OpenAI-compatible API** (`/v1/chat/completions`, `/v1/embeddings`, `/v1/models`)
- **Async job queue** with priority scheduling and WebSocket status updates
- **Vector alignment** via quantum-bert-xxl-v1 (1024-4096 dimensions)
- **.qyaml governance** with 5-phase validation and persistent audit trail
- **Argo CD GitOps** with self-healing staging and manual production sync
- **Full observability** (Prometheus, Grafana, Jaeger, Loki)
- **500 tests** across unit, integration, and E2E suites

## Quick Start

```bash
# Clone
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Install Python deps
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy

# Run tests (500 passing)
PYTHONPATH=. pytest tests/ -v

# Run CI validator
python3 tools/ci-validator/validate.py

# Full stack (Docker Compose)
cp .env.example .env.local
docker compose up -d

# Verify
curl http://localhost:8001/health   # AI service
curl http://localhost:3000/health   # API gateway
open http://localhost:5173          # Web frontend
```

## Architecture

```
indestructibleeco/
+-- src/                          # Root gateway (FastAPI, port 8000)
|   +-- app.py                    # Application factory + proxy routing
|   +-- schemas/                  # Pydantic v2 schemas (auth, inference, models)
|   +-- core/                     # Model registry + request queue
|   +-- middleware/               # API key auth + rate limiting
+-- backend/
|   +-- ai/                       # AI inference service (FastAPI, port 8001)
|   |   +-- src/                  # app, config, routes, governance, services
|   |   +-- engines/              # inference (7 adapters), compute, folding, index
|   +-- api/                      # API gateway (Express, port 3000)
|   |   +-- src/                  # server, routes, services, middleware, ws
|   +-- shared/                   # DB client, gRPC stubs, models, utils
|   +-- cloudflare/               # Edge webhook router (KV rate limiting)
|   +-- supabase/                 # Database migrations
|   +-- k8s/                      # Backend K8s manifests
+-- packages/
|   +-- shared-types/             # TypeScript shared types
|   +-- api-client/               # Typed HTTP client (retry + WS reconnect)
|   +-- ui-kit/                   # React components (Modal, Dropdown, Table, Toast)
+-- platforms/
|   +-- web/                      # React + Vite (6 pages, dark theme)
|   +-- desktop/                  # Electron app
|   +-- im-integration/           # 4 channel adapters (WhatsApp, Telegram, LINE, Messenger)
+-- ecosystem/
|   +-- monitoring/               # Grafana dashboards + Prometheus alerts (16 rules)
|   +-- tracing/                  # Distributed tracing (Jaeger/Tempo)
|   +-- logging/                  # Centralized logging (Loki)
|   +-- service-discovery/        # Service mesh (Consul)
+-- k8s/                          # Platform K8s manifests + Argo CD
+-- helm/                         # Helm chart (12 templates)
+-- tools/
|   +-- ci-validator/             # 8-validator CI engine
|   +-- yaml-toolkit/             # .qyaml generator + validator
|   +-- skill-creator/            # Skill scaffolding (70 tests)
+-- policy/                       # OPA governance policies
+-- docs/                         # API, Architecture, Deployment, Developer Guide,
|                                 # Env Reference, .qyaml Governance, Argo CD, Auto-Repair
+-- tests/                        # 500 tests (unit, integration, e2e)
```

## Inference Engines

| Engine | Features | Default Port |
|--------|----------|-------------|
| vLLM | PagedAttention, continuous batching, prefix caching | 8100 |
| TGI | Token streaming, watermarking, flash attention | 8101 |
| SGLang | RadixAttention, structured generation | 8102 |
| TensorRT-LLM | INT8/FP8 quantization, multi-GPU | 8103 |
| DeepSpeed | ZeRO inference, pipeline parallelism | 8104 |
| LMDeploy | TurboMind, persistent batch | 8105 |
| Ollama | Local models, pull-on-demand | 11434 |

All adapters implement a unified interface (`BaseInferenceAdapter`) with `generate()`, `stream()`, `health_check()`, and `list_models()`. The `EngineManager` provides automatic failover: if the preferred engine fails, it routes to the next healthy engine.

## CI/CD

5-gate pipeline (`.github/workflows/ci.yaml`):

| Gate | Name | Description |
|------|------|-------------|
| 1 | validate | CI Validator Engine (8 validators) |
| 2 | lint | Python compile + JS syntax + YAML governance |
| 3 | test | 500 tests (unit + integration + e2e + skill) |
| 4 | build | Docker build + structure verification |
| 5 | auto-fix | Diagnostic mode on failure |

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API.md) | Complete endpoint documentation with request/response examples |
| [Architecture](docs/ARCHITECTURE.md) | System architecture, component layers, data flow, resilience patterns |
| [Deployment Guide](docs/DEPLOYMENT.md) | Local dev, Docker Compose, Kubernetes, Helm, Argo CD |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Repository structure, conventions, adding engines, testing |
| [Environment Variables](docs/ENV_REFERENCE.md) | Complete ECO_* variable reference |
| [.qyaml Governance](docs/QYAML_GOVERNANCE.md) | Governance block specification, validation, audit trail |
| [Argo CD GitOps](docs/argocd-gitops-guide.md) | GitOps deployment guide |
| [Auto-Repair](docs/auto-repair-architecture.md) | Self-healing CI architecture |
| [OpenAPI Spec](backend/api/openapi.yaml) | OpenAPI 3.0.3 specification (723 lines) |

## Security

- JWT + API key authentication with RBAC (admin/developer/viewer)
- mTLS between services, network policies for namespace isolation
- Trivy vulnerability scanning, CycloneDX SBOM
- OPA/Conftest policy enforcement for .qyaml governance
- HMAC signature verification on IM webhook endpoints
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

## License

[Apache-2.0](LICENSE)
