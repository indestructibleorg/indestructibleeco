#!/usr/bin/env python3
"""Autonomous Bot — Phase 1: Detect all actionable problems."""
import json, os, subprocess, re, glob, urllib.request
from datetime import datetime, timezone

token = os.environ.get("GITHUB_TOKEN", "")
repo = os.environ.get("GITHUB_REPOSITORY", "")
ci_conclusion = os.environ.get("CI_CONCLUSION", "")
problems = []

def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers, method=method, data=json.dumps(data).encode() if data else None)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {path}: {e}")
        return {}

# 1. CI failure
if ci_conclusion == "failure":
    problems.append({"id": "ci-failure", "type": "ci_failure", "severity": "high",
        "title": "CI/CD pipeline failed",
        "description": "The eco-base CI/CD pipeline failed. Auto-fix engine will attempt remediation.",
        "auto_fixable": True, "fix_strategy": "run_autofix_engine"})

# 2. Dependabot alerts
try:
    url = f"https://api.github.com/repos/{repo}/dependabot/alerts?state=open&per_page=30"
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req) as r:
        alerts = json.loads(r.read())
    for alert in alerts:
        sev = alert.get("security_advisory", {}).get("severity", "unknown")
        pkg = alert.get("dependency", {}).get("package", {}).get("name", "unknown")
        eco = alert.get("dependency", {}).get("package", {}).get("ecosystem", "unknown")
        if sev in ("critical", "high"):
            problems.append({"id": f"dep-{alert['number']}", "type": "dependency_vulnerability",
                "severity": sev, "title": f"[{sev.upper()}] Vulnerable dependency: {pkg} ({eco})",
                "description": f"Dependabot alert #{alert['number']}: {pkg} has a {sev} severity vulnerability.",
                "auto_fixable": True, "fix_strategy": "bump_dependency",
                "package": pkg, "ecosystem": eco, "alert_number": alert["number"]})
except Exception as e:
    print(f"Could not fetch Dependabot alerts: {e}")

# 3. Workflow YAML lint
try:
    result = subprocess.run(["python3", "tools/ci-validator/validate.py", "--report=/tmp/validate-report.json"],
        capture_output=True, text=True, timeout=60)
    if os.path.exists("/tmp/validate-report.json"):
        with open("/tmp/validate-report.json") as f:
            report = json.load(f)
        errors = report.get("errors", [])
        if errors:
            problems.append({"id": "workflow-lint", "type": "workflow_lint", "severity": "medium",
                "title": f"Workflow lint: {len(errors)} error(s) detected",
                "description": f"CI validator found {len(errors)} workflow syntax/policy errors.",
                "auto_fixable": True, "fix_strategy": "run_autofix_engine", "error_count": len(errors)})
except Exception as e:
    print(f"Validator error: {e}")

# 4. Unpinned GitHub Actions
unpinned = []
for wf_file in glob.glob(".github/workflows/*.yaml") + glob.glob(".github/workflows/*.yml"):
    with open(wf_file) as f:
        content = f.read()
    for use in re.findall(r"uses:\s+(\S+)", content):
        if "@" in use:
            ref = use.split("@")[1]
            if not re.match(r"^[0-9a-f]{40}$", ref):
                unpinned.append(f"{wf_file}: {use}")
if unpinned:
    problems.append({"id": "unpinned-actions", "type": "security_policy", "severity": "medium",
        "title": f"Security: {len(unpinned)} unpinned GitHub Actions",
        "description": f"{len(unpinned)} GitHub Actions are not pinned to a full SHA.",
        "auto_fixable": True, "fix_strategy": "pin_actions", "count": len(unpinned)})

# Output
print(f"Total problems detected: {len(problems)}")
for p in problems:
    print(f"  [{p['severity'].upper()}] {p['title']} (auto_fixable={p['auto_fixable']})")

problems_json = json.dumps(problems)
with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
    f.write(f"has_problems={'true' if problems else 'false'}\n")
    f.write(f"problem_count={len(problems)}\n")
    escaped = problems_json.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    f.write(f"problems_json={escaped}\n")
