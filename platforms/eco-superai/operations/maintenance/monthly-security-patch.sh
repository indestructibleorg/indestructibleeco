#!/bin/bash
# Monthly Security Patch Automation Script
# P0 Critical: Automated security patching for dependencies and base images

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
PATCH_WINDOW="${PATCH_WINDOW:-$(date +%Y-%m-01) 02:00-06:00}"
DRY_RUN="${DRY_RUN:-false}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"
SEVERITY_THRESHOLD="${SEVERITY_THRESHOLD:-HIGH}"

log_info "Starting Monthly Security Patch Automation"
log_info "Patch window: ${PATCH_WINDOW}"
log_info "Severity threshold: ${SEVERITY_THRESHOLD}"

# Check for required tools
check_tools() {
    log_step "Checking required tools..."
    
    for tool in python3 docker trivy safety; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool not found"
            exit 1
        fi
    done
    
    log_info "All required tools found"
}

# Scan Python dependencies for vulnerabilities
scan_python_deps() {
    log_step "Scanning Python dependencies..."
    
    # Safety scan
    log_info "Running safety scan..."
    safety check --json > /tmp/safety-report.json || true
    
    # Count vulnerabilities
    local critical=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "critical")] | length' || echo 0)
    local high=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "high")] | length' || echo 0)
    local medium=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "medium")] | length' || echo 0)
    local low=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "low")] | length' || echo 0)
    
    log_info "Vulnerabilities found:"
    log_info "  Critical: $critical"
    log_info "  High: $high"
    log_info "  Medium: $medium"
    log_info "  Low: $low"
    
    # Report vulnerabilities
    if [ $((critical + high)) -gt 0 ]; then
        log_warn "Critical/High vulnerabilities found - immediate attention required"
    fi
}

# Scan Docker images for vulnerabilities
scan_docker_images() {
    log_step "Scanning Docker images..."
    
    local images=(
        "python:3.11-slim"
        "alpine:3.19"
        "ubuntu:22.04"
    )
    
    for image in "${images[@]}"; do
        log_info "Scanning image: $image"
        
        trivy image --severity CRITICAL,HIGH \
            --format json \
            --output /tmp/trivy-$(echo $image | tr '/' '-').json \
            "$image" || true
        
        local vulnerabilities=$(cat /tmp/trivy-$(echo $image | tr '/' '-').json | jq '.Results[0].Vulnerabilities | length' || echo 0)
        log_info "  Vulnerabilities: $vulnerabilities"
    done
}

# Update Python dependencies
update_python_deps() {
    log_step "Updating Python dependencies..."
    
    # Check for updates
    log_info "Checking for outdated packages..."
    pip list --outdated --format=json > /tmp/outdated.json
    
    # Update security-critical packages
    log_info "Updating security-critical packages..."
    pip install --upgrade pip setuptools wheel
    pip install --upgrade $(cat pyproject.toml | grep -A 100 'dependencies =' | grep -E '^\s+"' | sed 's/.*"\(.*\)==.*/\1/' | tr '\n' ' ')
    
    log_info "Python dependencies updated"
}

# Update base Docker images
update_base_images() {
    log_step "Updating base Docker images..."
    
    docker pull python:3.11-slim
    docker pull alpine:3.19
    docker pull ubuntu:22.04
    
    log_info "Base images updated"
}

# Update Kubernetes components
update_k8s_components() {
    log_step "Updating Kubernetes components..."
    
    if [ -f "helm/Chart.yaml" ]; then
        log_info "Updating Helm dependencies..."
        helm dependency update helm/
    fi
    
    log_info "Kubernetes components updated"
}

# Create patch report
create_patch_report() {
    log_step "Creating patch report..."
    
    local report_file="./reports/security-patch-$(date +%Y%m%d).md"
    mkdir -p ./reports
    
    cat > "$report_file" << EOF
# Security Patch Report - $(date +%Y-%m-%d)

## Summary
- Date: $(date +%Y-%m-%d)
- Patch Window: ${PATCH_WINDOW}
- Severity Threshold: ${SEVERITY_THRESHOLD}

## Python Dependencies
EOF
    
    cat /tmp/safety-report.json | jq -r '.[] | "- \(.package): \(.id) - \(.severity)"' >> "$report_file"
    
    cat >> "$report_file" << EOF

## Docker Images
EOF
    
    cat /tmp/trivy-python-3.11-slim.json | jq -r '.Results[0].Vulnerabilities[]? | "- \(.TargetID): \(.VulnerabilityID) - \(.Severity)"' >> "$report_file"
    
    log_info "Patch report created: $report_file"
}

# Send metrics to Prometheus
send_metrics() {
    log_step "Sending metrics..."
    
    local critical=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "critical")] | length' || echo 0)
    local high=$(cat /tmp/safety-report.json | jq '[.[] | select(.severity == "high")] | length' || echo 0)
    
    cat <<EOF | curl --data-binary @- http://pushgateway.monitoring.svc.cluster.local:9091/metrics/job/security_patch
# HELP security_vulnerabilities_critical Number of CRITICAL vulnerabilities
# TYPE security_vulnerabilities_critical gauge
security_vulnerabilities_critical ${critical}

# HELP security_vulnerabilities_high Number of HIGH vulnerabilities
# TYPE security_vulnerabilities_high gauge
security_vulnerabilities_high ${high}
EOF
    
    log_info "Metrics sent to Prometheus"
}

# Main execution
main() {
    check_tools
    scan_python_deps
    scan_docker_images
    
    if [ "$DRY_RUN" != "true" ]; then
        update_python_deps
        update_base_images
        update_k8s_components
    fi
    
    create_patch_report
    send_metrics
    
    log_info "Monthly security patch completed"
}

main "$@"