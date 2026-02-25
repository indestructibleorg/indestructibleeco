#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform — Database Backup Script
# ============================================================================
# Usage: ./scripts/backup-db.sh [--output-dir /path] [--compress] [--upload s3://bucket]
# ============================================================================
set -euo pipefail

# --- Defaults ---
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-superai_db}"
DB_USER="${DB_USER:-superai}"
OUTPUT_DIR="${OUTPUT_DIR:-./backups}"
COMPRESS="${COMPRESS:-true}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
BACKUP_NAME="superai_db_${TIMESTAMP}"

log_info()  { echo "[backup] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[backup] $(date -u +%FT%TZ) ERROR $*" >&2; }

# --- Parse arguments ---
S3_BUCKET=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --compress)   COMPRESS="true"; shift ;;
        --no-compress) COMPRESS="false"; shift ;;
        --upload)     S3_BUCKET="$2"; shift 2 ;;
        --retention)  RETENTION_DAYS="$2"; shift 2 ;;
        *) log_error "Unknown argument: $1"; exit 1 ;;
    esac
done

mkdir -p "${OUTPUT_DIR}"

# --- Pre-flight checks ---
if ! command -v pg_dump &>/dev/null; then
    log_error "pg_dump not found. Install postgresql-client."
    exit 1
fi

log_info "Starting backup of ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log_info "Output directory: ${OUTPUT_DIR}"

# --- Execute backup ---
BACKUP_FILE="${OUTPUT_DIR}/${BACKUP_NAME}.sql"

pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    --format=plain \
    --verbose \
    > "${BACKUP_FILE}" 2>/dev/null

DUMP_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}")
log_info "Dump completed: ${BACKUP_FILE} (${DUMP_SIZE} bytes)"

# --- Compress ---
if [ "${COMPRESS}" = "true" ]; then
    gzip -9 "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}")
    log_info "Compressed: ${BACKUP_FILE} (${COMPRESSED_SIZE} bytes)"
fi

# --- Generate checksum ---
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
log_info "Checksum: ${BACKUP_FILE}.sha256"

# --- Upload to S3 (optional) ---
if [ -n "${S3_BUCKET}" ]; then
    if command -v aws &>/dev/null; then
        aws s3 cp "${BACKUP_FILE}" "${S3_BUCKET}/${BACKUP_NAME}.sql.gz" --sse AES256
        aws s3 cp "${BACKUP_FILE}.sha256" "${S3_BUCKET}/${BACKUP_NAME}.sql.gz.sha256"
        log_info "Uploaded to ${S3_BUCKET}"
    else
        log_error "AWS CLI not found. Skipping upload."
    fi
fi

# --- Prune old backups ---
if [ "${RETENTION_DAYS}" -gt 0 ]; then
    PRUNED=$(find "${OUTPUT_DIR}" -name "superai_db_*.sql*" -mtime +"${RETENTION_DAYS}" -delete -print | wc -l)
    log_info "Pruned ${PRUNED} backups older than ${RETENTION_DAYS} days"
fi

log_info "Backup completed successfully: ${BACKUP_FILE}"