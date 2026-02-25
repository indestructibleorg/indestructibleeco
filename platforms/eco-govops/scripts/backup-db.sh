#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GovOps Platform — Database Backup Script
# Creates timestamped PostgreSQL backups with SHA-256 verification.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[backup] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[backup] $(date -u +%FT%TZ) ERROR $*" >&2; }
log_ok()    { echo "[backup] $(date -u +%FT%TZ) OK    $*"; }

DB_HOST="${GOVOPS_DB_HOST:-localhost}"
DB_PORT="${GOVOPS_DB_PORT:-5432}"
DB_NAME="${GOVOPS_DB_NAME:-govops}"
DB_USER="${GOVOPS_DB_USER:-govops}"
BACKUP_DIR="${GOVOPS_BACKUP_DIR:-${PROJECT_ROOT}/backups}"
RETENTION_DAYS="${GOVOPS_BACKUP_RETENTION:-30}"

TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/govops_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

# ---------------------------------------------------------------------------
# Create backup
# ---------------------------------------------------------------------------
log_info "Starting backup of ${DB_NAME}@${DB_HOST}:${DB_PORT}..."

pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    --verbose 2>/dev/null \
    | gzip -9 > "${BACKUP_FILE}"

# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------
sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
log_ok "Backup created: ${BACKUP_FILE}"
log_info "Checksum: $(cat "${CHECKSUM_FILE}")"

# ---------------------------------------------------------------------------
# Retention pruning
# ---------------------------------------------------------------------------
if [[ ${RETENTION_DAYS} -gt 0 ]]; then
    PRUNED=$(find "${BACKUP_DIR}" -name "govops_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
    find "${BACKUP_DIR}" -name "govops_*.sql.gz.sha256" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    if [[ ${PRUNED} -gt 0 ]]; then
        log_info "Pruned ${PRUNED} backups older than ${RETENTION_DAYS} days"
    fi
fi

log_ok "Backup complete"
