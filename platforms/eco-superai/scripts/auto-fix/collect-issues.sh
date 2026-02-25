#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform - Collect CI/CD Issues
# ============================================================================
# Parses workflow run logs, classifies issues into categories (lint, type,
# security, dependency), and outputs a structured JSON report.
#
# Usage:
#   ./scripts/auto-fix/collect-issues.sh [options]
#
# Options:
#   --run-id <id>        GitHub Actions run ID to analyze
#   --repo <owner/name>  Repository (default: from git remote)
#   --output <path>      Output file (default: artifacts/reports/ci-issues.json)
#   --local              Parse local tool output instead of GH Actions logs
#   --verbose            Show detailed output
#
# Exit code: number of issues found (capped at 125)
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/reports"
OUTPUT_FILE="${OUTPUT_DIR}/ci-issues.json"
TEMP_DIR="$(mktemp -d)"

RUN_ID=""
REPO=""
LOCAL_MODE=false
VERBOSE=false

# Cleanup temp dir on exit
trap 'rm -rf "${TEMP_DIR}"' EXIT

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-id)   RUN_ID="$2"; shift 2 ;;
        --repo)     REPO="$2"; shift 2 ;;
        --output)   OUTPUT_FILE="$2"; shift 2 ;;
        --local)    LOCAL_MODE=true; shift ;;
        --verbose)  VERBOSE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--run-id <id>] [--repo <owner/name>] [--output <path>] [--local] [--verbose]"
            exit 0
            ;;
        *) echo "ERROR: Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "[collect-issues] $*" >&2
    fi
}

detect_repo() {
    if [[ -n "${REPO}" ]]; then
        return
    fi
    REPO="$(git -C "${PROJECT_ROOT}" remote get-url origin 2>/dev/null \
        | sed -E 's#.*github\.com[:/]##; s/\.git$//' || echo "")"
    if [[ -z "${REPO}" ]]; then
        log "Could not detect repository from git remote"
    fi
}

# ---------------------------------------------------------------------------
# Issue collection: Local mode
# ---------------------------------------------------------------------------
collect_local_issues() {
    log "Collecting issues from local tool runs..."
    cd "${PROJECT_ROOT}"

    local issues_file="${TEMP_DIR}/issues.jsonl"
    touch "${issues_file}"

    # Activate venv if present
    if [[ -f ".venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source ".venv/bin/activate"
    elif [[ -f "venv/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "venv/bin/activate"
    fi

    # --- Lint issues (ruff) ---
    if command -v ruff &>/dev/null; then
        log "Running ruff..."
        local ruff_output="${TEMP_DIR}/ruff.txt"
        ruff check src/ tests/ --output-format=json 2>/dev/null > "${ruff_output}" || true

        python3 -c "
import json, sys

try:
    with open('${ruff_output}') as f:
        issues = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)

for issue in issues:
    entry = {
        'category': 'lint',
        'tool': 'ruff',
        'rule': issue.get('code', 'unknown'),
        'severity': 'warning' if issue.get('code', '').startswith('W') else 'error',
        'message': issue.get('message', ''),
        'file': issue.get('filename', ''),
        'line': issue.get('location', {}).get('row', 0),
        'column': issue.get('location', {}).get('column', 0),
        'fixable': issue.get('fix', {}).get('applicability', '') == 'safe'
    }
    print(json.dumps(entry))
" >> "${issues_file}" 2>/dev/null || true
    fi

    # --- Type check issues (mypy) ---
    if command -v mypy &>/dev/null; then
        log "Running mypy..."
        local mypy_output="${TEMP_DIR}/mypy.txt"
        mypy src/ --ignore-missing-imports --no-color-output 2>/dev/null > "${mypy_output}" || true

        while IFS= read -r line; do
            # Parse mypy output: file:line: severity: message [code]
            if [[ "${line}" =~ ^(.+):([0-9]+):\ (error|warning|note):\ (.+)$ ]]; then
                local file="${BASH_REMATCH[1]}"
                local lineno="${BASH_REMATCH[2]}"
                local severity="${BASH_REMATCH[3]}"
                local message="${BASH_REMATCH[4]}"

                # Extract mypy error code if present
                local rule="unknown"
                if [[ "${message}" =~ \[([a-z-]+)\]$ ]]; then
                    rule="${BASH_REMATCH[1]}"
                fi

                python3 -c "
import json
print(json.dumps({
    'category': 'type',
    'tool': 'mypy',
    'rule': '${rule}',
    'severity': '${severity}',
    'message': $(python3 -c "import json; print(json.dumps('${message}'))" 2>/dev/null || echo '""'),
    'file': '${file}',
    'line': ${lineno},
    'column': 0,
    'fixable': False
}))
" >> "${issues_file}" 2>/dev/null || true
            fi
        done < "${mypy_output}"
    fi

    # --- Security issues (bandit) ---
    if command -v bandit &>/dev/null; then
        log "Running bandit..."
        local bandit_output="${TEMP_DIR}/bandit.json"
        bandit -r src/ -f json 2>/dev/null > "${bandit_output}" || true

        python3 -c "
import json, sys

try:
    with open('${bandit_output}') as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)

for result in data.get('results', []):
    sev = result.get('issue_severity', 'MEDIUM').lower()
    entry = {
        'category': 'security',
        'tool': 'bandit',
        'rule': result.get('test_id', 'unknown'),
        'severity': 'error' if sev == 'high' else 'warning',
        'message': result.get('issue_text', ''),
        'file': result.get('filename', ''),
        'line': result.get('line_number', 0),
        'column': 0,
        'fixable': False
    }
    print(json.dumps(entry))
" >> "${issues_file}" 2>/dev/null || true
    fi

    # --- Dependency issues (pip-audit or safety) ---
    if command -v pip-audit &>/dev/null; then
        log "Running pip-audit..."
        local audit_output="${TEMP_DIR}/pip-audit.json"
        pip-audit --format=json 2>/dev/null > "${audit_output}" || true

        python3 -c "
import json, sys

try:
    with open('${audit_output}') as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)

deps = data if isinstance(data, list) else data.get('dependencies', [])
for dep in deps:
    vulns = dep.get('vulns', [])
    for vuln in vulns:
        entry = {
            'category': 'dependency',
            'tool': 'pip-audit',
            'rule': vuln.get('id', 'unknown'),
            'severity': 'error',
            'message': f\"{dep.get('name', 'unknown')}=={dep.get('version', '?')}: {vuln.get('description', vuln.get('id', ''))}\",
            'file': 'pyproject.toml',
            'line': 0,
            'column': 0,
            'fixable': bool(vuln.get('fix_versions', []))
        }
        print(json.dumps(entry))
" >> "${issues_file}" 2>/dev/null || true
    fi

    echo "${issues_file}"
}

# ---------------------------------------------------------------------------
# Issue collection: GitHub Actions mode
# ---------------------------------------------------------------------------
collect_gh_issues() {
    log "Collecting issues from GitHub Actions run ${RUN_ID}..."

    if ! command -v gh &>/dev/null; then
        echo "ERROR: gh CLI is required for GitHub Actions mode" >&2
        exit 1
    fi

    detect_repo
    if [[ -z "${REPO}" ]]; then
        echo "ERROR: Could not determine repository. Use --repo flag." >&2
        exit 1
    fi

    local issues_file="${TEMP_DIR}/issues.jsonl"
    touch "${issues_file}"

    # Get the run ID if not specified (use latest)
    if [[ -z "${RUN_ID}" ]]; then
        RUN_ID="$(gh run list --repo "${REPO}" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || echo "")"
        if [[ -z "${RUN_ID}" ]]; then
            echo "ERROR: Could not find any workflow runs" >&2
            exit 1
        fi
        log "Using latest run ID: ${RUN_ID}"
    fi

    # Download logs
    local logs_dir="${TEMP_DIR}/logs"
    mkdir -p "${logs_dir}"
    gh run view "${RUN_ID}" --repo "${REPO}" --log 2>/dev/null > "${logs_dir}/full.log" || {
        echo "ERROR: Failed to download logs for run ${RUN_ID}" >&2
        exit 1
    }

    local full_log="${logs_dir}/full.log"

    # Parse lint issues from ruff output
    while IFS= read -r line; do
        if [[ "${line}" =~ ([a-zA-Z_/]+\.py):([0-9]+):([0-9]+):\ ([A-Z][0-9]+)\ (.+) ]]; then
            python3 -c "
import json
print(json.dumps({
    'category': 'lint',
    'tool': 'ruff',
    'rule': '${BASH_REMATCH[4]}',
    'severity': 'error',
    'message': $(python3 -c "import json; print(json.dumps('''${BASH_REMATCH[5]}'''))" 2>/dev/null || echo '""'),
    'file': '${BASH_REMATCH[1]}',
    'line': ${BASH_REMATCH[2]},
    'column': ${BASH_REMATCH[3]},
    'fixable': False
}))
" >> "${issues_file}" 2>/dev/null || true
        fi
    done < <(grep -E '\.py:[0-9]+:[0-9]+: [A-Z][0-9]+' "${full_log}" 2>/dev/null || true)

    # Parse mypy issues
    while IFS= read -r line; do
        if [[ "${line}" =~ ([a-zA-Z_/]+\.py):([0-9]+):\ (error|warning):\ (.+) ]]; then
            python3 -c "
import json
print(json.dumps({
    'category': 'type',
    'tool': 'mypy',
    'rule': 'type-error',
    'severity': '${BASH_REMATCH[3]}',
    'message': $(python3 -c "import json; print(json.dumps('''${BASH_REMATCH[4]}'''))" 2>/dev/null || echo '""'),
    'file': '${BASH_REMATCH[1]}',
    'line': ${BASH_REMATCH[2]},
    'column': 0,
    'fixable': False
}))
" >> "${issues_file}" 2>/dev/null || true
        fi
    done < <(grep -E '\.py:[0-9]+: (error|warning):' "${full_log}" 2>/dev/null || true)

    # Parse bandit issues
    while IFS= read -r line; do
        if [[ "${line}" =~ Issue:\ \[([A-Z][0-9]+:[a-z_]+)\]\ (.+) ]]; then
            python3 -c "
import json
print(json.dumps({
    'category': 'security',
    'tool': 'bandit',
    'rule': '${BASH_REMATCH[1]}',
    'severity': 'warning',
    'message': $(python3 -c "import json; print(json.dumps('''${BASH_REMATCH[2]}'''))" 2>/dev/null || echo '""'),
    'file': '',
    'line': 0,
    'column': 0,
    'fixable': False
}))
" >> "${issues_file}" 2>/dev/null || true
        fi
    done < <(grep -E 'Issue: \[' "${full_log}" 2>/dev/null || true)

    echo "${issues_file}"
}

# ---------------------------------------------------------------------------
# Build final report
# ---------------------------------------------------------------------------
build_report() {
    local issues_file="$1"
    local issue_count=0

    mkdir -p "$(dirname "${OUTPUT_FILE}")"

    python3 -c "
import json, sys
from collections import Counter
from datetime import datetime, timezone

issues = []
with open('${issues_file}') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            issues.append(json.loads(line))
        except json.JSONDecodeError:
            continue

# Deduplicate by (file, line, rule)
seen = set()
unique_issues = []
for issue in issues:
    key = (issue.get('file', ''), issue.get('line', 0), issue.get('rule', ''))
    if key not in seen:
        seen.add(key)
        unique_issues.append(issue)

# Classify
categories = Counter(i['category'] for i in unique_issues)
severities = Counter(i['severity'] for i in unique_issues)
fixable_count = sum(1 for i in unique_issues if i.get('fixable', False))

report = {
    'metadata': {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'tool': 'collect-issues',
        'run_id': '${RUN_ID}' if '${RUN_ID}' else None,
        'mode': 'local' if ${LOCAL_MODE:+True}${LOCAL_MODE:+}$( [[ "${LOCAL_MODE}" == "false" ]] && echo "False") else 'github',
        'project': 'superai-platform'
    },
    'summary': {
        'total_issues': len(unique_issues),
        'by_category': dict(categories),
        'by_severity': dict(severities),
        'fixable_count': fixable_count,
        'categories': {
            'lint': categories.get('lint', 0),
            'type': categories.get('type', 0),
            'security': categories.get('security', 0),
            'dependency': categories.get('dependency', 0)
        }
    },
    'issues': unique_issues
}

with open('${OUTPUT_FILE}', 'w') as f:
    json.dump(report, f, indent=2)

print(len(unique_issues))
" 2>/dev/null

    issue_count="$(python3 -c "
import json
with open('${OUTPUT_FILE}') as f:
    data = json.load(f)
print(data['summary']['total_issues'])
" 2>/dev/null || echo "0")"

    echo ""
    echo "============================================================================"
    echo "  CI/CD Issue Collection Report"
    echo "============================================================================"
    echo ""
    echo "  Output: ${OUTPUT_FILE}"
    echo ""

    python3 -c "
import json
with open('${OUTPUT_FILE}') as f:
    data = json.load(f)
summary = data['summary']
print(f\"  Total Issues: {summary['total_issues']}\")
print(f\"  Fixable:      {summary['fixable_count']}\")
print()
cats = summary.get('categories', {})
print(f\"  By Category:\")
print(f\"    Lint:       {cats.get('lint', 0)}\")
print(f\"    Type:       {cats.get('type', 0)}\")
print(f\"    Security:   {cats.get('security', 0)}\")
print(f\"    Dependency: {cats.get('dependency', 0)}\")
print()
sevs = summary.get('by_severity', {})
print(f\"  By Severity:\")
for sev, count in sorted(sevs.items()):
    print(f\"    {sev}: {count}\")
" 2>/dev/null || true

    echo ""
    echo "============================================================================"

    # Exit with issue count (capped at 125)
    if [[ ${issue_count} -gt 125 ]]; then
        exit 125
    fi
    exit "${issue_count}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local issues_file

    if [[ "${LOCAL_MODE}" == "true" ]]; then
        issues_file="$(collect_local_issues)"
    else
        issues_file="$(collect_gh_issues)"
    fi

    build_report "${issues_file}"
}

main "$@"
