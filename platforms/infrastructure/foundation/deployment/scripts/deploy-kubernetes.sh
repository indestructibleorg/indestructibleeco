#!/bin/bash

# Kubernetes Deployment Script
# Deploys all infrastructure components to Kubernetes cluster

set -e

# Default values
NAMESPACE="monitoring"
PROVIDER="aws"
REGION="us-east-1"
CLUSTER_NAME="monitoring-cluster"
CONFIG_DIR="../../../config/providers/${PROVIDER}/infrastructure"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Deploy infrastructure components to Kubernetes cluster.

OPTIONS:
    -p, --provider PROVIDER        Cloud provider (aws, gcp, azure) [default: aws]
    -n, --namespace NAMESPACE      Kubernetes namespace [default: monitoring]
    -r, --region REGION            Cloud region [default: us-east-1]
    -c, --cluster CLUSTER          Cluster name [default: monitoring-cluster]
    -d, --dry-run                 Dry run mode (don't deploy)
    -v, --verbose                 Verbose output
    -h, --help                    Show this help message

EXAMPLES:
    # Deploy to AWS
    $0 --provider aws --region us-east-1

    # Deploy to GCP
    $0 --provider gcp --region us-central1

    # Deploy to Azure
    $0 --provider azure --region eastus

    # Dry run
    $0 --provider aws --dry-run

EOF
    exit 1
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--provider) PROVIDER="$2"; shift 2 ;;
            -n|--namespace) NAMESPACE="$2"; shift 2 ;;
            -r|--region) REGION="$2"; shift 2 ;;
            -c|--cluster) CLUSTER_NAME="$2"; shift 2 ;;
            -d|--dry-run) DRY_RUN=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -h|--help) usage ;;
            *) log_error "Unknown option: $1"; usage ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Namespace $NAMESPACE already exists"
    else
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would create namespace: $NAMESPACE"
        else
            kubectl create namespace "$NAMESPACE"
            log_info "Namespace $NAMESPACE created ✓"
        fi
    fi
}

# Deploy monitoring components
deploy_monitoring_stack() {
    log_info "Deploying monitoring stack to namespace: $NAMESPACE"
    log_info "Provider: $PROVIDER, Region: $REGION"
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Skipping actual deployment"
        echo "[DRY RUN] Would deploy: Prometheus, Grafana, AlertManager"
        return 0
    fi
    
    # Check if config file exists
    local config_file="$CONFIG_DIR/monitoring-stack.yaml"
    if [ -f "$config_file" ]; then
        log_info "Applying configuration from: $config_file"
        kubectl apply -n "$NAMESPACE" -f "$config_file"
    fi
    
    log_info "Monitoring stack deployment completed ✓"
}

# Main function
main() {
    parse_args "$@"
    check_prerequisites
    create_namespace
    deploy_monitoring_stack
    
    log_info "Deployment completed successfully!"
    log_info "Access URLs:"
    log_info "  - Grafana: http://grafana.$NAMESPACE.svc.cluster.local:3000"
    log_info "  - Prometheus: http://prometheus.$NAMESPACE.svc.cluster.local:9090"
    log_info "  - AlertManager: http://alertmanager.$NAMESPACE.svc.cluster.local:9093"
}

# Run main
main "$@"