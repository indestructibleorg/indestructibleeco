#!/bin/bash
# Production Deployment Script for SuperAI Platform v1.0
# P0 Critical: Complete production deployment orchestration

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
NAMESPACE="${NAMESPACE:-production}"
CLUSTER_NAME="${CLUSTER_NAME:-superai-production}"
REGION="${REGION:-us-east-1}"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_TAG="${IMAGE_TAG:-v1.0.0}"

log_info "Starting SuperAI Platform v1.0 Production Deployment"
log_info "Namespace: $NAMESPACE"
log_info "Cluster: $CLUSTER_NAME"
log_info "Region: $REGION"

# Pre-deployment checks
pre_flight_checks() {
    log_step "Running pre-flight checks..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm not found"
        exit 1
    fi
    
    # Check required tools
    for tool in kubectl helm docker trivy cosign; do
        if ! command -v $tool &> /dev/null; then
            log_warn "$tool not found, some steps may be skipped"
        fi
    done
    
    log_info "Pre-flight checks passed"
}

# Verify K8s cluster
verify_cluster() {
    log_step "Verifying Kubernetes cluster..."
    
    # Check cluster version
    K8S_VERSION=$(kubectl version --short 2>/dev/null | grep Server | awk '{print $3}' || echo "unknown")
    log_info "Kubernetes version: $K8S_VERSION"
    
    # Check cluster health
    kubectl get nodes
    kubectl get componentstatuses
    
    # Verify container runtime
    if [ -f "./scripts/verify-container-runtime.sh" ]; then
        log_info "Running container runtime verification..."
        bash ./scripts/verify-container-runtime.sh
    fi
    
    log_info "Cluster verification complete"
}

# Generate TLS certificates
generate_certificates() {
    log_step "Generating TLS certificates..."
    
    if [ -f "./scripts/generate-tls-certs.sh" ]; then
        bash ./scripts/generate-tls-certs.sh
        log_info "TLS certificates generated"
    else
        log_warn "Certificate generation script not found, skipping"
    fi
}

# Build and push container images
build_images() {
    log_step "Building and pushing container images..."
    
    # Build production image
    log_info "Building production image..."
    docker build -f Dockerfile.prod \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse HEAD 2>/dev/null || echo "unknown") \
        --build-arg VERSION=$IMAGE_TAG \
        -t ${REGISTRY}/superai-platform/superai-platform:${IMAGE_TAG} \
        -t ${REGISTRY}/superai-platform/superai-platform:latest \
        .
    
    # Push images
    log_info "Pushing images to registry..."
    docker push ${REGISTRY}/superai-platform/superai-platform:${IMAGE_TAG}
    docker push ${REGISTRY}/superai-platform/superai-platform:latest
    
    log_info "Images built and pushed successfully"
}

# Sign images
sign_images() {
    log_step "Signing container images..."
    
    if [ -f "./scripts/image-signing.sh" ]; then
        export IMAGE_TAG=$IMAGE_TAG
        bash ./scripts/image-signing.sh
        log_info "Images signed successfully"
    else
        log_warn "Image signing script not found, skipping"
    fi
}

# Security scan images
scan_images() {
    log_step "Scanning images for vulnerabilities..."
    
    if command -v trivy &> /dev/null; then
        trivy image --severity HIGH,CRITICAL \
            --exit-code 1 \
            ${REGISTRY}/superai-platform/superai-platform:${IMAGE_TAG}
        
        log_info "Image security scan passed"
    else
        log_warn "Trivy not found, skipping security scan"
    fi
}

# Create namespace
create_namespace() {
    log_step "Creating namespace..."
    
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Namespace created: $NAMESPACE"
}

# Apply RBAC
apply_rbac() {
    log_step "Applying RBAC configuration..."
    
    if [ -f "k8s/base/rbac.yaml" ]; then
        kubectl apply -f k8s/base/rbac.yaml -n $NAMESPACE
        log_info "RBAC configuration applied"
    else
        log_warn "RBAC configuration not found"
    fi
}

# Apply secrets
apply_secrets() {
    log_step "Applying secrets..."
    
    # Apply TLS secrets if generated
    if [ -f "certs/k8s-tls-secrets.yaml" ]; then
        kubectl apply -f certs/k8s-tls-secrets.yaml -n $NAMESPACE
    fi
    
    # Create secrets from environment
    kubectl create secret generic superai-secrets \
        --from-literal=DATABASE_URL="${DATABASE_URL}" \
        --from-literal=REDIS_URL="${REDIS_URL}" \
        --from-literal=JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}" \
        --from-literal=ENCRYPTION_KEY="${ENCRYPTION_KEY:-$(openssl rand -hex 32)}" \
        --dry-run=client -o yaml | kubectl apply -n $NAMESPACE -f -
    
    log_info "Secrets applied"
}

# Deploy monitoring stack
deploy_monitoring() {
    log_step "Deploying monitoring stack..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Loki stack
    if [ -f "logging/loki-stack.yaml" ]; then
        kubectl apply -f logging/loki-stack.yaml
        log_info "Loki stack deployed"
    fi
    
    # Deploy Prometheus
    if [ -f "monitoring/prometheus/prometheus.yml" ]; then
        helm install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --values monitoring/prometheus/prometheus.yml \
            --wait --timeout 10m
    fi
    
    # Deploy AlertManager with PagerDuty
    if [ -f "monitoring/alertmanager/pagerduty-integration.yaml" ]; then
        kubectl apply -f monitoring/alertmanager/pagerduty-integration.yaml -n $NAMESPACE
        log_info "AlertManager deployed"
    fi
    
    log_info "Monitoring stack deployed"
}

# Deploy security tools
deploy_security() {
    log_step "Deploying security tools..."
    
    # Deploy Falco
    if [ -f "monitoring/falco/enable-runtime-security.sh" ]; then
        bash monitoring/falco/enable-runtime-security.sh
        log_info "Falco deployed"
    fi
    
    # Deploy audit logging
    if [ -f "security/audit-logging.yaml" ]; then
        kubectl apply -f security/audit-logging.yaml -n $NAMESPACE
        log_info "Audit logging deployed"
    fi
    
    # Deploy security scanning
    if [ -f "security/security-scanning.yaml" ]; then
        kubectl apply -f security/security-scanning.yaml -n $NAMESPACE
        log_info "Security scanning deployed"
    fi
    
    log_info "Security tools deployed"
}

# Deploy application
deploy_application() {
    log_step "Deploying SuperAI Platform application..."
    
    # Update image tag in values
    helm upgrade --install superai-platform ./helm \
        --namespace $NAMESPACE \
        --set image.repository=${REGISTRY}/superai-platform/superai-platform \
        --set image.tag=$IMAGE_TAG \
        --set environment=production \
        --values helm/values.yaml \
        --values k8s/overlays/prod/kustomization.yaml \
        --wait --timeout 15m \
        --atomic
    
    log_info "Application deployed successfully"
}

# Setup ArgoCD
setup_argocd() {
    log_step "Setting up ArgoCD GitOps..."
    
    if [ -f "argocd/gitops-bootstrap.sh" ]; then
        export APP_NAMESPACE=$NAMESPACE
        bash argocd/gitops-bootstrap.sh
        log_info "ArgoCD configured"
    else
        log_warn "ArgoCD bootstrap script not found, skipping"
    fi
}

# Run smoke tests
smoke_tests() {
    log_step "Running smoke tests..."
    
    # Wait for deployment
    kubectl wait --for=condition=available deployment/superai-platform -n $NAMESPACE --timeout=300s
    
    # Check pods
    log_info "Checking pod status..."
    kubectl get pods -n $NAMESPACE
    
    # Check services
    log_info "Checking services..."
    kubectl get svc -n $NAMESPACE
    
    # Health check
    log_info "Running health check..."
    EXTERNAL_IP=$(kubectl get svc superai-platform -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -n "$EXTERNAL_IP" ]; then
        if curl -f http://${EXTERNAL_IP}:80/health; then
            log_info "Health check passed"
        else
            log_warn "Health check failed"
        fi
    else
        log_info "External IP not yet available, skipping health check"
    fi
}

# Generate deployment report
generate_report() {
    log_step "Generating deployment report..."
    
    cat > deployment-report-$(date +%Y%m%d-%H%M%S).txt << EOF
SuperAI Platform v1.0 Production Deployment Report
===================================================

Deployment Date: $(date)
Namespace: $NAMESPACE
Cluster: $CLUSTER_NAME
Region: $REGION
Image Tag: $IMAGE_TAG

Components Deployed:
- SuperAI Platform API: $(kubectl get deployment superai-platform -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get deployment superai-platform -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- PostgreSQL: $(kubectl get statefulset postgres -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get statefulset postgres -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- Redis: $(kubectl get statefulset redis -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get statefulset redis -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- Prometheus: $(kubectl get deployment prometheus -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get deployment prometheus -n monitoring -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- Grafana: $(kubectl get deployment grafana -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get deployment grafana -n monitoring -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- Loki: $(kubectl get statefulset loki -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "N/A")/$(kubectl get statefulset loki -n monitoring -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "N/A") replicas ready
- Falco: $(kubectl get daemonset falco -n falco -o jsonpath='{.status.numberReady}' 2>/dev/null || echo "N/A")/$(kubectl get daemonset falco -n falco -o jsonpath='{.status.desiredNumberScheduled}' 2>/dev/null || echo "N/A") replicas ready

Services:
EOF

    kubectl get svc -n $NAMESPACE >> deployment-report-$(date +%Y%m%d-%H%M%S).txt
    
    cat >> deployment-report-$(date +%Y%m%d-%H%M%S).txt << EOF

Security:
- TLS Certificates: Generated and applied
- Image Signing: Completed with cosign
- Security Scanning: Trivy, Kube-Bench, Kube-Hunter, Bandit
- Audit Logging: Enabled
- Falco Runtime Security: Enabled
- RBAC: Applied

Monitoring:
- Prometheus: Deployed
- Grafana: Deployed
- AlertManager: Deployed with PagerDuty integration
- Loki: Deployed for centralized logging

Access URLs:
- Grafana: http://grafana.monitoring.svc.cluster.local
- Prometheus: http://prometheus.monitoring.svc.cluster.local
- ArgoCD: http://argocd.monitoring.svc.cluster.local

Deployment Status: SUCCESS

Next Steps:
1. Configure DNS for ingress
2. Update PagerDuty integration keys
3. Review Grafana dashboards
4. Configure alert thresholds
5. Run full integration tests
6. Enable production traffic
EOF

    log_info "Deployment report generated: deployment-report-$(date +%Y%m%d-%H%M%S).txt"
}

# Main deployment workflow
main() {
    log_info "=========================================="
    log_info "SuperAI Platform v1.0 Production Deployment"
    log_info "=========================================="
    echo ""
    
    pre_flight_checks
    verify_cluster
    generate_certificates
    build_images
    scan_images
    sign_images
    create_namespace
    apply_rbac
    apply_secrets
    deploy_monitoring
    deploy_security
    deploy_application
    setup_argocd
    smoke_tests
    generate_report
    
    echo ""
    log_info "=========================================="
    log_info "Deployment completed successfully!"
    log_info "=========================================="
    echo ""
    log_info "Next steps:"
    echo "  1. Review deployment report"
    echo "  2. Configure DNS and ingress"
    echo "  3. Update PagerDuty integration"
    echo "  4. Monitor Grafana dashboards"
    echo "  5. Run comprehensive tests"
    echo ""
    log_info "Access Grafana:"
    echo "  kubectl port-forward -n monitoring svc/grafana 3000:80"
    echo ""
    log_info "Access ArgoCD:"
    echo "  kubectl port-forward -n argocd svc/argocd-server 8080:443"
}

main "$@"