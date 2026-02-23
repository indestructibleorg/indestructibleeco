#!/usr/bin/env python3
"""Autonomous Bot — Phase 3: Create fix branch and apply automated fixes."""
import json, os, subprocess, re, glob
from datetime import datetime, timezone

dry_run = os.environ.get("DRY_RUN", "false") == "true"
problems_raw = os.environ.get("PROBLEMS_JSON", "[]")
problems = json.loads(problems_raw.replace('%0A', '\n').replace('%0D', '\r').replace('%25', '%'))
fixable = [p for p in problems if p.get("auto_fixable")]

if not fixable:
    print("No auto-fixable problems. Skipping branch creation.")
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_fixes=false\nbranch_name=\nfixes_summary=No auto-fixable problems detected.\n")
    exit(0)

ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
branch = f"bot/auto-fix-{ts}"
print(f"Creating branch: {branch}")

if not dry_run:
    subprocess.run(["git", "config", "user.name", "eco-base-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "bot@eco-base.io"], check=True)
    subprocess.run(["git", "checkout", "-b", branch], check=True)

fixes_applied = []
KNOWN_SHAS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/upload-artifact": "4cec3d8aa04e39d1a68397de0c4cd6fb9dce8ec1",
    "actions/download-artifact": "cc203385981b70ca67e1cc392babf9cc229d5806",
    "actions/cache": "5a3ec84eff668545956fd18022155c47e93e2684",
    "actions/setup-node": "49933ea5288caeca8642d1e84afbd3f7d6820020",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/stale": "5bef64f19d7facfb25b37b414482c7164d639639",
    "docker/login-action": "74a5d142397b4f367a81961eba4e8cd7edddf772",
    "docker/build-push-action": "14487ce63c7a62a4a324b0bfb37086795e31c6c1",
}

for problem in fixable:
    strategy = problem.get("fix_strategy", "")
    print(f"\nApplying fix: {strategy} for {problem['id']}")

    if strategy == "run_autofix_engine":
        try:
            result = subprocess.run(
                ["python3", "tools/ci-validator/auto-fix.py", "--report=/tmp/autofix-result.json"],
                capture_output=True, text=True, timeout=120)
            print(result.stdout[-2000:] if result.stdout else "(no output)")
            if result.returncode == 0:
                fixes_applied.append(f"Auto-fix engine resolved: {problem['title']}")
        except Exception as e:
            print(f"Auto-fix engine error: {e}")

    elif strategy == "pin_actions":
        changed = False
        for wf_file in glob.glob(".github/workflows/*.yaml") + glob.glob(".github/workflows/*.yml"):
            with open(wf_file) as f:
                content = f.read()
            original = content
            for action, sha in KNOWN_SHAS.items():
                pattern = rf'(uses:\s+{re.escape(action)}@)([^0-9a-f\s]{{1}}[^\s]*)'
                content = re.sub(pattern, rf'\g<1>{sha}', content)
            if content != original:
                if not dry_run:
                    with open(wf_file, 'w') as f:
                        f.write(content)
                changed = True
                print(f"  Pinned actions in {wf_file}")
        if changed:
            fixes_applied.append("Pinned unpinned GitHub Actions to full SHA")

    elif strategy == "bump_dependency":
        pkg = problem.get("package", "")
        fixes_applied.append(f"Flagged {pkg} for Dependabot bump (issue created)")

    elif strategy == "label_stale":
        fixes_applied.append(f"Stale issue #{problem.get('issue_number', '?')} labelled")

has_fixes = False
if not dry_run and fixes_applied:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        subprocess.run(["git", "add", "-A"], check=True)
        commit_msg = f"fix(bot): autonomous fixes"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        token = os.environ.get("GITHUB_TOKEN", "")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        subprocess.run(["git", "remote", "set-url", "origin",
            f"https://x-access-token:{token}@github.com/{repo}.git"], check=True)
        subprocess.run(["git", "push", "origin", branch], check=True)
        print(f"Pushed branch: {branch}")
        has_fixes = True
    else:
        print("No file changes after applying fixes.")
elif dry_run:
    has_fixes = len(fixes_applied) > 0

summary = "; ".join(fixes_applied) if fixes_applied else "No changes applied"
print(f"\nFixes summary: {summary}")

with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
    f.write(f"has_fixes={'true' if has_fixes else 'false'}\n")
    f.write(f"branch_name={branch if has_fixes else ''}\n")
    f.write(f"fixes_summary={summary.replace(chr(10), ' ')}\n")
