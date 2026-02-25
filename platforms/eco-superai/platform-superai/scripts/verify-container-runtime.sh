#!/bin/bash
# Container Runtime Verification Script
# P0 Critical: Verify containerd/CRI-O runtime configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "Starting Container Runtime Verification..."

# Detect container runtime
detect_runtime() {
    local runtime=""
    
    if command -v containerd &> /dev/null; then
        runtime="containerd"
    elif command -v crio &> /dev/null; then
        runtime="cri-o"
    else
        log_error "No supported container runtime found (containerd or CRI-O)"
        exit 1
    fi
    
    echo "$runtime"
}

RUNTIME=$(detect_runtime)
log_info "Detected runtime: $RUNTIME"

# Verify runtime is active
verify_runtime_active() {
    log_info "Verifying $RUNTIME is active..."
    
    if ! systemctl is-active --quiet $RUNTIME; then
        log_error "$RUNTIME service is not active"
        exit 1
    fi
    
    log_info "$RUNTIME service is active"
}

# Check runtime version
check_version() {
    log_info "Checking $RUNTIME version..."
    
    case $RUNTIME in
        containerd)
            VERSION=$($RUNTIME --version | grep -oP '\d+\.\d+\.\d+')
            ;;
        crio)
            VERSION=$RUNTIME --version | grep -oP '\d+\.\d+\.\d+'
            ;;
    esac
    
    log_info "$RUNTIME version: $VERSION"
}

# Verify runtime configuration
verify_config() {
    log_info "Verifying $RUNTIME configuration..."
    
    case $RUNTIME in
        containerd)
            verify_containerd_config
            ;;
        crio)
            verify_crio_config
            ;;
    esac
}

# Verify containerd specific configuration
verify_containerd_config() {
    local config_file="/etc/containerd/config.toml"
    
    if [[ ! -f "$config_file" ]]; then
        log_warn "Containerd config file not found at $config_file"
        return
    fi
    
    # Check for SystemdCgroup
    if grep -q "SystemdCgroup = true" "$config_file"; then
        log_info "SystemdCgroup is enabled (recommended)"
    else
        log_warn "SystemdCgroup not found in config"
    fi
    
    # Check for registry mirroring
    if grep -q "\[plugins.&quot;io.containerd.grpc.v1.cri&quot;.registry.mirrors\]" "$config_file"; then
        log_info "Registry mirrors configured"
    fi
}

# Verify CRI-O specific configuration
verify_crio_config() {
    local config_file="/etc/crio/crio.conf"
    
    if [[ ! -f "$config_file" ]]; then
        log_warn "CRI-O config file not found at $config_file"
        return
    fi
    
    # Check for cgroup manager
    if grep -q 'cgroup_manager = "systemd"' "$config_file"; then
        log_info "Systemd cgroup manager is enabled (recommended)"
    fi
}

# Verify storage driver
verify_storage_driver() {
    log_info "Verifying storage driver..."
    
    case $RUNTIME in
        containerd)
            DRIVER=$(containerd config dump 2>/dev/null | grep -A 5 "snapshotter" | grep "type" | head -1 || echo "unknown")
            ;;
        crio)
            DRIVER=$(grep "storage_driver" /etc/crio/crio.conf 2>/dev/null | awk -F'=' '{print $2}' | tr -d '"' || echo "unknown")
            ;;
    esac
    
    log_info "Storage driver: $DRIVER"
}

# Verify runtime socket
verify_socket() {
    log_info "Verifying runtime socket..."
    
    case $RUNTIME in
        containerd)
            SOCKET="/run/containerd/containerd.sock"
            ;;
        crio)
            SOCKET="/run/crio/crio.sock"
            ;;
    esac
    
    if [[ -S "$SOCKET" ]]; then
        log_info "Runtime socket exists: $SOCKET"
    else
        log_error "Runtime socket not found: $SOCKET"
        exit 1
    fi
}

# Test runtime functionality
test_runtime() {
    log_info "Testing runtime functionality..."
    
    # Try to pull a test image
    TEST_IMAGE="docker.io/library/alpine:latest"
    
    case $RUNTIME in
        containerd)
            if ctr images pull "$TEST_IMAGE" &> /dev/null; then
                log_info "Successfully pulled test image with ctr"
                ctr images rm "$TEST_IMAGE" &> /dev/null || true
            else
                log_warn "Failed to pull test image with ctr (may be permission issue)"
            fi
            ;;
        crio)
            if crictl pull "$TEST_IMAGE" &> /dev/null; then
                log_info "Successfully pulled test image with crictl"
                crictl rmi "$TEST_IMAGE" &> /dev/null || true
            else
                log_warn "Failed to pull test image with crictl (may be permission issue)"
            fi
            ;;
    esac
}

# Verify runtime metrics endpoint
verify_metrics() {
    log_info "Verifying metrics endpoint..."
    
    case $RUNTIME in
        containerd)
            if curl -s --unix-socket /run/containerd/containerd.sock http://localhost/metrics &> /dev/null; then
                log_info "Containerd metrics endpoint is accessible"
            fi
            ;;
        crio)
            # CRI-O metrics typically exposed via separate service
            if systemctl is-active --quiet crio-metrics 2>/dev/null; then
                log_info "CRI-O metrics service is active"
            fi
            ;;
    esac
}

# Main execution
main() {
    verify_runtime_active
    check_version
    verify_config
    verify_storage_driver
    verify_socket
    test_runtime
    verify_metrics
    
    log_info "Container runtime verification completed successfully!"
}

main "$@"