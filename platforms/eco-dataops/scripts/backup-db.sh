#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DataOps Platform — Database Backup Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[backup] $(date -u +%FT%TZ) INFO  $*"; }
log_ok()    { echo "[backup] $(date -u +%FT%TZ) OK    $*"; }

DB_HOST="${DATAOPS_DB_HOST:-localhost}"
DB_PORT="${DATAOPS_DB_PORT:-5432}"
DB_NAME="${DATAOPS_DB_NAME:-dataops}"
DB_USER="${DATAOPS_DB_USER:-dataops}"
BACKUP_DIR="${DATAOPS_BACKUP_DIR:-${PROJECT_ROOT}/backups}"
RETENTION_DAYS="${DATAOPS_BACKUP_RETENTION:-30}"

TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/dataops_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

log_info "Starting backup of ${DB_NAME}@${DB_HOST}:${DB_PORT}..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom --compress=9 --no-owner --no-privileges --verbose 2>/dev/null \
    | gzip -9 > "${BACKUP_FILE}"

sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
log_ok "Backup created: ${BACKUP_FILE}"

if [[ ${RETENTION_DAYS} -gt 0 ]]; then
    find "${BACKUP_DIR}" -name "dataops_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "dataops_*.sql.gz.sha256" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
fi

log_ok "Backup complete"
