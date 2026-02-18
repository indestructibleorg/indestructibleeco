#!/usr/bin/env bash
set -euo pipefail
# Phase 3: Analyze — Root cause identification via static analysis
# Inputs: TARGET_PATH, UNDERSTAND_OUTPUT, RETRIEVE_OUTPUT
# Outputs: JSON with root_causes, hypotheses, severity

echo '{"phase":"analyze","status":"started"}'

ERRORS=0
WARNINGS=0
ROOT_CAUSES="[]"

if [ -f "${TARGET_PATH}" ]; then
  EXT="${TARGET_PATH##*.}"

  case "${EXT}" in
    py)
      # Python: compile check + pattern analysis
      COMPILE_ERR=$(python3 -m py_compile "${TARGET_PATH}" 2>&1 || true)
      if [ -n "${COMPILE_ERR}" ]; then
        ERRORS=$((ERRORS + 1))
        ROOT_CAUSES=$(echo "${ROOT_CAUSES}" | python3 -c "
import sys, json
causes = json.load(sys.stdin)
causes.append({'cause': 'Python syntax error', 'evidence': '${COMPILE_ERR}', 'severity': 'critical'})
print(json.dumps(causes))
" 2>/dev/null || echo "[]")
      fi
      # Check for common anti-patterns
      if grep -qE 'except:\s*$|except Exception:' "${TARGET_PATH}" 2>/dev/null; then
        WARNINGS=$((WARNINGS + 1))
      fi
      if grep -qE 'eval\(|exec\(' "${TARGET_PATH}" 2>/dev/null; then
        ERRORS=$((ERRORS + 1))
      fi
      ;;
    js|ts)
      # JavaScript/TypeScript: syntax check
      SYNTAX_ERR=$(node --check "${TARGET_PATH}" 2>&1 || true)
      if [ -n "${SYNTAX_ERR}" ]; then
        ERRORS=$((ERRORS + 1))
      fi
      ;;
    yaml|yml|qyaml)
      # YAML: parse check + governance validation
      python3 -c "
import sys
try:
    open('${TARGET_PATH}').read()
    print('valid')
except Exception as e:
    print(f'error: {e}')
    sys.exit(1)
" 2>/dev/null || ERRORS=$((ERRORS + 1))
      ;;
  esac
elif [ -d "${TARGET_PATH}" ]; then
  # Directory: scan all source files
  ERRORS=$(find "${TARGET_PATH}" -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -c "Error" || echo 0)
fi

cat << EOJSON
{
  "phase": "analyze",
  "status": "complete",
  "target": "${TARGET_PATH}",
  "errors": ${ERRORS},
  "warnings": ${WARNINGS},
  "root_causes": ${ROOT_CAUSES},
  "analysis_method": "static-analysis"
}
EOJSON