# IndestructibleEco — Argo CD GitOps Guide

**URI:** `indestructibleeco://docs/argocd-gitops-guide`
**Version:** 1.0.0
**Last Updated:** 2025-02-20

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [GitHub Webhook Setup](#github-webhook-setup)
7. [Testing & Verification](#testing--verification)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

---

## Overview

IndestructibleEco uses Argo CD as its GitOps continuous delivery engine. Every change pushed to the `main` branch is automatically synchronized to the Kubernetes cluster, ensuring the cluster state always matches the Git repository — the single source of truth.

The GitOps loop operates as follows: a developer pushes a commit to `main`, which triggers the CI/CD pipeline (GitHub Actions 4-gate validation). Once all gates pass, a GitHub webhook notifies Argo CD, which detects the change in the `k8s/` directory and automatically syncs all `.qyaml` manifests to the target cluster. If the cluster state drifts from Git (manual kubectl edits, pod restarts, etc.), Argo CD's self-heal mechanism automatically corrects the drift back to the Git-defined state.

This approach eliminates manual `kubectl apply` operations, provides full audit trails through Git history, and ensures that every deployed state is reproducible, reviewable, and rollback-capable.

---

## Architecture

The IndestructibleEco GitOps architecture consists of three layers working in concert. The source layer is the GitHub repository containing all Kubernetes manifests in the `k8s/` directory as `.qyaml` files (governance-validated YAML). The orchestration layer is Argo CD, which watches the repository and manages synchronization. The target layer is the Kubernetes cluster with two namespaces: `indestructibleeco` for production and `ecosystem-staging` for pre-production validation.

```
┌─────────────────────────────────────────────────────────────┐
│                    GitOps Control Loop                       │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  GitHub   │───▶│  Argo CD │───▶│   K8s    │              │
│  │   Repo    │    │  Server  │    │ Cluster  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│   push/merge     webhook/poll     sync/heal                 │
│       │               │               │                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ CI/CD    │    │ Notifier │    │ Staging  │              │
│  │ Pipeline │    │ (Slack)  │    │ + Prod   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Argo CD Applications

Two Argo CD Applications are defined for the IndestructibleEco platform. The production application (`indestructibleeco`) syncs to the `indestructibleeco` namespace and is the primary deployment target. The staging application (`indestructibleeco-staging`) syncs to the `ecosystem-staging` namespace and serves as the pre-production validation environment. Both applications watch the same `k8s/` directory on the `main` branch, with staging receiving changes first for validation before production promotion.

### File Structure

```
k8s/
├── argocd/
│   ├── namespace.qyaml              # ArgoCD namespace + RBAC
│   ├── argo-app.yaml                # Production Application
│   ├── argo-app-staging.yaml        # Staging Application
│   ├── argocd-notifications-cm.yaml # Slack/webhook notifications
│   └── argocd-repo-secret.yaml      # Repository credentials template
├── base/
│   ├── api-gateway.qyaml            # API Gateway deployment + HPA
│   ├── configmap.qyaml              # Platform configuration
│   ├── namespace.qyaml              # Platform namespace + RBAC
│   ├── ollama-engine.qyaml          # Ollama inference engine
│   ├── postgres.qyaml               # PostgreSQL StatefulSet
│   ├── redis.qyaml                  # Redis deployment
│   ├── sglang-engine.qyaml          # SGLang inference engine
│   ├── tgi-engine.qyaml             # TGI inference engine
│   └── vllm-engine.qyaml            # vLLM inference engine
├── ingress/
│   └── ingress.qyaml                # Ingress rules
└── monitoring/
    ├── grafana.qyaml                # Grafana dashboard
    └── prometheus.qyaml             # Prometheus monitoring
```

---

## Prerequisites

Before installing Argo CD, ensure the following requirements are met. You need a running Kubernetes cluster (GKE, EKS, AKS, or local minikube/kind) with `kubectl` configured and cluster-admin permissions. You also need `curl` and `openssl` available on your workstation for the installation and webhook setup scripts.

| Requirement | Minimum Version | Purpose |
|---|---|---|
| Kubernetes | 1.26+ | Target cluster |
| kubectl | 1.26+ | Cluster management |
| curl | 7.x | Download Argo CD manifests |
| openssl | 1.1+ | Generate webhook secrets |
| GitHub PAT | — | Repository access + webhook setup |

---

## Installation

### Automated Installation

The repository includes a fully automated installation script that handles namespace creation, Argo CD deployment, CLI installation, and application registration.

```bash
# Default installation (latest stable Argo CD)
./scripts/argocd-install.sh

# Specific version
./scripts/argocd-install.sh --version v2.13.3

# Skip CLI installation (server only)
./scripts/argocd-install.sh --skip-cli

# Skip application deployment (install Argo CD only)
./scripts/argocd-install.sh --skip-apps
```

The script executes seven steps in sequence. First, it verifies that `kubectl` is configured and can reach the cluster. Second, it creates the `argocd` namespace using the governance-validated `k8s/argocd/namespace.qyaml` manifest. Third, it downloads and applies the official Argo CD installation manifests. Fourth, it waits for all Argo CD pods to reach ready state (timeout: 300 seconds). Fifth, it installs the `argocd` CLI binary. Sixth, it checks for repository credentials and provides setup instructions if missing. Seventh, it deploys the staging and production Argo CD Applications.

### Manual Installation

If you prefer manual control, execute each step individually:

```bash
# Step 1: Create namespace
kubectl apply -f k8s/argocd/namespace.qyaml

# Step 2: Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Step 3: Wait for readiness
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Step 4: Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d

# Step 5: Apply notifications config
kubectl apply -f k8s/argocd/argocd-notifications-cm.yaml

# Step 6: Deploy applications
kubectl apply -f k8s/argocd/argo-app-staging.yaml
kubectl apply -f k8s/argocd/argo-app.yaml
```

### Post-Installation Verification

After installation, verify that all components are running:

```bash
# Check Argo CD pods
kubectl get pods -n argocd

# Expected output:
# argocd-application-controller-xxx   Running
# argocd-applicationset-controller-xxx Running
# argocd-dex-server-xxx               Running
# argocd-notifications-controller-xxx Running
# argocd-redis-xxx                    Running
# argocd-repo-server-xxx              Running
# argocd-server-xxx                   Running

# Check applications
kubectl get applications -n argocd

# Expected output:
# indestructibleeco          Synced  Healthy
# indestructibleeco-staging  Synced  Healthy
```

---

## Configuration

### Repository Credentials

For private repositories, Argo CD needs credentials to access the Git repository. Three authentication methods are supported.

**HTTPS with Personal Access Token (recommended for simplicity):**

```bash
kubectl create secret generic argocd-repo-indestructibleeco \
  --from-literal=type=git \
  --from-literal=url=https://github.com/indestructibleorg/indestructibleeco \
  --from-literal=username=<GITHUB_USERNAME> \
  --from-literal=password=<GITHUB_PAT> \
  -n argocd
```

**SSH Key (recommended for production):**

```bash
kubectl create secret generic argocd-repo-indestructibleeco \
  --from-literal=type=git \
  --from-literal=url=git@github.com:indestructibleorg/indestructibleeco.git \
  --from-file=sshPrivateKey=~/.ssh/id_ed25519 \
  -n argocd
```

**GitHub App (recommended for enterprise):**

```bash
kubectl create secret generic argocd-repo-indestructibleeco \
  --from-literal=type=git \
  --from-literal=url=https://github.com/indestructibleorg/indestructibleeco \
  --from-literal=githubAppID=<APP_ID> \
  --from-literal=githubAppInstallationID=<INSTALLATION_ID> \
  --from-file=githubAppPrivateKey=<PATH_TO_PEM> \
  -n argocd
```

For public repositories, no credentials are needed — Argo CD can access the repository directly.

### Sync Policy

Both applications are configured with automated sync policies that include self-healing and pruning. Self-heal means that if someone manually modifies a resource in the cluster (e.g., `kubectl edit deployment`), Argo CD will automatically revert the change to match the Git state. Prune means that if a resource is removed from Git, Argo CD will automatically delete it from the cluster.

The retry policy is configured with exponential backoff: 5 retries with delays of 5s, 10s, 20s, 40s, and 80s (capped at 3 minutes). This handles transient failures such as API server timeouts or resource conflicts.

### Notifications

The notification system is configured in `k8s/argocd/argocd-notifications-cm.yaml` and supports both Slack and generic webhooks. Four event types are monitored: sync succeeded (green), sync failed (red), health degraded (orange), and sync running (blue).

To enable Slack notifications:

```bash
# Create Slack app at https://api.slack.com/apps
# Add bot token scope: chat:write
# Install to workspace and get token

kubectl create secret generic argocd-notifications-secret \
  --from-literal=slack-token=xoxb-YOUR-BOT-TOKEN \
  -n argocd
```

---

## GitHub Webhook Setup

The webhook creates a closed-loop system where every push to `main` immediately triggers Argo CD synchronization, eliminating the default 3-minute polling interval.

### Automated Setup

```bash
# Set environment variables
export GITHUB_TOKEN=ghp_your_token_here
export ARGOCD_URL=https://argocd.your-domain.com

# Run setup script
./scripts/argocd-setup-webhook.sh
```

The script creates a webhook on the GitHub repository that sends `push` and `pull_request` events to the Argo CD webhook endpoint. It generates a random secret for HMAC signature verification and provides the `kubectl` command to store the secret in Argo CD.

### Manual Setup

Navigate to your repository settings on GitHub: Settings → Webhooks → Add webhook. Set the Payload URL to `https://<ARGOCD_URL>/api/webhook`, Content type to `application/json`, and add a secret. Select "Just the push event" and ensure the webhook is active.

Then store the secret in Argo CD:

```bash
kubectl -n argocd patch secret argocd-secret \
  --type merge -p '{"stringData": {"webhook.github.secret": "<YOUR_SECRET>"}}'
```

### Verification

After setup, push a commit and verify the webhook delivery on GitHub (Settings → Webhooks → Recent Deliveries). A successful delivery shows a 200 response code. Then check Argo CD for sync activity:

```bash
# Port-forward to access Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open https://localhost:8080 in browser
# Login with admin / <initial-password>
# Check application sync status
```

---

## Testing & Verification

### Test 1: Push-Triggered Sync

Make a small change to any `.qyaml` file (e.g., add a comment), commit, and push. Then observe the sync:

```bash
# Make a change
echo "# Test sync $(date)" >> k8s/base/configmap.qyaml
git add -A && git commit -m "test: verify Argo CD sync" && git push

# Watch sync status
kubectl get applications -n argocd -w

# Or via CLI
argocd app get indestructibleeco
```

### Test 2: Self-Heal Verification

Manually modify a resource in the cluster and verify Argo CD reverts it:

```bash
# Manually scale a deployment
kubectl scale deployment eco-api-gateway -n indestructibleeco --replicas=5

# Wait 30-60 seconds, then check
kubectl get deployment eco-api-gateway -n indestructibleeco
# Replicas should revert to the Git-defined value
```

### Test 3: Prune Verification

Remove a resource from Git and verify Argo CD deletes it from the cluster:

```bash
# Remove a test resource from k8s/ directory
# Commit and push
# Verify the resource is deleted from the cluster
```

---

## Monitoring & Alerts

### Argo CD Dashboard

Access the Argo CD web UI via port-forward:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
```

The dashboard shows all applications with their sync status (Synced/OutOfSync), health status (Healthy/Degraded/Progressing), and recent sync history. Click on an application to see individual resource status, diff views, and sync logs.

### Slack Notifications

When configured, the notification system sends messages to the `#indestructibleeco-deployments` Slack channel for all sync events. Green messages indicate successful syncs, red messages indicate failures with error details, and orange messages indicate health degradation.

### Prometheus Metrics

Argo CD exposes Prometheus metrics on port 8082. The ecosystem monitoring stack (configured in `ecosystem/monitoring/`) can scrape these metrics for dashboards and alerting:

```yaml
# Add to prometheus.yml scrape configs
- job_name: argocd
  static_configs:
    - targets: ['argocd-metrics.argocd.svc.cluster.local:8082']
```

---

## Troubleshooting

### Application Stuck in "Progressing"

This usually indicates a resource that cannot reach ready state. Check the application details:

```bash
argocd app get indestructibleeco --show-operation
kubectl get events -n indestructibleeco --sort-by='.lastTimestamp'
```

### Sync Failed with "ComparisonError"

This occurs when Argo CD cannot parse the manifests. Verify your `.qyaml` files are valid:

```bash
python3 tools/ci-validator/validate.py
```

### Webhook Not Triggering

Check the webhook delivery status on GitHub (Settings → Webhooks → Recent Deliveries). Common issues include incorrect URL, expired secret, or network connectivity. Verify the Argo CD server is accessible from the internet.

### Permission Denied

Ensure the Argo CD service account has the necessary RBAC permissions. The `k8s/argocd/namespace.qyaml` includes a ClusterRole with broad permissions for managing resources.

---

## Security Considerations

Argo CD handles sensitive operations and should be secured appropriately. The initial admin password should be changed immediately after installation. RBAC should be configured to limit user access based on roles. The Argo CD server should be exposed via HTTPS with a valid TLS certificate (use cert-manager for automatic certificate management). Repository credentials should use GitHub Apps or SSH keys rather than personal access tokens for production environments. The webhook secret should be rotated periodically and stored securely in Kubernetes secrets.

For SOC2 compliance, all sync operations are logged and auditable through both Argo CD's built-in audit log and the Git commit history. The governance blocks in `.qyaml` files provide additional traceability with unique IDs, URIs, and compliance tags.