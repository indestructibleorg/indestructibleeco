# IndestructibleEco Architecture

URI: indestructibleeco://docs/ARCHITECTURE

## System Overview

IndestructibleEco is an enterprise cloud-native AI platform built as a mono-repository. It provides multi-engine inference routing across 7 engine backends, .qyaml governance enforcement, Argo CD GitOps deployment, and a full observability stack. The platform is designed for high availability with circuit breakers, connection pooling, automatic failover, and self-healing infrastructure.

## High-Level Architecture

```
                                    +------------------+
                                    |   Cloudflare     |
                                    |   Edge Worker    |
                                    | (webhook-router) |
                                    +--------+---------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
            +-------+-------+       +-------+-------+       +-------+-------+
            |  Root Gateway |       |  API Gateway  |       |  Web Frontend |
            |  (FastAPI)    |       |  (Express)    |       |  (React+Vite) |
            |  port 8000    |       |  port 3000    |       |  port 5173    |
            +-------+-------+       +-------+-------+       +---------------+
                    |                        |
                    +----------+-------------+
                               |
                    +----------+----------+
                    |    AI Service       |
                    |    (FastAPI)        |
                    |    HTTP:8001        |
                    |    gRPC:8000        |
                    +----------+----------+
                               |
          +--------------------+--------------------+
          |          |         |         |          |
     +----+---+ +---+---+ +---+---+ +---+---+ +---+---+
     | vLLM   | | TGI   | |Ollama | |SGLang | | More  |
     | :8100  | | :8101 | |:11434 | | :8102 | | ...   |
     +--------+ +-------+ +-------+ +-------+ +-------+

                    +----------+----------+
                    |   Data Layer        |
                    +-----+-----+--------+
                    |     |     |        |
               Postgres Redis FAISS  Elasticsearch
                          Neo4j
```

## Component Layers

The system is organized into six dependency layers. Each layer depends only on layers below it.

### Layer 0: Schema & Types

Shared data contracts that all other layers depend on. Changes here propagate everywhere.

| Component | Path | Language | Description |
|-----------|------|----------|-------------|
| Pydantic Schemas | `src/schemas/` | Python | `auth.py` (UserRole, APIKeyCreate/Info/Result), `inference.py` (ChatCompletionRequest/Response, UsageInfo, ChatMessage, ChatRole), `models.py` (ModelFormat, ModelCapability, ModelStatus, ModelRegisterRequest, QuantizationConfig, ModelHardwareRequirements) |
| Shared Types | `packages/shared-types/src/` | TypeScript | `entities/` (user.ts, platform.ts, ai.ts, yaml.ts), `api/` (requests.ts, responses.ts) |
| gRPC Stubs | `backend/shared/proto/generated/` | Python | Dataclass-based lightweight stubs matching proto message interfaces |
| API Types | `backend/api/src/types.ts` | TypeScript | ServiceHealth, PaginatedResponse, ErrorResponse, JobStatus, AIGenerateRequest/Response, YAMLGenerateRequest |

### Layer 1: Core Business Logic

Stateless business logic modules used by multiple services.

| Component | Path | LOC | Description |
|-----------|------|-----|-------------|
| Auth Middleware | `src/middleware/auth.py` | 172 | API key lifecycle (create/revoke/rotate), JWT validation, rate limiting per key, role-based access (admin/developer/viewer) |
| Model Registry | `src/core/registry.py` | 213 | Central model catalog with 6 default models, resolve by ID/capability, filter by engine compatibility, lifecycle management (register/unload/retire) |
| Request Queue | `src/core/queue.py` | 145 | Priority-based async queue (HIGH/NORMAL/LOW), depth tracking, dequeue with timeout, queue statistics |

### Layer 2: Service Integration

Stateful services that manage connections, pools, and background tasks.

**AI Service (`backend/ai/src/services/`):**

| Service | LOC | Description |
|---------|-----|-------------|
| `engine_manager.py` | 280+ | Orchestrates 7 engine adapters. Initializes connection pools and circuit breakers per engine. Provides `generate()` with automatic failover: tries preferred engine, falls back through healthy alternatives. Tracks per-engine health metrics. |
| `circuit_breaker.py` | ~120 | Three-state machine (CLOSED -> OPEN -> HALF_OPEN). Configurable failure threshold and recovery timeout. Per-engine isolation prevents cascade failures. |
| `connection_pool.py` | ~100 | Persistent `httpx.AsyncClient` pool per engine endpoint. Configurable pool size, timeouts, and keepalive. Shared across all requests to an engine. |
| `worker.py` | ~250 | Async inference job queue with priority scheduling (HIGH/NORMAL/LOW). Job lifecycle: submit -> poll -> complete/fail/cancel. Stale job cleanup. Expiry enforcement. |
| `grpc_server.py` | ~200 | gRPC inference server with `GenerateCompletion`, `StreamCompletion`, `GenerateEmbedding`, `HealthCheck` RPCs. Internal high-performance communication channel. |
| `embedding.py` | ~220 | Batch embedding service. 3-tier priority: EmbeddingService (engine) -> sentence-transformers -> deterministic hash fallback. Cosine similarity, Euclidean distance, dimension reduction. |
| `health_monitor.py` | ~180 | Periodic engine health probing. Circuit breaker recovery (HALF_OPEN -> CLOSED on success). Registry sync. Worker stale cleanup. Degraded mode detection when all engines are down. |

**API Service (`backend/api/src/services/`):**

| Service | LOC | Description |
|---------|-----|-------------|
| `supabase.ts` | 232 | Singleton Supabase client with typed CRUD for users, platforms, ai_jobs, governance_records. Service role key for RLS bypass. |
| `ai-proxy.ts` | 213 | HTTP proxy to AI service with per-endpoint timeouts, exponential backoff retry (max 2), 4xx fail-fast, structured error mapping. |
| `job-poller.ts` | 171 | Interval poller for pending jobs. Checks upstream AI service status, updates Supabase, pushes status via Socket.IO. Stale job timeout. Governance audit logging. |

**Shared (`backend/shared/`):**

| Service | Path | Description |
|---------|------|-------------|
| DB Client | `db/client.py` | Supabase client wrapper with typed CRUD, connection pooling via httpx, automatic retry on transient failures, health check. |

### Layer 3: API Routes

HTTP/gRPC endpoints that compose Layer 1 and Layer 2 components.

**AI Service Routes (`backend/ai/src/routes.py`, 759 LOC):**

- OpenAI-compatible: `/v1/chat/completions` (SSE streaming), `/v1/completions`, `/v1/embeddings`, `/v1/models`
- Legacy: `/generate`, `/vector/align`, `/embeddings`, `/embeddings/similarity`
- Jobs: `/jobs` (POST/GET), `/jobs/:id` (GET/DELETE)
- Governance: `/qyaml/descriptor`
- All model resolution through `ModelRegistry.resolve_model()`
- Shared `_generate_via_engine()` helper with engine manager failover

**API Gateway Routes (`backend/api/src/routes/`):**

| Route File | Mount Path | Description |
|------------|-----------|-------------|
| `auth.ts` | `/auth/*` | Supabase Auth signup/login/refresh/logout/me |
| `platforms.ts` | `/api/v1/platforms/*` | CRUD backed by Supabase, admin-only writes |
| `ai.ts` | `/api/v1/ai/*` | Proxies to AI service via ai-proxy, persists jobs to Supabase |
| `yaml.ts` | `/api/v1/yaml/*` | Proxies to AI YAML Toolkit, local fallback generation/validation |
| `health.ts` | `/health/*`, `/ready`, `/metrics` | Liveness/readiness probes, Prometheus metrics |
| `im-webhook.ts` | `/api/v1/im/*` | Receives normalized payloads from Cloudflare edge worker |

**Root Gateway (`src/app.py`, 359 LOC):**

- Unified entry point with `ServiceProxy` for HTTP forwarding
- `/v1/chat/completions` proxied to AI service with local fallback
- `/api/v1/generate`, `/api/v1/yaml/*`, `/api/v1/platforms` proxied to respective services
- API key authentication via `AuthMiddleware`

### Layer 4: Frontend & Client Applications

| Application | Path | Technology | Description |
|-------------|------|-----------|-------------|
| Web Dashboard | `platforms/web/app/src/` | React + Vite | 6 pages: Dashboard, AIPlayground, Models, Platforms, Settings, YAMLStudio. Dark theme. Stores (auth, ai, platform), hooks (useAuth, useAI, useWebSocket). |
| Desktop App | `platforms/desktop/` | Electron | Desktop wrapper for the web application |
| IM Integration | `platforms/im-integration/` | Node.js + Express | 4 channel adapters (WhatsApp, Telegram, LINE, Messenger) with shared normalizer/router. HMAC signature verification, typing indicators, graceful shutdown. |
| API Client | `packages/api-client/` | TypeScript | Typed HTTP client with retry, interceptors, WebSocket reconnect with exponential backoff and heartbeat |
| UI Kit | `packages/ui-kit/` | React | Reusable components: Modal, Dropdown, Table, Toast |

### Layer 5: Infrastructure

| Component | Path | Description |
|-----------|------|-------------|
| Kubernetes Manifests | `k8s/` | `.qyaml` manifests for base services (namespace, API gateway, engines, postgres, redis), ingress, monitoring (Grafana, Prometheus), Argo CD |
| Backend K8s | `backend/k8s/` | Service-specific manifests: deployments, services, configmaps, ingress, secrets, security (mTLS, network policies, RBAC) |
| Helm Chart | `helm/` | 12 templates: deployment, service, HPA, PDB, ingress, configmap, secrets, serviceaccount, networkpolicy, servicemonitor, NOTES.txt, _helpers.tpl |
| Argo CD | `k8s/argocd/` | ApplicationSet for multi-env (staging tracks `develop`, production tracks `main`). Self-healing, pruning, Slack notifications. |
| Cloudflare Worker | `backend/cloudflare/` | Edge webhook router with KV-backed rate limiting, request deduplication, per-channel payload normalization, retry with dead-letter queue |
| Docker Compose | `docker-compose.yml` | 7 services (postgres, redis, ai, api, web, prometheus, grafana) with health checks, named networks, persistent volumes |
| Monitoring | `ecosystem/monitoring/` | Grafana dashboards (9-panel AI service dashboard), Prometheus alert rules (16 alerts in 4 groups) |
| Tracing | `ecosystem/tracing/` | Distributed tracing configuration (Jaeger/Tempo) |
| Logging | `ecosystem/logging/` | Centralized logging (Loki) |
| Service Discovery | `ecosystem/service-discovery/` | Service mesh configuration (Consul) |

## Inference Engine Adapters

All adapters implement `BaseInferenceAdapter` (defined in `backend/ai/engines/inference/base.py`) providing a unified interface: `generate()`, `stream()`, `health_check()`, `list_models()`, and optional `embeddings()`.

| Engine | Adapter Path | Features |
|--------|-------------|----------|
| vLLM | `adapters/vllm_adapter.py` | PagedAttention for efficient KV-cache, continuous batching, prefix caching, tensor parallelism for multi-GPU |
| TGI | `adapters/tgi_adapter.py` | Token streaming, watermarking, flash attention |
| Ollama | `adapters/ollama_adapter.py` | Local model management, pull-on-demand, CPU/GPU inference |
| SGLang | `adapters/sglang_adapter.py` | RadixAttention, structured generation, constrained decoding |
| TensorRT-LLM | `adapters/tensorrt_adapter.py` | INT8/FP8 quantization, multi-GPU pipeline parallelism, in-flight batching |
| DeepSpeed | `adapters/deepspeed_adapter.py` | ZeRO inference, pipeline parallelism, kernel injection |
| LMDeploy | `adapters/lmdeploy_adapter.py` | TurboMind backend, persistent batch scheduling |

**Resilience Layer** (`backend/ai/engines/inference/resilience.py`):

Every adapter request passes through the resilience layer which provides:

1. **Connection Pool**: Persistent `httpx.AsyncClient` per adapter (avoids connection setup overhead)
2. **Circuit Breaker**: Per-adapter CLOSED -> OPEN -> HALF_OPEN state machine. Opens after N consecutive failures, auto-recovers after timeout.
3. **Retry**: Exponential backoff (base 0.5s, max 8s, multiplier 2x). 4xx errors fail-fast (no retry). 5xx and connection errors retry up to 2 times.

## Compute, Folding, and Index Engines

Beyond inference, the platform includes specialized engine categories:

**Compute Engines** (`backend/ai/engines/compute/`):

| Engine | Description |
|--------|-------------|
| `similarity.py` | Cosine similarity, dot product, Euclidean distance between vectors |
| `ranking.py` | Relevance ranking with BM25 and vector-based scoring |
| `clustering.py` | K-means, DBSCAN clustering on embedding spaces |
| `reasoning.py` | Chain-of-thought reasoning pipeline |

**Folding Engines** (`backend/ai/engines/folding/`):

| Engine | Description |
|--------|-------------|
| `vector_folding.py` | 3-tier embed priority (EmbeddingService -> sentence-transformers -> hash fallback). Injects `embedding_service` for engine-backed embeddings. |
| `graph_folding.py` | Graph-based knowledge folding |
| `hybrid_folding.py` | Combined vector + graph folding |
| `realtime_index.py` | WAL-backed realtime index updater. Append-only JSONL write-ahead log with `recover_from_wal()` for crash recovery. |

**Index Engines** (`backend/ai/engines/index/`):

| Engine | Config Prefix | Description |
|--------|--------------|-------------|
| `faiss_index.py` | `ECO_FAISS_*` | FAISS vector index (IVFFlat, GPU support, persistent storage) |
| `elasticsearch_index.py` | `ECO_ES_*` | Elasticsearch hybrid search (vector + keyword) |
| `neo4j_index.py` | `ECO_NEO4J_*` | Neo4j graph index for relationship queries |
| `hybrid_router.py` | - | Routes queries to optimal index based on query type |

## Governance Architecture

All `.qyaml` manifests must contain four governance blocks. Validation is enforced at three levels:

1. **GovernanceEngine** (`backend/ai/src/governance.py`, 400 LOC): YAML-parse validation via `yaml.safe_load_all`. 5-phase pipeline: YAML parse -> block check -> field check -> GKE compatibility -> semantic validation. Persistent audit log (append-only JSONL with rotation).

2. **OPA Policies** (`policy/qyaml_governance.rego`): Rego-based policy enforcement for CI/CD gates.

3. **CI Validator** (`tools/ci-validator/validate.py`): 8-validator engine run in CI pipeline gate 1.

**Required Governance Blocks:**

| Block | Required Fields | Purpose |
|-------|----------------|---------|
| `document_metadata` | `unique_id` (UUID v1), `uri`, `urn`, `target_system`, `schema_version`, `generated_by`, `created_at` | Document identity and traceability |
| `governance_info` | `owner`, `compliance_tags`, `lifecycle_policy` | Ownership and compliance |
| `registry_binding` | `service_endpoint`, `health_check_path` | Service discovery integration |
| `vector_alignment_map` | `alignment_model`, `coherence_vector_dim` | Vector space alignment |

See [.qyaml Governance Specification](QYAML_GOVERNANCE.md) for the complete specification.

## Data Flow: Chat Completion Request

```
1. Client sends POST /v1/chat/completions
   |
2. Root Gateway (src/app.py)
   |- AuthMiddleware validates API key
   |- ServiceProxy.forward() to AI service
   |
3. AI Service (backend/ai/src/routes.py)
   |- _resolve_model_id() via ModelRegistry
   |- _generate_via_engine() dispatches to EngineManager
   |
4. EngineManager (backend/ai/src/services/engine_manager.py)
   |- Selects preferred engine from MODEL_ENGINE_MAP
   |- Checks CircuitBreaker.allow_request()
   |- Gets httpx.AsyncClient from ConnectionPool
   |
5. Engine Adapter (e.g., vllm_adapter.py)
   |- Builds engine-native payload
   |- Sends HTTP request to engine endpoint
   |- Parses response into InferenceResponse
   |
6. Response flows back through layers
   |- EngineManager records success/failure
   |- Routes formats OpenAI-compatible response
   |- Gateway returns to client
```

**Failover Path:**

If the preferred engine fails (circuit open or HTTP error), EngineManager iterates through remaining healthy engines in order. If all engines fail, returns 503 with degraded status.

## Resilience Patterns Summary

| Pattern | Implementation | Scope |
|---------|---------------|-------|
| Circuit Breaker | `services/circuit_breaker.py` + `engines/inference/resilience.py` | Per-engine, CLOSED/OPEN/HALF_OPEN |
| Connection Pool | `services/connection_pool.py` + `engines/inference/resilience.py` | Per-engine persistent httpx.AsyncClient |
| Retry | `engines/inference/resilience.py` + `services/ai-proxy.ts` | Exponential backoff, 4xx fail-fast |
| Health Monitor | `services/health_monitor.py` | Periodic probing, degraded mode detection |
| WAL | `engines/folding/realtime_index.py` | Append-only JSONL, crash recovery |
| Job Queue | `services/worker.py` | Priority scheduling, stale cleanup, cancellation |
| Audit Log | `governance.py` AuditPersistence | Append-only JSONL with rotation |

## CI/CD Pipeline

5-gate pipeline defined in `.github/workflows/ci.yaml` (344 LOC):

| Gate | Name | Checks |
|------|------|--------|
| 1 | validate | CI Validator Engine (8 validators), .qyaml governance |
| 2 | lint | Python `py_compile` (all .py files), JS syntax check, YAML governance, skill validation |
| 3 | test | 448 tests (unit + integration + e2e + skill) |
| 4 | build | Docker build, repository structure verification (42+ dirs, 24+ files) |
| 5 | auto-fix | Diagnostic mode on failure (runs `auto-fix.py`) |

## Security Architecture

| Layer | Mechanism | Implementation |
|-------|-----------|---------------|
| Authentication | JWT + API Keys | Supabase Auth, `src/middleware/auth.py` |
| Authorization | RBAC | admin/developer/viewer roles |
| Transport | mTLS | `backend/k8s/security/mtls.qyaml` |
| Network | Network Policies | `backend/k8s/security/network-policies.qyaml`, `helm/templates/networkpolicy.yaml` |
| RBAC | Kubernetes RBAC | `backend/k8s/security/rbac.qyaml` |
| Secrets | External Secret Manager | `backend/k8s/secrets/sealed-secrets.qyaml` |
| Scanning | Trivy + SBOM | `.trivy.yaml`, `sbom.json` (CycloneDX) |
| Policy | OPA/Conftest | `policy/` directory |
| Rate Limiting | Per-key limits | `src/middleware/auth.py`, `backend/api/src/middleware/rate-limiter.ts` |
| Edge Security | HMAC verification | Cloudflare worker + IM channel adapters |

## Related Documentation

- [API Reference](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Environment Variables Reference](ENV_REFERENCE.md)
- [.qyaml Governance Specification](QYAML_GOVERNANCE.md)
- [Argo CD GitOps Guide](argocd-gitops-guide.md)
- [Auto-Repair Architecture](auto-repair-architecture.md)
