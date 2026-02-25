#!/bin/bash
# GL Quantum K3s Manual Upgrade Script
# Supports single-node and cluster environments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CURRENT_VERSION=$(k3s --version | grep -oP 'k3s version v\K[0-9.]+')
TARGET_VERSION="${TARGET_VERSION:-v1.26.0+k3s1}"
BACKUP_DIR="/var/lib/rancher/k3s/backups"
LOG_FILE="/var/log/k3s-upgrade.log"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# Error handler
error_exit() {
    log "ERROR" "$1"
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root"
    fi
}

# Backup etcd
backup_etcd() {
    log "INFO" "Creating etcd snapshot..."
    k3s etcd-snapshot save --name "pre-upgrade-$(date +%Y%m%d-%H%M%S)" || error_exit "Failed to create etcd snapshot"
    log "INFO" "✅ Etcd snapshot created successfully"
}

# Download k3s binary
download_k3s() {
    local version=$1
    log "INFO" "Downloading k3s ${version}..."
    
    curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${version}" sh - || error_exit "Failed to download and install k3s ${version}"
    
    log "INFO" "✅ k3s ${version} downloaded and installed"
}

# Verify upgrade
verify_upgrade() {
    local expected_version=$1
    local actual_version=$(k3s --version | grep -oP 'k3s version v\K[0-9.]+')
    
    if [[ "${actual_version}" == "${expected_version}" ]]; then
        log "INFO" "✅ Upgrade verified: k3s version ${actual_version}"
        return 0
    else
        error_exit "Upgrade verification failed. Expected: ${expected_version}, Actual: ${actual_version}"
    fi
}

# Check cluster health
check_cluster_health() {
    log "INFO" "Checking cluster health..."
    
    # Check nodes
    if ! kubectl get nodes &>/dev/null; then
        error_exit "Failed to get nodes"
    fi
    
    # Wait for nodes to be ready
    local max_wait=300
    local waited=0
    while true; do
        local not_ready=$(kubectl get nodes --no-headers | grep -c "NotReady" || true)
        if [[ ${not_ready} -eq 0 ]]; then
            log "INFO" "✅ All nodes are ready"
            break
        fi
        
        if [[ ${waited} -ge ${max_wait} ]]; then
            error_exit "Timed out waiting for nodes to be ready"
        fi
        
        log "INFO" "Waiting for nodes to be ready... (${waited}/${max_wait}s)"
        sleep 10
        waited=$((waited + 10))
    done
    
    # Check pods
    local max_wait=600
    local waited=0
    while true; do
        local not_running=$(kubectl get pods --all-namespaces --no-headers | grep -c -v "Running\|Completed" || true)
        if [[ ${not_running} -eq 0 ]]; then
            log "INFO" "✅ All pods are running"
            break
        fi
        
        if [[ ${waited} -ge ${max_wait} ]]; then
            log "WARNING" "Some pods are still not running after ${max_wait}s"
            break
        fi
        
        log "INFO" "Waiting for pods to be ready... (${waited}/${max_wait}s)"
        sleep 10
        waited=$((waited + 10))
    done
}

# Rollback function
rollback() {
    log "WARNING" "Initiating rollback..."
    
    local backup_file="${BACKUP_DIR}/$(ls -t ${BACKUP_DIR} | head -1)"
    
    if [[ -z "${backup_file}" ]]; then
        error_exit "No backup file found for rollback"
    fi
    
    log "INFO" "Restoring from backup: ${backup_file}"
    
    # Restore etcd snapshot
    k3s etcd-snapshot restore "${backup_file}" || error_exit "Failed to restore etcd snapshot"
    
    # Restart k3s
    systemctl restart k3s
    
    # Wait for k3s to start
    sleep 30
    
    log "INFO" "✅ Rollback completed"
}

# Main upgrade function
upgrade() {
    log "INFO" "========================================="
    log "INFO" "Starting K3s Upgrade Process"
    log "INFO" "========================================="
    log "INFO" "Current Version: ${CURRENT_VERSION}"
    log "INFO" "Target Version: ${TARGET_VERSION}"
    
    # Pre-upgrade checks
    check_root
    backup_etcd
    
    # Download and install new version
    download_k3s "${TARGET_VERSION}"
    
    # Restart k3s
    log "INFO" "Restarting k3s..."
    systemctl restart k3s
    
    # Wait for k3s to start
    sleep 30
    
    # Verify upgrade
    verify_upgrade "${TARGET_VERSION}"
    
    # Check cluster health
    check_cluster_health
    
    log "INFO" "========================================="
    log "INFO" "✅ K3s Upgrade Completed Successfully"
    log "INFO" "========================================="
}

# Parse command line arguments
case "${1:-upgrade}" in
    upgrade)
        upgrade
        ;;
    rollback)
        rollback
        ;;
    health)
        check_cluster_health
        ;;
    backup)
        backup_etcd
        ;;
    *)
        echo "Usage: $0 {upgrade|rollback|health|backup}"
        echo ""
        echo "Environment Variables:"
        echo "  TARGET_VERSION   Target k3s version (default: v1.26.0+k3s1)"
        exit 1
        ;;
esac

exit 0