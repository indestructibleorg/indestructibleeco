#!/bin/bash
# Periodic Vulnerability Scanning Script
# P0 Critical: Automated daily/weekly vulnerability scanning

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
SCAN_TYPE="${SCAN_TYPE:-daily}"  # daily or weekly
NAMESPACE="${NAMESPACE:-default}"
REGISTRY="${REGISTRY:-ghcr.io/superai-platform}"

log_info "Starting Periodic Vulnerability Scan - ${SCAN_TYPE}"
log_info "Namespace: $NAMESPACE"

# Check for required tools
check_tools() {
    log_step "Checking required tools..."
    
    for tool in trivy kube-bench kube-hunter; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool not found"
            exit 1
        fi
    done
    
    log_info "All required tools found"
}

# Scan container images
scan_images() {
    log_step "Scanning container images..."
    
    kubectl get pods -n "$NAMESPACE" -o json | \
    jq -r '.items[].spec.containers[].image' | \
    sort -u | while read image; do
        log_info "Scanning image: $image"
        
        trivy image --severity HIGH,CRITICAL \
            --format json \
            --output /tmp/trivy-$(echo $image | sed 's/[\/:]/_/g').json \
            "$image" || true
        
        local critical=$(jq '.Results[0].Vulnerabilities[]? | select(.Severity=="CRITICAL") | length' /tmp/trivy-$(echo $image | sed 's/[\/:]/_/g').json | awk '{s+=$1} END {print s+0}')
        local high=$(jq '.Results[0].Vulnerabilities[]? | select(.Severity=="HIGH") | length' /tmp/trivy-$(echo $image | sed 's/[\/:]/_/g').json | awk '{s+=$1} END {print s+0}')
        
        log_info "  CRITICAL: $critical"
        log_info "  HIGH: $high"
    done
}

# Run Kube-Bench for CIS compliance
run_kube_bench() {
    log_step "Running Kube-Bench for CIS compliance..."
    
    if [ "$SCAN_TYPE" == "weekly" ]; then
        kube-bench --json > /tmp/kube-bench.json
        
        local passed=$(jq '.total_pass' /tmp/kube-bench.json)
        local failed=$(jq '.total_fail' /tmp/kube-bench.json)
        local warn=$(jq '.total_warn' /tmp/kube-bench.json)
        
        log_info "CIS Benchmark Results:"
        log_info "  Passed: $passed"
        log_info "  Failed: $failed"
        log_info "  Warnings: $warn"
    fi
}

# Run Kube-Hunter for penetration testing
run_kube_hunter() {
    log_step "Running Kube-Hunter..."
    
    if [ "$SCAN_TYPE" == "weekly" ]; then
        kube-hunter --pod --report json --output /tmp/kube-hunter.json || true
        
        local vulnerabilities=$(jq '.vulnerabilities | length' /tmp/kube-hunter.json || echo 0)
        log_info "Kube-Hunter found $vulnerabilities vulnerabilities"
    fi
}

# Scan Kubernetes configurations
scan_k8s_configs() {
    log_step "Scanning Kubernetes configurations..."
    
    kubectl config view --minify --raw > /tmp/kube-config.yaml
    
    # Check for insecure configurations
    if grep -q "insecure-skip-tls-verify: true" /tmp/kube-config.yaml; then
        log_warn "Insecure TLS verification found in kubeconfig"
    fi
}

# Generate scan report
generate_report() {
    log_step "Generating scan report..."
    
    local report_dir="./reports/vulnerability-scans/$(date +%Y/%m/%d)"
    mkdir -p "$report_dir"
    
    cat > "${report_dir}/${SCAN_TYPE}-scan-$(date +%H%M%S).md" << EOF
# Vulnerability Scan Report - $(date +%Y-%m-%d)

## Scan Type: ${SCAN_TYPE}
## Namespace: $NAMESPACE

## Summary

EOF
    
    log_info "Scan report generated: ${report_dir}/${SCAN_TYPE}-scan-$(date +%H%M%S).md"
}

# Send metrics to Prometheus
send_metrics() {
    log_step "Sending metrics..."
    
    local total_critical=0
    local total_high=0
    
    for file in /tmp/trivy-*.json; do
        total_critical=$((total_critical + $(jq '.Results[0].Vulnerabilities[]? | select(.Severity=="CRITICAL") | length' $file | awk '{s+=$1} END {print s+0}')))
        total_high=$((total_high + $(jq '.Results[0].Vulnerabilities[]? | select(.Severity=="HIGH") | length' $file | awk '{s+=$1} END {print s+0}')))
    done
    
    cat <<EOF | curl --data-binary @- http://pushgateway.monitoring.svc.cluster.local:9091/metrics/job/vulnerability_scan
# HELP vulnerability_scan_critical Total CRITICAL vulnerabilities
# TYPE vulnerability_scan_critical gauge
vulnerability_scan_critical ${total_critical}

# HELP vulnerability_scan_high Total HIGH vulnerabilities
# TYPE vulnerability_scan_high gauge
vulnerability_scan_high ${total_high}
EOF
    
    log_info "Metrics sent to Prometheus"
}

# Main execution
main() {
    check_tools
    scan_images
    run_kube_bench
    run_kube_hunter
    scan_k8s_configs
    generate_report
    send_metrics
    
    log_info "Periodic vulnerability scan completed"
}

main "$@"