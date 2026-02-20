# IndestructibleEco API Reference

URI: indestructibleeco://docs/API

## Overview

IndestructibleEco exposes a multi-layer API surface through three service tiers. The AI service (FastAPI, port 8001) handles inference, embeddings, and governance. The API gateway (Express, port 3000) handles authentication, platform management, and proxies AI requests with job persistence. The root gateway (FastAPI, port 8000) provides a unified entry point with proxy routing to both backend services.

All services share a common authentication model, error format, and URI/URN identification scheme.

## Base URLs

| Environment | AI Service | API Gateway | Root Gateway |
|-------------|-----------|-------------|--------------|
| Development | `http://localhost:8001` | `http://localhost:3000` | `http://localhost:8000` |
| Staging | `https://ai-staging.indestructibleeco.io` | `https://api-staging.indestructibleeco.io` | `https://staging.indestructibleeco.io` |
| Production | `https://ai.indestructibleeco.io` | `https://api.indestructibleeco.io` | `https://indestructibleeco.io` |

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header. Two token types are supported:

**JWT Session Token** (issued by Supabase Auth via `/auth/login`):

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**API Key** (issued by the root gateway's AuthMiddleware):

```
Authorization: Bearer sk-eco-<key>
```

API keys support three roles with different permission levels:

| Role | Permissions |
|------|------------|
| `admin` | Full access to all endpoints including platform CRUD write operations |
| `developer` | Read/write access to AI endpoints, read-only platform access |
| `viewer` | Read-only access to all endpoints |

Rate limiting is enforced per API key. Default: 100 requests/minute. Configurable per key via `rate_limit_per_minute` at creation time. When exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header.

---

## Health & Monitoring Endpoints

These endpoints do not require authentication.

### GET /health

Returns service liveness status. Used by Kubernetes liveness probes.

**Response 200:**

```json
{
  "status": "healthy",
  "service": "ai",
  "version": "1.0.0",
  "engines": ["vllm", "tgi", "ollama", "sglang"],
  "uptime_seconds": 3621.4,
  "models_registered": 6,
  "uri": "indestructibleeco://backend/ai/health"
}
```

When all engines are down, the AI service returns `"status": "degraded"` instead of `"healthy"`.

### GET /ready

Readiness probe. Checks downstream dependencies (Redis, AI service). Returns `503` if any dependency is unhealthy.

**Response 200:**

```json
{
  "status": "healthy",
  "service": "api",
  "version": "1.0.0",
  "components": {
    "redis": { "status": "healthy", "latencyMs": 2 },
    "ai": { "status": "healthy", "latencyMs": 15 }
  },
  "timestamp": "2026-02-20T10:00:00.000Z"
}
```

**Response 503:**

```json
{
  "status": "unhealthy",
  "components": {
    "redis": { "status": "unhealthy", "message": "ECONNREFUSED" },
    "ai": { "status": "healthy", "latencyMs": 12 }
  }
}
```

### GET /metrics

Prometheus-compatible metrics in text exposition format.

**AI Service metrics include:**

```
eco_uptime_seconds 3621.4
eco_total_requests 1542
eco_active_engines 4
eco_models_registered 6
eco_queue_depth 3
eco_worker_active_jobs 2
eco_grpc_active_streams 0
eco_embedding_requests_total 89
eco_health_monitor_checks_total 120
eco_registry_models_gauge 6
```

**API Gateway metrics include:**

```
api_uptime_seconds 3600.00
api_memory_heap_used_bytes 52428800
api_memory_heap_total_bytes 67108864
api_memory_rss_bytes 89128960
```

### GET /health/worker

Worker subsystem health (AI service only).

```json
{
  "status": "healthy",
  "active_jobs": 2,
  "pending_jobs": 5,
  "completed_total": 142,
  "failed_total": 3
}
```

### GET /health/grpc

gRPC server health (AI service only).

```json
{
  "status": "healthy",
  "port": 8000,
  "active_streams": 0
}
```

### GET /health/embedding

Embedding service health (AI service only).

```json
{
  "status": "healthy",
  "default_model": "quantum-bert-xxl-v1",
  "default_dimensions": 1024,
  "requests_total": 89
}
```

### GET /health/registry

Model registry health (AI service only).

```json
{
  "status": "healthy",
  "models_count": 6,
  "models": ["llama-3.1-8b-instruct", "llama-3.1-70b-instruct", "qwen2.5-72b-instruct", "qwen2.5-coder-32b-instruct", "deepseek-r1", "mistral-7b-instruct"]
}
```

### GET /health/monitor

Health monitor status (AI service only).

```json
{
  "status": "healthy",
  "engines_checked": 7,
  "engines_healthy": 4,
  "engines_degraded": 0,
  "last_check_seconds_ago": 12.5,
  "degraded_mode": false
}
```

---

## Authentication Endpoints

Served by the API gateway at `/auth/*`. No authentication required for signup, login, and refresh.

### POST /auth/signup

Create a new user account via Supabase Auth.

**Request:**

```json
{
  "email": "dev@example.com",
  "password": "securePassword123",
  "display_name": "Dev User"
}
```

**Response 201:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "dev@example.com",
    "urn": "urn:indestructibleeco:iam:user:550e8400-e29b-41d4-a716-446655440000"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "v1.MjAyNi0wMi0yMFQx...",
    "expires_at": 1740100800
  }
}
```

**Error 409:** Email already registered.

### POST /auth/login

Sign in with email and password.

**Request:**

```json
{
  "email": "dev@example.com",
  "password": "securePassword123"
}
```

**Response 200:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "dev@example.com",
    "role": "member",
    "urn": "urn:indestructibleeco:iam:user:550e8400-e29b-41d4-a716-446655440000"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "v1.MjAyNi0wMi0yMFQx...",
    "expires_at": 1740100800
  }
}
```

**Error 401:** Invalid credentials.

### POST /auth/refresh

Refresh an expired session token.

**Request:**

```json
{
  "refresh_token": "v1.MjAyNi0wMi0yMFQx..."
}
```

**Response 200:**

```json
{
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "v1.MjAyNi0wMi0yMFQx...",
    "expires_at": 1740187200
  }
}
```

**Error 401:** Invalid or expired refresh token.

### POST /auth/logout

Sign out the current session. Requires authentication.

**Response 200:**

```json
{ "ok": true }
```

### GET /auth/me

Get the current authenticated user profile.

**Response 200:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "dev@example.com",
    "role": "member",
    "urn": "urn:indestructibleeco:iam:user:550e8400-e29b-41d4-a716-446655440000"
  },
  "uri": "indestructibleeco://backend/api/auth/me"
}
```

---

## OpenAI-Compatible Endpoints

These endpoints are served directly by the AI service and follow the OpenAI API specification. They are also proxied through the root gateway and API gateway.

### POST /v1/chat/completions

Generate a chat completion. Supports streaming via SSE when `stream: true`.

**Request:**

```json
{
  "model": "llama-3.1-8b-instruct",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Explain Kubernetes in one paragraph." }
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

**Response 200 (non-streaming):**

```json
{
  "id": "chatcmpl-abc123def456",
  "object": "chat.completion",
  "model": "llama-3.1-8b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Kubernetes is an open-source container orchestration platform..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 87,
    "total_tokens": 115
  },
  "system_fingerprint": "eco-vllm-1.0"
}
```

**Response 200 (streaming):** Server-Sent Events with `Content-Type: text/event-stream`:

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"Kubernetes"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":" is"},"finish_reason":null}]}

data: [DONE]
```

### POST /v1/completions

Legacy text completion endpoint.

**Request:**

```json
{
  "model": "llama-3.1-8b-instruct",
  "prompt": "The capital of France is",
  "max_tokens": 50,
  "temperature": 0.3
}
```

**Response 200:**

```json
{
  "id": "cmpl-abc123def456",
  "object": "text_completion",
  "model": "llama-3.1-8b-instruct",
  "choices": [
    {
      "text": " Paris, which is also the largest city in France...",
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 42,
    "total_tokens": 49
  }
}
```

### POST /v1/embeddings

Generate vector embeddings in OpenAI format.

**Request:**

```json
{
  "input": "Kubernetes pod scheduling",
  "model": "quantum-bert-xxl-v1",
  "dimensions": 1024
}
```

**Response 200:**

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0123, -0.0456, 0.0789, ...],
      "index": 0
    }
  ],
  "model": "quantum-bert-xxl-v1",
  "usage": {
    "prompt_tokens": 4,
    "total_tokens": 4
  }
}
```

### GET /v1/models

List all available models from the registry with engine availability.

**Response 200:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama-3.1-8b-instruct",
      "object": "model",
      "owned_by": "indestructibleeco",
      "capabilities": ["chat", "completion"],
      "compatible_engines": ["vllm", "tgi", "ollama", "sglang"],
      "context_length": 131072
    },
    {
      "id": "quantum-bert-xxl-v1",
      "object": "model",
      "owned_by": "indestructibleeco",
      "capabilities": ["embedding"],
      "compatible_engines": ["vllm"],
      "context_length": 8192
    }
  ]
}
```

---

## AI Service Endpoints (Legacy)

These endpoints are served by the AI service and provide the original IndestructibleEco API format. They remain available for backward compatibility.

### POST /generate

Generate text from a prompt using the engine manager with automatic failover.

**Request:**

```json
{
  "prompt": "Write a haiku about cloud computing",
  "model_id": "llama-3.1-8b-instruct",
  "max_tokens": 100,
  "temperature": 0.8,
  "top_p": 0.9
}
```

**Response 200:**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Servers in the sky\nData flows like morning mist\nScalable and free",
  "model_id": "llama-3.1-8b-instruct",
  "engine": "vllm",
  "uri": "indestructibleeco://ai/generation/550e8400-e29b-41d4-a716-446655440000",
  "urn": "urn:indestructibleeco:ai:generation:550e8400-e29b-41d4-a716-446655440000",
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 18,
    "total_tokens": 26
  },
  "finish_reason": "stop",
  "latency_ms": 245.3,
  "created_at": "2026-02-20T10:00:00.000000+00:00"
}
```

### POST /vector/align

Compute vector alignment for a set of tokens using the configured alignment model.

**Request:**

```json
{
  "tokens": ["kubernetes", "deployment", "scaling"],
  "target_dim": 1024,
  "alignment_model": "quantum-bert-xxl-v1",
  "tolerance": 0.001
}
```

**Response 200:**

```json
{
  "coherence_vector": [0.0123, -0.0456, ...],
  "dimension": 1024,
  "alignment_model": "quantum-bert-xxl-v1",
  "alignment_score": 0.9847,
  "function_keywords": ["kubernetes", "deployment", "scaling"],
  "uri": "indestructibleeco://ai/vector/align/550e8400",
  "urn": "urn:indestructibleeco:ai:vector:align:550e8400"
}
```

### POST /embeddings

Generate embeddings in the IndestructibleEco native format.

**Request:**

```json
{
  "input": "cloud-native architecture patterns",
  "model": "quantum-bert-xxl-v1",
  "dimensions": 1024
}
```

### POST /embeddings/similarity

Compute cosine similarity between two texts.

**Request:**

```json
{
  "text_a": "Kubernetes pod scheduling",
  "text_b": "Container orchestration placement",
  "model": "quantum-bert-xxl-v1"
}
```

**Response 200:**

```json
{
  "cosine_similarity": 0.8923,
  "euclidean_distance": 0.4631
}
```

---

## Async Job Management

Submit long-running inference tasks as async jobs. Jobs are persisted to Supabase and status updates are pushed via WebSocket.

### POST /jobs (AI Service) or POST /api/v1/ai/generate (API Gateway)

Submit an async inference job.

**Request (AI Service):**

```json
{
  "prompt": "Write a comprehensive guide to microservices",
  "model_id": "llama-3.1-70b-instruct",
  "max_tokens": 4096,
  "priority": "high"
}
```

**Response 202:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### GET /jobs

List jobs. Supports filtering by status.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | (all) | Filter: `pending`, `running`, `completed`, `failed`, `cancelled` |
| `limit` | integer | 100 | Maximum results |

**Response 200:**

```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "model_id": "llama-3.1-70b-instruct",
      "created_at": "2026-02-20T10:00:00.000Z",
      "completed_at": "2026-02-20T10:00:12.345Z",
      "latency_ms": 12345
    }
  ],
  "total": 1
}
```

### GET /jobs/:id

Get detailed status of a specific job.

### DELETE /jobs/:id

Cancel a pending or running job.

**Response 200:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled"
}
```

---

## Platform Management

CRUD operations for platform entities. Backed by Supabase. Admin-only for write operations.

### GET /api/v1/platforms

List all registered platforms.

**Response 200:**

```json
{
  "platforms": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Web Dashboard",
      "slug": "web-dashboard",
      "type": "web",
      "status": "active",
      "capabilities": ["chat", "models", "yaml-studio"],
      "k8s_namespace": "indestructibleeco",
      "urn": "urn:indestructibleeco:platform:module:web-dashboard:550e8400"
    }
  ],
  "total": 1
}
```

### POST /api/v1/platforms

Register a new platform (admin only).

**Request:**

```json
{
  "name": "Mobile App",
  "slug": "mobile-app",
  "type": "mobile",
  "capabilities": ["chat"],
  "deploy_target": "app-store"
}
```

**Response 201:**

```json
{
  "platform": {
    "id": "...",
    "name": "Mobile App",
    "slug": "mobile-app",
    "status": "active",
    "urn": "urn:indestructibleeco:platform:module:mobile-app:..."
  }
}
```

### GET /api/v1/platforms/:id

Get a single platform by ID or slug.

### PUT /api/v1/platforms/:id

Update platform configuration (admin only).

### DELETE /api/v1/platforms/:id

Delete a platform (admin only).

---

## YAML Governance Endpoints

Generate and validate .qyaml governance manifests.

### POST /api/v1/yaml/generate

Generate a .qyaml manifest with all four governance blocks.

**Request:**

```json
{
  "module": {
    "name": "eco-payment-service",
    "ports": [8080],
    "depends_on": ["eco-auth-service", "eco-db"]
  },
  "target": "k8s"
}
```

**Response 200:**

```json
{
  "qyaml_content": "...",
  "valid": true,
  "warnings": [],
  "source": "ai-service"
}
```

### POST /api/v1/yaml/validate

Validate a .qyaml manifest for governance compliance.

**Request:**

```json
{
  "content": "{ &quot;document_metadata&quot;: { ... }, &quot;governance_info&quot;: { ... }, ... }"
}
```

**Response 200:**

```json
{
  "valid": true,
  "missing_blocks": [],
  "missing_fields": [],
  "source": "ai-service"
}
```

**Response 200 (invalid):**

```json
{
  "valid": false,
  "missing_blocks": ["vector_alignment_map"],
  "missing_fields": ["document_metadata.schema_version"],
  "source": "local-fallback"
}
```

### POST /api/v1/qyaml/descriptor

Generate a governance descriptor for a service.

**Request:**

```json
{
  "service_name": "eco-ai-service",
  "namespace": "indestructibleeco",
  "kind": "Deployment"
}
```

---

## IM Webhook Endpoints

Receive normalized webhook payloads from the Cloudflare edge worker. These are internal endpoints used by the IM channel adapters.

### POST /api/v1/im/webhook

Receive a normalized IM webhook payload.

**Request (from edge worker):**

```json
{
  "channel": "telegram",
  "sender_id": "123456789",
  "message": "Hello from Telegram",
  "timestamp": "2026-02-20T10:00:00.000Z",
  "metadata": {
    "chat_id": "-100123456789",
    "message_id": 42
  }
}
```

---

## WebSocket API

The API gateway exposes a Socket.IO endpoint at `/ws` for real-time updates.

**Connection:**

```javascript
import { io } from "socket.io-client";

const socket = io("http://localhost:3000", {
  path: "/ws",
  auth: { token: "Bearer eyJhbGciOiJIUzI1NiIs..." }
});
```

**Events:**

| Event | Direction | Description |
|-------|-----------|-------------|
| `job:status` | Server -> Client | Job status update (pending/running/completed/failed) |
| `job:result` | Server -> Client | Job completion with result payload |
| `engine:health` | Server -> Client | Engine health status change |
| `model:update` | Server -> Client | Model registry change |

---

## Error Response Format

All endpoints return errors in a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": {},
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Standard Error Codes:**

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `validation_error` | Invalid request body or parameters |
| 401 | `auth_error` | Missing or invalid authentication |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Resource does not exist |
| 409 | `conflict` | Resource already exists |
| 422 | `unprocessable_entity` | Request understood but cannot be processed |
| 429 | `rate_limited` | Rate limit exceeded |
| 500 | `internal_error` | Unexpected server error |
| 502 | `upstream_error` | Backend service returned an error |
| 503 | `service_unavailable` | Service temporarily unavailable |
| 504 | `gateway_timeout` | Backend service did not respond in time |

---

## OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available at [`backend/api/openapi.yaml`](../backend/api/openapi.yaml) (723 lines). It includes all endpoint definitions, request/response schemas, and component definitions.

Import into Swagger UI, Postman, or any OpenAPI-compatible tool:

```bash
# Serve OpenAPI spec locally
npx @redocly/cli preview-docs backend/api/openapi.yaml

# Validate spec
npx @redocly/cli lint backend/api/openapi.yaml
```

---

## SDK & Client Libraries

### TypeScript/JavaScript

The `@indestructibleeco/api-client` package provides a typed HTTP client with retry and interceptors:

```typescript
import { EcoClient } from "@indestructibleeco/api-client";

const client = new EcoClient({
  baseUrl: "http://localhost:3000",
  token: "sk-eco-...",
  retries: 2,
  timeout: 30000,
});

const response = await client.chat({
  model: "llama-3.1-8b-instruct",
  messages: [{ role: "user", content: "Hello" }],
});
```

### WebSocket Client

```typescript
import { EcoWebSocket } from "@indestructibleeco/api-client/ws";

const ws = new EcoWebSocket("ws://localhost:3000/ws", {
  token: "sk-eco-...",
  reconnect: true,
  heartbeatInterval: 30000,
});

ws.on("job:status", (data) => console.log("Job update:", data));
```

### Python

Use `httpx` directly against the OpenAI-compatible endpoints:

```python
import httpx

client = httpx.AsyncClient(
    base_url="http://localhost:8001",
    headers={"Authorization": "Bearer sk-eco-..."},
    timeout=30.0,
)

response = await client.post("/v1/chat/completions", json={
    "model": "llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
})
```

---

## gRPC API

The AI service exposes a gRPC endpoint on port 8000 for high-performance internal communication.

**Services:**

| RPC | Request | Response | Description |
|-----|---------|----------|-------------|
| `GenerateCompletion` | `GenerateRequest` | `GenerateResponse` | Unary completion |
| `StreamCompletion` | `GenerateRequest` | `stream GenerateResponse` | Server-streaming completion |
| `GenerateEmbedding` | `EmbeddingRequest` | `EmbeddingResponse` | Vector embedding |
| `HealthCheck` | `HealthRequest` | `HealthResponse` | Service health |

Proto stubs are available at `backend/shared/proto/generated/`.

---

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Environment Variables Reference](ENV_REFERENCE.md)
- [.qyaml Governance Specification](QYAML_GOVERNANCE.md)
