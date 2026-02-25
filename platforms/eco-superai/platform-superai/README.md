# SuperAI Platform

> Production-grade Cloud-Native Platform with Quantum-AI Hybrid Capabilities

[![CI/CD](https://github.com/your-org/superai-platform/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/superai-platform/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

SuperAI Platform is an enterprise-grade, cloud-native application that integrates quantum computing algorithms, AI/ML pipelines, scientific computing modules, and vector database capabilities into a unified, production-ready system. Built on Clean Architecture (Hexagonal / Ports & Adapters) principles, it delivers a modular, testable, and horizontally scalable platform suitable for research institutions, fintech, biotech, and advanced engineering organizations.

### Key Capabilities

| Domain | Features |
|---|---|
| **Quantum Computing** | VQE, QAOA, QML algorithms via Qiskit/Cirq runtime abstraction |
| **AI / ML** | Expert factory, task executor agents, embedding generation, RAG pipelines |
| **Vector Database** | ChromaDB / Qdrant integration for semantic search and retrieval |
| **Scientific Computing** | Matrix operations, statistical analysis, signal processing, optimization |
| **Infrastructure** | Kubernetes-native, Helm charts, ArgoCD GitOps, Terraform IaC |
| **Observability** | Prometheus metrics, Grafana dashboards, structured logging (ELK-ready) |
| **Security** | RBAC, JWT/OAuth2, OWASP compliance, secret management, network policies |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│  FastAPI Routes: health │ users │ quantum │ ai │ admin   │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│  Use Cases │ DTOs │ Event Handlers │ Services            │
├─────────────────────────────────────────────────────────┤
│                     Domain Layer                         │
│  Entities │ Value Objects │ Repositories │ Specifications │
├─────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                    │
│  PostgreSQL │ Redis │ S3 │ External APIs │ Config        │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Quantum  │    AI    │Scientific│      Shared            │
│ Runtime  │ Factory  │ Analysis │  Exceptions/Utils      │
│ VQE/QAOA │ Agents   │ ML Train │  Schemas/Constants     │
│ QML      │ VectorDB │ Stats    │  Decorators/Models     │
└──────────┴──────────┴──────────┴────────────────────────┘
```

---

## Directory Structure

```
superai-platform/
├── src/                          # Application source code
│   ├── presentation/             # API layer (FastAPI)
│   │   ├── api/
│   │   │   ├── main.py           # FastAPI application entry
│   │   │   ├── routes/           # Endpoint modules
│   │   │   ├── middleware/       # Request/response middleware
│   │   │   ├── schemas/         # Pydantic request/response models
│   │   │   └── dependencies/    # Dependency injection
│   │   └── exceptions/          # Global exception handlers
│   ├── application/              # Use cases & orchestration
│   │   ├── use_cases/           # Business logic orchestrators
│   │   ├── services/            # Application services
│   │   ├── dto/                 # Data transfer objects
│   │   └── events/              # Domain event handlers
│   ├── domain/                   # Core business logic
│   │   ├── entities/            # Domain entities (User, etc.)
│   │   ├── value_objects/       # Immutable value types
│   │   ├── repositories/       # Repository interfaces (ports)
│   │   ├── specifications/     # Query specifications
│   │   ├── events/             # Domain events
│   │   └── exceptions/         # Domain-specific exceptions
│   ├── infrastructure/           # External adapters
│   │   ├── config/              # Settings & configuration
│   │   ├── persistence/         # Database (PostgreSQL, migrations)
│   │   ├── cache/               # Redis client
│   │   ├── security/           # Auth & encryption
│   │   ├── tasks/              # Background task runners
│   │   └── external/           # Third-party API clients
│   ├── quantum/                  # Quantum computing module
│   │   ├── runtime/             # Quantum backend executor
│   │   ├── algorithms/          # VQE, QAOA, QML implementations
│   │   ├── circuits/           # Circuit builders
│   │   └── hybrid/             # Classical-quantum hybrid
│   ├── ai/                       # AI/ML module
│   │   ├── factory/             # Expert AI factory
│   │   ├── agents/              # Task executor agents
│   │   ├── vectordb/            # Vector DB manager
│   │   ├── embeddings/          # Embedding generator
│   │   └── prompts/            # Prompt templates
│   ├── scientific/               # Scientific computing module
│   │   ├── analysis/            # Matrix, stats, signal, optimization
│   │   ├── ml/                  # ML trainer
│   │   └── pipelines/          # Data processing pipelines
│   └── shared/                   # Cross-cutting concerns
│       ├── exceptions/          # Base exceptions
│       ├── utils/               # Utility functions
│       ├── schemas/             # Shared schemas
│       ├── constants/           # Global constants
│       ├── models/              # Shared data models
│       └── decorators/          # Reusable decorators
├── tests/                        # Test suites
│   ├── unit/                    # Unit tests by module
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end tests
│   └── fixtures/                # Test fixtures & factories
├── docs/                         # Documentation
│   ├── architecture/            # Architecture design docs
│   ├── api/                     # API reference (OpenAPI)
│   ├── guides/                  # Developer guides
│   ├── adr/                     # Architecture Decision Records
│   └── runbooks/                # Operations runbooks
├── infrastructure/               # IaC & deployment configs
│   ├── terraform/               # Terraform modules & envs
│   ├── docker/                  # Docker build configs
│   └── scripts/                 # DB init & migration scripts
├── k8s/                          # Kubernetes manifests
│   ├── base/                    # Base deployment & service
│   └── overlays/                # Kustomize per-env overlays
├── helm/                         # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── charts/                  # Sub-chart dependencies
│   └── templates/               # K8s resource templates
├── argocd/                       # ArgoCD GitOps application
├── monitoring/                   # Observability stack
│   └── prometheus/              # Prometheus config & alerts
│   └── grafana/                 # Grafana dashboards & provisioning
├── logging/                      # Logging configuration
├── security/                     # Security policies
├── tools/                        # Developer utilities
├── pyproject.toml                # Project metadata & dependencies
├── Dockerfile.prod               # Production Docker image
├── docker-compose.yml            # Local development stack
├── Makefile                      # Developer command shortcuts
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
└── CHANGELOG.md                  # Release changelog
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Make (optional but recommended)

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/superai-platform.git
cd superai-platform
cp .env.example .env
```

### 2. Start with Docker Compose

```bash
make up
# or directly:
docker compose up -d
```

### 3. Start Development Server

```bash
make dev
# or:
pip install -e ".[dev]"
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Tests

```bash
make test          # all tests
make test-unit     # unit tests only
make test-cov      # with coverage report
```

### 5. Access Services

| Service | URL |
|---|---|
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Redis Commander | http://localhost:8081 |

---

## Development

### Code Quality

```bash
make lint          # ruff linting
make format        # ruff formatting
make type-check    # mypy type checking
make security      # bandit security scan
```

### Database Migrations

```bash
make db-migrate    # run pending migrations
make db-rollback   # rollback last migration
make db-seed       # seed development data
```

### Quantum Module

```bash
# Run VQE optimization
python -m src.quantum.algorithms.vqe

# Run QAOA solver
python -m src.quantum.algorithms.qaoa

# Run QML classifier
python -m src.quantum.algorithms.qml
```

---

## Deployment

### Kubernetes (via Helm)

```bash
helm install superai ./helm \
  --namespace superai \
  --create-namespace \
  -f helm/values.yaml
```

### ArgoCD (GitOps)

```bash
kubectl apply -f argocd/application.yaml
```

### Terraform (Infrastructure)

```bash
cd infrastructure/terraform/environments/prod
terraform init
terraform plan
terraform apply
```

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the complete list.

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Application name | `superai-platform` |
| `APP_ENV` | Environment (dev/staging/prod) | `development` |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `QUANTUM_BACKEND` | Quantum simulator backend | `aer_simulator` |
| `OPENAI_API_KEY` | OpenAI API key for AI module | — |
| `VECTOR_DB_TYPE` | Vector DB type (chroma/qdrant) | `chroma` |
| `JWT_SECRET_KEY` | JWT signing secret | — |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Contributing

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

## License

This project is licensed under the MIT License — see the [LICENSE](../license) file for details.