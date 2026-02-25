#!/bin/bash
# Enterprise-grade Jaeger installation script
# This script installs Jaeger with production-ready configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="jaeger"
RELEASE_NAME="jaeger"
CHART_REPO="jaegertracing"
CHART_NAME="jaeger"
CHART_VERSION="0.73.0"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &amp;&gt; /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &amp;&gt; /dev/null; then
        print_error "helm is not installed. Please install helm first."
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &amp;&gt; /dev/null; then
        print_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_info "All prerequisites are met."
}

install_elasticsearch_operator() {
    print_info "Installing Elasticsearch operator..."
    
    # Add Elasticsearch operator repository
    helm repo add elastic https://helm.elastic.co
    helm repo update
    
    # Create namespace
    kubectl create namespace elasticsearch --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Elasticsearch operator
    helm upgrade --install elastic-operator elastic/eck-operator \
        --namespace elasticsearch \
        --create-namespace \
        --set managedNamespaces={elasticsearch,jaeger} \
        --wait \
        --timeout 5m
    
    print_info "Elasticsearch operator installed successfully."
}

deploy_elasticsearch() {
    print_info "Deploying Elasticsearch for trace storage..."
    
    # Wait for Elasticsearch operator to be ready
    kubectl wait --for=condition=available \
        -n elasticsearch \
        deployment/elastic-operator \
        --timeout=5m
    
    # Create Elasticsearch cluster
    cat &lt;&lt;EOF | kubectl apply -f -
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: jaeger-es
  namespace: elasticsearch
spec:
  version: 8.11.0
  nodeSets:
  - name: nodes
    count: 3
    config:
      node.store.allow_mmap: false
    resources:
      requests:
        memory: 4Gi
        cpu: 2
      limits:
        memory: 8Gi
        cpu: 4
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 100Gi
    podTemplate:
      spec:
        containers:
        - name: elasticsearch
          resources:
            limits:
              memory: 8Gi
            requests:
              memory: 4Gi
EOF
    
    print_info "Waiting for Elasticsearch to be ready..."
    kubectl wait --for=condition=ready \
        -n elasticsearch \
        elasticsearch/jaeger-es \
        --timeout=15m
    
    print_info "Elasticsearch deployed successfully."
}

install_jaeger() {
    print_info "Installing Jaeger..."
    
    # Add Jaeger repository
    helm repo add $CHART_REPO https://$CHART_REPO.github.io/helm-charts
    helm repo update
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Get Elasticsearch credentials
    ES_PASSWORD=$(kubectl get secret jaeger-es-es-elastic-user -n elasticsearch -o jsonpath='{.data.elastic}' | base64 --decode)
    
    # Install Jaeger with Elasticsearch backend
    helm upgrade --install $RELEASE_NAME $CHART_REPO/$CHART_NAME \
        --namespace $NAMESPACE \
        --version $CHART_VERSION \
        --values k8s/jaeger/values.yaml \
        --set storage.elasticsearch.user=elastic \
        --set storage.elasticsearch.password="$ES_PASSWORD" \
        --set storage.elasticsearch.tls.enabled=false \
        --set collector.replicaCount=3 \
        --set query.replicaCount=2 \
        --set agent.replicaCount=3 \
        --set agent.daemonset.useHostPort=false \
        --wait \
        --timeout 10m
    
    print_info "Jaeger installed successfully."
}

configure_istio_tracing() {
    print_info "Configuring Istio for Jaeger tracing..."
    
    # Check if Istio is installed
    if ! kubectl get namespace istio-system &amp;&gt; /dev/null; then
        print_warn "Istio is not installed. Skipping Istio configuration."
        return
    fi
    
    # Apply Istio tracing configuration
    kubectl apply -f k8s/jaeger/istio-config.yaml
    
    print_info "Istio tracing configured successfully."
}

verify_installation() {
    print_info "Verifying installation..."
    
    # Check Jaeger pods
    print_info "Checking Jaeger pods..."
    kubectl get pods -n $NAMESPACE
    
    # Check services
    print_info "Checking Jaeger services..."
    kubectl get svc -n $NAMESPACE
    
    # Check Elasticsearch
    print_info "Checking Elasticsearch..."
    kubectl get elasticsearch -n elasticsearch
    
    print_info "Installation verification complete."
}

print_access_info() {
    print_info "Access Information:"
    echo ""
    echo "Jaeger Query UI:"
    echo "  Port-forward: kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-query 16686:16686"
    echo "  Open browser:  http://localhost:16686"
    echo ""
    echo "Services:"
    echo "  Agent:        $RELEASE_NAME-agent.$NAMESPACE.svc:6831 (UDP)"
    echo "  Collector:    $RELEASE_NAME-collector.$NAMESPACE.svc:14250 (gRPC)"
    echo "  Query:        $RELEASE_NAME-query.$NAMESPACE.svc:16686 (HTTP)"
    echo ""
    echo "To enable tracing in your applications:"
    echo "  1. Add OpenTelemetry instrumentation"
    echo "  2. Configure Jaeger exporter"
    echo "  3. Set sampling rate"
    echo ""
}

main() {
    print_info "Starting Jaeger installation..."
    echo ""
    
    check_prerequisites
    install_elasticsearch_operator
    deploy_elasticsearch
    install_jaeger
    configure_istio_tracing
    verify_installation
    print_access_info
    
    print_info "Installation completed successfully!"
}

# Run main function
main "$@"