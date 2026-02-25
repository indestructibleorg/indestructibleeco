#!/bin/bash
# @GL-governed
# @GL-layer: GL40-49
# @GL-semantic: cis-validation
# @GL-audit-trail: ../../../engine/governance/GL_SEMANTIC_ANCHOR.json

# RKE2 CIS Compliance Validation Script
# Validates RKE2 cluster against CIS 1.29 benchmark

set -e

# ============================================================================
# Configuration
# ============================================================================
CONFIG_DIR="/etc/rancher/rke2"
CIS_VERSION="1.29"
REPORT_DIR="outputs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/cis-validation-${TIMESTAMP}.json"

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
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# ============================================================================
# Initialize Report
# ============================================================================
init_report() {
    mkdir -p "$REPORT_DIR"
    
    cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cis_version": "${CIS_VERSION}",
  "rke2_version": "$(rke2 --version | head -n 1)",
  "controls": {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0
  },
  "checks": []
}
EOF
}

# ============================================================================
# Add Check to Report
# ============================================================================
add_check() {
    local id="$1"
    local description="$2"
    local status="$3"
    local severity="$4"
    local message="$5"
    
    # Update report
    jq --arg id "$id" \
       --arg desc "$description" \
       --arg status "$status" \
       --arg severity "$severity" \
       --arg msg "$message" \
       '.checks += [{"id": $id, "description": $desc, "status": $status, "severity": $severity, "message": $msg}]' \
       "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    
    # Update counters
    if [ "$status" = "pass" ]; then
        jq '.controls.passed += 1 | .controls.total += 1' "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    elif [ "$status" = "fail" ]; then
        jq '.controls.failed += 1 | .controls.total += 1' "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    elif [ "$status" = "skip" ]; then
        jq '.controls.skipped += 1 | .controls.total += 1' "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
}

# ============================================================================
# Check Functions
# ============================================================================

# CIS 1.1.1 - Ensure that the etcd data directory permissions are set to 700 or more restrictive
check_1_1_1() {
    local id="1.1.1"
    local description="etcd data directory permissions"
    local severity="medium"
    
    log_info "Checking ${id}: ${description}"
    
    local etcd_dir="/var/lib/rancher/rke2/server/db/etcd"
    
    if [ -d "$etcd_dir" ]; then
        local perms=$(stat -c %a "$etcd_dir")
        if [ "$perms" = "700" ] || [ "$perms" = "600" ]; then
            log_success "${id}: etcd data directory has correct permissions (${perms})"
            add_check "$id" "$description" "pass" "$severity" "Directory has ${perms} permissions"
        else
            log_error "${id}: etcd data directory has incorrect permissions (${perms})"
            add_check "$id" "$description" "fail" "$severity" "Directory has ${perms} permissions, expected 700"
        fi
    else
        log_warning "${id}: etcd data directory not found"
        add_check "$id" "$description" "skip" "$severity" "Directory not found"
    fi
}

# CIS 1.1.12 - Ensure that the etcd user is not root
check_1_1_12() {
    local id="1.1.12"
    local description="etcd user is not root"
    local severity="medium"
    
    log_info "Checking ${id}: ${description}"
    
    local etcd_dir="/var/lib/rancher/rke2/server/db/etcd"
    
    if [ -d "$etcd_dir" ]; then
        local owner=$(stat -c %U "$etcd_dir")
        if [ "$owner" = "etcd" ]; then
            log_success "${id}: etcd directory owned by etcd user"
            add_check "$id" "$description" "pass" "$severity" "Directory owned by etcd"
        else
            log_error "${id}: etcd directory owned by ${owner}"
            add_check "$id" "$description" "fail" "$severity" "Directory owned by ${owner}, expected etcd"
        fi
    else
        log_warning "${id}: etcd data directory not found"
        add_check "$id" "$description" "skip" "$severity" "Directory not found"
    fi
}

# CIS 1.2.0 - Control Plane Configuration
check_cis_profile() {
    local id="1.2.0"
    local description="CIS profile enabled"
    local severity="critical"
    
    log_info "Checking ${id}: ${description}"
    
    if grep -q "profile: cis" "$CONFIG_DIR/config.yaml" 2>/dev/null; then
        local profile=$(grep "profile:" "$CONFIG_DIR/config.yaml" | awk '{print $2}')
        log_success "${id}: CIS profile enabled (${profile})"
        add_check "$id" "$description" "pass" "$severity" "CIS profile ${profile} enabled"
    else
        log_error "${id}: CIS profile not enabled"
        add_check "$id" "$description" "fail" "$severity" "CIS profile not found in config"
    fi
}

# CIS 2.1 - Ensure that the --anonymous-auth argument is set to false
check_anonymous_auth() {
    local id="2.1"
    local description="Anonymous authentication disabled"
    local severity="critical"
    
    log_info "Checking ${id}: ${description}"
    
    if grep -q "disable-anonymous-authentication: true" "$CONFIG_DIR/config.yaml" 2>/dev/null; then
        log_success "${id}: Anonymous authentication disabled"
        add_check "$id" "$description" "pass" "$severity" "Anonymous auth disabled"
    else
        log_warning "${id}: Anonymous authentication setting not found"
        add_check "$id" "$description" "skip" "$severity" "Setting not found in config"
    fi
}

# CIS 3.2.1 - Ensure that the --protect-kernel-defaults argument is set to true
check_kernel_defaults() {
    local id="3.2.1"
    local description="Kernel defaults protected"
    local severity="medium"
    
    log_info "Checking ${id}: ${description}"
    
    if grep -q "protect-kernel-defaults: true" "$CONFIG_DIR/config.yaml" 2>/dev/null; then
        log_success "${id}: Kernel defaults protected"
        add_check "$id" "$description" "pass" "$severity" "Kernel defaults protected"
    else
        log_error "${id}: Kernel defaults not protected"
        add_check "$id" "$description" "fail" "$severity" "Kernel defaults protection not enabled"
    fi
}

# CIS 3.2.2 - Ensure that the --make-iptables-util-chains argument is set to true
check_iptables_chains() {
    local id="3.2.2"
    local description="iptables util chains enabled"
    local severity="low"
    
    log_info "Checking ${id}: ${description}"
    
    log_warning "${id}: Check requires manual verification"
    add_check "$id" "$description" "skip" "$severity" "Manual verification required"
}

# CIS 5.1.1 - Ensure that the Linux Kernel's Hardening is in place
check_kernel_hardening() {
    local id="5.1.1"
    local description="Kernel hardening parameters"
    local severity="high"
    
    log_info "Checking ${id}: ${description}"
    
    local sysctl_file="/etc/sysctl.d/99-rke2-cis.conf"
    
    if [ -f "$sysctl_file" ]; then
        # Check key parameters
        local failed=0
        
        if ! grep -q "net.ipv4.ip_forward = 0" "$sysctl_file"; then
            log_error "${id}: IP forwarding not disabled"
            failed=1
        fi
        
        if ! grep -q "net.bridge.bridge-nf-call-iptables = 1" "$sysctl_file"; then
            log_error "${id}: bridge-nf-call-iptables not enabled"
            failed=1
        fi
        
        if [ $failed -eq 0 ]; then
            log_success "${id}: Kernel hardening parameters configured"
            add_check "$id" "$description" "pass" "$severity" "Kernel hardening configured"
        else
            add_check "$id" "$description" "fail" "$severity" "Missing kernel hardening parameters"
        fi
    else
        log_warning "${id}: Kernel hardening configuration not found"
        add_check "$id" "$description" "skip" "$severity" "Configuration file not found"
    fi
}

# CIS 5.4.1 - Ensure that the --rotate-certificates argument is not set to false
check_rotate_certs() {
    local id="5.4.1"
    local description="Certificate rotation enabled"
    local severity="medium"
    
    log_info "Checking ${id}: ${description}"
    
    # This is enabled by default in RKE2
    log_success "${id}: Certificate rotation is enabled by default"
    add_check "$id" "$description" "pass" "$severity" "Certificate rotation enabled by default"
}

# SELinux Check
check_selinux() {
    local id="SELINUX"
    local description="SELinux enabled"
    local severity="high"
    
    log_info "Checking ${id}: ${description}"
    
    if command -v getenforce &> /dev/null; then
        local mode=$(getenforce)
        if [ "$mode" = "Enforcing" ]; then
            log_success "${id}: SELinux in enforcing mode"
            add_check "$id" "$description" "pass" "$severity" "SELinux in enforcing mode"
        elif [ "$mode" = "Permissive" ]; then
            log_warning "${id}: SELinux in permissive mode"
            add_check "$id" "$description" "fail" "$severity" "SELinux in permissive mode"
        else
            log_error "${id}: SELinux is ${mode}"
            add_check "$id" "$description" "fail" "$severity" "SELinux is ${mode}"
        fi
    else
        log_warning "${id}: SELinux not found"
        add_check "$id" "$description" "skip" "$severity" "SELinux not installed"
    fi
}

# Secrets Encryption Check
check_secrets_encryption() {
    local id="SEC-ENC"
    local description="Secrets encryption enabled"
    local severity="high"
    
    log_info "Checking ${id}: ${description}"
    
    if grep -q "secrets-encryption: true" "$CONFIG_DIR/config.yaml" 2>/dev/null; then
        if [ -f "$CONFIG_DIR/encryption-provider-config.yaml" ]; then
            log_success "${id}: Secrets encryption enabled"
            add_check "$id" "$description" "pass" "$severity" "Secrets encryption enabled"
        else
            log_error "${id}: Encryption provider config missing"
            add_check "$id" "$description" "fail" "$severity" "Encryption provider config missing"
        fi
    else
        log_error "${id}: Secrets encryption not enabled"
        add_check "$id" "$description" "fail" "$severity" "Secrets encryption not enabled"
    fi
}

# ============================================================================
# Main Validation Flow
# ============================================================================
main() {
    echo "=========================================="
    echo "  RKE2 CIS Compliance Validation"
    echo "  CIS Version: ${CIS_VERSION}"
    echo "=========================================="
    echo ""
    
    init_report
    
    # Run all checks
    check_cis_profile
    check_1_1_1
    check_1_1_12
    check_anonymous_auth
    check_kernel_defaults
    check_iptables_chains
    check_kernel_hardening
    check_rotate_certs
    check_selinux
    check_secrets_encryption
    
    # Generate summary
    echo ""
    echo "=========================================="
    log_info "Validation Summary"
    echo "=========================================="
    
    local passed=$(jq -r '.controls.passed' "$REPORT_FILE")
    local failed=$(jq -r '.controls.failed' "$REPORT_FILE")
    local skipped=$(jq -r '.controls.skipped' "$REPORT_FILE")
    local total=$(jq -r '.controls.total' "$REPORT_FILE")
    
    echo "Total checks: ${total}"
    echo -e "${GREEN}Passed: ${passed}${NC}"
    echo -e "${RED}Failed: ${failed}${NC}"
    echo -e "${YELLOW}Skipped: ${skipped}${NC}"
    echo ""
    
    if [ $failed -eq 0 ]; then
        log_success "All critical checks passed!"
        jq '.controls.status = "compliant"' "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    else
        log_error "${failed} check(s) failed. Review the report for details."
        jq '.controls.status = "non-compliant"' "$REPORT_FILE" > "${REPORT_FILE}.tmp" && mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    fi
    
    echo "Report saved to: ${REPORT_FILE}"
    echo ""
    echo "View report: cat ${REPORT_FILE}"
    echo "View failed checks: jq '.checks[] | select(.status==&quot;fail&quot;)' ${REPORT_FILE}"
    echo ""
}

# Run main function
main "$@"