# SuperAI Platform — API Reference

> Version 1.0 | Base URL: `http://localhost:8000/api/v1`

---

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/health` | System health check | No |
| `GET` | `/health/ready` | Readiness probe (K8s) | No |
| `GET` | `/health/live` | Liveness probe (K8s) | No |

#### `GET /health`

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-02-11T08:00:00Z",
  "components": {
    "database": "connected",
    "redis": "connected",
    "quantum_runtime": "available"
  }
}
```

---

### Users

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/users` | Create a new user | No |
| `GET` | `/users` | List users (paginated) | Yes |
| `GET` | `/users/{id}` | Get user by ID | Yes |
| `PUT` | `/users/{id}` | Update user | Yes |
| `DELETE` | `/users/{id}` | Delete user | Yes (Admin) |

#### `POST /users`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecureP@ss123",
  "full_name": "John Doe",
  "role": "researcher"
}
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "researcher",
  "is_active": true,
  "created_at": "2025-02-11T08:00:00Z"
}
```

#### `GET /users`

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `size` | int | 20 | Items per page |
| `sort_by` | string | `created_at` | Sort field |
| `order` | string | `desc` | Sort order (asc/desc) |

**Response 200:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

### Quantum Computing

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/quantum/execute` | Execute quantum algorithm | Yes |
| `GET` | `/quantum/backends` | List available backends | Yes |
| `GET` | `/quantum/jobs/{id}` | Get job result | Yes |
| `POST` | `/quantum/vqe` | Run VQE optimization | Yes |
| `POST` | `/quantum/qaoa` | Run QAOA solver | Yes |
| `POST` | `/quantum/qml/classify` | Run QML classification | Yes |

#### `POST /quantum/execute`

**Request Body:**
```json
{
  "algorithm": "vqe",
  "backend": "aer_simulator",
  "parameters": {
    "num_qubits": 4,
    "depth": 3,
    "optimizer": "COBYLA",
    "max_iterations": 100
  },
  "hamiltonian": {
    "type": "molecular",
    "molecule": "H2",
    "basis_set": "sto-3g"
  }
}
```

**Response 202:**
```json
{
  "job_id": "qj-550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "algorithm": "vqe",
  "backend": "aer_simulator",
  "submitted_at": "2025-02-11T08:00:00Z",
  "estimated_duration_seconds": 30
}
```

#### `GET /quantum/jobs/{id}`

**Response 200:**
```json
{
  "job_id": "qj-550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "algorithm": "vqe",
  "result": {
    "optimal_value": -1.8572,
    "optimal_parameters": [0.5923, -0.2341, 1.0472],
    "num_iterations": 47,
    "convergence_history": [...]
  },
  "execution_time_seconds": 12.34,
  "backend": "aer_simulator",
  "completed_at": "2025-02-11T08:00:12Z"
}
```

---

### AI / ML

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/ai/expert` | Create AI expert instance | Yes |
| `POST` | `/ai/chat` | Chat with AI expert | Yes |
| `POST` | `/ai/embeddings` | Generate embeddings | Yes |
| `POST` | `/ai/vectordb/store` | Store vectors | Yes |
| `POST` | `/ai/vectordb/search` | Semantic search | Yes |
| `POST` | `/ai/agents/execute` | Execute agent task | Yes |

#### `POST /ai/expert`

**Request Body:**
```json
{
  "domain": "quantum_physics",
  "model": "gpt-4",
  "system_prompt": "You are an expert in quantum physics...",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response 201:**
```json
{
  "expert_id": "exp-550e8400",
  "domain": "quantum_physics",
  "model": "gpt-4",
  "created_at": "2025-02-11T08:00:00Z"
}
```

#### `POST /ai/vectordb/search`

**Request Body:**
```json
{
  "query": "quantum entanglement applications",
  "collection": "research_papers",
  "top_k": 10,
  "threshold": 0.75
}
```

**Response 200:**
```json
{
  "results": [
    {
      "id": "doc-001",
      "content": "Quantum entanglement has been demonstrated...",
      "score": 0.92,
      "metadata": {
        "source": "arxiv:2401.12345",
        "author": "Smith et al.",
        "year": 2024
      }
    }
  ],
  "total": 10,
  "query_time_ms": 45
}
```

---

### Scientific Computing

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/scientific/matrix/eigenvalues` | Compute eigenvalues | Yes |
| `POST` | `/scientific/matrix/svd` | Singular value decomposition | Yes |
| `POST` | `/scientific/matrix/solve` | Solve linear system | Yes |
| `POST` | `/scientific/stats/describe` | Descriptive statistics | Yes |
| `POST` | `/scientific/stats/hypothesis-test` | Hypothesis testing | Yes |
| `POST` | `/scientific/signal/fft` | Fast Fourier Transform | Yes |
| `POST` | `/scientific/optimize` | Run optimization | Yes |
| `POST` | `/scientific/ml/train` | Train ML model | Yes |
| `GET` | `/scientific/ml/models/{id}` | Get model info | Yes |

#### `POST /scientific/matrix/eigenvalues`

**Request Body:**
```json
{
  "matrix": [[4, -2], [1, 1]],
  "compute_vectors": true
}
```

**Response 200:**
```json
{
  "eigenvalues": [3.0, 2.0],
  "eigenvectors": [[0.8944, 0.4472], [0.7071, 0.7071]],
  "computation_time_ms": 2
}
```

#### `POST /scientific/ml/train`

**Request Body:**
```json
{
  "model_type": "random_forest",
  "task": "classification",
  "dataset": {
    "source": "upload",
    "format": "csv"
  },
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 10,
    "test_size": 0.2
  }
}
```

**Response 202:**
```json
{
  "model_id": "ml-550e8400",
  "status": "training",
  "model_type": "random_forest",
  "submitted_at": "2025-02-11T08:00:00Z"
}
```

---

### Admin

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/admin/metrics` | System metrics | Yes (Admin) |
| `GET` | `/admin/config` | Runtime configuration | Yes (Admin) |
| `POST` | `/admin/cache/flush` | Flush Redis cache | Yes (Admin) |
| `GET` | `/admin/audit-log` | Audit log entries | Yes (Admin) |

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "req-550e8400",
    "timestamp": "2025-02-11T08:00:00Z"
  }
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic validation failure |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Dependency unavailable |

---

## Rate Limiting

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Free | 60 | 10 |
| Standard | 300 | 50 |
| Enterprise | 3000 | 500 |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1707638460
```