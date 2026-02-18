#!/usr/bin/env bash
# IndestructibleEco v1.0 — Deployment Script
# URI: indestructibleeco://scripts/deploy
set -euo pipefail

NAMESPACE="${ECO_NAMESPACE:-indestructibleeco}"
RELEASE_NAME="${ECO_RELEASE:-indestructibleeco}"
CHART_DIR="./helm"
VALUES_FILE="./helm/values.yaml"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     IndestructibleEco v1.0 — Deployment Script          ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ── Pre-deploy validation ─────────────────────────────────────
echo "[0/7] Running CI Validator Engine (pre-deploy gate)..."
if ! python3 tools/ci-validator/validate.py; then
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║  DEPLOY ABORTED — Validation failed                     ║"
  echo "║  Fix all errors before deploying.                       ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  exit 1
fi
echo "  Pre-deploy validation passed"
echo ""

# ── Pre-flight checks ────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || { echo "kubectl required"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "helm required"; exit 1; }

echo "[1/7] Creating namespace..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "[2/7] Applying base resources..."
kubectl apply -f k8s/base/namespace.qyaml
kubectl apply -f k8s/base/configmap.qyaml

echo "[3/7] Deploying infrastructure (Redis, PostgreSQL)..."
kubectl apply -f k8s/base/redis.qyaml
kubectl apply -f k8s/base/postgres.qyaml

echo "  Waiting for Redis..."
kubectl rollout status statefulset/redis -n "$NAMESPACE" --timeout=120s
echo "  Waiting for PostgreSQL..."
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=120s

echo "[4/7] Deploying inference engines..."
kubectl apply -f k8s/base/vllm-engine.qyaml
kubectl apply -f k8s/base/tgi-engine.qyaml
kubectl apply -f k8s/base/sglang-engine.qyaml
kubectl apply -f k8s/base/ollama-engine.qyaml

echo "[5/7] Deploying API Gateway..."
kubectl apply -f k8s/base/api-gateway.qyaml

echo "  Waiting for API Gateway..."
kubectl rollout status deployment/eco-api-gateway -n "$NAMESPACE" --timeout=300s

echo "[6/7] Deploying backend services..."
kubectl apply -f backend/k8s/namespaces/platform.qyaml
kubectl apply -f backend/k8s/configmaps/api-config.qyaml
kubectl apply -f backend/k8s/secrets/sealed-secrets.qyaml
kubectl apply -f backend/k8s/security/rbac.qyaml
kubectl apply -f backend/k8s/security/network-policies.qyaml
kubectl apply -f backend/k8s/security/mtls.qyaml
kubectl apply -f backend/k8s/deployments/ai.qyaml
kubectl apply -f backend/k8s/deployments/api.qyaml
kubectl apply -f backend/k8s/services/ai-svc.qyaml
kubectl apply -f backend/k8s/services/api-svc.qyaml
kubectl apply -f backend/k8s/ingress/main-ingress.qyaml

echo "[7/7] Deploying monitoring & ingress..."
kubectl apply -f k8s/monitoring/prometheus.qyaml
kubectl apply -f k8s/monitoring/grafana.qyaml
kubectl apply -f k8s/ingress/ingress.qyaml

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Deployment Complete                        ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  API:        kubectl port-forward svc/eco-api-svc 8000:8000 -n $NAMESPACE"
echo "║  Prometheus: kubectl port-forward svc/prometheus-svc 9090:9090 -n $NAMESPACE"
echo "║  Grafana:    kubectl port-forward svc/grafana-svc 3000:3000 -n $NAMESPACE"
echo "╚══════════════════════════════════════════════════════════╝"

kubectl get pods -n "$NAMESPACE" -o wide