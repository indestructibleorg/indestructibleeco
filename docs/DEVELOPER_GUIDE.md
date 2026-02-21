# IndestructibleEco Developer Guide

URI: indestructibleeco://docs/DEVELOPER_GUIDE

## Repository Structure

```
indestructibleeco/
├── src/                          # Root gateway (FastAPI)
│   ├── app.py                    # Application factory + proxy routing (359 LOC)
│   ├── schemas/                  # Pydantic v2 schemas (auth, inference, models)
│   ├── core/                     # Registry (213 LOC) + Queue (145 LOC)
│   └── middleware/               # Auth middleware (172 LOC)
├── backend/
│   ├── ai/                       # AI inference service (FastAPI)
│   │   ├── src/
│   │   │   ├── app.py            # FastAPI entry + engine lifecycle (351 LOC)
│   │   │   ├── config.py         # ECO_* env config (all engines + indexes)
│   │   │   ├── routes.py         # REST + OpenAI-compatible endpoints (759 LOC)
│   │   │   ├── governance.py     # YAML-parse governance engine + audit (400 LOC)
│   │   │   └── services/         # engine_manager, circuit_breaker, connection_pool,
│   │   │                         # worker, grpc_server, embedding, health_monitor
│   │   └── engines/
│   │       ├── inference/        # 7 adapters + resilience layer + base + router
│   │       ├── compute/          # similarity, ranking, clustering, reasoning
│   │       ├── folding/          # vector, graph, hybrid, realtime (WAL)
│   │       └── index/            # FAISS, Elasticsearch, Neo4j, hybrid router
│   ├── api/                      # API gateway (Express/TypeScript)
│   │   └── src/
│   │       ├── server.ts         # Express entry + Socket.IO
│   │       ├── config.ts         # ECO_* env config
│   │       ├── types.ts          # Shared TypeScript types
│   │       ├── routes/           # auth, platforms, ai, yaml, health, im-webhook
│   │       ├── services/         # supabase, ai-proxy, job-poller
│   │       ├── middleware/       # auth, rate-limiter, error-handler
│   │       └── ws/               # WebSocket handler
│   ├── shared/
│   │   ├── db/                   # Supabase client wrapper
│   │   ├── proto/generated/      # gRPC stubs (dataclass-based)
│   │   ├── models/               # Shared data models
│   │   └── utils/                # Shared utilities
│   ├── cloudflare/               # Edge webhook router
│   └── k8s/                      # Backend K8s manifests
├── packages/
│   ├── shared-types/             # TypeScript shared types (entities + API)
│   ├── api-client/               # Typed HTTP client (retry + interceptors + WS)
│   └── ui-kit/                   # React components (Modal, Dropdown, Table, Toast)
├── platforms/
│   ├── web/                      # React + Vite (6 pages, dark theme)
│   ├── desktop/                  # Electron app
│   └── im-integration/           # 4 channel adapters + shared normalizer
├── ecosystem/
│   ├── monitoring/               # Grafana dashboards + Prometheus alerts
│   ├── tracing/                  # Distributed tracing
│   ├── logging/                  # Centralized logging
│   └── service-discovery/        # Service mesh
├── supabase/                     # Shared Supabase migrations + RLS policies
├── k8s/                          # Platform K8s manifests + Argo CD
├── helm/                         # Helm chart (12 templates)
├── tools/
│   ├── ci-validator/             # 8-validator CI engine
│   ├── yaml-toolkit/             # .qyaml generator + validator
│   └── skill-creator/            # Skill scaffolding (70 tests)
├── policy/                       # OPA governance policies
├── docs/                         # Documentation
└── tests/                        # 448 tests (unit, integration, e2e)
```

## Development Workflow

### External Platform Onboarding (安全導入原則)

Current repository structure does **not** support silently or forcibly registering an external platform by illegal/implicit operations. New platform integration must be explicit and reviewable in Git:

1. Add platform code under a clear ownership path (usually `platforms/<platform-name>/`).
2. Add dependency/mapping/reference changes explicitly (API routes, manifests, env/config, CI paths).
3. Pass repository validation (`npm run validate`) and related tests before merge.

This keeps imports auditable and prevents hidden cross-platform coupling.

### Platform Pollution Isolation

If an imported external platform is chaotic/polluted, handle it with a **policy-enforced quarantine flow**, not unreviewed force operations (such as bypassing PR review, force-pushing direct rewrites, or bulk cross-tree edits without scoped ownership):

1. Place incoming platform code in an isolated path (for example `platforms/my-new-platform/` only).
2. Block cross-tree coupling until validation passes (no direct edits outside approved paths).
3. Run `npm run validate` plus related tests, then fix mappings/dependencies/references in explicit commits.
4. Merge only when structure and governance checks are clean and review-approved.

This gives you an enforced cleanup result through CI policy gates and code review, while remaining legal, auditable, and reversible.

### 1. Branch Strategy

- `main` - Production branch. Protected. Argo CD production tracks this.
- `develop` - Integration branch. Argo CD staging tracks this.
- Feature branches: `feat/description`, `fix/description`, `docs/description`

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feat/my-feature develop

# Make changes
# ... edit files ...

# Run tests locally
PYTHONPATH=. pytest tests/ -v

# Run CI validator
python3 tools/ci-validator/validate.py

# Commit with conventional format
git commit -m "feat: add new inference endpoint"

# Push and create PR
git push origin feat/my-feature
```

### 3. Commit Message Format

```
type: description

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation
  test:     Tests
  refactor: Code refactoring
  ci:       CI/CD changes
  chore:    Maintenance
```

### 4. Adding a New Test File

When adding a new test file, you must also add it to the CI build gate structure check in `.github/workflows/ci.yaml`:

```yaml
# In the build job, structure verification section:
test -f tests/unit/test_your_new_test.py
```

## Code Conventions

### Python (backend/ai, src/)

- Python 3.11+ with type hints on all public functions
- Pydantic v2 for all request/response schemas
- All identifiers use UUID v1 (`uuid.uuid1()`)
- All resources have `uri` + `urn` fields:
  - URI: `indestructibleeco://service/resource/id`
  - URN: `urn:indestructibleeco:service:resource:id`
- Environment variables use `ECO_*` prefix
- Module docstrings include URI: `indestructibleeco://module/path`
- Logging via `logging.getLogger(__name__)`
- Async functions for all I/O operations

### TypeScript (backend/api, packages/, platforms/)

- TypeScript strict mode
- Express for API service
- React + Vite for web frontend
- pnpm workspaces for package management
- Pino for structured logging
- All routes use `express-async-errors` for error propagation

### .qyaml Governance

Every `.qyaml` manifest must contain 4 governance blocks. See [.qyaml Governance Specification](QYAML_GOVERNANCE.md).

### Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Container names | `eco-*` | `eco-ai-service` |
| Image registry | `ghcr.io/indestructibleorg/*` | `ghcr.io/indestructibleorg/ai:1.0.0` |
| Namespace | `indestructibleeco` | `indestructibleeco`, `indestructibleeco-staging` |
| Config prefix | `ECO_*` | `ECO_AI_HTTP_PORT` |
| URI scheme | `indestructibleeco://` | `indestructibleeco://backend/ai/health` |
| URN namespace | `urn:indestructibleeco:` | `urn:indestructibleeco:ai:job:uuid` |

## Adding a New Inference Engine

1. Create adapter in `backend/ai/engines/inference/adapters/`:

```python
from ..base import BaseInferenceAdapter, EngineType, InferenceRequest, InferenceResponse

class MyEngineAdapter(BaseInferenceAdapter):
    def __init__(self, endpoint: str, **kwargs):
        super().__init__(EngineType.MY_ENGINE, endpoint, **kwargs)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        # Implement engine-specific generation
        ...

    async def stream(self, request: InferenceRequest):
        # Implement streaming
        ...

    async def health_check(self):
        # Implement health check
        ...

    async def list_models(self):
        # Implement model listing
        ...
```

2. Register in `backend/ai/engines/inference/adapters/__init__.py`
3. Add endpoint config in `backend/ai/src/config.py` (`ECO_MYENGINE_URL`)
4. Add to `EngineManager` in `backend/ai/src/services/engine_manager.py`
5. Add model mapping in `MODEL_ENGINE_MAP`
6. Add Kubernetes manifest in `k8s/base/myengine-engine.qyaml`
7. Add Helm values in `helm/values.yaml`
8. Add tests in `tests/unit/`
9. Update `docs/ARCHITECTURE.md` engine table

## Testing

### Test Organization

```
tests/
├── unit/                    # 30+ test files, isolated unit tests
│   ├── test_auth.py         # AuthMiddleware tests
│   ├── test_registry.py     # ModelRegistry tests
│   ├── test_schemas.py      # Pydantic schema tests
│   ├── test_worker.py       # InferenceWorker tests (18 tests)
│   ├── test_grpc_server.py  # gRPC server tests (16 tests)
│   ├── test_embedding.py    # EmbeddingService tests (23 tests)
│   ├── test_health_monitor.py # HealthMonitor tests (14 tests)
│   ├── test_governance_engine.py # GovernanceEngine tests (30 tests)
│   └── ...
├── integration/
│   └── test_api.py          # API integration tests
└── e2e/
    ├── test_full_flow.py    # Full flow E2E tests (12 tests)
    └── test_service_lifecycle.py # Service lifecycle E2E (59 tests)
```

### Running Tests

```bash
# All tests
PYTHONPATH=. pytest tests/ -v

# Specific test file
PYTHONPATH=. pytest tests/unit/test_worker.py -v

# With coverage
PYTHONPATH=. pytest tests/ --cov=src --cov=backend --cov-report=html

# Skill tests
pytest tools/skill-creator/skills/ -v
```

### Writing Tests

- Use `pytest` with `pytest-asyncio` for async tests
- Mock external services (engines, Supabase, Redis)
- Each test file should be self-contained with its own fixtures
- Test file naming: `test_<module_name>.py`
- Minimum: test happy path, error cases, edge cases

## Related Documentation

- [API Reference](API.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Environment Variables Reference](ENV_REFERENCE.md)
- [.qyaml Governance Specification](QYAML_GOVERNANCE.md)
