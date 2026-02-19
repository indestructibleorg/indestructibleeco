#!/usr/bin/env bash
# IndestructibleEco v1.0 — Argo CD Automated Installation
# URI: indestructibleeco://scripts/argocd-install
#
# Usage:
#   ./scripts/argocd-install.sh                    # Install with defaults
#   ./scripts/argocd-install.sh --version 2.13.3   # Specific version
#   ./scripts/argocd-install.sh --skip-cli         # Skip CLI install
#
# Prerequisites:
#   - kubectl configured with cluster access
#   - Cluster admin permissions
#   - curl available
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────
ARGOCD_VERSION="${ARGOCD_VERSION:-stable}"
ARGOCD_NAMESPACE="argocd"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_CLI=false
SKIP_APPS=false

# ── Parse arguments ──────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --version)   ARGOCD_VERSION="$2"; shift 2 ;;
    --skip-cli)  SKIP_CLI=true; shift ;;
    --skip-apps) SKIP_APPS=true; shift ;;
    --help|-h)
      echo "Usage: $0 [--version VERSION] [--skip-cli] [--skip-apps]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  IndestructibleEco — Argo CD Installation               ║"
echo "║  Version: ${ARGOCD_VERSION}                             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Verify prerequisites ────────────────────────────
echo "[1/7] Verifying prerequisites..."
if ! command -v kubectl &>/dev/null; then
  echo "  ERROR: kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"
  exit 1
fi

if ! kubectl cluster-info &>/dev/null; then
  echo "  ERROR: Cannot connect to Kubernetes cluster."
  echo "  Ensure kubectl is configured: kubectl config current-context"
  exit 1
fi

CURRENT_CONTEXT=$(kubectl config current-context)
echo "  Cluster context: ${CURRENT_CONTEXT}"
echo "  kubectl version: $(kubectl version --client --short 2>/dev/null || kubectl version --client -o yaml | grep gitVersion | head -1)"
echo ""

# ── Step 2: Create ArgoCD namespace ─────────────────────────
echo "[2/7] Creating ArgoCD namespace..."
if kubectl get namespace "${ARGOCD_NAMESPACE}" &>/dev/null; then
  echo "  Namespace '${ARGOCD_NAMESPACE}' already exists — skipping"
else
  kubectl apply -f "${REPO_ROOT}/k8s/argocd/namespace.qyaml"
  echo "  Namespace '${ARGOCD_NAMESPACE}' created with governance blocks"
fi
echo ""

# ── Step 3: Install Argo CD ─────────────────────────────────
echo "[3/7] Installing Argo CD (version: ${ARGOCD_VERSION})..."
INSTALL_URL="https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"

if [[ "${ARGOCD_VERSION}" == "stable" ]]; then
  INSTALL_URL="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
fi

kubectl apply -n "${ARGOCD_NAMESPACE}" -f "${INSTALL_URL}"
echo "  Argo CD manifests applied"
echo ""

# ── Step 4: Wait for Argo CD to be ready ────────────────────
echo "[4/7] Waiting for Argo CD pods to be ready (timeout: 300s)..."
kubectl wait --for=condition=available deployment/argocd-server \
  -n "${ARGOCD_NAMESPACE}" --timeout=300s 2>/dev/null || {
  echo "  WARNING: argocd-server not ready within 300s"
  echo "  Check: kubectl get pods -n ${ARGOCD_NAMESPACE}"
  echo "  Continuing anyway..."
}

kubectl wait --for=condition=available deployment/argocd-repo-server \
  -n "${ARGOCD_NAMESPACE}" --timeout=300s 2>/dev/null || true

kubectl wait --for=condition=available deployment/argocd-applicationset-controller \
  -n "${ARGOCD_NAMESPACE}" --timeout=300s 2>/dev/null || true

echo "  Argo CD pods:"
kubectl get pods -n "${ARGOCD_NAMESPACE}" --no-headers 2>/dev/null | sed 's/^/    /'
echo ""

# ── Step 5: Install Argo CD CLI ──────────────────────────────
if [[ "${SKIP_CLI}" == "false" ]]; then
  echo "[5/7] Installing Argo CD CLI..."
  if command -v argocd &>/dev/null; then
    echo "  argocd CLI already installed: $(argocd version --client --short 2>/dev/null || echo 'unknown')"
  else
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    case "${ARCH}" in
      x86_64)  ARCH="amd64" ;;
      aarch64) ARCH="arm64" ;;
    esac

    CLI_URL="https://github.com/argoproj/argo-cd/releases/latest/download/argocd-${OS}-${ARCH}"
    echo "  Downloading: ${CLI_URL}"
    curl -sSL -o /usr/local/bin/argocd "${CLI_URL}"
    chmod +x /usr/local/bin/argocd
    echo "  Installed: $(argocd version --client --short 2>/dev/null || echo 'done')"
  fi
else
  echo "[5/7] Skipping CLI installation (--skip-cli)"
fi
echo ""

# ── Step 6: Configure repository credentials ────────────────
echo "[6/7] Configuring repository access..."
if kubectl get secret argocd-repo-indestructibleeco -n "${ARGOCD_NAMESPACE}" &>/dev/null; then
  echo "  Repository secret already exists — skipping"
else
  echo "  Repository secret not found."
  echo "  To configure, run one of:"
  echo ""
  echo "  # Option A: HTTPS with PAT"
  echo "  kubectl create secret generic argocd-repo-indestructibleeco \&quot;
  echo "    --from-literal=type=git \&quot;
  echo "    --from-literal=url=https://github.com/indestructibleorg/indestructibleeco \&quot;
  echo "    --from-literal=username=<GITHUB_USERNAME> \&quot;
  echo "    --from-literal=password=<GITHUB_PAT> \&quot;
  echo "    -n argocd"
  echo ""
  echo "  # Option B: SSH"
  echo "  kubectl create secret generic argocd-repo-indestructibleeco \&quot;
  echo "    --from-literal=type=git \&quot;
  echo "    --from-literal=url=git@github.com:indestructibleorg/indestructibleeco.git \&quot;
  echo "    --from-file=sshPrivateKey=~/.ssh/id_ed25519 \&quot;
  echo "    -n argocd"
  echo ""
  echo "  NOTE: For public repos, this step is optional."
fi
echo ""

# ── Step 7: Deploy Argo Applications ────────────────────────
if [[ "${SKIP_APPS}" == "false" ]]; then
  echo "[7/7] Deploying Argo CD Applications..."

  # Apply notifications config
  if [[ -f "${REPO_ROOT}/k8s/argocd/argocd-notifications-cm.yaml" ]]; then
    kubectl apply -f "${REPO_ROOT}/k8s/argocd/argocd-notifications-cm.yaml"
    echo "  Notifications config applied"
  fi

  # Apply staging application
  kubectl apply -f "${REPO_ROOT}/k8s/argocd/argo-app-staging.yaml"
  echo "  Staging application deployed"

  # Apply production application
  kubectl apply -f "${REPO_ROOT}/k8s/argocd/argo-app.yaml"
  echo "  Production application deployed"

  echo ""
  echo "  Applications:"
  kubectl get applications -n "${ARGOCD_NAMESPACE}" --no-headers 2>/dev/null | sed 's/^/    /' || echo "    (waiting for CRD registration...)"
else
  echo "[7/7] Skipping application deployment (--skip-apps)"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Installation Complete                                   ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Get admin password:                                     ║"
echo "║    kubectl -n argocd get secret argocd-initial-admin-    ║"
echo "║    secret -o jsonpath='{.data.password}' | base64 -d     ║"
echo "║                                                          ║"
echo "║  Port-forward UI:                                        ║"
echo "║    kubectl port-forward svc/argocd-server -n argocd      ║"
echo "║    8080:443                                              ║"
echo "║                                                          ║"
echo "║  Login:                                                  ║"
echo "║    argocd login localhost:8080 --username admin           ║"
echo "║    --password <PASSWORD> --insecure                      ║"
echo "║                                                          ║"
echo "║  Dashboard: https://localhost:8080                       ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"