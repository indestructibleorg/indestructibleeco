# IndestructibleEco API Reference

URI: indestructibleeco://docs/API

## Base URL

- Development: `http://localhost:8001`
- Staging: `https://staging.indestructibleeco.io`
- Production: `https://api.indestructibleeco.io`

## Authentication

All endpoints (except `/health` and `/metrics`) require Bearer token:

```
Authorization: Bearer sk-eco-<token>
```

## Endpoints

### Health & Monitoring

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/health/worker` | Worker health |
| GET | `/health/grpc` | gRPC server health |
| GET | `/health/embedding` | Embedding service health |
| GET | `/health/registry` | Model registry health |
| GET | `/health/monitor` | Health monitor status |

### OpenAI-Compatible

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | Chat completion (streaming supported) |
| POST | `/v1/completions` | Legacy text completion |
| POST | `/v1/embeddings` | Generate embeddings |
| GET | `/v1/models` | List available models |

### AI Service

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate text |
| POST | `/embeddings` | Batch embeddings |
| POST | `/embeddings/similarity` | Compute similarity |
| POST | `/vector/align` | Vector alignment |

### Job Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/jobs` | Submit async job |
| GET | `/jobs` | List jobs |
| GET | `/jobs/:id` | Get job status |
| DELETE | `/jobs/:id` | Cancel job |

### YAML Governance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/yaml/generate` | Generate .qyaml |
| POST | `/yaml/validate` | Validate .qyaml |
| GET | `/yaml/descriptor` | Get governance descriptor |

### Platforms

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/platforms` | List platforms |
| POST | `/api/v1/platforms` | Create platform |
| GET | `/api/v1/platforms/:id` | Get platform |
| PUT | `/api/v1/platforms/:id` | Update platform |
| DELETE | `/api/v1/platforms/:id` | Delete platform |

## Error Responses

```json
{
  "error": "string",
  "code": "ERROR_CODE",
  "details": {},
  "request_id": "uuid"
}
```

## Rate Limiting

- Default: 100 requests/minute per API key
- Configurable per key via `rate_limit_per_minute`
- Returns `429 Too Many Requests` when exceeded
