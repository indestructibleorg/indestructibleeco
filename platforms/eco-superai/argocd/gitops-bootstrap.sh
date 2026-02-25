#!/bin/bash
# ArgoCD GitOps Bootstrap Script
# P0 Critical: Setup GitOps deployment pipeline with ArgoCD

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
ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}"
APP_NAMESPACE="${APP_NAMESPACE:-default}"
REPO_URL="${REPO_URL:-https://github.com/organization/superai-platform}"
TARGET_REVISION="${TARGET_REVISION:-main}"
ARGOCD_VERSION="${ARGOCD_VERSION:-2.10.0}"

log_info "Starting ArgoCD GitOps Bootstrap..."
log_info "ArgoCD namespace: $ARGOCD_NAMESPACE"
log_info "Application namespace: $APP_NAMESPACE"
log_info "Repository: $REPO_URL"
log_info "Target revision: $TARGET_REVISION"

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

# Install ArgoCD
install_argocd() {
    log_step "Installing ArgoCD..."
    
    # Create namespace
    kubectl create namespace "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install ArgoCD
    kubectl apply -n "$ARGOCD_NAMESPACE" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    log_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available deployment/argocd-server -n "$ARGOCD_NAMESPACE" --timeout=300s
    
    log_info "ArgoCD installed successfully"
}

# Create ArgoCD Application
create_application() {
    log_step "Creating ArgoCD Application..."
    
    kubectl apply -f - << EOF
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: superai-platform
  namespace: $ARGOCD_NAMESPACE
spec:
  description: SuperAI Platform Project
  sourceRepos:
  - $REPO_URL
  destinations:
  - namespace: $APP_NAMESPACE
    server: https://kubernetes.default.svc
  - namespace: monitoring
    server: https://kubernetes.default.svc
  - namespace: falco
    server: https://kubernetes.default.svc
  clusterResourceWhitelist:
  - group: '*'
    kind: '*'
  namespaceResourceWhitelist:
  - group: '*'
    kind: '*'
  orphanedResources:
    warn: false
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: superai-platform
  namespace: $ARGOCD_NAMESPACE
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: superai-platform
  source:
    repoURL: $REPO_URL
    targetRevision: $TARGET_REVISION
    path: k8s/base
    helm:
      valueFiles:
      - ../../helm/values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: $APP_NAMESPACE
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jqPathExpressions:
    - .spec.template.metadata.annotations
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: superai-monitoring
  namespace: $ARGOCD_NAMESPACE
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: superai-platform
  source:
    repoURL: $REPO_URL
    targetRevision: $TARGET_REVISION
    path: monitoring
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: superai-falco
  namespace: $ARGOCD_NAMESPACE
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: superai-platform
  source:
    repoURL: $REPO_URL
    targetRevision: $TARGET_REVISION
    path: monitoring/falco
    helm:
      valueFiles:
      - falco-values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: falco
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
    
    log_info "ArgoCD Applications created"
}

# Create Auto-Remediation ConfigMap
create_remediation_config() {
    log_step "Creating Auto-Remediation Configuration..."
    
    kubectl apply -f - << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: auto-remediation-policies
  namespace: $APP_NAMESPACE
  labels:
    app: superai-platform
    component: auto-remediation
data:
  policies.yaml: |
    # Auto-Remediation Policies for SuperAI Platform
    
    policies:
      # Pod Restart Remediation
      - name: restart-crashing-pod
        trigger:
          alert: PodCrashLooping
          severity: critical
        actions:
          - type: restart_pod
            max_retries: 3
            cooldown: 300
        notification:
          channels: [slack, pagerduty]
      
      # Scale Up Remediation
      - name: scale-up-under-load
        trigger:
          alert: HighCPUUsage
          severity: warning
        actions:
          - type: scale_deployment
            replicas_max: 10
            step: 2
            cooldown: 60
        notification:
          channels: [slack]
      
      # Database Connection Remediation
      - name: restart-db-connections
        trigger:
          alert: DatabaseConnectionFailure
          severity: critical
        actions:
          - type: restart_deployment
            deployments: [postgres, redis]
          - type: run_command
            command: "python scripts/verify-db-connection.py"
        notification:
          channels: [pagerduty, slack]
      
      # Security Incident Remediation
      - name: isolate-compromised-pod
        trigger:
          alert: SecurityViolationDetected
          severity: critical
        actions:
          - type: isolate_pod
            network_policy: deny-all
          - type: capture_logs
            duration: 3600
          - type: create_incident
            severity: P1
        notification:
          channels: [pagerduty, slack, email]
      
      # Resource Exhaustion Remediation
      - name: handle-resource-exhaustion
        trigger:
          alert: HighMemoryUsage
          severity: warning
        actions:
          - type: scale_deployment
            replicas_max: 5
            step: 1
        notification:
          channels: [slack]
      
      # Quantum Job Failure Remediation
      - name: retry-quantum-job
        trigger:
          alert: QuantumJobFailed
          severity: warning
        actions:
          - type: requeue_job
            max_retries: 2
        notification:
          channels: [slack]
    
    # Remediation Actions Definition
    actions:
      restart_pod:
        command: "kubectl delete pod {{ .labels.pod }} -n {{ .labels.namespace }}"
        description: "Restart the failing pod"
      
      restart_deployment:
        command: "kubectl rollout restart deployment/{{ .action.deployment }} -n {{ .labels.namespace }}"
        description: "Rolling restart of deployment"
      
      scale_deployment:
        command: "kubectl scale deployment/{{ .labels.deployment }} --replicas={{ .replicas }} -n {{ .labels.namespace }}"
        description: "Scale deployment to specified replica count"
      
      isolate_pod:
        command: "kubectl label pod {{ .labels.pod }} -n {{ .labels.namespace }} isolated=true --overwrite"
        description: "Label pod as isolated for security investigation"
      
      capture_logs:
        command: "kubectl logs {{ .labels.pod }} -n {{ .labels.namespace }} --tail=1000 > /tmp/pod-logs-{{ .labels.pod }}.txt"
        description: "Capture pod logs for investigation"
      
      requeue_job:
        command: "curl -X POST http://api/quantum/jobs/{{ .labels.job_id }}/retry"
        description: "Retry failed quantum job"
      
      create_incident:
        command: "python scripts/create-incident.py --severity={{ .action.severity }} --alert={{ .labels.alertname }}"
        description: "Create incident in ticketing system"
EOF
    
    log_info "Auto-Remediation Configuration created"
}

# Create Event Response Automation
create_event_response() {
    log_step "Creating Event Response Automation..."
    
    kubectl apply -f - << EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: health-check-remediator
  namespace: $APP_NAMESPACE
  labels:
    app: superai-platform
    component: event-response
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 3
      activeDeadlineSeconds: 300
      template:
        spec:
          serviceAccountName: superai-app
          restartPolicy: OnFailure
          containers:
          - name: remediator
            image: ghcr.io/superai-platform/auto-remediator:latest
            args:
            - --namespace=$APP_NAMESPACE
            - --config=/etc/remediation/policies.yaml
            volumeMounts:
            - name: policies
              mountPath: /etc/remediation
            resources:
              requests:
                cpu: 100m
                memory: 100Mi
              limits:
                cpu: 500m
                memory: 500Mi
          volumes:
          - name: policies
            configMap:
              name: auto-remediation-policies
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: auto-remediator
  namespace: $APP_NAMESPACE
  labels:
    app: superai-platform
    component: event-response
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: auto-remediator
  labels:
    app: superai-platform
    component: event-response
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "create"]
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "watch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: auto-remediator
  labels:
    app: superai-platform
    component: event-response
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: auto-remediator
subjects:
  - kind: ServiceAccount
    name: auto-remediator
    namespace: $APP_NAMESPACE
EOF
    
    log_info "Event Response Automation created"
}

# Create Rollback Configuration
create_rollback_config() {
    log_step "Creating Rollback Configuration..."
    
    kubectl apply -f - << EOF
apiVersion: argoproj.io/v1alpha1
kind: RolloutManager
metadata:
  name: superai-platform
  namespace: $APP_NAMESPACE
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: superai-platform-active
      previewService: superai-platform-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: superai-platform-preview
      promotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: superai-platform-active
---
apiVersion: analysistemplate.argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: $APP_NAMESPACE
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.95
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.default.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[2m]))
          /
          sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
---
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: superai-platform
  namespace: $APP_NAMESPACE
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: superai-platform-canary
      - setWeight: 40
      - pause: {duration: 5m}
      - setWeight: 60
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 5m}
      analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: superai-platform-canary
      - setWeight: 100
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: superai-platform
      component: api
  template:
    metadata:
      labels:
        app: superai-platform
        component: api
    spec:
      containers:
      - name: api
        image: ghcr.io/superai-platform/superai-platform:latest
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: superai-platform-active
  namespace: $APP_NAMESPACE
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: superai-platform
    component: api
---
apiVersion: v1
kind: Service
metadata:
  name: superai-platform-preview
  namespace: $APP_NAMESPACE
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: superai-platform
    component: api
EOF
    
    log_info "Rollback Configuration created"
}

# Get ArgoCD password
get_argocd_password() {
    log_step "Retrieving ArgoCD password..."
    
    ARGOCD_PASSWORD=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    
    log_info "ArgoCD initial password: $ARGOCD_PASSWORD"
    log_info "ArgoCD URL: https://argocd.$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}' | sed 's|https://||')"
    log_info ""
    log_info "Login with:"
    echo "  argocd login $(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
    echo "  Username: admin"
    echo "  Password: $ARGOCD_PASSWORD"
}

# Main execution
main() {
    check_kubectl
    install_argocd
    create_application
    create_remediation_config
    create_event_response
    create_rollback_config
    get_argocd_password
    
    log_info "ArgoCD GitOps Bootstrap Complete!"
    echo ""
    echo "Deployment summary:"
    echo "  ArgoCD namespace: $ARGOCD_NAMESPACE"
    echo "  Application namespace: $APP_NAMESPACE"
    echo "  Repository: $REPO_URL"
    echo "  Target revision: $TARGET_REVISION"
    echo ""
    log_info "Next steps:"
    echo "  1. Access ArgoCD UI"
    echo "  2. Configure Git repository credentials"
    echo "  3. Sync applications"
    echo "  4. Monitor deployment status"
    echo "  5. Test auto-remediation policies"
}

main "$@"