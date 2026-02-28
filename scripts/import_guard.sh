#!/usr/bin/env bash
set -euo pipefail

# IMPORT-GUARD: Enforces cross-domain import boundaries
# Usage: bash scripts/import_guard.sh
# Domain boundaries: apps ↔ ops ↔ infra

echo "IMPORT-GUARD: checking cross-domain import boundaries..."

# Define forbidden import patterns
# apps should not import from ops or infra
# ops should not import from infra
# infra should not import from apps or ops

violations=0

# Check apps/ → ops/ or infra/ imports
if [[ -d "apps" ]]; then
  if grep -r "from ops\." apps/ 2>/dev/null || grep -r "import.*ops\." apps/ 2>/dev/null; then
    echo "IMPORT-GUARD: forbidden: apps/ importing from ops/"
    violations=$((violations + 1))
  fi
  if grep -r "from infra\." apps/ 2>/dev/null || grep -r "import.*infra\." apps/ 2>/dev/null; then
    echo "IMPORT-GUARD: forbidden: apps/ importing from infra/"
    violations=$((violations + 1))
  fi
fi

# Check ops/ → infra/ imports
if [[ -d "ops" ]]; then
  if grep -r "from infra\." ops/ 2>/dev/null || grep -r "import.*infra\." ops/ 2>/dev/null; then
    echo "IMPORT-GUARD: forbidden: ops/ importing from infra/"
    violations=$((violations + 1))
  fi
fi

# Check infra/ → apps/ or ops/ imports
if [[ -d "infra" ]]; then
  if grep -r "from apps\." infra/ 2>/dev/null || grep -r "import.*apps\." infra/ 2>/dev/null; then
    echo "IMPORT-GUARD: forbidden: infra/ importing from apps/"
    violations=$((violations + 1))
  fi
  if grep -r "from ops\." infra/ 2>/dev/null || grep -r "import.*ops\." infra/ 2>/dev/null; then
    echo "IMPORT-GUARD: forbidden: infra/ importing from ops/"
    violations=$((violations + 1))
  fi
fi

if [[ $violations -gt 0 ]]; then
  echo "IMPORT-GUARD: found $violations boundary violation(s)"
  exit 1
fi

echo "IMPORT-GUARD: ✓ no cross-domain import violations"
exit 0
# 規則：
# - apps/** 內的 TS/JS 檔案不得 import/require ops/ 或 infra/
# - ops/** 不得 import/require apps/
# - 共用只能走 packages/**

fail=0

scan() {
  local base="$1"
  local bad1="$2"
  local bad2="$3"

  if [[ ! -d "$base" ]]; then return 0; fi

  while IFS= read -r f; do
    if grep -nE "(from\s+['\"](\.\./)+$bad1/|from\s+['\"](\.\./)+$bad2/|require\(['\"](\.\./)+$bad1/|require\(['\"](\.\./)+$bad2/)" "$f" >/dev/null; then
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
