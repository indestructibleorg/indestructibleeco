#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GovOps Platform — Docker Entrypoint
# Handles database readiness, migrations, and application startup.
# =============================================================================

log_info() { echo "[entrypoint] $(date -u +%FT%TZ) INFO  $*"; }
log_error(){ echo "[entrypoint] $(date -u +%FT%TZ) ERROR $*" >&2; }

# ---------------------------------------------------------------------------
# Wait for database
# ---------------------------------------------------------------------------
DB_HOST="${GOVOPS_DB_HOST:-postgres}"
DB_PORT="${GOVOPS_DB_PORT:-5432}"
MAX_WAIT="${GOVOPS_DB_WAIT:-30}"

log_info "Waiting for database at ${DB_HOST}:${DB_PORT}..."
ELAPSED=0
while ! python3 -c "
import socket, sys
try:
    s = socket.create_connection(('${DB_HOST}', ${DB_PORT}), timeout=2)
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    if [[ ${ELAPSED} -ge ${MAX_WAIT} ]]; then
        log_error "Timeout waiting for database after ${MAX_WAIT}s"
        exit 1
    fi
done
log_info "Database is ready"

# ---------------------------------------------------------------------------
# Run migrations (optional)
# ---------------------------------------------------------------------------
if [[ "${GOVOPS_RUN_MIGRATIONS:-false}" == "true" ]]; then
    log_info "Running database migrations..."
    python3 -m alembic upgrade head || log_error "Migration failed"
fi

# ---------------------------------------------------------------------------
# Start application
# ---------------------------------------------------------------------------
if [[ $# -gt 0 ]]; then
    log_info "Executing: $*"
    exec "$@"
else
    WORKERS="${GOVOPS_WORKERS:-4}"
    PORT="${GOVOPS_PORT:-8090}"
    ENV="${GOVOPS_ENV:-production}"

    if [[ "${ENV}" == "development" ]]; then
        log_info "Starting uvicorn in development mode on port ${PORT}"
        exec uvicorn presentation.api.main:app \
            --host 0.0.0.0 \
            --port "${PORT}" \
            --reload \
            --log-level debug
    else
        log_info "Starting uvicorn with ${WORKERS} workers on port ${PORT}"
        exec uvicorn presentation.api.main:app \
            --host 0.0.0.0 \
            --port "${PORT}" \
            --workers "${WORKERS}" \
            --loop uvloop \
            --http httptools \
            --access-log \
            --log-level info \
            --timeout-keep-alive 30
    fi
fi
