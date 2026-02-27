#!/usr/bin/env bash
set -euo pipefail

# Rules:
# - apps/** TS/JS files must not import/require ops/ or infra/
# - ops/** must not import/require apps/
# - shared code must go through packages/**

fail=0

scan() {
  local base="$1"
  local bad1="$2"
  local bad2="$3"

  if [[ ! -d "$base" ]]; then return 0; fi

  while IFS= read -r f; do
    if grep -nE "(from\s+['\"](\.\./)+($bad1|$bad2)/|require\(['\"](\.\./)+($bad1|$bad2)/)" "$f" >/dev/null; then
      echo "IMPORT-GUARD: $f imports forbidden path ($bad1 or $bad2)" >&2
      grep -nE "(from\s+['\"](\.\./)+($bad1|$bad2)/|require\(['\"](\.\./)+($bad1|$bad2)/)" "$f" >&2 || true
      fail=1
    fi
  done < <(find "$base" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \))
}

scan "apps" "ops" "infra"

if [[ -d "ops" ]]; then
  while IFS= read -r f; do
    if grep -nE "(from\s+['\"](\.\./)+apps/|require\(['\"](\.\./)+apps/)" "$f" >/dev/null; then
      echo "IMPORT-GUARD: $f imports forbidden path (apps/)" >&2
      fail=1
    fi
  done < <(find ops -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \))
fi

exit "$fail"
