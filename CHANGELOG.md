# Changelog

All notable changes to IndestructibleEco are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-20

### Added

#### Core Platform

- Root gateway (FastAPI) with `ServiceProxy` forwarding to AI and API backends
- Multi-engine inference routing across 7 backends (vLLM, TGI, Ollama, SGLang, TensorRT-LLM, DeepSpeed, LMDeploy)
- OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/v1/models`)
- Async job queue with priority scheduling (HIGH/NORMAL/LOW) and WebSocket status updates
- Model registry with lifecycle management and capability filtering
- Request queue with priority-based async dequeuing
- Pydantic v2 schemas for auth, inference, and model definitions
- API key + JWT authentication middleware with RBAC (admin/developer/viewer)

#### AI Service (`backend/ai/`)

- FastAPI application with lifespan-managed services
- 7 inference engine adapters with unified `BaseInferenceAdapter` interface
- `EngineManager` with automatic failover and health-based routing
- `CircuitBreaker` state machine (CLOSED/OPEN/HALF_OPEN) per engine
- `ConnectionPool` with persistent `httpx.AsyncClient` per engine
- `InferenceWorker` with async job queue, timeout, expiry, stale cleanup
- `GrpcServer` with GenerateCompletion, StreamCompletion, GenerateEmbedding RPCs
- `EmbeddingService` with batch embed, similarity, dimension reduction, hash fallback
- `EngineHealthMonitor` with periodic probing, circuit breaker recovery, degraded mode
- `ResilientClient` with exponential backoff retry and 4xx fail-fast
- `GovernanceEngine` with 5-phase YAML-parse validation and persistent JSONL audit log
- Vector folding engine with 3-tier embed priority and WAL persistence
- Realtime index updater with crash-recovery WAL
- External dependency configs for FAISS, Elasticsearch, Neo4j

#### API Gateway (`backend/api/`)

- Express + TypeScript server with Socket.IO WebSocket
- Supabase client with typed CRUD for users, platforms, AI jobs, governance records
- AI proxy service with per-endpoint timeouts and exponential backoff retry
- Job poller with upstream status check, DB update, Socket.IO push
- Auth routes (signup, login, refresh, API key management)
- Platform CRUD routes with Supabase persistence
- AI routes with job persistence and ownership checks
- YAML routes with upstream AI proxy and local fallback
- IM webhook router for normalized payloads from edge worker
- OpenAPI 3.0.3 specification (723 lines, 12 reusable schemas)

#### Edge & Messaging

- Cloudflare Worker webhook router with KV rate limiting, request deduplication, HMAC verification
- 4 IM channel adapters (WhatsApp, Telegram, LINE, Messenger) with signature verification
- Shared normalizer/router with Redis retry and ephemeral session fallback

#### Frontend (`platforms/web/`)

- React + Vite application with 6 pages (Dashboard, Login, AIPlayground, Models, Platforms, Settings)
- YAMLStudio page for .qyaml editing
- Auth store, AI store, platform store (Zustand)
- useAuth, useAI, useWebSocket hooks
- Dark theme with CSS variables and comprehensive utility classes
- WebSocket client with exponential backoff reconnect and heartbeat

#### Packages

- `@indestructibleeco/shared-types` v1.0.0 -- TypeScript type definitions (user, platform, AI, requests, responses)
- `@indestructibleeco/api-client` v1.0.0 -- Typed HTTP client with retry, interceptors, WebSocket
- `@indestructibleeco/ui-kit` v1.0.0 -- React components (Modal, Dropdown, Table, Toast)

#### Infrastructure

- Kubernetes .qyaml manifests with governance blocks (24 files)
- Helm chart with 12 templates (Deployment, Service, Ingress, HPA, PDB, ConfigMap, Secrets, ServiceAccount, NetworkPolicy, ServiceMonitor, NOTES.txt)
- Argo CD ApplicationSet for multi-environment (staging auto-sync, production manual)
- Helm values for staging environment
- Docker Compose with 7 services and health checks
- Supabase migrations (initial schema + alignment migration)

#### Observability

- Grafana dashboard with 9 panels for AI service metrics
- 16 Prometheus alert rules in 4 groups (availability, latency, saturation, governance)
- Distributed tracing configuration (Jaeger/Tempo)
- Centralized logging (Loki)
- Service discovery (Consul)

#### CI/CD

- 5-gate CI pipeline (validate, lint, test, build, auto-fix)
- CI Validator Engine with 8 validators
- Auto-fix engine with dry-run diagnostic mode
- Deploy workflows for backend, web, desktop, IM integration
- YAML governance lint with strict block/field validation

#### Security

- Trivy vulnerability scanning configuration
- CycloneDX SBOM (sbom.json)
- OPA governance policies (Dockerfile, .qyaml)
- HMAC signature verification on webhook endpoints
- Network policies for namespace isolation

#### Tooling

- YAML Toolkit v8 with generate, validate, lint, convert commands
- Skill creator with scaffolding and 70 skill tests
- CI validator with 8 validation checks

#### Documentation

- API Reference (1003 lines) with request/response examples
- Architecture guide (315 lines) with 6-layer breakdown
- Deployment guide (434 lines) covering local, Docker, K8s, Helm, Argo CD
- Developer guide (252 lines) with conventions and workflow
- Environment variable reference (166 lines, 50+ ECO_* variables)
- .qyaml governance specification (275 lines)
- CONTRIBUTING.md, SECURITY.md, LICENSE (Apache-2.0)

#### Testing

- 500 tests across unit, integration, and E2E suites
- Test coverage for all core modules, services, engines, adapters
- E2E service lifecycle tests (59 tests)
- E2E full flow tests (12 tests)
- Skill manifest tests (70 tests)

[1.0.0]: https://github.com/indestructibleorg/indestructibleeco/releases/tag/v1.0.0
