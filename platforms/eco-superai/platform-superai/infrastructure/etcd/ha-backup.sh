#!/bin/bash
# High Availability etcd Backup Script
# P0 Critical: Automated etcd backup with multi-region replication

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/lib/etcd-backup}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_RETENTION="${BACKUP_RETENTION:-10}"
ETCD_ENDPOINTS="${ETCD_ENDPOINTS:-https://127.0.0.1:2379}"
BACKUP_NAME_PREFIX="etcd-backup-$(date +%Y%m%d-%H%M%S)"
REMOTE_REGIONS="${REMOTE_REGIONS:-us-west-2 eu-central-1 ap-southeast-1}"

log_info "Starting HA etcd Backup..."
log_info "Retention: ${RETENTION_DAYS} days"

# Check for required tools
check_tools() {
    log_step "Checking required tools..."
    
    for tool in etcdctl aws; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool not found"
            exit 1
        fi
    done
    
    log_info "All required tools found"
}

# Get etcd status
get_etcd_status() {
    log_step "Checking etcd cluster health..."
    
    ETCDCTL_API=3 etcdctl \
        --endpoints="$ETCD_ENDPOINTS" \
        --cacert=/etc/kubernetes/pki/etcd/ca.crt \
        --cert=/etc/kubernetes/pki/etcd/server.crt \
        --key=/etc/kubernetes/pki/etcd/server.key \
        endpoint health
    
    log_info "etcd cluster is healthy"
}

# Perform etcd snapshot
perform_snapshot() {
    log_step "Performing etcd snapshot..."
    
    local snapshot_file="$BACKUP_DIR/local/${BACKUP_NAME_PREFIX}.db"
    
    ETCDCTL_API=3 etcdctl \
        --endpoints="$ETCD_ENDPOINTS" \
        --cacert=/etc/kubernetes/pki/etcd/ca.crt \
        --cert=/etc/kubernetes/pki/etcd/server.crt \
        --key=/etc/kubernetes/pki/etcd/server.key \
        snapshot save "$snapshot_file"
    
    log_info "Snapshot saved to $snapshot_file"
}

# Compress snapshot
compress_snapshot() {
    log_step "Compressing snapshot..."
    
    local snapshot_file="$BACKUP_DIR/local/${BACKUP_NAME_PREFIX}.db"
    local compressed_file="${snapshot_file}.tar.gz"
    
    tar -czf "$compressed_file" \
        -C "$BACKUP_DIR/local" \
        "${BACKUP_NAME_PREFIX}.db"
    
    sha256sum "$compressed_file" > "${compressed_file}.sha256"
    
    log_info "Snapshot compressed"
}

# Replicate to remote regions
replicate_to_regions() {
    log_step "Replicating backup to remote regions..."
    
    local compressed_file="$BACKUP_DIR/local/${BACKUP_NAME_PREFIX}.db.tar.gz"
    
    for region in $REMOTE_REGIONS; do
        log_info "Replicating to region: $region"
        
        aws s3 cp "$compressed_file" \
            "s3://superai-etcd-backup-${region}/${BACKUP_NAME_PREFIX}.tar.gz" \
            --storage-class STANDARD_IA
    done
    
    log_info "Replication completed"
}

# Clean up old backups
cleanup_old_backups() {
    log_step "Cleaning up old backups..."
    
    find "$BACKUP_DIR/local" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete
    
    log_info "Cleanup completed"
}

# Main execution
main() {
    check_tools
    get_etcd_status
    perform_snapshot
    compress_snapshot
    replicate_to_regions
    cleanup_old_backups
    
    log_info "HA etcd backup completed successfully"
}

main "$@"