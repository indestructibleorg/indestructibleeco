#!/bin/bash
# @GL-governed
# @GL-layer: GL90-95 (Deployment Layer)
# @GL-semantic: automated-integration-setup
# @GL-charter-version: 5.0.0
# @GL-audit-trail: Created for GL Platform v5.0 deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_NAMESPACE="gl-platform"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if ! command -v yq &> /dev/null; then
        missing_tools+=("yq")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools and try again"
        exit 1
    fi
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $DEPLOYMENT_NAMESPACE"
    
    if kubectl get namespace "$DEPLOYMENT_NAMESPACE" &> /dev/null; then
        log_warning "Namespace $DEPLOYMENT_NAMESPACE already exists"
    else
        kubectl create namespace "$DEPLOYMENT_NAMESPACE"
        log_success "Namespace $DEPLOYMENT_NAMESPACE created"
    fi
}

# Deploy Alertmanager configuration
deploy_alertmanager_config() {
    log_info "Deploying Alertmanager configuration..."
    
    local config_file="$REPO_ROOT/deploy/platform/alertmanager/config.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Alertmanager config not found: $config_file"
        return 1
    fi
    
    kubectl apply -f "$config_file"
    log_success "Alertmanager configuration deployed"
}

# Deploy Prometheus rules
deploy_prometheus_rules() {
    log_info "Deploying Prometheus rules..."
    
    local rules_dir="$REPO_ROOT/observability/alerts/prometheus-rules"
    
    if [[ ! -d "$rules_dir" ]]; then
        log_warning "Prometheus rules directory not found: $rules_dir"
        return 0
    fi
    
    # Apply all rule files
    for rule_file in "$rules_dir"/*.yaml; do
        if [[ -f "$rule_file" ]]; then
            log_info "  Applying $(basename "$rule_file")"
            kubectl apply -f "$rule_file"
        fi
    done
    
    log_success "Prometheus rules deployed"
}

# Create integration secrets from config files
create_integration_secrets() {
    log_info "Creating integration secrets..."
    
    local integrations=("slack" "pagerduty" "prometheus")
    
    for integration in "${integrations[@]}"; do
        local config_file="$REPO_ROOT/integrations/$integration/config.yaml"
        local example_file="$REPO_ROOT/integrations/$integration/config.example.yaml"
        
        # Use config.yaml if exists, otherwise use example
        local actual_config="$config_file"
        if [[ ! -f "$config_file" ]]; then
            if [[ -f "$example_file" ]]; then
                log_warning "Using example config for $integration (please create actual config.yaml)"
                actual_config="$example_file"
            else
                log_warning "No config found for $integration, skipping"
                continue
            fi
        fi
        
        # Create secret from config
        local secret_name="gl-platform-${integration}-config"
        
        kubectl create secret generic "$secret_name" \
            --namespace="$DEPLOYMENT_NAMESPACE" \
            --from-file=config.yaml="$actual_config" \
            --dry-run=client -o yaml | \
            kubectl apply -f -
        
        log_success "Secret $secret_name created/updated"
    done
}

# Deploy Grafana dashboards
deploy_grafana_dashboards() {
    log_info "Deploying Grafana dashboards..."
    
    local dashboards_dir="$REPO_ROOT/observability/dashboards"
    
    if [[ ! -d "$dashboards_dir" ]]; then
        log_warning "Grafana dashboards directory not found: $dashboards_dir"
        return 0
    fi
    
    # Create configmap for dashboards
    local configmap_name="gl-platform-grafana-dashboards"
    
    kubectl create configmap "$configmap_name" \
        --namespace="$DEPLOYMENT_NAMESPACE" \
        --from-file="$dashboards_dir/" \
        --dry-run=client -o yaml | \
        kubectl apply -f -
    
    log_success "Grafana dashboards configmap created"
}

# Create service accounts and RBAC
create_service_accounts() {
    log_info "Creating service accounts and RBAC..."
    
    # Service account for platform components
    kubectl create serviceaccount gl-platform-bot \
        --namespace="$DEPLOYMENT_NAMESPACE" \
        --dry-run=client -o yaml | \
        kubectl apply -f -
    
    # Cluster role for read access
    kubectl create clusterrole gl-platform-read \
        --verb=get,list,watch \
        --resource=pods,services,deployments,statefulsets,daemonsets,configmaps,secrets,ingresses \
        --dry-run=client -o yaml | \
        kubectl apply -f -
    
    # Cluster role binding
    kubectl create clusterrolebinding gl-platform-read-binding \
        --clusterrole=gl-platform-read \
        --serviceaccount="$DEPLOYMENT_NAMESPACE:gl-platform-bot" \
        --dry-run=client -o yaml | \
        kubectl apply -f -
    
    log_success "Service accounts and RBAC created"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    local validation_passed=true
    
    # Check namespace exists
    if ! kubectl get namespace "$DEPLOYMENT_NAMESPACE" &> /dev/null; then
        log_error "Namespace $DEPLOYMENT_NAMESPACE not found"
        validation_passed=false
    fi
    
    # Check configmaps
    local expected_configmaps=(
        "alertmanager-config"
        "gl-platform-grafana-dashboards"
    )
    
    for cm in "${expected_configmaps[@]}"; do
        if kubectl get configmap "$cm" -n "$DEPLOYMENT_NAMESPACE" &> /dev/null; then
            log_success "ConfigMap $cm found"
        else
            log_warning "ConfigMap $cm not found"
        fi
    done
    
    # Check secrets
    local expected_secrets=(
        "gl-platform-slack-config"
        "gl-platform-pagerduty-config"
        "gl-platform-prometheus-config"
    )
    
    for secret in "${expected_secrets[@]}"; do
        if kubectl get secret "$secret" -n "$DEPLOYMENT_NAMESPACE" &> /dev/null; then
            log_success "Secret $secret found"
        else
            log_warning "Secret $secret not found (may be using example configs)"
        fi
    done
    
    # Check Prometheus rules
    local rule_count=$(kubectl get prometheusrule -n "$DEPLOYMENT_NAMESPACE" --no-headers 2>/dev/null | wc -l || echo "0")
    log_info "Found $rule_count PrometheusRule resources in $DEPLOYMENT_NAMESPACE"
    
    if $validation_passed; then
        log_success "Deployment validation passed"
    else
        log_warning "Deployment validation completed with warnings"
    fi
}

# Print next steps
print_next_steps() {
    cat << EOF

${GREEN}=== GL Platform Integration Setup Complete ===${NC}

${BLUE}Next Steps:${NC}

1. ${YELLOW}Configure Integration Secrets${NC}
   Edit the following files with your actual credentials:
   - integrations/slack/config.yaml
   - integrations/pagerduty/config.yaml
   - integrations/prometheus/config.yaml
   
   Then run this script again to apply the configurations.

2. ${YELLOW}Test Integrations${NC}
   - Send test message to Slack webhook
   - Trigger test alert to PagerDuty
   - Verify Prometheus targets are up

3. ${YELLOW}Run Discovery${NC}
   ./scripts/discovery/cluster-discovery.sh
   ./scripts/discovery/naming-audit.sh

4. ${YELLOW}Import Grafana Dashboards${NC}
   Access Grafana and import dashboards from:
   - observability/dashboards/naming-compliance.json
   - observability/dashboards/ops-sla-overview.json

5. ${YELLOW}Monitor Platform${NC}
   - Check Alertmanager: https://alertmanager.machinenativeops.io
   - Check Grafana: https://grafana.machinenativeops.io
   - Check Prometheus: https://prometheus.machinenativeops.io

${BLUE}Documentation:${NC}
- Migration Guide: docs/MIGRATION/PLATFORM-MIGRATION-GUIDE.md
- Training Handbook: docs/TRAINING/GL-PLATFORM-HANDBOOK.md
- Naming Playbook: docs/RUNBOOKS/naming-migration-playbook.md

${GREEN}Setup complete!${NC}

EOF
}

# Main execution
main() {
    log_info "Starting GL Platform Integration Setup..."
    
    check_prerequisites
    create_namespace
    create_service_accounts
    deploy_alertmanager_config
    deploy_prometheus_rules
    create_integration_secrets
    deploy_grafana_dashboards
    validate_deployment
    
    print_next_steps
    
    log_success "GL Platform Integration Setup completed successfully!"
}

# Run main function
main "$@"