#!/usr/bin/env bash
set -euo pipefail

# ROOT-GUARD: Enforces top-level directory whitelist
# Usage: bash scripts/root_guard.sh
# Reads: infra/root-guard/allowed-roots.txt

ALLOWED_ROOTS="infra/root-guard/allowed-roots.txt"

if [[ ! -f "$ALLOWED_ROOTS" ]]; then
  echo "ROOT-GUARD: missing allowlist file: $ALLOWED_ROOTS"
  exit 1
fi

# Load allowed roots into an associative array for fast lookup
declare -A allowed
while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip empty lines and comments
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  allowed["$line"]=1
done < "$ALLOWED_ROOTS"

# Check all top-level entries (excluding .git)
found_forbidden=0
for entry in */ .[!.]* ..?*; do
  # Skip if glob didn't match anything
  [[ -e "$entry" ]] || continue

  # Normalize: remove trailing slash
  entry="${entry%/}"

  # Skip .git directory
  [[ "$entry" == ".git" ]] && continue

  # Check if entry is in allowed list
  if [[ -z "${allowed[$entry]:-}" ]]; then
    echo "ROOT-GUARD: forbidden top-level entry: $entry"
    found_forbidden=1
  fi
done

if [[ $found_forbidden -eq 1 ]]; then
  echo "ROOT-GUARD: Add missing entries to $ALLOWED_ROOTS or remove them from the repository root"
  exit 1
fi

echo "ROOT-GUARD: ✓ all top-level entries are whitelisted"
exit 0
allow="infra/root-guard/allowed-roots.txt"
test -f "$allow"

mapfile -t allowed < <(sed '/^\s*$/d' "$allow")

declare -A ok=()
for x in "${allowed[@]}"; do ok["$x"]=1; done

fail=0
while IFS= read -r entry; do
  name="$(basename "$entry")"
  if [[ -z "${ok[$name]+x}" ]]; then
    echo "ROOT-GUARD: forbidden top-level entry: $name" >&2
    fail=1
  fi
done < <(find . -maxdepth 1 -mindepth 1 -printf '%p\n' | sed 's|^\./||')

exit "$fail"
