#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform — Container Entrypoint
# ============================================================================
# Handles pre-flight checks, migrations, and process startup.
# ============================================================================
set -euo pipefail

APP_ENV="${APP_ENV:-development}"
APP_PORT="${APP_PORT:-8000}"
APP_WORKERS="${APP_WORKERS:-4}"
APP_LOG_LEVEL="${APP_LOG_LEVEL:-info}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-false}"
WAIT_FOR_DB="${WAIT_FOR_DB:-true}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_TIMEOUT="${DB_TIMEOUT:-30}"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()  { echo "[entrypoint] INFO  $(date -u +%FT%TZ) $*"; }
log_warn()  { echo "[entrypoint] WARN  $(date -u +%FT%TZ) $*" >&2; }
log_error() { echo "[entrypoint] ERROR $(date -u +%FT%TZ) $*" >&2; }

# ---------------------------------------------------------------------------
# Wait for database readiness
# ---------------------------------------------------------------------------
wait_for_database() {
    if [ "${WAIT_FOR_DB}" != "true" ]; then
        return 0
    fi

    log_info "Waiting for database at ${DB_HOST}:${DB_PORT} (timeout: ${DB_TIMEOUT}s)..."
    local elapsed=0
    while [ "$elapsed" -lt "$DB_TIMEOUT" ]; do
        if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -q 2>/dev/null; then
            log_info "Database is ready."
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    log_error "Database not ready after ${DB_TIMEOUT}s — aborting."
    exit 1
}

# ---------------------------------------------------------------------------
# Run Alembic migrations
# ---------------------------------------------------------------------------
run_migrations() {
    if [ "${RUN_MIGRATIONS}" != "true" ]; then
        return 0
    fi

    log_info "Running database migrations..."
    if command -v alembic &>/dev/null; then
        alembic upgrade head
        log_info "Migrations completed."
    else
        log_warn "alembic not found — skipping migrations."
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    log_info "SuperAI Platform entrypoint — env=${APP_ENV}"

    wait_for_database
    run_migrations

    # If arguments are passed, execute them directly (e.g. celery worker)
    if [ $# -gt 0 ]; then
        log_info "Executing: $*"
        exec "$@"
    fi

    # Default: start the application server
    if [ "${APP_ENV}" = "production" ]; then
        log_info "Starting Gunicorn (workers=${APP_WORKERS}, port=${APP_PORT})..."
        exec gunicorn src.presentation.api.main:app \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind "0.0.0.0:${APP_PORT}" \
            --workers "${APP_WORKERS}" \
            --timeout 120 \
            --graceful-timeout 30 \
            --keep-alive 5 \
            --access-logfile - \
            --error-logfile - \
            --log-level "${APP_LOG_LEVEL}"
    else
        log_info "Starting Uvicorn dev server (port=${APP_PORT}, reload=on)..."
        exec uvicorn src.presentation.api.main:app \
            --host 0.0.0.0 \
            --port "${APP_PORT}" \
            --reload \
            --reload-dir src \
            --log-level "${APP_LOG_LEVEL}"
    fi
}

main "$@"