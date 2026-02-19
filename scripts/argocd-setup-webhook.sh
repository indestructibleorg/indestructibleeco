#!/usr/bin/env bash
# IndestructibleEco v1.0 — Argo CD GitHub Webhook Setup
# URI: indestructibleeco://scripts/argocd-setup-webhook
#
# This script configures a GitHub webhook to trigger Argo CD sync on push.
# Closes the GitOps loop: push → webhook → Argo CD sync → cluster updated.
#
# Usage:
#   ./scripts/argocd-setup-webhook.sh                          # Interactive
#   GITHUB_TOKEN=ghp_xxx ARGOCD_URL=https://argocd.example.com \
#     ./scripts/argocd-setup-webhook.sh                        # Non-interactive
#
# Prerequisites:
#   - GitHub PAT with admin:repo_hook permission
#   - Argo CD server accessible via public URL (or ngrok for local)
#   - curl, jq available
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────
GITHUB_OWNER="${GITHUB_OWNER:-indestructibleorg}"
GITHUB_REPO="${GITHUB_REPO:-indestructibleeco}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
ARGOCD_URL="${ARGOCD_URL:-}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-}"

# ── Validate prerequisites ───────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  IndestructibleEco — GitHub Webhook Setup for Argo CD   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

for cmd in curl jq; do
  if ! command -v "${cmd}" &>/dev/null; then
    echo "ERROR: ${cmd} not found. Install it first."
    exit 1
  fi
done

# ── Collect inputs ───────────────────────────────────────────
if [[ -z "${GITHUB_TOKEN}" ]]; then
  echo "GitHub Personal Access Token (needs admin:repo_hook scope):"
  read -rs GITHUB_TOKEN
  echo ""
fi

if [[ -z "${ARGOCD_URL}" ]]; then
  echo "Argo CD server URL (e.g., https://argocd.example.com):"
  read -r ARGOCD_URL
fi

# Strip trailing slash
ARGOCD_URL="${ARGOCD_URL%/}"

if [[ -z "${WEBHOOK_SECRET}" ]]; then
  WEBHOOK_SECRET=$(openssl rand -hex 20 2>/dev/null || head -c 40 /dev/urandom | xxd -p | head -c 40)
  echo "Generated webhook secret: ${WEBHOOK_SECRET}"
  echo "  Store this in Argo CD: argocd-secret → webhook.github.secret"
fi

WEBHOOK_URL="${ARGOCD_URL}/api/webhook"

echo ""
echo "Configuration:"
echo "  Repository:  ${GITHUB_OWNER}/${GITHUB_REPO}"
echo "  Webhook URL: ${WEBHOOK_URL}"
echo ""

# ── Step 1: Check existing webhooks ─────────────────────────
echo "[1/4] Checking existing webhooks..."
EXISTING=$(curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/hooks" | \
  jq -r ".[] | select(.config.url == &quot;${WEBHOOK_URL}&quot;) | .id" 2>/dev/null || echo "")

if [[ -n "${EXISTING}" ]]; then
  echo "  Webhook already exists (ID: ${EXISTING})"
  echo "  Updating configuration..."
  HTTP_METHOD="PATCH"
  API_URL="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/hooks/${EXISTING}"
else
  echo "  No existing webhook found — creating new"
  HTTP_METHOD="POST"
  API_URL="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/hooks"
fi
echo ""

# ── Step 2: Create/Update webhook ────────────────────────────
echo "[2/4] Configuring webhook..."
PAYLOAD=$(jq -n \
  --arg url "${WEBHOOK_URL}" \
  --arg secret "${WEBHOOK_SECRET}" \
  '{
    name: "web",
    active: true,
    events: ["push", "pull_request"],
    config: {
      url: $url,
      content_type: "json",
      secret: $secret,
      insecure_ssl: "0"
    }
  }')

RESPONSE=$(curl -s -X "${HTTP_METHOD}" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  "${API_URL}")

HOOK_ID=$(echo "${RESPONSE}" | jq -r '.id // empty')
if [[ -z "${HOOK_ID}" ]]; then
  echo "  ERROR: Failed to create webhook"
  echo "  Response: ${RESPONSE}" | head -5
  exit 1
fi

echo "  Webhook configured (ID: ${HOOK_ID})"
echo ""

# ── Step 3: Update Argo CD webhook secret ────────────────────
echo "[3/4] Updating Argo CD webhook secret..."
echo "  Run the following command to store the webhook secret in Argo CD:"
echo ""
echo "  kubectl -n argocd patch secret argocd-secret \&quot;
echo "    --type merge -p '{&quot;stringData&quot;: {&quot;webhook.github.secret&quot;: &quot;${WEBHOOK_SECRET}&quot;}}'"
echo ""
echo "  Or manually:"
echo "    kubectl edit secret argocd-secret -n argocd"
echo "    Add: webhook.github.secret: $(echo -n "${WEBHOOK_SECRET}" | base64)"
echo ""

# ── Step 4: Test webhook ────────────────────────────────────
echo "[4/4] Testing webhook delivery..."
TEST_RESPONSE=$(curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/hooks/${HOOK_ID}/tests")

echo "  Ping sent. Check delivery status:"
echo "  https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/hooks/${HOOK_ID}"
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Webhook Setup Complete                                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  GitOps Loop:                                            ║"
echo "║    git push → GitHub webhook → Argo CD → K8s sync       ║"
echo "║                                                          ║"
echo "║  Verify:                                                 ║"
echo "║    1. Push a commit to main                              ║"
echo "║    2. Check Argo CD UI for sync activity                 ║"
echo "║    3. Check GitHub webhook deliveries page               ║"
echo "║                                                          ║"
echo "║  Webhook ID: ${HOOK_ID}                                  ║"
echo "║  Secret stored? Run the kubectl patch command above.     ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"