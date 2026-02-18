#!/usr/bin/env bash
set -euo pipefail
# Understanding — Build mental model of the failed CI run
# Fetches failed jobs and steps from GitHub Actions API

gh api "repos/${REPO}/actions/runs/${RUN_ID}/jobs" \
  --jq '.jobs[] | select(.conclusion=="failure") | {name, conclusion, steps: [.steps[] | select(.conclusion=="failure") | {name, conclusion, number}]}'