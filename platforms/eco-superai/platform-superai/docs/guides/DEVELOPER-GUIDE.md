# SuperAI Platform — Developer Guide

> Getting started with development, testing, and contributing.

---

## 1. Development Environment Setup

### 1.1 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Local service orchestration |
| Make | 4.0+ | Command shortcuts |
| Git | 2.40+ | Version control |

### 1.2 Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/superai-platform.git
cd superai-platform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Install pre-commit hooks
pre-commit install

# Start infrastructure services
make up
```

### 1.3 IDE Configuration

**VS Code** (recommended `.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

---

## 2. Project Structure Conventions

### 2.1 Module Organization

Each layer follows a consistent internal structure:

```
module/
├── __init__.py          # Public API exports
├── interfaces.py        # Abstract base classes (if applicable)
├── implementations.py   # Concrete implementations
├── models.py            # Data models / schemas
├── exceptions.py        # Module-specific exceptions
└── tests/               # Co-located tests (optional)
```

### 2.2 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `snake_case.py` | `quantum_executor.py` |
| Classes | `PascalCase` | `QuantumExecutor` |
| Functions | `snake_case` | `execute_circuit()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_QUBITS` |
| Private | `_leading_underscore` | `_validate_input()` |
| Type aliases | `PascalCase` | `CircuitResult` |

### 2.3 Import Order

```python
# 1. Standard library
import os
from datetime import datetime
from typing import Optional

# 2. Third-party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import numpy as np

# 3. Local application imports
from src.domain.entities.user import User
from src.shared.exceptions import DomainException
```

---

## 3. Adding New Features

### 3.1 Adding a New API Endpoint

**Step 1:** Define the domain entity (if new) in `src/domain/entities/`:

```python
# src/domain/entities/experiment.py
from src.domain.entities.base import BaseEntity

class Experiment(BaseEntity):
    name: str
    description: str
    status: str = "draft"
    
    def start(self) -> None:
        if self.status != "draft":
            raise ValueError("Can only start draft experiments")
        self.status = "running"
```

**Step 2:** Define the repository interface in `src/domain/repositories/`:

```python
# src/domain/repositories/experiment_repo.py
from abc import ABC, abstractmethod
from src.domain.entities.experiment import Experiment

class ExperimentRepository(ABC):
    @abstractmethod
    async def save(self, experiment: Experiment) -> Experiment: ...
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Experiment | None: ...
```

**Step 3:** Create the use case in `src/application/use_cases/`:

```python
# src/application/use_cases/experiment_management.py
class CreateExperiment:
    def __init__(self, repo: ExperimentRepository):
        self._repo = repo
    
    async def execute(self, name: str, description: str) -> Experiment:
        experiment = Experiment(name=name, description=description)
        return await self._repo.save(experiment)
```

**Step 4:** Add the route in `src/presentation/api/routes/`:

```python
# src/presentation/api/routes/experiments.py
from fastapi import APIRouter

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("/", status_code=201)
async def create_experiment(request: CreateExperimentRequest):
    use_case = CreateExperiment(repo=get_experiment_repo())
    result = await use_case.execute(request.name, request.description)
    return result
```

**Step 5:** Register the router in `src/presentation/api/main.py`:

```python
from src.presentation.api.routes.experiments import router as experiments_router
app.include_router(experiments_router, prefix="/api/v1")
```

### 3.2 Adding a New Quantum Algorithm

1. Create the algorithm file in `src/quantum/algorithms/`
2. Implement the `QuantumAlgorithm` interface
3. Register it in the `QuantumExecutor` backend map
4. Add unit tests in `tests/unit/quantum/`
5. Add the API route in `src/presentation/api/routes/quantum.py`

---

## 4. Testing

### 4.1 Test Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── domain/              # Entity & value object tests
│   ├── quantum/             # Quantum algorithm tests
│   ├── ai/                  # AI module tests
│   ├── application/         # Use case tests
│   └── presentation/        # Route handler tests
├── integration/             # Tests with real dependencies
├── e2e/                     # Full API flow tests
└── fixtures/                # Shared test data & factories
```

### 4.2 Writing Unit Tests

```python
# tests/unit/domain/test_experiment.py
import pytest
from src.domain.entities.experiment import Experiment

class TestExperiment:
    def test_create_experiment(self):
        exp = Experiment(name="Test", description="A test experiment")
        assert exp.name == "Test"
        assert exp.status == "draft"
    
    def test_start_experiment(self):
        exp = Experiment(name="Test", description="A test")
        exp.start()
        assert exp.status == "running"
    
    def test_cannot_start_running_experiment(self):
        exp = Experiment(name="Test", description="A test")
        exp.start()
        with pytest.raises(ValueError):
            exp.start()
```

### 4.3 Running Tests

```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-cov          # With coverage report
make test-quantum      # Quantum module only
```

---

## 5. Code Quality

### 5.1 Pre-commit Hooks

The project uses pre-commit hooks that run automatically on `git commit`:

- **ruff** — Linting and formatting
- **mypy** — Type checking
- **bandit** — Security scanning
- **detect-secrets** — Secret leak prevention

### 5.2 Manual Quality Checks

```bash
make lint          # Ruff linting
make format        # Auto-format code
make type-check    # Mypy type checking
make security      # Bandit security scan
make quality       # All checks combined
```

---

## 6. Database Migrations

### 6.1 Creating a Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add experiments table"

# Create empty migration
alembic revision -m "add custom index"
```

### 6.2 Running Migrations

```bash
make db-migrate    # Apply all pending
make db-rollback   # Rollback last one
make db-reset      # Full reset (dev only)
```

---

## 7. Docker Development

### 7.1 Building Images

```bash
make build         # Build all images
make rebuild       # Build and restart
```

### 7.2 Debugging Containers

```bash
make logs                                    # Tail all logs
docker compose exec app bash                 # Shell into app container
docker compose exec postgres psql -U superai # PostgreSQL shell
docker compose exec redis redis-cli          # Redis CLI
```

---

## 8. Git Workflow

### 8.1 Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<description>` | `feature/quantum-grover` |
| Bugfix | `fix/<description>` | `fix/vqe-convergence` |
| Hotfix | `hotfix/<description>` | `hotfix/auth-bypass` |
| Refactor | `refactor/<description>` | `refactor/clean-arch` |
| Docs | `docs/<description>` | `docs/api-reference` |

### 8.2 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(quantum): add Grover's search algorithm
fix(ai): resolve embedding dimension mismatch
docs(api): update quantum endpoint examples
refactor(domain): extract value objects from User entity
test(scientific): add matrix decomposition tests
ci: add CodeQL security scanning
```

### 8.3 Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all quality checks pass (`make quality`)
4. Open PR with description following the template
5. Address review comments
6. Squash merge into `main`