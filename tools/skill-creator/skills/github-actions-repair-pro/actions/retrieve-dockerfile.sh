#!/usr/bin/env bash
set -euo pipefail
# Retrieval — Fetch all Dockerfiles and their build contexts

for df in $(gh api "repos/${REPO}/git/trees/HEAD?recursive=1" --jq '.tree[] | select(.path | test("Dockerfile")) | .path'); do
  echo "=== ${df} ==="
  gh api "repos/${REPO}/contents/${df}" --jq '.content' | base64 -d
  echo ""
done