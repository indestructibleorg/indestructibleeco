#!/usr/bin/env bash
set -euo pipefail
# Retrieval — Fetch the workflow YAML definition that failed

WORKFLOW_PATH=$(gh api "repos/${REPO}/actions/runs/${RUN_ID}" --jq '.path')
gh api "repos/${REPO}/contents/${WORKFLOW_PATH}" --jq '.content' | base64 -d