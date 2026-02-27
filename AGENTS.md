# AGENTS.md

## Cursor Cloud specific instructions

### Overview

eco-base is an enterprise cloud-native AI inference platform monorepo with Python (FastAPI) backend services and TypeScript (Express/React) frontend packages managed via pnpm workspaces.

### Running services

- **Root FastAPI gateway** (port 8000): `PYTHONPATH=. python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload`
  - Provides `/health`, `/metrics`, `/v1/models`, `/v1/chat/completions` endpoints
  - Falls back to simulated inference when no GPU engines are connected
- Authenticate via JWT: generate a token with `python3 -c "import sys; sys.path.insert(0,'.'); from src.middleware.auth import AuthMiddleware; print(AuthMiddleware().create_jwt_token('dev-user','admin'))"`

### Testing

- **Root Python tests**: `PYTHONPATH=. pytest tests/ -v` (625 pass; 16 pre-existing failures due to missing web frontend source files)
- **CI validator**: `python3 tools/ci-validator/validate.py` (has pre-existing validation errors in workflow files)
- **Platform-specific tests** (run from each platform directory):
  - `cd platforms/eco-govops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (159 pass)
  - `cd platforms/eco-core && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (32 pass)
  - `cd platforms/eco-observops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (22 pass)
  - `cd platforms/eco-seccompops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (6 pass)
  - `cd platforms/eco-dataops && python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/e2e -q` (18 pass)
  - `cd platforms/eco-superai && python3 -m pytest tests/unit/ -q` (1223 pass; 87 pre-existing failures needing optional deps like celery, openai, chromadb)

### Linting

- **Python**: `ruff check src/ backend/ai/` (pre-existing style warnings; config in `pyproject.toml`)
- **TypeScript**: `ESLINT_USE_FLAT_CONFIG=false npx eslint packages/ backend/api/src/ --ext .ts,.tsx` (repo uses `.eslintrc.json`; ESLint v9 requires `ESLINT_USE_FLAT_CONFIG=false` flag)

### Gotchas

- `pip install -e ".[dev]"` fails because hatchling can't resolve the `eco_base` package directory. Install deps directly: `pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy uvicorn pydantic-settings prometheus-client PyJWT redis python-multipart ruff mypy pytest-cov structlog`.
- The web frontend (`platforms/web/`) is scaffolding only — no React source files exist under `app/src/`. Tests referencing those paths (test_web_frontend.py, test_yaml_studio.py) fail.
- pnpm warns about `"workspaces"` field in `package.json` (pnpm prefers `pnpm-workspace.yaml`), but install succeeds.
- `$HOME/.local/bin` must be on `PATH` for ruff, mypy, and other pip-installed scripts.

### Deployment (Third-Party Platforms)

Five platform deploy workflows exist in `.github/workflows/`:
- **GitHub CI/CD**: 27 workflows total; `release.yml` + `publish-{npm,docker,pypi}.yml` handle releases
- **Supabase**: `supabase-deploy.yml` runs migrations and deploys 4 edge functions. Seed data in `supabase/seed.sql`
- **Vercel**: `vercel-deploy.yml` deploys `platforms/web/` (static landing page) with preview on PRs. Config: `platforms/web/vercel.json`
- **GKE**: `gke-deploy.yml` does Helm deploy to staging/production. Argo CD apps in `k8s/argocd/`. Helm chart in `helm/`
- **Cloudflare**: `cloudflare-deploy.yml` deploys webhook router Worker. Config: `backend/cloudflare/wrangler.toml`

All deploy workflows require secrets configured in GitHub repository settings. See `platform_config_summary.log` or each workflow file for required secret names.
