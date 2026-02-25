#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DataOps Platform — Docker Entrypoint
# =============================================================================

log_info() { echo "[entrypoint] $(date -u +%FT%TZ) INFO  $*"; }
log_error(){ echo "[entrypoint] $(date -u +%FT%TZ) ERROR $*" >&2; }

DB_HOST="${DATAOPS_DB_HOST:-postgres}"
DB_PORT="${DATAOPS_DB_PORT:-5432}"
MAX_WAIT="${DATAOPS_DB_WAIT:-30}"

log_info "Waiting for database at ${DB_HOST}:${DB_PORT}..."
ELAPSED=0
while ! python3 -c "
import socket, sys
try:
    s = socket.create_connection(('${DB_HOST}', ${DB_PORT}), timeout=2); s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1; ELAPSED=$((ELAPSED + 1))
    [[ ${ELAPSED} -ge ${MAX_WAIT} ]] && { log_error "Timeout waiting for database"; exit 1; }
done
log_info "Database is ready"

if [[ "${DATAOPS_RUN_MIGRATIONS:-false}" == "true" ]]; then
    log_info "Running migrations..."
    python3 -m alembic upgrade head || log_error "Migration failed"
fi

if [[ $# -gt 0 ]]; then
    exec "$@"
else
    WORKERS="${DATAOPS_WORKERS:-4}"
    PORT="${DATAOPS_PORT:-8085}"
    log_info "Starting uvicorn with ${WORKERS} workers on port ${PORT}"
    exec uvicorn presentation.api.main:app \
        --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}" \
        --loop uvloop --http httptools --access-log --log-level info \
        --timeout-keep-alive 30
fi
