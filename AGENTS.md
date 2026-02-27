# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

eco-base is an enterprise cloud-native AI platform monorepo with multi-engine inference routing. See `README.md` for full architecture and `docs/DEVELOPER_GUIDE.md` for conventions.

### Services

| Service | Port | How to start |
|---------|------|-------------|
| FastAPI gateway (root `src/`) | 8000 | `PYTHONPATH=. uvicorn src.app:app --host 0.0.0.0 --port 8000` |
| Express API (`backend/api/`) | 3000 | `cd backend/api && npx ts-node src/server.ts` |
| Vite web frontend (`platforms/web/`) | 5173 | `cd platforms/web && npx vite --host 0.0.0.0 --port 5173` |
| PostgreSQL (Docker) | 5432 | `docker compose --env-file .env.local up -d postgres` |
| Redis (Docker) | 6379 | `docker compose --env-file .env.local up -d redis` |

### Important gotchas

- **`.env.local` inline comments break Redis**: The `.env.local.example` has inline comments (e.g. `REDIS_PASSWORD=  # comment`). Docker Compose passes these as literal values. When creating `.env.local`, strip inline comments. Set `REDIS_PASSWORD=redis` (not empty) since the docker-compose uses `--requirepass ${REDIS_PASSWORD:-}` which fails with an empty string.
- **`pip install -e ".[dev]"` fails**: The root `pyproject.toml` uses hatchling but lacks `tool.hatch.build.targets.wheel.packages` config. Install Python deps directly: `pip install pydantic fastapi httpx pytest pytest-asyncio jsonschema pyyaml numpy pytest-cov ruff mypy uvicorn pydantic-settings prometheus-client PyJWT redis python-multipart`.
- **pnpm workspaces warning**: The root `package.json` uses the `workspaces` field, but pnpm requires `pnpm-workspace.yaml` (which doesn't exist). Root `pnpm install` installs only root devDependencies (eslint, typescript, prettier). Workspace packages (`backend/api`, `platforms/web`) need individual `npm install --no-workspaces` calls.
- **API Docker dev target issue**: The `docker-compose.yml` api service uses `target: builder` which has no CMD. Run the Express API locally with `ts-node` instead of via Docker for dev.
- **ESLint requires legacy config flag**: Root uses `.eslintrc.json` (not flat config). Run with `ESLINT_USE_FLAT_CONFIG=false` prefix.

### Testing

- **Python tests**: `PYTHONPATH=. pytest tests/ -v` (609 passing, 32 pre-existing failures from missing workflow/frontend files)
- **CI validator**: `python3 tools/ci-validator/validate.py`
- **Skill tests**: `pytest tools/skill-creator/skills/ -v`
- **Python lint**: `ruff check src/ backend/ai/`
- **TS lint**: `ESLINT_USE_FLAT_CONFIG=false npx eslint packages/ backend/ --ext .ts,.tsx`

### Docker

Docker must be installed and configured with `fuse-overlayfs` storage driver and `iptables-legacy` for the Cloud Agent VM environment. Start Docker daemon with `sudo dockerd &` and ensure `/var/run/docker.sock` is accessible.
