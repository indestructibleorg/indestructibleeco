#!/bin/bash
set -euo pipefail

# IndestructibleEco Supabase Edge Function Deployment Script
# Deploys hello-world function to Supabase

ECO_SCRIPT_VERSION="1.0.0"
ECO_SCRIPT_NAME="deploy-supabase-function"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check required environment variables
check_env() {
    if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
        log_error "SUPABASE_PROJECT_REF environment variable is required"
        log_info "Set it with: export SUPABASE_PROJECT_REF=your-project-ref"
        exit 1
    fi
    
    if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
        log_error "SUPABASE_ACCESS_TOKEN environment variable is required"
        log_info "Set it with: export SUPABASE_ACCESS_TOKEN=your-access-token"
        exit 1
    fi
}

# Check if Supabase CLI is installed
check_cli() {
    if ! command -v supabase &> /dev/null; then
        log_error "Supabase CLI is not installed"
        log_info "Install it with: npm install -g supabase"
        exit 1
    fi
    
    local version=$(supabase --version)
    log_info "Supabase CLI version: $version"
}

# Deploy function
deploy_function() {
    local function_name="hello-world"
    local function_dir="supabase/functions/$function_name"
    
    if [[ ! -d "$function_dir" ]]; then
        log_error "Function directory not found: $function_dir"
        exit 1
    fi
    
    log_info "Deploying function: $function_name"
    
    cd "$function_dir"
    
    # Deploy function with JWT verification enabled
    supabase functions deploy "$function_name" \
        --project-ref "$SUPABASE_PROJECT_REF"
    
    if [[ $? -eq 0 ]]; then
        log_info "Function deployed successfully"
        
        # Get function URL
        local function_url="https://${SUPABASE_PROJECT_REF}.supabase.co/functions/v1/${function_name}"
        log_info "Function URL: $function_url"
        
        # Test deployment
        log_info "Testing deployment..."
        sleep 2
        
        curl -X POST "$function_url" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${SUPABASE_ANON_KEY:-}" \
            -d '{"name": "DeployTest"}' \
            --fail --silent --show-error || {
            log_warn "Function test failed (may need JWT verification)"
        }
    else
        log_error "Function deployment failed"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting Supabase Edge Function deployment"
    log_info "Script version: $ECO_SCRIPT_VERSION"
    
    check_env
    check_cli
    deploy_function
    
    log_info "Deployment completed successfully"
}

main "$@"