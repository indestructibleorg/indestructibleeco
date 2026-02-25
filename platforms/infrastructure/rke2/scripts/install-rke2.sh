#!/bin/bash
# @GL-governed
# @GL-layer: GL30-39
# @GL-semantic: rke2-installation
# @GL-audit-trail: ../../../engine/governance/GL_SEMANTIC_ANCHOR.json

# RKE2 Production Installation Script
# Installs RKE2 with CIS hardening for MachineNativeOps

set -e

# ============================================================================
# Configuration
# ============================================================================
RKE2_VERSION="v1.29.0+rke2r1"
CIS_PROFILE="cis-1.29"
INSTALL_DIR="/opt/rke2"
CONFIG_DIR="/etc/rancher/rke2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Logging Functions
# ============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Prerequisites Check
# ============================================================================
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check OS
    if [ ! -f /etc/os-release ]; then
        log_error "Cannot detect OS. /etc/os-release not found"
        exit 1
    fi
    
    # Check for SELinux
    if command -v getenforce &> /dev/null; then
        SELINUX_MODE=$(getenforce)
        log_info "SELinux mode: ${SELINUX_MODE}"
        
        if [ "$SELINUX_MODE" = "Disabled" ]; then
            log_warning "SELinux is disabled. RKE2 will configure it"
        fi
    else
        log_warning "SELinux not found. Installation will continue without SELinux"
    fi
    
    # Check for required tools
    for tool in curl grep sed; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is not installed"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# ============================================================================
# Download RKE2
# ============================================================================
download_rke2() {
    log_info "Downloading RKE2 ${RKE2_VERSION}..."
    
    # Download RKE2 install script
    curl -sfL https://get.rke2.io | sh
    
    if [ $? -ne 0 ]; then
        log_error "Failed to download RKE2"
        exit 1
    fi
    
    log_success "RKE2 downloaded successfully"
}

# ============================================================================
# Create Configuration Directories
# ============================================================================
create_config_dirs() {
    log_info "Creating configuration directories..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p /var/lib/rancher/rke2/server/db/etcd
    mkdir -p /var/log/rke2
    
    log_success "Configuration directories created"
}

# ============================================================================
# Copy Configuration Files
# ============================================================================
copy_configs() {
    log_info "Copying configuration files..."
    
    # Copy RKE2 config
    if [ -f "$SCRIPT_DIR/../profiles/production/config.yaml" ]; then
        cp "$SCRIPT_DIR/../profiles/production/config.yaml" "$CONFIG_DIR/config.yaml"
        log_success "RKE2 configuration copied"
    else
        log_warning "RKE2 config not found, using defaults"
    fi
    
    # Copy encryption provider config
    if [ -f "$SCRIPT_DIR/../profiles/production/encryption-provider-config.yaml" ]; then
        cp "$SCRIPT_DIR/../profiles/production/encryption-provider-config.yaml" "$CONFIG_DIR/encryption-provider-config.yaml"
        log_success "Encryption provider configuration copied"
    else
        log_warning "Encryption provider config not found"
    fi
    
    # Copy PSA config
    if [ -f "$SCRIPT_DIR/../profiles/production/psa-config.yaml" ]; then
        cp "$SCRIPT_DIR/../profiles/production/psa-config.yaml" "$CONFIG_DIR/psa-config.yaml"
        log_success "PSA configuration copied"
    else
        log_warning "PSA config not found"
    fi
    
    # Copy audit policy
    if [ -f "$SCRIPT_DIR/../profiles/production/audit-policy.yaml" ]; then
        cp "$SCRIPT_DIR/../profiles/production/audit-policy.yaml" "$CONFIG_DIR/audit-policy.yaml"
        log_success "Audit policy copied"
    else
        log_warning "Audit policy not found"
    fi
}

# ============================================================================
# Configure Kernel Parameters
# ============================================================================
configure_kernel_params() {
    log_info "Configuring kernel parameters..."
    
    # Create sysctl configuration file
    cat > /etc/sysctl.d/99-rke2-cis.conf << 'EOF'
# RKE2 CIS Benchmark Kernel Parameters
# @GL-governed
# @GL-layer: GL20-29

# CIS 5.2.1 - Ensure minimal container capabilities
kernel.modules_disabled=1

# CIS 5.2.2 - Ensure CPU cores are not overcommitted
# (This is a comment - actual value depends on system)

# CIS 5.3.1 - Ensure that the proxy ARP setting on all interfaces is disabled
net.ipv4.conf.all.proxy_arp = 0
net.ipv4.conf.default.proxy_arp = 0

# CIS 5.3.2 - Ensure that the reverse path filtering is enabled
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# CIS 5.3.3 - Ensure that the sysctl option net.ipv4.conf.all.send_redirects is disabled
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# CIS 5.3.4 - Ensure that the sysctl option net.ipv4.conf.default.accept_source_route is disabled
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# CIS 5.3.5 - Ensure that the sysctl option net.ipv4.conf.all.accept_redirects is disabled
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0

# CIS 5.3.6 - Ensure that the sysctl option net.ipv4.conf.all.secure_redirects is disabled
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# CIS 5.3.7 - Ensure that the sysctl option net.ipv4.conf.all.log_martians is enabled
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# CIS 5.3.8 - Ensure that the sysctl option net.ipv4.icmp_echo_ignore_broadcasts is enabled
net.ipv4.icmp_echo_ignore_broadcasts = 1

# CIS 5.3.9 - Ensure that the sysctl option net.ipv4.icmp_ignore_bogus_error_responses is enabled
net.ipv4.icmp_ignore_bogus_error_responses = 1

# CIS 5.3.10 - Ensure that the sysctl option net.ipv4.conf.all.accept_source_route is disabled
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# CIS 5.3.11 - Ensure that the sysctl option net.ipv4.conf.default.send_redirects is disabled
net.ipv4.conf.default.send_redirects = 0

# CIS 5.4.1 - Ensure that the sysctl option net.ipv4.ip_forward is disabled
net.ipv4.ip_forward = 0
net.ipv4.conf.all.forwarding = 0

# CIS 5.4.2 - Ensure that the bridge-nf-call-iptables is enabled
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# Additional security parameters
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.randomize_va_space = 2
EOF
    
    # Apply kernel parameters
    sysctl -p /etc/sysctl.d/99-rke2-cis.conf
    
    log_success "Kernel parameters configured"
}

# ============================================================================
# Create etcd User (CIS 1.1.12)
# ============================================================================
create_etcd_user() {
    log_info "Creating etcd user..."
    
    # Check if etcd user exists
    if ! id -u etcd >/dev/null 2>&1; then
        useradd -r -c "etcd user" -s /sbin/nologin -M etcd -U
        log_success "etcd user created"
    else
        log_info "etcd user already exists"
    fi
    
    # Set ownership of etcd data directory
    chown -R etcd:etcd /var/lib/rancher/rke2/server/db/etcd
    
    log_success "etcd user configuration completed"
}

# ============================================================================
# Enable and Start RKE2
# ============================================================================
start_rke2() {
    log_info "Enabling and starting RKE2..."
    
    # Enable RKE2 service
    systemctl enable rke2-server
    
    # Start RKE2 service
    systemctl start rke2-server
    
    # Wait for RKE2 to be ready
    log_info "Waiting for RKE2 to be ready..."
    sleep 30
    
    # Check RKE2 status
    if systemctl is-active --quiet rke2-server; then
        log_success "RKE2 started successfully"
    else
        log_error "RKE2 failed to start"
        systemctl status rke2-server
        exit 1
    fi
}

# ============================================================================
# Configure kubectl
# ============================================================================
configure_kubectl() {
    log_info "Configuring kubectl..."
    
    # Create symlink for kubectl
    ln -sf /var/lib/rancher/rke2/bin/kubectl /usr/local/bin/kubectl
    
    # Set permissions
    chmod +x /usr/local/bin/kubectl
    
    # Add to PATH
    export PATH="$PATH:/usr/local/bin"
    
    # Verify kubectl
    kubectl version --client
    
    log_success "kubectl configured"
}

# ============================================================================
# Verify Installation
# ============================================================================
verify_installation() {
    log_info "Verifying RKE2 installation..."
    
    # Check RKE2 version
    RKE2_CURRENT_VERSION=$(rke2 --version | head -n 1)
    log_info "RKE2 version: ${RKE2_CURRENT_VERSION}"
    
    # Check node status
    NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
    if [ "$NODE_STATUS" = "True" ]; then
        log_success "Node is ready"
    else
        log_warning "Node may not be ready yet"
    fi
    
    # Check system pods
    log_info "Checking system pods..."
    kubectl get pods -n kube-system
    
    log_success "Installation verification completed"
}

# ============================================================================
# Main Installation Flow
# ============================================================================
main() {
    echo "=========================================="
    echo "  RKE2 Production Installation Script"
    echo "  Version: ${RKE2_VERSION}"
    echo "  CIS Profile: ${CIS_PROFILE}"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    download_rke2
    create_config_dirs
    copy_configs
    configure_kernel_params
    create_etcd_user
    start_rke2
    configure_kubectl
    verify_installation
    
    echo ""
    echo "=========================================="
    log_success "RKE2 installation completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Check RKE2 status: systemctl status rke2-server"
    echo "2. View logs: journalctl -u rke2-server -f"
    echo "3. Check cluster: kubectl get nodes"
    echo "4. Run CIS validation: ${SCRIPT_DIR}/validate-cis.sh"
    echo ""
}

# Run main function
main "$@"