# AGENTS.md

## Cursor Cloud-specific instructions

### Overview

eco-base is an enterprise cloud-native AI inference platform monorepo with Python (FastAPI) backend services and TypeScript (Express/React) frontend packages managed via pnpm workspaces.

### Running services

- **Root FastAPI gateway** (port 8000): `PYTHONPATH=. python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload`
  - Provides `/health`, `/metrics`, `/v1/models`, `/v1/chat/completions` endpoints
  - Falls back to simulated inference when the upstream AI proxy/service is unreachable or returns an error
  - Authenticate via JWT: generate a token with `python3 -c "import sys; sys.path.insert(0,'.'); from src.middleware.auth import AuthMiddleware; print(AuthMiddleware().create_jwt_token('dev-user','developer'))"` (for local development only; do not reuse this approach or token in production)

### Testing

- **Root Python tests**: `PYTHONPATH=. pytest tests/ -v` (may report pre-existing failures related to missing web frontend source files)
- **CI validator**: `python3 tools/ci-validator/validate.py` (may report validation errors for some workflow files)
- **Platform-specific tests** (run from each platform directory):
  - `cd platforms/eco-govops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (runs unit tests for eco-govops; integration and e2e tests are excluded)
  - `cd platforms/eco-core && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (runs unit tests for eco-core; integration and e2e tests are excluded)
  - `cd platforms/eco-observops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (runs unit tests for eco-observops; integration and e2e tests are excluded)
  - `cd platforms/eco-seccompops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (runs unit tests for eco-seccompops; integration and e2e tests are excluded)
  - `cd platforms/eco-dataops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (runs unit tests for eco-dataops; integration and e2e tests are excluded)
  - `cd platforms/eco-superai && python3 -m pytest tests/unit/ -q` (many tests passing; some pre-existing failures needing optional deps like celery, openai, chromadb)

### Linting

- **Python**: `ruff check src/ backend/ai/` (pre-existing style warnings; config in `pyproject.toml`)
- **TypeScript**: `ESLINT_USE_FLAT_CONFIG=false npx eslint packages/ backend/api/src/ --ext .ts,.tsx` (repo uses `.eslintrc.json`; ESLint v9 requires `ESLINT_USE_FLAT_CONFIG=false` flag)

### Gotchas

- `pip install -e ".[dev]"` may fail because editable installs via `hatchling` are not fully configured for this monorepo layout. Prefer installing dependencies via the project’s packaging metadata (e.g., using the appropriate extras defined in `pyproject.toml` under `[project.optional-dependencies]` such as `dev`, or the relevant `requirements*.txt` file) instead of relying on an editable install with a hardcoded dependency list.
- The web frontend (`platforms/web/`) is scaffolding only — no React source files exist under `app/src/`. Tests referencing those paths (test_web_frontend.py, test_yaml_studio.py) fail.
- pnpm workspaces are configured via the `"workspaces"` field in the root `package.json` (there is no `pnpm-workspace.yaml` in this repo). pnpm may warn that it prefers `pnpm-workspace.yaml`, but `pnpm install` still succeeds and the warning can be safely ignored.
- `$HOME/.local/bin` must be on `PATH` for ruff, mypy, and other pip-installed scripts.

### Deployment (Third-Party Platforms)

Five platform deploy workflows exist in `.github/workflows/`:
- **GitHub CI/CD**: 27 workflows total; `release.yml` + `publish-{npm,docker,pypi}.yml` handle releases
- **Supabase**: `supabase-deploy.yml` runs migrations and deploys 4 edge functions. Seed data in `supabase/seed.sql`
- **Vercel**: `vercel-deploy.yml` deploys `platforms/web/` (static landing page) with preview on PRs. Config: `platforms/web/vercel.json`
- **GKE**: `gke-deploy.yml` does Helm deploy to staging/production. Argo CD apps in `k8s/argocd/`. Helm chart in `helm/`
- **Cloudflare**: `cloudflare-deploy.yml` deploys webhook router Worker. Config: `backend/cloudflare/wrangler.toml`

All deploy workflows require secrets configured in GitHub repository settings. See each workflow file for required secret names.

### Capability modules system

The repo uses a pluggable capability-based deployment model:
- `capabilities.yaml` — feature flags for modules (vercel, cloudflare, supabase, keycloak, n8n)
- `secrets.required.yaml` — per-module required secrets
- `scripts/capabilities.py` — parses flags, outputs enabled modules JSON
- `scripts/preflight_secrets.sh` — CD pre-gate that fails fast on missing secrets
- `.github/workflows/deploy.yml` — CD workflow with per-module jobs gated by capabilities + preflight

To check which modules are enabled: `python3 scripts/capabilities.py capabilities.yaml`
To validate secrets: `bash scripts/preflight_secrets.sh artifacts/_tmp/capabilities.enabled.json secrets.required.yaml`

### AutoOps enforced workflow

- `scripts/autoops/run.py` — Stage 0→1→Core execution engine producing `artifacts/_internal/*`
- `scripts/autoops/guards.sh` — hard-fail guards (manifest, secrets, write scope)
- `.github/workflows/autoops.yml` — triggers: ChatOps (`/autoops run`), CI-failure, manual
- Spec: `docs/prompt-workflow.enforced.md`

### Repo guards

- `scripts/root_guard.sh` — top-level directory whitelist enforcement (`infra/root-guard/allowed-roots.txt`)
- `scripts/import_guard.sh` — cross-domain import boundary (apps↔ops↔infra)
- `.github/workflows/guards.yml` — runs both guards on PR/push
