#!/bin/bash
# Falco Runtime Monitoring Setup Script
# P0 Critical: Deploy and configure Falco for security monitoring

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
NAMESPACE="${NAMESPACE:-default}"
FALCO_NAMESPACE="${FALCO_NAMESPACE:-falco}"
FALCO_VERSION="${FALCO_VERSION:-latest}"

log_info "Starting Falco Runtime Security Setup..."
log_info "Target namespace: $NAMESPACE"
log_info "Falco namespace: $FALCO_NAMESPACE"

# Check kubectl availability
check_kubectl() {
    log_step "Checking kubectl availability..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "kubectl is available and cluster is accessible"
}

# Create Falco namespace
create_namespace() {
    log_step "Creating Falco namespace..."
    
    kubectl create namespace "$FALCO_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Namespace created/verified: $FALCO_NAMESPACE"
}

# Add Falco Helm repository
add_helm_repo() {
    log_step "Adding Falco Helm repository..."
    
    helm repo add falcosecurity https://falcosecurity.github.io/charts || true
    helm repo update
    
    log_info "Falco Helm repository added/updated"
}

# Install Falco
install_falco() {
    log_step "Installing Falco..."
    
    # Create Falco values file
    cat > /tmp/falco-values.yaml << EOF
# Falco Configuration for SuperAI Platform

image:
  pullPolicy: IfNotPresent

# Enable Falco as a DaemonSet
daemonset:
  enabled: true

# Enable gRPC output
grpc:
  enabled: true
  outputFormat: json

# Enable web UI
falcosidekick:
  enabled: true
  webui:
    enabled: true
  config:
    aws:
      accesskeyid: ""
      secretaccesskey: ""
    cloudflare:
      apitoken: ""
    datadog:
      apikey: ""
    elasticsearch:
      hostport: ""
      username: ""
      password: ""
    influxdb:
      hostport: ""
      username: ""
      password: ""
    loki:
      hostport: ""
      username: ""
      password: ""
    mattermost:
      webhookurl: ""
    opsgenie:
      apikey: ""
    pagerduty:
      integrationkey: ""
    rocketchat:
      webhookurl: ""
    slack:
      webhookurl: ""
    teams:
      webhookurl: ""
    telegram:
      token: ""
      chatid: ""
    alertmanager:
      hostport: ""

# Custom rules
customRules:
  rules:
    - content: |
        - rule: Detect Privileged Container
          desc: Detect privileged container start (needed for debugging only)
          condition: >
            container.privileged=true
            and not user.name in (falco, rootkit_scanner)
          output: >
            Privileged container started (user=%user.name container=%container.name image=%container.image.repository)
          priority: WARNING
          tags: [container, security, cis]
        
        - rule: Mount Sensitive Host Paths
          desc: Detect container mounting sensitive host paths
          condition: >
            container.mounts exists (/proc, /sys, /etc, /root, /var/run/docker.sock, /var/lib/kubelet)
            and not container.name startswith "falco"
          output: >
            Sensitive host path mounted (user=%user.name container=%container.name path=%container.mounts)
          priority: WARNING
          tags: [container, mount, security]
        
        - rule: Unexpected Outbound Connection
          desc: Detect outbound connections to unexpected destinations
          condition: >
            outbound and not fd.sport in (80, 443, 53, 22)
            and not fd.sip in (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            and not container.name in (falco, proxy)
          output: >
            Unexpected outbound connection (user=%user.name container=%container.name fd.sip=%fd.sip fd.sport=%fd.sport)
          priority: NOTICE
          tags: [network, security]
        
        - rule: Shell spawned in container
          desc: Detect shell spawned in container (potential backdoor)
          condition: >
            spawned_process and shell_procs
            and container.id != host
            and not proc.name in (docker-entrypoint, tini, supervisor)
          output: >
            Shell spawned in container (user=%user.name container=%container.name shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
          priority: WARNING
          tags: [process, shell, security]
        
        - rule: Python Code Execution
          desc: Detect Python code execution in production containers
          condition: >
            spawned_process and proc.name = python
            and container.image.tag in (prod, production, v1.0.0)
            and not proc.cmdline contains "gunicorn"
            and not proc.cmdline contains "celery"
          output: >
            Python code execution in production (user=%user.name container=%container.name cmdline=%proc.cmdline)
          priority: NOTICE
          tags: [process, python, superai]
        
        - rule: Quantum Circuit File Access
          desc: Detect access to quantum circuit files
          condition: >
            open_read and fd.name endswith (.qasm, .py)
            and container.labels.app = superai-platform
            and not user.name in (system, root)
          output: >
            Quantum circuit file access (user=%user.name container=%container.name file=%fd.name)
          priority: INFO
          tags: [superai, quantum, file]
        
        - rule: AI Model File Modification
          desc: Detect modification of AI model files
          condition: >
            open_write and fd.name endswith (.pkl, .h5, .onnx, .pt)
            and container.labels.app = superai-platform
          output: >
            AI model file modification (user=%user.name container=%container.name file=%fd.name)
          priority: WARNING
          tags: [superai, ai, model]
        
        - rule: Database Connection from Unusual Source
          desc: Detect database connections from unexpected containers
          condition: >
            outbound and fd.sport in (5432, 3306, 6379)
            and not container.labels.app = superai-platform
            and not container.name in (falco, monitoring)
          output: >
            Database connection from unusual source (user=%user.name container=%container.name fd.sip=%fd.sip)
          priority: WARNING
          tags: [network, database, security]
        
        - rule: Kubernetes API Access
          desc: Detect Kubernetes API access
          condition: >
            outbound and fd.sport in (6443, 443)
            and fd.sip in (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            and not user.name in (system, root, kube-system)
          output: >
            Kubernetes API access (user=%user.name container=%container.name fd.sip=%fd.sip)
          priority: NOTICE
          tags: [network, k8s, security]

# Enable audit log
auditLog:
  enabled: true

# Set log level
logLevel: info

# Syslog output
syslog:
  enabled: false

# File output
fileOutput:
  enabled: false

# Stdout output
stdoutOutput:
  enabled: true
EOF

    # Install Falco using Helm
    helm install falco falcosecurity/falco \
        --namespace "$FALCO_NAMESPACE" \
        --version "$FALCO_VERSION" \
        --values /tmp/falco-values.yaml \
        --wait \
        --timeout 5m
    
    log_info "Falco installed successfully"
}

# Create Falco rules ConfigMap
create_rules_configmap() {
    log_step "Creating Falco rules ConfigMap..."
    
    kubectl create configmap falco-extra-rules \
        --namespace "$FALCO_NAMESPACE" \
        --from-file=../../security/falco/falco-rules.yaml \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Falco rules ConfigMap created"
}

# Create Falco ServiceAccount and RBAC
create_rbac() {
    log_step "Creating Falco RBAC resources..."
    
    kubectl apply -f - << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: falco
  namespace: $FALCO_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: falco-cluster-role
rules:
  - apiGroups: [""]
    resources: ["pods", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions", "networking.k8s.io"]
    resources: ["networkpolicies"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: falco-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: falco-cluster-role
subjects:
  - kind: ServiceAccount
    name: falco
    namespace: $FALCO_NAMESPACE
EOF
    
    log_info "Falco RBAC resources created"
}

# Create Falco ServiceMonitor (if Prometheus Operator is installed)
create_servicemonitor() {
    log_step "Creating Falco ServiceMonitor..."
    
    if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
        kubectl apply -f - << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: falco
  namespace: $FALCO_NAMESPACE
  labels:
    app: falco
spec:
  selector:
    matchLabels:
      app: falco
  namespaceSelector:
    matchNames:
      - $FALCO_NAMESPACE
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics
EOF
        log_info "Falco ServiceMonitor created"
    else
        log_warn "Prometheus Operator not found, skipping ServiceMonitor"
    fi
}

# Verify Falco deployment
verify_deployment() {
    log_step "Verifying Falco deployment..."
    
    # Wait for Falco pods to be ready
    kubectl wait --for=condition=ready pod -l app=falco -n "$FALCO_NAMESPACE" --timeout=300s
    
    log_info "Falco pods are ready"
    
    # Check Falco logs
    log_info "Recent Falco logs:"
    kubectl logs -l app=falco -n "$FALCO_NAMESPACE" --tail=10 || true
}

# Create anomaly detection configuration
create_anomaly_detection() {
    log_step "Creating anomaly detection configuration..."
    
    cat > /tmp/falco-anomaly-rules.yaml << EOF
- rule: High Rate of Failed SSH Connections
  desc: Detect potential brute force attack via SSH
  condition: >
    ssh and evt.type = accept and ssh.failed_attempts > 10
  output: >
    High rate of failed SSH connections (user=%user.name src_ip=%ssh.ip_address dest_ip=%ssh.destination_ip)
  priority: CRITICAL
  tags: [ssh, brute-force, security]

- rule: Unexpected File System Changes
  desc: Detect unexpected modifications to system files
  condition: >
    open_write and fd.name in (/etc/passwd, /etc/shadow, /etc/group, /etc/hosts)
    and not user.name in (root, system)
  output: >
    Unexpected file system modification (user=%user.name file=%fd.name)
  priority: CRITICAL
  tags: [filesystem, security]

- rule: Sudden Spike in Network Traffic
  desc: Detect unusual network traffic patterns
  condition: >
    outbound and fd.net_bytes_sent > 10485760
    and not container.name in (monitoring, falco)
  output: >
    Sudden spike in network traffic (container=%container.name bytes=%fd.net_bytes_sent)
  priority: WARNING
  tags: [network, anomaly]

- rule: Container Escape Attempt
  desc: Detect attempts to escape container isolation
  condition: >
    spawned_process and proc.name in (chroot, mount, umount, nsenter)
    and not user.name in (root, system)
  output: >
    Container escape attempt detected (user=%user.name process=%proc.name cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [container, escape, security]
EOF

    kubectl create configmap falco-anomaly-rules \
        --namespace "$FALCO_NAMESPACE" \
        --from-file=/tmp/falco-anomaly-rules.yaml \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Anomaly detection rules created"
}

# Main execution
main() {
    check_kubectl
    create_namespace
    add_helm_repo
    install_falco
    create_rules_configmap
    create_rbac
    create_servicemonitor
    verify_deployment
    create_anomaly_detection
    
    log_info "Falco Runtime Security Setup Complete!"
    echo ""
    echo "Deployment summary:"
    echo "  Namespace: $FALCO_NAMESPACE"
    echo "  Version: $FALCO_VERSION"
    echo "  Web UI: kubectl port-forward -n $FALCO_NAMESPACE svc/falcosidekick-ui 2802:2802"
    echo ""
    log_info "Next steps:"
    echo "  1. Configure alert destinations in falcosidekick"
    echo "  2. Review and customize Falco rules"
    echo "  3. Set up PagerDuty/Slack integrations"
    echo "  4. Test alerting mechanisms"
}

main "$@"