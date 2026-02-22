# Contributing to IndestructibleEco

## Getting Started

```bash
# Clone the repository
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Install Python dependencies
pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy

# Run all tests (448 tests)
PYTHONPATH=. pytest tests/ -v

# Run skill tests (70 tests)
pytest tools/skill-creator/skills/ -v

# Run CI validator
python3 tools/ci-validator/validate.py
```

## Development Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout -b feat/my-feature develop
   ```

2. Make changes following the conventions documented in the [Developer Guide](docs/DEVELOPER_GUIDE.md).

3. Run all tests locally:
   ```bash
   PYTHONPATH=. pytest tests/ -v
   ```

4. Run CI validator:
   ```bash
   python3 tools/ci-validator/validate.py
   ```

5. Push and open a PR against `develop`:
   ```bash
   git push origin feat/my-feature
   ```

6. If you want Codacy Production bot AI context review directly in GitHub, add the `codacy-review` label to your PR.

## Code Conventions

### Python (backend/ai, src/)

- Python 3.11+ with type hints
- Pydantic v2 for all schemas
- All IDs use UUID v1 (`uuid.uuid1()`)
- All resources have `uri` + `urn` fields
- Environment variables use `ECO_*` prefix
- Module docstrings include URI: `indestructibleeco://module/path`

### TypeScript (backend/api, packages/, platforms/)

- TypeScript strict mode
- Express for API service
- React + Vite for web frontend
- pnpm workspaces for package management

### .qyaml Governance

Every `.qyaml` manifest must contain 4 governance blocks:

1. `document_metadata` -- unique_id (UUID v1), uri, urn, schema_version
2. `governance_info` -- owner, compliance_tags, lifecycle_policy
3. `registry_binding` -- service_endpoint, health_check_path
4. `vector_alignment_map` -- alignment_model, coherence_vector_dim

See [.qyaml Governance Specification](docs/QYAML_GOVERNANCE.md) for details.

### Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Container names | `eco-*` | `eco-ai-service` |
| Image registry | `ghcr.io/indestructibleorg/*` | `ghcr.io/indestructibleorg/ai:1.0.0` |
| Namespace | `indestructibleeco` | |
| Config prefix | `ECO_*` | `ECO_AI_HTTP_PORT` |

## Testing

```bash
# Core tests (Python)
PYTHONPATH=. pytest tests/ -v

# Skill tests
pytest tools/skill-creator/skills/ -v

# CI validator
python3 tools/ci-validator/validate.py

# YAML validation
node tools/yaml-toolkit/bin/cli.js validate k8s/base/*.qyaml
```

When adding a new test file, add it to the CI build gate structure check in `.github/workflows/ci.yaml`.

## CI/CD Pipeline

5-gate pipeline (all must pass):

1. **validate** -- CI Validator Engine (8 validators)
2. **lint** -- Python compile + JS syntax + YAML governance + skill validation
3. **test** -- Core tests (448) + skill tests (70)
4. **build** -- Docker build + structure verification
5. **auto-fix** -- Diagnostic mode on failure

## Commit Messages

Format: `type: description`

| Type | Description |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `test:` | Tests |
| `refactor:` | Code refactoring |
| `ci:` | CI/CD changes |
| `chore:` | Maintenance |

## Security

- Never commit secrets or API keys
- Use `ECO_*` environment variables for all configuration
- Report vulnerabilities via [GitHub Security Advisories](https://github.com/indestructibleorg/indestructibleeco/security/advisories/new)
- See [SECURITY.md](SECURITY.md) for details

## Documentation

When making changes, update relevant documentation:

- [API Reference](docs/API.md) -- endpoint changes
- [Architecture](docs/ARCHITECTURE.md) -- structural changes
- [Deployment Guide](docs/DEPLOYMENT.md) -- deployment changes
- [Developer Guide](docs/DEVELOPER_GUIDE.md) -- workflow changes
- [Environment Variables](docs/ENV_REFERENCE.md) -- new ECO_* variables
- [.qyaml Governance](docs/QYAML_GOVERNANCE.md) -- governance changes

## License

Apache-2.0. By contributing, you agree that your contributions will be licensed under the same license.
