#!/bin/bash
set -euo pipefail

# IndestructibleEco GCP SSD Quota Increase Request Script
# Automates quota increase request for eco-production cluster

ECO_SCRIPT_VERSION="1.0.0"
ECO_SCRIPT_NAME="setup-gcp-quota"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed"
        log_info "Install it with: curl https://sdk.cloud.google.com | bash"
        exit 1
    fi
    
    local version=$(gcloud --version | head -n 1)
    log_info "gcloud version: $version"
}

# Check authentication
check_auth() {
    log_step "Checking GCP authentication..."
    
    local account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
    
    if [[ -z "$account" ]]; then
        log_error "Not authenticated to GCP"
        log_info "Run: gcloud auth login"
        exit 1
    fi
    
    log_info "Authenticated as: $account"
}

# Set project
set_project() {
    log_step "Setting GCP project..."
    
    local project_id="my-project-ops-1991"
    
    gcloud config set project "$project_id"
    log_info "Project set to: $project_id"
}

# Check current quota
check_current_quota() {
    log_step "Checking current SSD quota in asia-east1..."
    
    local quota_output=$(gcloud compute regions describe asia-east1 \
        --format="json(quotas)" \
        --filter="quotas.metric='SSD_TOTAL_STORAGE_GB'" 2>/dev/null || echo "{}")
    
    local current_limit=$(echo "$quota_output" | jq -r '.quotas[0].limit // "N/A"')
    local current_usage=$(echo "$quota_output" | jq -r '.quotas[0].usage // "N/A"')
    
    log_info "Current SSD quota limit: $current_limit GB"
    log_info "Current SSD quota usage: $current_usage GB"
    
    if [[ "$current_limit" == "N/A" ]]; then
        log_error "Failed to retrieve quota information"
        exit 1
    fi
}

# Request quota increase
request_quota_increase() {
    log_step "Requesting SSD quota increase..."
    
    log_info "Opening GCP Console for quota request..."
    log_info "Please follow these steps:"
    echo ""
    echo "1. The browser will open the GCP Quotas page"
    echo "2. Filter by: Service = Compute Engine, Metric = SSD Total Storage"
    echo "3. Select asia-east1 region"
    echo "4. Click 'Edit Quotas'"
    echo "5. Request new limit: 500 GB"
    echo "6. Provide justification: 'Production cluster deployment for IndestructibleEco platform'"
    echo "7. Submit request"
    echo ""
    
    local quota_url="https://console.cloud.google.com/iam-admin/quotas?project=my-project-ops-1991"
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "$quota_url" 2>/dev/null || log_warn "Could not open browser automatically"
    elif command -v open &> /dev/null; then
        open "$quota_url" 2>/dev/null || log_warn "Could not open browser automatically"
    else
        log_warn "Could not open browser automatically"
        log_info "Please open this URL manually: $quota_url"
    fi
    
    log_info "URL: $quota_url"
}

# Monitor quota status
monitor_quota_status() {
    log_step "Monitoring quota status..."
    
    log_info "To check quota status later, run:"
    echo "  gcloud compute regions describe asia-east1 --format='json(quotas)' --filter=\"quotas.metric='SSD_TOTAL_STORAGE_GB'\""
    echo ""
    log_info "Expected quota after approval: 500 GB"
    log_info "Required for production cluster: ~200 GB"
}

# Main execution
main() {
    log_info "Starting GCP SSD quota increase request"
    log_info "Script version: $ECO_SCRIPT_VERSION"
    echo ""
    
    check_gcloud
    check_auth
    set_project
    check_current_quota
    request_quota_increase
    monitor_quota_status
    
    echo ""
    log_info "Quota request process initiated"
    log_warn "Please complete the request in the GCP Console"
    log_info "After approval, proceed with eco-production cluster recreation"
}

main "$@"