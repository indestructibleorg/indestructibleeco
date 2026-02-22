#!/bin/bash
set -euo pipefail

# IndestructibleEco OAuth Consent Screen Configuration Script
# Guides through OAuth consent screen setup in GCP Console

ECO_SCRIPT_VERSION="1.0.0"
ECO_SCRIPT_NAME="configure-oauth-consent"

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

# Open OAuth consent screen configuration
open_oauth_config() {
    log_step "Opening OAuth consent screen configuration..."
    
    log_info "Opening GCP Console for OAuth consent screen setup..."
    log_info "Please follow these steps:"
    echo ""
    echo "1. The browser will open the OAuth consent screen page"
    echo "2. Select 'External' user type (for production)"
    echo "3. Click 'Create'"
    echo "4. Fill in required information:"
    echo "   - App name: IndestructibleEco"
    echo "   - User support email: your-email@indestructibleeco.io"
    echo "   - Developer contact: your-email@indestructibleeco.io"
    echo "5. Add required scopes:"
    echo "   - openid"
    echo "   - email"
    echo "   - profile"
    echo "6. Save and continue"
    echo "7. Add test users (if using External user type)"
    echo "8. Submit for verification (if required)"
    echo ""
    
    local oauth_url="https://console.cloud.google.com/apis/credentials/consent?project=my-project-ops-1991"
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "$oauth_url" 2>/dev/null || log_warn "Could not open browser automatically"
    elif command -v open &> /dev/null; then
        open "$oauth_url" 2>/dev/null || log_warn "Could not open browser automatically"
    else
        log_warn "Could not open browser automatically"
        log_info "Please open this URL manually: $oauth_url"
    fi
    
    log_info "URL: $oauth_url"
}

# Verify OAuth configuration
verify_oauth_config() {
    log_step "Verifying OAuth configuration..."
    
    log_info "To verify OAuth configuration later, run:"
    echo "  gcloud auth application-default login"
    echo "  gcloud iam service-accounts list"
    echo ""
    log_info "Required OAuth scopes:"
    echo "  - openid"
    echo "  - email"
    echo "  - profile"
}

# Main execution
main() {
    log_info "Starting OAuth consent screen configuration"
    log_info "Script version: $ECO_SCRIPT_VERSION"
    echo ""
    
    check_gcloud
    check_auth
    set_project
    open_oauth_config
    verify_oauth_config
    
    echo ""
    log_info "OAuth consent screen configuration process initiated"
    log_warn "Please complete the configuration in the GCP Console"
    log_info "After configuration, OAuth authentication will be enabled"
}

main "$@"