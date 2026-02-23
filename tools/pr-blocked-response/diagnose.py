#!/usr/bin/env python3
"""
PR Blocked Response — Diagnose and Respond
eco-base autonomous bot: detects blocked PRs, diagnoses root cause,
attempts auto-fix, escalates to Issue if manual intervention needed.

Root causes handled:
  1. BEHIND main (strict_required_status_checks_policy=true) → auto update-branch
  2. CircleCI false positive in commit statuses → auto-fix via .circleci/config.yml
  3. dependabot.yml invalid Docker ignore rules → auto-fix
  4. DIRTY (merge conflict) → trigger @dependabot rebase
  5. Failing required checks → label + create tracking issue
"""
import os
import json
import subprocess
import sys
import re
import urllib.request
import urllib.error

REPO = os.environ.get("REPO", "indestructibleorg/eco-base")
SPECIFIC_PR = os.environ.get("SPECIFIC_PR", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "")

REQUIRED_CHECKS = {"validate", "lint", "test", "build", "opa-policy", "supply-chain"}


def gh_run(args, **kwargs):
    return subprocess.run(["gh"] + args, capture_output=True, text=True, **kwargs)


def gh_api(path, method="GET", data=None):
    """Call GitHub API directly using urllib (no extra deps)."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    if data:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [API ERROR] {method} {path}: HTTP {e.code} — {body[:120]}")
        return {}
    except Exception as e:
        print(f"  [API ERROR] {method} {path}: {e}")
        return {}


def get_open_prs():
    if SPECIFIC_PR:
        r = gh_run(["pr", "view", SPECIFIC_PR, "--repo", REPO, "--json",
                    "number,title,state,mergeable,mergeStateStatus,statusCheckRollup,"
                    "labels,headRefName,headRefOid,author"])
        return [json.loads(r.stdout)] if r.returncode == 0 and r.stdout.strip() else []
    r = gh_run(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "50",
                "--json", "number,title,state,mergeable,mergeStateStatus,statusCheckRollup,"
                          "labels,headRefName,headRefOid,author"])
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []


def get_commit_statuses(head_sha):
    """Get commit statuses (different from check runs) for a SHA."""
    data = gh_api(f"/repos/{REPO}/commits/{head_sha}/statuses?per_page=50")
    if isinstance(data, list):
        return data
    return []


def get_check_runs(head_sha):
    """Get check runs for a SHA."""
    data = gh_api(f"/repos/{REPO}/commits/{head_sha}/check-runs?per_page=50")
    return data.get("check_runs", [])


def update_branch(pr_num, head_sha):
    """Update PR branch to be up-to-date with base (fixes BEHIND state)."""
    print(f"  [AUTO-FIX] Updating branch for PR #{pr_num} (was BEHIND main)...")
    result = gh_api(
        f"/repos/{REPO}/pulls/{pr_num}/update-branch",
        method="PUT",
        data={"expected_head_sha": head_sha}
    )
    msg = result.get("message", "")
    if "already up-to-date" in msg.lower() or "scheduled" in msg.lower() or msg == "":
        print(f"  [AUTO-FIX] Branch update triggered for PR #{pr_num}")
        return True
    # Also try without expected_head_sha if it fails
    result2 = gh_api(
        f"/repos/{REPO}/pulls/{pr_num}/update-branch",
        method="PUT",
        data={}
    )
    msg2 = result2.get("message", "")
    print(f"  [AUTO-FIX] Branch update result: {msg2 or 'OK'}")
    return True


def fix_circleci():
    """Create .circleci/config.yml to suppress CircleCI false positive."""
    path = ".circleci/config.yml"
    os.makedirs(".circleci", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(
                "version: 2.1\n"
                "# eco-base uses GitHub Actions for CI/CD.\n"
                "# This file exists solely to prevent CircleCI from attempting to parse\n"
                "# GitHub Actions workflow files as CircleCI configuration.\n"
                "# The actual CI/CD pipeline is defined in .github/workflows/ci.yaml\n"
                "# No CircleCI workflows are defined or used in this project.\n"
            )
        print("  [AUTO-FIX] Created .circleci/config.yml")
        return True
    return False


def fix_dependabot_yaml():
    """Fix invalid Docker ignore version rules in dependabot.yml."""
    path = ".github/dependabot.yml"
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        content = f.read()
    patterns = [
        r"\n    ignore:\n      # Python [^\n]+\n      - dependency-name: \"python\"\n        versions: \[[^\]]+\]\n      # Node [^\n]+\n      - dependency-name: \"node\"\n        versions: \[[^\]]+\]",
        r"\n    ignore:\n      - dependency-name: \"node\"\n        versions: \[[^\]]+\]",
        r"\n    ignore:\n      - dependency-name: \"python\"\n        versions: \[[^\]]+\]",
    ]
    fixed = content
    for p in patterns:
        fixed = re.sub(p, "", fixed)
    if fixed != content:
        with open(path, "w") as f:
            f.write(fixed)
        print("  [AUTO-FIX] Removed invalid Docker ignore version rules from dependabot.yml")
        return True
    return False


def trigger_rebase(pr_num):
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO,
                "--body", "@dependabot rebase"])
    ok = r.returncode == 0
    print(f"  [AUTO-FIX] @dependabot rebase on #{pr_num}: {'OK' if ok else r.stderr[:60]}")
    return ok


def enable_auto_merge(pr_num):
    """Enable auto-merge on a PR so it merges automatically once checks pass."""
    r = gh_run(["pr", "merge", str(pr_num), "--repo", REPO, "--auto", "--squash"])
    if r.returncode == 0:
        print(f"  [AUTO-MERGE] Enabled auto-merge for PR #{pr_num}")
        return True
    msg = r.stderr.strip()
    if "already enabled" in msg.lower() or "auto merge" in msg.lower():
        print(f"  [AUTO-MERGE] Already enabled for PR #{pr_num}")
        return True
    print(f"  [AUTO-MERGE] Failed for PR #{pr_num}: {msg[:80]}")
    return False


def add_label(pr_num, label):
    r = gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--add-label", label])
    if r.returncode == 0:
        print(f"  [LABEL] Added '{label}' to PR #{pr_num}")


def remove_label(pr_num, label):
    r = gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--remove-label", label])
    if r.returncode == 0:
        print(f"  [LABEL] Removed '{label}' from PR #{pr_num}")


def post_diagnosis_comment(pr_num, merge_status, failing, commit_status_failures,
                           skipped, diagnosis, auto_fixable, manual_required):
    # Check for existing diagnosis comment to avoid spam
    r = gh_run(["pr", "view", str(pr_num), "--repo", REPO, "--json", "comments"])
    if r.returncode == 0 and r.stdout.strip():
        comments = json.loads(r.stdout).get("comments", [])
        if any("Autonomous Bot" in c.get("body", "") and "PR Blocked Diagnosis" in c.get("body", "")
               for c in comments):
            print(f"  [COMMENT] Diagnosis comment already exists for #{pr_num}, skipping")
            return

    diagnosis_lines = "\n".join(f"- {d}" for d in diagnosis) if diagnosis else "- No specific diagnosis"
    auto_fix_lines = "\n".join(f"- `{a}`" for a in auto_fixable) if auto_fixable else "- None"
    manual_lines = "\n".join(f"- `{m}`" for m in manual_required) if manual_required else "- None"
    failing_lines = "\n".join(f"- ❌ `{f['name']}`" for f in failing) if failing else "- None"
    cs_lines = "\n".join(f"- ⚠️ `{s['context']}` ({s['state']})" for s in commit_status_failures) if commit_status_failures else "- None"
    skipped_lines = "\n".join(f"- ⏭ `{s}`" for s in skipped) if skipped else "- None"

    body = (
        f"## Autonomous Bot: PR Blocked Diagnosis\n\n"
        f"PR #{pr_num} is currently blocked (`{merge_status}`).\n\n"
        f"### Root Cause Analysis\n{diagnosis_lines}\n\n"
        f"### Auto-Fix Actions Taken\n{auto_fix_lines}\n\n"
        f"### Requires Manual Review\n{manual_lines}\n\n"
        f"### Failing Check Runs\n{failing_lines}\n\n"
        f"### Failing Commit Statuses\n{cs_lines}\n\n"
        f"### Skipped Checks (expected)\n{skipped_lines}\n\n"
        f"---\n"
        f"*Auto-generated by PR Blocked Response workflow. "
        f"If the issue persists after auto-fix, please review the failing checks above.*\n"
    )
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO, "--body", body])
    print(f"  [COMMENT] Posted diagnosis: {'OK' if r.returncode == 0 else r.stderr[:80]}")


def create_tracking_issue(pr_num, pr_title, pr_branch, merge_status, manual_required, diagnosis):
    r = gh_run(["issue", "list", "--repo", REPO, "--state", "open",
                "--label", "blocked", "--json", "number,title"])
    existing = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    if any(f"PR #{pr_num}" in i["title"] for i in existing):
        print(f"  [ISSUE] Tracking issue for #{pr_num} already exists")
        return

    diagnosis_lines = "\n".join(f"- {d}" for d in diagnosis)
    manual_lines = "\n".join(f"- `{m}`" for m in manual_required)
    title = f"[Auto] PR #{pr_num} blocked: {', '.join(manual_required[:3])}"
    body = (
        f"## PR #{pr_num} is blocked and requires manual intervention\n\n"
        f"**PR:** https://github.com/{REPO}/pull/{pr_num}\n"
        f"**Title:** {pr_title}\n"
        f"**Branch:** `{pr_branch}`\n"
        f"**Block reason:** `{merge_status}`\n\n"
        f"### Failing Checks (require manual fix)\n{manual_lines}\n\n"
        f"### Diagnosis\n{diagnosis_lines}\n\n"
        f"### Next Steps\n"
        f"1. Review the failing checks in the PR\n"
        f"2. Fix the root cause in the source branch\n"
        f"3. Push the fix to trigger a new CI run\n"
        f"4. The PR will auto-merge once all required checks pass\n\n"
        f"---\n*Auto-created by PR Blocked Response workflow*\n"
    )
    r = gh_run(["issue", "create", "--repo", REPO,
                "--title", title, "--body", body,
                "--label", "blocked,needs-attention"])
    print(f"  [ISSUE] Created: {'OK - ' + r.stdout.strip() if r.returncode == 0 else r.stderr[:80]}")


def commit_auto_fixes():
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not r.stdout.strip():
        print("\n[GIT] No auto-fixes to commit")
        return
    subprocess.run(["git", "config", "user.email", "bot@eco-base.dev"])
    subprocess.run(["git", "config", "user.name", "eco-base-bot"])
    import time
    branch = f"bot/auto-fix-blocked-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m",
                    "fix(bot): auto-fix PR blocked issues\n\n"
                    "- Added .circleci/config.yml to suppress CircleCI false positive\n"
                    "- Fixed dependabot.yml invalid Docker ignore version rules"])
    r_push = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True)
    if r_push.returncode != 0:
        print(f"\n[GIT] Push failed: {r_push.stderr[:80]}")
        return
    r_pr = subprocess.run([
        "gh", "pr", "create",
        "--title", "fix(bot): auto-fix PR blocked issues",
        "--body", "Automated fix by PR Blocked Response workflow.\n\n"
                  "- Added .circleci/config.yml to suppress CircleCI false positive\n"
                  "- Fixed dependabot.yml invalid Docker ignore version rules\n\n"
                  "This PR was created automatically and will auto-merge once required checks pass.",
        "--label", "automated,bot-pr",
        "--base", "main",
        "--head", branch
    ], capture_output=True, text=True)
    if r_pr.returncode == 0:
        pr_url = r_pr.stdout.strip()
        print(f"\n[GIT] Created PR: {pr_url}")
        subprocess.run(["gh", "pr", "merge", pr_url, "--auto", "--squash"])
        print("[GIT] Auto-merge enabled")
    else:
        print(f"\n[GIT] PR creation failed: {r_pr.stderr[:80]}")


def main():
    prs = get_open_prs()
    print(f"Scanning {len(prs)} open PRs...")

    # ── Phase 1: Handle BEHIND PRs (strict_required_status_checks_policy) ──
    # These are PRs where all required checks pass but the branch is behind main.
    # The fix is to call update-branch API and enable auto-merge.
    behind_prs = [p for p in prs if p.get("mergeStateStatus") == "BEHIND"]
    print(f"Found {len(behind_prs)} BEHIND PRs: {[p['number'] for p in behind_prs]}")

    for pr in behind_prs:
        pr_num = pr["number"]
        pr_title = pr["title"]
        head_sha = pr.get("headRefOid", "")
        labels = [l["name"] for l in pr.get("labels", [])]

        print(f"\n=== PR #{pr_num} [BEHIND]: {pr_title[:60]} ===")

        # Skip if human review required
        if "human-review-required" in labels:
            print(f"  SKIP: has human-review-required label")
            continue

        # Update branch to sync with main
        if head_sha:
            update_branch(pr_num, head_sha)
        else:
            update_branch(pr_num, "")

        # Enable auto-merge so it merges automatically after CI passes
        enable_auto_merge(pr_num)

    # ── Phase 2: Handle BLOCKED PRs ──
    blocked = [p for p in prs if p.get("mergeStateStatus") in ("BLOCKED", "DIRTY", "UNSTABLE")]
    print(f"\nFound {len(blocked)} BLOCKED/DIRTY/UNSTABLE PRs: {[p['number'] for p in blocked]}")

    any_auto_fix = False

    for pr in blocked:
        pr_num = pr["number"]
        pr_title = pr["title"]
        pr_branch = pr.get("headRefName", "")
        head_sha = pr.get("headRefOid", "")
        merge_status = pr.get("mergeStateStatus", "BLOCKED")
        checks = pr.get("statusCheckRollup", [])
        labels = [l["name"] for l in pr.get("labels", [])]

        print(f"\n=== PR #{pr_num}: {pr_title[:60]} ===")
        print(f"  MergeStateStatus: {merge_status}")

        # Check runs (GitHub Actions)
        failing_checks = [c for c in checks
                          if c.get("conclusion") in ("FAILURE", "failure", "ERROR", "error")]
        skipped = [c.get("name") or c.get("context", "?") for c in checks
                   if c.get("conclusion") == "SKIPPED" or c.get("status") == "SKIPPED"]

        # Commit statuses (CircleCI, CodeRabbit, etc.) — SEPARATE from check runs!
        commit_statuses = get_commit_statuses(head_sha) if head_sha else []
        failing_commit_statuses = [s for s in commit_statuses
                                   if s.get("state") in ("error", "failure", "pending")]
        # Filter out non-blocking commit statuses (CircleCI is a false positive)
        circleci_statuses = [s for s in failing_commit_statuses
                             if "circleci" in s.get("context", "").lower()]
        other_failing_statuses = [s for s in failing_commit_statuses
                                  if "circleci" not in s.get("context", "").lower()]

        print(f"  Failing check runs: {[f.get('name') for f in failing_checks]}")
        print(f"  Failing commit statuses: {[s.get('context') for s in failing_commit_statuses]}")

        # Check if all REQUIRED checks pass
        passing_required = {c.get("name") for c in checks
                            if c.get("conclusion") in ("SUCCESS", "success")
                            and c.get("name") in REQUIRED_CHECKS}
        all_required_pass = REQUIRED_CHECKS.issubset(passing_required)
        print(f"  Required checks passing: {passing_required}")
        print(f"  All required pass: {all_required_pass}")

        diagnosis = []
        auto_fixable = []
        manual_required = []

        # ── Diagnose check run failures ──
        for f in failing_checks:
            name = f.get("name", "")
            if name == ".github/dependabot.yml":
                diagnosis.append("dependabot.yml has invalid syntax (Docker ignore version format)")
                auto_fixable.append("dependabot.yml")
            elif name == "CircleCI Pipeline":
                diagnosis.append("CircleCI false positive (not a CircleCI project)")
                auto_fixable.append("circleci")
            elif any(k in name.lower() for k in ("yaml-lint", "validate", "lint")):
                diagnosis.append(f"Workflow validation failed: {name}")
                auto_fixable.append("workflow-lint")
            elif any(k in name.lower() for k in ("test", "spec")):
                diagnosis.append(f"Tests failing: {name}")
                manual_required.append(name)
            elif any(k in name.lower() for k in ("security", "scan", "cve", "grype")):
                diagnosis.append(f"Security scan failed: {name}")
                manual_required.append(name)
            else:
                diagnosis.append(f"Unknown failure: {name}")
                manual_required.append(name)

        # ── Diagnose commit status failures ──
        if circleci_statuses:
            diagnosis.append("CircleCI commit status error (false positive — not a CircleCI project)")
            auto_fixable.append("circleci")
            print(f"  [DIAGNOSIS] CircleCI commit status is blocking merge (false positive)")

        for s in other_failing_statuses:
            ctx = s.get("context", "unknown")
            state = s.get("state", "error")
            diagnosis.append(f"Commit status '{ctx}' is {state}")
            # Non-required statuses shouldn't block, but they do affect mergeable_state
            # We can't auto-fix these, but we can note them
            print(f"  [DIAGNOSIS] Non-required commit status blocking: {ctx} ({state})")

        # ── Handle BEHIND within BLOCKED (strict policy) ──
        if merge_status == "BLOCKED" and all_required_pass and not failing_checks and not other_failing_statuses:
            if not circleci_statuses:
                # Branch is behind main (strict policy) — update it
                diagnosis.append("Branch is behind main (strict_required_status_checks_policy=true)")
                auto_fixable.append("update-branch")
                print(f"  [DIAGNOSIS] Branch behind main, triggering update-branch")
                if head_sha:
                    update_branch(pr_num, head_sha)
                enable_auto_merge(pr_num)

        if merge_status == "DIRTY":
            diagnosis.append("Merge conflict with main branch")
            auto_fixable.append("rebase")

        # ── Execute auto-fixes ──
        if "circleci" in auto_fixable:
            if fix_circleci():
                any_auto_fix = True

        if "dependabot.yml" in auto_fixable:
            if fix_dependabot_yaml():
                any_auto_fix = True

        if "rebase" in auto_fixable:
            trigger_rebase(pr_num)

        # If all required checks pass and only CircleCI commit status is blocking,
        # enable auto-merge — it will merge once the branch is updated
        if all_required_pass and not failing_checks and not manual_required:
            if "human-review-required" not in labels:
                enable_auto_merge(pr_num)
                # Also try to update the branch
                if head_sha and merge_status == "BLOCKED":
                    update_branch(pr_num, head_sha)

        # ── Label management ──
        if failing_checks and "blocked" not in labels:
            add_label(pr_num, "blocked")
        elif not failing_checks and "blocked" in labels:
            remove_label(pr_num, "blocked")

        if manual_required and "human-review-required" not in labels:
            add_label(pr_num, "human-review-required")

        # ── Post diagnosis comment (only when there are real failures) ──
        if failing_checks or other_failing_statuses:
            post_diagnosis_comment(pr_num, merge_status, failing_checks,
                                   failing_commit_statuses, skipped,
                                   diagnosis, auto_fixable, manual_required)

        # ── Create tracking issue for manual-required items ──
        if manual_required:
            create_tracking_issue(pr_num, pr_title, pr_branch, merge_status,
                                  manual_required, diagnosis)

    # ── Phase 3: Commit any file-based auto-fixes ──
    if any_auto_fix:
        commit_auto_fixes()

    print("\nDone! PR Blocked Response complete.")


if __name__ == "__main__":
    main()
