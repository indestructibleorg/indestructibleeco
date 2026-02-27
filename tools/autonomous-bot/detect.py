#!/usr/bin/env python3
"""Autonomous Bot — Phase 1: Detect all actionable problems.
Defense Matrix Layer 4: AI Risk Assessment + Human-in-the-Loop Gate
"""
import json, os, subprocess, re, glob, urllib.request
from datetime import datetime, timezone

token = os.environ.get("GITHUB_TOKEN", "")
repo = os.environ.get("GITHUB_REPOSITORY", "")
ci_conclusion = os.environ.get("CI_CONCLUSION", "")
problems = []

# ── Sensitive path patterns (require human review — bot cannot auto-merge) ──
SENSITIVE_PATHS = [
    r"secrets/", r"\.enc\.yaml$", r"\.sops\.yaml$",
    r"policy/", r"SECURITY\.md", r"security-gates\.yaml",
    r"supply-chain\.yaml", r"\.github/CODEOWNERS", r"\.mergify\.yml",
    r"k8s/overlays/prod/", r"payment/", r"credential",
]

def is_sensitive_path(path: str) -> bool:
    return any(re.search(p, path) for p in SENSITIVE_PATHS)

def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        url, headers=headers, method=method,
        data=json.dumps(data).encode() if data else None,
    )
    try:
        with urllib.request.urlopen(req, encoding='utf-8') as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {path}: {e}")
        return {}

def ai_risk_score(problem: dict) -> dict:
    """
    AI-style risk assessment based on problem attributes.
    Returns risk_level (low/medium/high/critical) and requires_human_review.
    In production, this would call an LLM API for semantic analysis.
    """
    severity = problem.get("severity", "low")
    fix_strategy = problem.get("fix_strategy", "")
    affected_paths = problem.get("affected_paths", [])

    # Check if any affected path is sensitive
    touches_sensitive = any(is_sensitive_path(p) for p in affected_paths)

    # Risk scoring matrix
    base_score = {"critical": 90, "high": 70, "medium": 40, "low": 20}.get(severity, 20)

    if touches_sensitive:
        base_score += 30
    if fix_strategy in ("bump_dependency", "pin_actions"):
        base_score -= 10  # Well-understood, low-risk fixes
    if fix_strategy == "run_autofix_engine":
        base_score += 10  # Less predictable

    risk_level = (
        "critical" if base_score >= 90 else
        "high" if base_score >= 70 else
        "medium" if base_score >= 40 else
        "low"
    )

    requires_human = touches_sensitive or risk_level in ("critical", "high")

    return {
        "risk_score": min(base_score, 100),
        "risk_level": risk_level,
        "requires_human_review": requires_human,
        "touches_sensitive_paths": touches_sensitive,
        "ai_assessment": f"Risk {risk_level} ({base_score}/100). {'Human review required.' if requires_human else 'Safe for auto-merge.'}",
    }

# ── 1. CI failure ────────────────────────────────────────────────────────────
if ci_conclusion == "failure":
    p = {
        "id": "ci-failure",
        "type": "ci_failure",
        "severity": "high",
        "title": "CI/CD pipeline failed",
        "description": "The eco-base CI/CD pipeline failed. Auto-fix engine will attempt remediation.",
        "auto_fixable": True,
        "fix_strategy": "run_autofix_engine",
        "affected_paths": [".github/workflows/"],
    }
    p["risk"] = ai_risk_score(p)
    problems.append(p)

# ── 2. Dependabot alerts ─────────────────────────────────────────────────────
try:
    url = f"https://api.github.com/repos/{repo}/dependabot/alerts?state=open&per_page=30"
    req = urllib.request.Request(url, headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req, encoding='utf-8') as r:
        alerts = json.loads(r.read())
    for alert in alerts:
        sev = alert.get("security_advisory", {}).get("severity", "unknown")
        pkg = alert.get("dependency", {}).get("package", {}).get("name", "unknown")
        eco = alert.get("dependency", {}).get("package", {}).get("ecosystem", "unknown")
        if sev in ("critical", "high"):
            p = {
                "id": f"dep-{alert['number']}",
                "type": "dependency_vulnerability",
                "severity": sev,
                "title": f"[{sev.upper()}] Vulnerable dependency: {pkg} ({eco})",
                "description": f"Dependabot alert #{alert['number']}: {pkg} has a {sev} severity vulnerability.",
                "auto_fixable": True,
                "fix_strategy": "bump_dependency",
                "package": pkg,
                "ecosystem": eco,
                "alert_number": alert["number"],
                "affected_paths": [],
            }
            p["risk"] = ai_risk_score(p)
            problems.append(p)
except Exception as e:
    print(f"Could not fetch Dependabot alerts: {e}")

# ── 3. Workflow YAML lint ────────────────────────────────────────────────────
try:
    result = subprocess.run(
        ["python3", "tools/ci-validator/validate.py", "--report=/tmp/validate-report.json"],
        capture_output=True, text=True, timeout=60,
    )
    if os.path.exists("/tmp/validate-report.json"):
        with open("/tmp/validate-report.json", encoding='utf-8') as f:
            report = json.load(f)
        errors = report.get("errors", [])
        if errors:
            p = {
                "id": "workflow-lint",
                "type": "workflow_lint",
                "severity": "medium",
                "title": f"Workflow lint: {len(errors)} error(s) detected",
                "description": f"CI validator found {len(errors)} workflow syntax/policy errors.",
                "auto_fixable": True,
                "fix_strategy": "run_autofix_engine",
                "error_count": len(errors),
                "affected_paths": [".github/workflows/"],
            }
            p["risk"] = ai_risk_score(p)
            problems.append(p)
except Exception as e:
    print(f"Validator error: {e}")

# ── 4. Unpinned GitHub Actions ───────────────────────────────────────────────
unpinned = []
for wf_file in glob.glob(".github/workflows/*.yaml") + glob.glob(".github/workflows/*.yml"):
    with open(wf_file, encoding='utf-8') as f:
        content = f.read()
    for use in re.findall(r"uses:\s+(\S+)", content):
        if "@" in use:
            ref = use.split("@")[1]
            if not re.match(r"^[0-9a-f]{40}$", ref):
                unpinned.append(f"{wf_file}: {use}")
if unpinned:
    p = {
        "id": "unpinned-actions",
        "type": "security_policy",
        "severity": "medium",
        "title": f"Security: {len(unpinned)} unpinned GitHub Actions",
        "description": f"{len(unpinned)} GitHub Actions are not pinned to a full SHA.",
        "auto_fixable": True,
        "fix_strategy": "pin_actions",
        "count": len(unpinned),
        "affected_paths": [".github/workflows/"],
    }
    p["risk"] = ai_risk_score(p)
    problems.append(p)

# ── 5. Stale merged branches (cleanup) ──────────────────────────────────────
try:
    branches_resp = gh_api("/branches?per_page=100")
    if isinstance(branches_resp, list):
        bot_branches = [
            b["name"] for b in branches_resp
            if b["name"].startswith(("bot/", "fix/", "feat/", "chore/", "dependabot/"))
        ]
        # Check which are already merged
        merged_resp = gh_api("/pulls?state=closed&per_page=100")
        merged_branches = set()
        if isinstance(merged_resp, list):
            for pr in merged_resp:
                if pr.get("merged_at") and pr.get("head", {}).get("ref"):
                    merged_branches.add(pr["head"]["ref"])
        stale = [b for b in bot_branches if b in merged_branches]
        if stale:
            p = {
                "id": "stale-branches",
                "type": "branch_cleanup",
                "severity": "low",
                "title": f"Branch cleanup: {len(stale)} merged branches to delete",
                "description": f"Merged branches pending deletion: {', '.join(stale[:5])}{'...' if len(stale) > 5 else ''}",
                "auto_fixable": True,
                "fix_strategy": "delete_merged_branches",
                "branches": stale,
                "affected_paths": [],
            }
            p["risk"] = ai_risk_score(p)
            problems.append(p)
except Exception as e:
    print(f"Branch cleanup check error: {e}")

# ── 6. Security alerts (GitHub Advanced Security) ───────────────────────────
try:
    code_alerts = gh_api("/code-scanning/alerts?state=open&per_page=20")
    if isinstance(code_alerts, list) and code_alerts:
        critical_alerts = [a for a in code_alerts if a.get("rule", {}).get("severity") in ("critical", "high")]
        if critical_alerts:
            p = {
                "id": "code-scanning-alerts",
                "type": "security_alert",
                "severity": "high",
                "title": f"Code scanning: {len(critical_alerts)} critical/high alerts",
                "description": f"GitHub Code Scanning found {len(critical_alerts)} high-severity issues.",
                "auto_fixable": False,
                "fix_strategy": "manual_review_required",
                "count": len(critical_alerts),
                "affected_paths": list(set(
                    a.get("most_recent_instance", {}).get("location", {}).get("path", "")
                    for a in critical_alerts
                )),
            }
            p["risk"] = ai_risk_score(p)
            problems.append(p)
except Exception as e:
    print(f"Code scanning check: {e}")

# ── Output ───────────────────────────────────────────────────────────────────
print(f"\nTotal problems detected: {len(problems)}")
for p in problems:
    risk = p.get("risk", {})
    human_flag = " [HUMAN REQUIRED]" if risk.get("requires_human_review") else " [AUTO-FIXABLE]"
    print(f"  [{p['severity'].upper()}] {p['title']}{human_flag}")
    print(f"    Risk: {risk.get('risk_level','?')} ({risk.get('risk_score','?')}/100) — {risk.get('ai_assessment','')}")

problems_json = json.dumps(problems)
with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
    f.write(f"has_problems={'true' if problems else 'false'}\n")
    f.write(f"problem_count={len(problems)}\n")
    escaped = problems_json.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    f.write(f"problems_json={escaped}\n")
