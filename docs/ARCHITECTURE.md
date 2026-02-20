# IndestructibleEco Architecture

URI: indestructibleeco://docs/ARCHITECTURE

## System Overview

IndestructibleEco is an enterprise cloud-native AI platform built as a mono-repository
with multi-engine inference routing, .qyaml governance, and Argo CD GitOps deployment.

## Component Layers

### Layer 0: Schema & Types
- `src/schemas/` - Pydantic v2 models (auth, inference, models)
- `packages/shared-types/` - TypeScript shared types
- `backend/shared/proto/` - gRPC proto stubs

### Layer 1: Core Business Logic
- `src/middleware/auth.py` - API key lifecycle, JWT, rate limiting
- `src/core/registry.py` - Model registry (6 default models)
- `src/core/queue.py` - Priority-based async request queue

### Layer 2: Service Integration
- `backend/ai/src/services/` - Engine manager, circuit breaker, connection pool, worker, gRPC, embedding, health monitor
- `backend/api/src/services/` - Supabase client, AI proxy, job poller
- `backend/shared/db/` - Shared Supabase client wrapper

### Layer 3: API Routes
- `backend/ai/src/routes.py` - AI service REST + OpenAI-compatible endpoints
- `backend/api/src/routes/` - Auth, platforms, AI, YAML, health, IM webhook
- `src/app.py` - Root gateway with proxy routing

### Layer 4: Frontend
- `platforms/web/` - React + Vite (Dashboard, AIPlayground, Models, Platforms, Settings, YAMLStudio)
- `platforms/desktop/` - Electron app
- `platforms/im-integration/` - WhatsApp, Telegram, LINE, Messenger adapters

### Layer 5: Infrastructure
- `k8s/` - Kubernetes .qyaml manifests (base, ingress, monitoring, argocd)
- `helm/` - Helm chart with templates (deployment, service, HPA, PDB, ingress, configmap, secrets, networkpolicy, servicemonitor)
- `backend/cloudflare/` - Edge webhook router
- `ecosystem/` - Monitoring (Grafana, Prometheus), tracing, logging, service discovery

## Inference Engine Adapters

| Engine | Adapter | Features |
|--------|---------|----------|
| vLLM | `vllm_adapter.py` | PagedAttention, continuous batching, prefix caching |
| TGI | `tgi_adapter.py` | Token streaming, watermarking |
| Ollama | `ollama_adapter.py` | Local models, pull-on-demand |
| SGLang | `sglang_adapter.py` | RadixAttention, structured generation |
| TensorRT-LLM | `tensorrt_adapter.py` | INT8/FP8 quantization, multi-GPU |
| DeepSpeed | `deepspeed_adapter.py` | ZeRO inference, pipeline parallelism |
| LMDeploy | `lmdeploy_adapter.py` | TurboMind, persistent batch |

## Resilience Patterns

- **Circuit Breaker**: CLOSED -> OPEN -> HALF_OPEN per engine
- **Connection Pool**: Persistent httpx.AsyncClient per adapter
- **Retry**: Exponential backoff with 4xx fail-fast
- **Health Monitor**: Periodic engine probing with degraded mode detection
- **WAL**: Write-ahead log for crash recovery in realtime index

## Governance

All .qyaml manifests must contain 4 governance blocks:
1. `document_metadata` - UUID v1, URI, URN, schema_version
2. `governance_info` - owner, compliance_tags, lifecycle_policy
3. `registry_binding` - service_endpoint, health_check_path
4. `vector_alignment_map` - alignment_model, coherence_vector_dim

Validation is enforced by:
- GovernanceEngine (Python, YAML parsing)
- OPA policies (policy/qyaml_governance.rego)
- CI validator (tools/ci-validator/validate.py)
