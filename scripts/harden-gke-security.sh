#!/bin/bash
set -euo pipefail

# IndestructibleEco GKE Security Hardening Script
# Removes 0.0.0.0/0 from master authorized networks

ECO_SCRIPT_VERSION="1.0.0"
ECO_SCRIPT_NAME="harden-gke-security"

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

# Check current authorized networks
check_authorized_networks() {
    log_step "Checking current master authorized networks..."
    
    local cluster_name="eco-staging"
    local region="asia-east1"
    
    local networks=$(gcloud container clusters describe "$cluster_name" \
        --region="$region" \
        --format="value(masterAuthorizedNetworks.cidrBlocks)" 2>/dev/null || echo "")
    
    if [[ -z "$networks" ]]; then
        log_warn "No master authorized networks configured"
        return
    fi
    
    log_info "Current authorized networks:"
    echo "$networks" | while read -r network; do
        if [[ "$network" == *"0.0.0.0/0"* ]]; then
            log_warn "  ⚠️  $network (INSECURE - allows all IPs)"
        else
            log_info "  ✓  $network"
        fi
    done
}

# Remove 0.0.0.0/0 from authorized networks
remove_insecure_networks() {
    log_step "Removing 0.0.0.0/0 from master authorized networks..."
    
    local cluster_name="eco-staging"
    local region="asia-east1"
    
    log_warn "This will remove 0.0.0.0/0 from authorized networks"
    log_warn "Make sure you have added your current IP before proceeding"
    echo ""
    
    read -p "Do you want to continue? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
    
    # Get current networks excluding 0.0.0.0/0
    local current_networks=$(gcloud container clusters describe "$cluster_name" \
        --region="$region" \
        --format="json(masterAuthorizedNetworks.cidrBlocks)" 2>/dev/null || echo "[]")
    
    local filtered_networks=$(echo "$current_networks" | \
        jq -r '.[] | select(. != "0.0.0.0/0")' | \
        paste -sd ',' -)
    
    if [[ -z "$filtered_networks" ]]; then
        log_warn "No networks will remain after removing 0.0.0.0/0"
        log_warn "This will disable master authorized networks entirely"
        echo ""
        
        read -p "Do you want to disable master authorized networks? (yes/no): " confirm_disable
        
        if [[ "$confirm_disable" != "yes" ]]; then
            log_info "Operation cancelled"
            exit 0
        fi
        
        # Disable master authorized networks
        gcloud container clusters update "$cluster_name" \
            --region="$region" \
            --no-enable-master-authorized-networks
        
        log_info "Master authorized networks disabled"
    else
        # Update with filtered networks
        gcloud container clusters update "$cluster_name" \
            --region="$region" \
            --enable-master-authorized-networks \
            --master-authorized-networks="$filtered_networks"
        
        log_info "Master authorized networks updated"
    fi
}

# Add current IP to authorized networks
add_current_ip() {
    log_step "Adding current IP to authorized networks..."
    
    local cluster_name="eco-staging"
    local region="asia-east1"
    
    # Get current public IP
    local current_ip=$(curl -s https://api.ipify.org || echo "")
    
    if [[ -z "$current_ip" ]]; then
        log_error "Failed to determine current IP"
        exit 1
    fi
    
    log_info "Current public IP: $current_ip"
    
    # Get current networks
    local current_networks=$(gcloud container clusters describe "$cluster_name" \
        --region="$region" \
        --format="json(masterAuthorizedNetworks.cidrBlocks)" 2>/dev/null || echo "[]")
    
    # Add current IP
    local updated_networks=$(echo "$current_networks" | \
        jq --arg ip "$current_ip/32" '. + [$ip] | unique')
    
    # Update cluster
    local networks_str=$(echo "$updated_networks" | jq -r 'join(",")')
    
    gcloud container clusters update "$cluster_name" \
        --region="$region" \
        --enable-master-authorized-networks \
        --master-authorized-networks="$networks_str"
    
    log_info "Current IP added to authorized networks"
}

# Verify changes
verify_changes() {
    log_step "Verifying security hardening..."
    
    local cluster_name="eco-staging"
    local region="asia-east1"
    
    local networks=$(gcloud container clusters describe "$cluster_name" \
        --region="$region" \
        --format="value(masterAuthorizedNetworks.cidrBlocks)" 2>/dev/null || echo "")
    
    if [[ "$networks" == *"0.0.0.0/0"* ]]; then
        log_error "Security hardening failed: 0.0.0.0/0 still present"
        exit 1
    fi
    
    log_info "✓ Security hardening successful"
    log_info "✓ 0.0.0.0/0 removed from authorized networks"
    
    if [[ -n "$networks" ]]; then
        log_info "Current authorized networks:"
        echo "$networks" | while read -r network; do
            log_info "  - $network"
        done
    else
        log_warn "Master authorized networks disabled"
    fi
}

# Main execution
main() {
    log_info "Starting GKE security hardening"
    log_info "Script version: $ECO_SCRIPT_VERSION"
    echo ""
    
    check_gcloud
    check_auth
    set_project
    check_authorized_networks
    
    echo ""
    log_info "Choose an option:"
    echo "  1. Add current IP to authorized networks (recommended first)"
    echo "  2. Remove 0.0.0.0/0 from authorized networks"
    echo "  3. Both: Add current IP and remove 0.0.0.0/0"
    echo "  4. Exit"
    echo ""
    
    read -p "Enter option (1-4): " option
    
    case "$option" in
        1)
            add_current_ip
            verify_changes
            ;;
        2)
            remove_insecure_networks
            verify_changes
            ;;
        3)
            add_current_ip
            remove_insecure_networks
            verify_changes
            ;;
        4)
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "Security hardening completed successfully"
    log_warn "Remember to add IPs for all administrators and CI/CD systems"
}

main "$@"