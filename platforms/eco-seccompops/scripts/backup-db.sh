#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# SecCompOps Platform — Database Backup Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[backup] $(date -u +%FT%TZ) INFO  $*"; }
log_ok()    { echo "[backup] $(date -u +%FT%TZ) OK    $*"; }

DB_HOST="${SECCOMPOPS_DB_HOST:-localhost}"
DB_PORT="${SECCOMPOPS_DB_PORT:-5432}"
DB_NAME="${SECCOMPOPS_DB_NAME:-seccompops}"
DB_USER="${SECCOMPOPS_DB_USER:-seccompops}"
BACKUP_DIR="${SECCOMPOPS_BACKUP_DIR:-${PROJECT_ROOT}/backups}"
RETENTION_DAYS="${SECCOMPOPS_BACKUP_RETENTION:-30}"

TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/seccompops_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

log_info "Starting backup of ${DB_NAME}@${DB_HOST}:${DB_PORT}..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom --compress=9 --no-owner --no-privileges --verbose 2>/dev/null \
    | gzip -9 > "${BACKUP_FILE}"

sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
log_ok "Backup created: ${BACKUP_FILE}"

if [[ ${RETENTION_DAYS} -gt 0 ]]; then
    find "${BACKUP_DIR}" -name "seccompops_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "seccompops_*.sql.gz.sha256" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
fi

log_ok "Backup complete"
