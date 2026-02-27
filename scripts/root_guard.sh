#!/usr/bin/env bash
set -euo pipefail

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
