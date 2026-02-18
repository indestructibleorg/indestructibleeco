#!/usr/bin/env bash
# IndestructibleEco v1.0 — Build Script
# URI: indestructibleeco://scripts/build
set -euo pipefail

VERSION="${1:-1.0.0}"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/indestructibleorg}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     IndestructibleEco v1.0 — Build v${VERSION}              ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ── Pre-build validation ──────────────────────────────────────
echo "[0/5] Running CI Validator Engine (pre-build gate)..."
if ! python3 tools/ci-validator/validate.py; then
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║  BUILD ABORTED — Validation failed                      ║"
  echo "║  Fix all errors before building.                        ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  exit 1
fi
echo "  Pre-build validation passed"
echo ""

echo "[1/5] Building API Gateway image..."
docker build \
  -t "${REGISTRY}/api:${VERSION}" \
  -t "${REGISTRY}/api:latest" \
  -f docker/Dockerfile \
  .

echo "[2/5] Building AI Service image..."
docker build \
  -t "${REGISTRY}/ai:${VERSION}" \
  -t "${REGISTRY}/ai:latest" \
  -f backend/ai/Dockerfile \
  backend/ai/

echo "[3/5] Building vLLM engine image..."
docker build \
  -t "${REGISTRY}/vllm:${VERSION}" \
  -f docker/Dockerfile.gpu \
  --target vllm \
  .

echo "[4/5] Building SGLang engine image..."
docker build \
  -t "${REGISTRY}/sglang:${VERSION}" \
  -f docker/Dockerfile.gpu \
  --target sglang \
  .

echo "[5/5] Pushing images..."
docker push "${REGISTRY}/api:${VERSION}"
docker push "${REGISTRY}/api:latest"
docker push "${REGISTRY}/ai:${VERSION}"
docker push "${REGISTRY}/ai:latest"
docker push "${REGISTRY}/vllm:${VERSION}"
docker push "${REGISTRY}/sglang:${VERSION}"

echo ""
echo "Build complete. Images:"
echo "  ${REGISTRY}/api:${VERSION}"
echo "  ${REGISTRY}/ai:${VERSION}"
echo "  ${REGISTRY}/vllm:${VERSION}"
echo "  ${REGISTRY}/sglang:${VERSION}"