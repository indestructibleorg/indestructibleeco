#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform — Database Restore Script
# ============================================================================
# Usage: ./scripts/restore-db.sh <backup_file> [--target-db superai_db]
# ============================================================================
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-superai_db}"
DB_USER="${DB_USER:-superai}"

log_info()  { echo "[restore] $(date -u +%FT%TZ) INFO  $*"; }
log_warn()  { echo "[restore] $(date -u +%FT%TZ) WARN  $*" >&2; }
log_error() { echo "[restore] $(date -u +%FT%TZ) ERROR $*" >&2; }

# --- Parse arguments ---
BACKUP_FILE=""
SKIP_CONFIRM="${SKIP_CONFIRM:-false}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target-db) DB_NAME="$2"; shift 2 ;;
        --host)      DB_HOST="$2"; shift 2 ;;
        --port)      DB_PORT="$2"; shift 2 ;;
        --user)      DB_USER="$2"; shift 2 ;;
        --yes)       SKIP_CONFIRM="true"; shift ;;
        -*)          log_error "Unknown flag: $1"; exit 1 ;;
        *)           BACKUP_FILE="$1"; shift ;;
    esac
done

if [ -z "${BACKUP_FILE}" ]; then
    log_error "Usage: $0 <backup_file> [--target-db name] [--yes]"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# --- Pre-flight checks ---
if ! command -v psql &>/dev/null; then
    log_error "psql not found. Install postgresql-client."
    exit 1
fi

# --- Verify checksum if available ---
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    log_info "Verifying checksum..."
    if sha256sum --check "${CHECKSUM_FILE}" --quiet 2>/dev/null; then
        log_info "Checksum verified OK"
    else
        log_error "Checksum verification FAILED. Aborting."
        exit 1
    fi
else
    log_warn "No checksum file found. Skipping verification."
fi

# --- Confirmation ---
log_warn "This will OVERWRITE database '${DB_NAME}' on ${DB_HOST}:${DB_PORT}"
if [ "${SKIP_CONFIRM}" != "true" ]; then
    read -rp "[restore] Type 'yes' to confirm: " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        log_info "Restore cancelled."
        exit 0
    fi
fi

# --- Decompress if needed ---
RESTORE_FILE="${BACKUP_FILE}"
TEMP_FILE=""
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    log_info "Decompressing backup..."
    TEMP_FILE=$(mktemp /tmp/superai_restore_XXXXXX.sql)
    gunzip -c "${BACKUP_FILE}" > "${TEMP_FILE}"
    RESTORE_FILE="${TEMP_FILE}"
    log_info "Decompressed to ${RESTORE_FILE}"
fi

# --- Terminate existing connections ---
log_info "Terminating existing connections to ${DB_NAME}..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
" 2>/dev/null || true

# --- Execute restore ---
log_info "Restoring ${RESTORE_FILE} to ${DB_NAME}@${DB_HOST}:${DB_PORT}..."

psql \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --single-transaction \
    --set ON_ERROR_STOP=on \
    -f "${RESTORE_FILE}" \
    2>&1 | tail -5

RESTORE_EXIT=$?

# --- Cleanup temp file ---
if [ -n "${TEMP_FILE}" ] && [ -f "${TEMP_FILE}" ]; then
    rm -f "${TEMP_FILE}"
fi

# --- Verify ---
if [ ${RESTORE_EXIT} -eq 0 ]; then
    TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "
        SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
    " 2>/dev/null | tr -d ' ')
    log_info "Restore completed. Tables in database: ${TABLE_COUNT}"
else
    log_error "Restore failed with exit code ${RESTORE_EXIT}"
    exit ${RESTORE_EXIT}
fi

log_info "Database restore completed successfully."