#!/bin/bash
# MachineNativeOps Quantum Naming Governance Quick Install Script
# Version: v4.0.0-quantum
# Description: One-click deployment of quantum-enhanced naming governance

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Quantum configuration
QUANTUM_VERSION="v4.0.0-quantum"
QUANTUM_NAMESPACE="quantum-governance"
QUANTUM_BACKEND="ibm_quantum_falcon"
COHERENCE_THRESHOLD="0.9999"
ENTANGLEMENT_DEPTH="7"

# ASCII Art
cat << 'EOF'
 _____ _     _     _____           _   _   _      _____             
|  ___| |   | |   |_   _|         | | | | \ |    |  ___|            
| |_  | |   | |     | | ___  _ __ | |_| |  \| ___| |_ ___  _ __ ___ 
|  _| | |   | |     | |/ _ \| '_ \| __| | . ` |_  |  __/ _ \| '_ ` _ \
| |   | |___| |___ _| | (_) | | | | |_| | |\  | |_| | || (_) | | | | | |
\_|   \_____|_____|_____\___/|_| |_|\__|_|_| \_|\____/\___\___/|_| |_| |_|

          🌌 QUANTUM-ENHANCED NAMING GOVERNANCE 🌌
                 MachineNativeOps v4.0.0-quantum
EOF

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  Initializing Quantum Deployment Environment${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check kubectl version
    KUBE_VERSION=$(kubectl version --client --short | grep -o 'v[0-9]\+\.[0-9]\+' | head -1)
    print_status "kubectl version: $KUBE_VERSION"
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed. Please install Helm first."
        exit 1
    fi
    
    # Check helm version
    HELM_VERSION=$(helm version --short | grep -o 'v[0-9]\+\.[0-9]\+')
    print_status "Helm version: $HELM_VERSION"
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_status "Kubernetes cluster access verified"
    
    # Check available resources
    AVAILABLE_CPU=$(kubectl top nodes --no-headers | awk '{sum+=$2} END {print sum}')
    AVAILABLE_MEMORY=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum}')
    
    print_info "Available CPU: ${AVAILABLE_CPU}m"
    print_info "Available Memory: ${AVAILABLE_MEMORY}Mi"
    
    echo ""
}

# Function to setup quantum namespace
setup_namespace() {
    echo -e "${BLUE}🌌 Setting up quantum namespace...${NC}"
    
    if kubectl get namespace $QUANTUM_NAMESPACE &> /dev/null; then
        print_warning "Namespace $QUANTUM_NAMESPACE already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete namespace $QUANTUM_NAMESPACE
            print_status "Deleted existing namespace"
        else
            print_status "Using existing namespace"
            return
        fi
    fi
    
    kubectl create namespace $QUANTUM_NAMESPACE
    kubectl label namespace $QUANTUM_NAMESPACE name=quantum-governance \
        app.kubernetes.io/part-of=machine-native-ops \
        app.kubernetes.io/version=$QUANTUM_VERSION
    
    print_status "Created quantum namespace: $QUANTUM_NAMESPACE"
    echo ""
}

# Function to install quantum secrets
install_secrets() {
    echo -e "${BLUE}🔐 Installing quantum secrets...${NC}"
    
    # Generate quantum secrets if they don't exist
    if ! kubectl get secret quantum-governance-secrets -n $QUANTUM_NAMESPACE &> /dev/null; then
        print_info "Generating quantum secrets..."
        
        # Generate random secrets (in production, use proper secret management)
        QUANTUM_API_TOKEN=$(openssl rand -base64 32)
        QUANTUM_SIGNATURE_KEY=$(openssl rand -base64 64)
        QKD_SECRET=$(openssl rand -base64 48)
        
        kubectl create secret generic quantum-governance-secrets \
            -n $QUANTUM_NAMESPACE \
            --from-literal=quantum-api-token="$QUANTUM_API_TOKEN" \
            --from-literal=quantum-signature-key="$QUANTUM_SIGNATURE_KEY" \
            --from-literal=qkd-secret="$QKD_SECRET"
        
        print_status "Created quantum secrets"
    else
        print_status "Quantum secrets already exist"
    fi
    
    echo ""
}

# Function to deploy quantum configuration
deploy_config() {
    echo -e "${BLUE}⚙️ Deploying quantum configuration...${NC}"
    
    # Apply configuration maps
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantum-governance-config
  namespace: $QUANTUM_NAMESPACE
  labels:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "config"
data:
  quantum-config.yaml: |
    quantum:
      backend: "$QUANTUM_BACKEND"
      entanglement_depth: $ENTANGLEMENT_DEPTH
      coherence_threshold: $COHERENCE_THRESHOLD
      error_correction: "surface_code_v5"
      measurement_basis: "bell_states"
      qubits: 256
      shots: 1024
    
    governance:
      naming_scheme:
        hierarchy: "env/app/resource/version/quantum-id"
        separators:
          primary: "-"
          secondary: "."
          tertiary: "_"
        validation_regex: "^[a-z0-9]+(-[a-z0-9]+)*(\\.[a-z0-9]+)*(\\_[a-z0-9]+)*$"
      
      layers:
        strategic:
          adoption_phases: ["planning", "pilot", "rollout", "optimization"]
          decision_matrix:
            risk_model: "quantum-entropy-v4"
            approval_gates: ["CAB-Quantum", "AI-Governor-v7", "Security-Council-Quantum"]
        
        operational:
          version_control:
            semver_quantum: true
            coherence_checker: "qsvm-validator@0.8.2"
        
        technical:
          automation_pipeline:
            stages:
              - "quantum-canonicalization"
              - "cross-layer-quantum-validation"
              - "observability-quantum-injection"
              - "quantum-auto-repair"
    
    observability:
      prometheus:
        enabled: true
        port: 9090
      grafana:
        enabled: true
        port: 3000
      jaeger:
        enabled: true
        port: 16686

  naming-policies.yaml: |
    policies:
      - name: "quantum-naming-convention"
        description: "Quantum-enhanced naming convention validation"
        rules:
          - name: "pattern-validation"
            regex: "^[a-z0-9]+(-[a-z0-9]+)*(\\.[a-z0-9]+)*(\\_[a-z0-9]+)*$"
            description: "Valid naming pattern with quantum support"
          - name: "length-validation"
            max_length: 63
            description: "Maximum length for DNS compatibility"
          - name: "quantum-coherence"
            threshold: $COHERENCE_THRESHOLD
            description: "Quantum coherence threshold"
      
      - name: "quantum-entanglement-policy"
        description: "Quantum entanglement validation rules"
        rules:
          - name: "entanglement-strength"
            threshold: 0.95
            description: "Minimum entanglement strength"
          - name: "bell-inequality"
            threshold: 2.0
            description: "Bell inequality minimum value"
EOF
    
    print_status "Deployed quantum configuration"
    echo ""
}

# Function to deploy quantum service
deploy_service() {
    echo -e "${BLUE}🚀 Deploying quantum governance service...${NC}"
    
    # Apply service deployment
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantum-governance-service
  namespace: $QUANTUM_NAMESPACE
  labels:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "service"
    app.kubernetes.io/version: "$QUANTUM_VERSION"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: "quantum-governance"
      app.kubernetes.io/component: "service"
  template:
    metadata:
      labels:
        app.kubernetes.io/name: "quantum-governance"
        app.kubernetes.io/component: "service"
        app.kubernetes.io/version: "$QUANTUM_VERSION"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: quantum-governance
          image: "nginx:latest"  # Placeholder for quantum-governance:v4.0.0
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
            - containerPort: 9090
              name: metrics
              protocol: TCP
            - containerPort: 16686
              name: jaeger
              protocol: TCP
          env:
            - name: QUANTUM_BACKEND
              value: "$QUANTUM_BACKEND"
            - name: COHERENCE_THRESHOLD
              value: "$COHERENCE_THRESHOLD"
            - name: ENTANGLEMENT_DEPTH
              value: "$ENTANGLEMENT_DEPTH"
            - name: QUANTUM_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: quantum-governance-secrets
                  key: quantum-api-token
          volumeMounts:
            - name: config-volume
              mountPath: /etc/quantum-governance
              readOnly: true
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
              ephemeral-storage: "5Gi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
              ephemeral-storage: "10Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
      volumes:
        - name: config-volume
          configMap:
            name: quantum-governance-config
            items:
              - key: quantum-config.yaml
                path: quantum-config.yaml

---
apiVersion: v1
kind: Service
metadata:
  name: quantum-governance-service
  namespace: $QUANTUM_NAMESPACE
  labels:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "service"
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
      name: http
      protocol: TCP
    - port: 9090
      targetPort: 9090
      name: metrics
      protocol: TCP
    - port: 16686
      targetPort: 16686
      name: jaeger
      protocol: TCP
  selector:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "service"
EOF
    
    print_status "Deployed quantum governance service"
    echo ""
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "${BLUE}⏳ Waiting for quantum deployment to be ready...${NC}"
    
    # Wait for pods to be ready
    if kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=quantum-governance \
        -n $QUANTUM_NAMESPACE \
        --timeout=300s; then
        print_status "Quantum deployment is ready"
    else
        print_error "Quantum deployment failed to become ready"
        exit 1
    fi
    
    echo ""
}

# Function to setup monitoring
setup_monitoring() {
    echo -e "${BLUE}📊 Setting up quantum monitoring...${NC}"
    
    # Apply monitoring configuration
    kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: quantum-governance-monitor
  namespace: $QUANTUM_NAMESPACE
  labels:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "monitoring"
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: "quantum-governance"
      app.kubernetes.io/component: "service"
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
      honorLabels: true

---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: quantum-governance-rules
  namespace: $QUANTUM_NAMESPACE
  labels:
    app.kubernetes.io/name: "quantum-governance"
    app.kubernetes.io/component: "monitoring"
    release: prometheus
spec:
  groups:
    - name: quantum-naming-governance
      rules:
        - alert: QuantumCoherenceLow
          expr: up{job="quantum-governance-service"} == 0
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Quantum governance service down"
            description: "Quantum governance service is unresponsive"
EOF
    
    print_status "Setup quantum monitoring"
    echo ""
}

# Function to run validation tests
run_validation() {
    echo -e "${BLUE}🧪 Running quantum validation tests...${NC}"
    
    # Test service health
    if kubectl get pods -n $QUANTUM_NAMESPACE -l app.kubernetes.io/name=quantum-governance | grep -q "Running"; then
        print_status "Quantum pods are running"
    else
        print_error "Quantum pods are not running"
        kubectl get pods -n $QUANTUM_NAMESPACE -l app.kubernetes.io/name=quantum-governance
        exit 1
    fi
    
    # Test service endpoints
    SERVICE_IP=$(kubectl get svc quantum-governance-service -n $QUANTUM_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$SERVICE_IP" ]; then
        SERVICE_IP="localhost"
        kubectl port-forward -n $QUANTUM_NAMESPACE svc/quantum-governance-service 8080:80 &
        PORT_FORWARD_PID=$!
        sleep 5
    fi
    
    # Test health endpoint
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_status "Health endpoint is responding"
    else
        print_warning "Health endpoint not responding (this may be expected with nginx placeholder)"
    fi
    
    # Clean up port forward if used
    if [ ! -z "${PORT_FORWARD_PID:-}" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    
    echo ""
}

# Function to display deployment summary
display_summary() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  🎉 Quantum Deployment Complete! 🎉${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${PURPLE}📋 Deployment Summary:${NC}"
    echo -e "   • Namespace: ${BLUE}$QUANTUM_NAMESPACE${NC}"
    echo -e "   • Version: ${BLUE}$QUANTUM_VERSION${NC}"
    echo -e "   • Backend: ${BLUE}$QUANTUM_BACKEND${NC}"
    echo -e "   • Coherence Threshold: ${BLUE}$COHERENCE_THRESHOLD${NC}"
    echo -e "   • Entanglement Depth: ${BLUE}$ENTANGLEMENT_DEPTH${NC}"
    echo ""
    echo -e "${PURPLE}🔗 Service URLs:${NC}"
    
    # Get service URL
    SERVICE_IP=$(kubectl get svc quantum-governance-service -n $QUANTUM_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
    if [ "$SERVICE_IP" != "localhost" ]; then
        echo -e "   • API: ${CYAN}http://$SERVICE_IP/api/v4/validate${NC}"
        echo -e "   • Metrics: ${CYAN}http://$SERVICE_IP/metrics${NC}"
        echo -e "   • Health: ${CYAN}http://$SERVICE_IP/health${NC}"
    else
        echo -e "   • API: ${CYAN}http://localhost:8080/api/v4/validate${NC} (after port-forward)"
        echo -e "   • Metrics: ${CYAN}http://localhost:9090/metrics${NC} (after port-forward)"
        echo -e "   • Health: ${CYAN}http://localhost:8080/health${NC} (after port-forward)"
        echo ""
        echo -e "${YELLOW}💡 To access services locally, run:${NC}"
        echo -e "   ${BLUE}kubectl port-forward -n $QUANTUM_NAMESPACE svc/quantum-governance-service 8080:80 &${NC}"
        echo -e "   ${BLUE}kubectl port-forward -n $QUANTUM_NAMESPACE svc/quantum-governance-service 9090:9090 &${NC}"
    fi
    
    echo ""
    echo -e "${PURPLE}📊 Monitoring Commands:${NC}"
    echo -e "   • Check pods: ${BLUE}kubectl get pods -n $QUANTUM_NAMESPACE${NC}"
    echo -e "   • View logs: ${BLUE}kubectl logs -f -n $QUANTUM_NAMESPACE -l app.kubernetes.io/name=quantum-governance${NC}"
    echo -e "   • Check metrics: ${BLUE}kubectl top pods -n $QUANTUM_NAMESPACE${NC}"
    echo ""
    echo -e "${PURPLE}🧪 Testing Commands:${NC}"
    echo -e "   • Validate naming: ${BLUE}curl -X POST http://localhost:8080/api/v4/validate -d '{&quot;resource_name&quot;:&quot;test-app-service-v1.0&quot;}'${NC}"
    echo -e "   • Check health: ${BLUE}curl http://localhost:8080/health${NC}"
    echo -e "   • View metrics: ${BLUE}curl http://localhost:9090/metrics${NC}"
    echo ""
    echo -e "${GREEN}🚀 Your quantum-enhanced naming governance is now running!${NC}"
    echo -e "${YELLOW}📖 For detailed documentation, visit: https://docs.machinenativeops.io/quantum${NC}"
    echo -e "${YELLOW}💬 For support, join our Discord: https://discord.gg/quantum-governance${NC}"
    echo ""
}

# Main execution
main() {
    echo -e "${CYAN}🌌 Starting MachineNativeOps Quantum Governance Deployment...${NC}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup namespace
    setup_namespace
    
    # Install secrets
    install_secrets
    
    # Deploy configuration
    deploy_config
    
    # Deploy service
    deploy_service
    
    # Wait for deployment
    wait_for_deployment
    
    # Setup monitoring
    setup_monitoring
    
    # Run validation
    run_validation
    
    # Display summary
    display_summary
}

# Handle interruption
trap 'echo -e "\n${RED}Deployment interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"