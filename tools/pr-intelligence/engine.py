#!/usr/bin/env python3
"""
PR Intelligence Engine — eco-base
Scans ALL open PRs, classifies each one, and takes the correct action
according to industry best practices.

Decision Matrix:
  SAFE_TO_MERGE              → enable auto-merge (squash)
  NEEDS_REBASE               → comment @dependabot rebase / git rebase
  NEEDS_CI_FIX               → re-run failed checks
  MAJOR_VERSION              → label human-review-required + comment
  STALE                      → warn or close after 60d
  CLOSE_UNSAFE               → close + comment safe replacement
  BOT_PR_CI_FAILED           → re-run CI on bot PR
  REMOVE_HUMAN_REVIEW_AND_MERGE → remove label, enable auto-merge
  HUMAN_REVIEW               → add label + comment reason
  ALREADY_HANDLED            → no action (auto-merge already enabled)
  MONITOR                    → no action (CI in progress)
  SKIP                       → draft PR, ignore
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "indestructibleorg/eco-base")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Versions known to be non-LTS or beta — should be replaced
# title_must_contain prevents false positives (e.g. nginx matching node patterns)
UNSAFE_DOCKER_VERSIONS = {
    "node": {
        "title_must_contain": "node",
        "unsafe_patterns": [" 21-", " 23-", " 25-", " 27-", "node:21", "node:23", "node:25", "node:27"],
        "safe_replacement": "22-alpine",
        "reason": "Node 25 is odd-numbered (non-LTS). Use Node 22 LTS.",
    },
    "python": {
        "title_must_contain": "python",
        "unsafe_patterns": ["3.14-", "3.15-", "3.14.", "3.15."],
        "safe_replacement": "3.13-slim",
        "reason": "Python 3.14 is beta (stable Oct 2026). Use Python 3.13.",
    },
}

# Major version upgrades assessed as low-risk — can be auto-approved
MAJOR_VERSION_SAFE = {
    "sigstore/cosign-installer": True,
    "github/codeql-action": True,
    "nginx": True,
}


def gh(args, capture=True):
    """Run gh CLI command."""
    cmd = ["gh"] + args
    if capture:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    else:
        return subprocess.run(cmd).returncode, "", ""


def get_all_open_prs():
    """Get all open PRs with full details."""
    code, out, err = gh([
        "pr", "list", "--repo", REPO,
        "--state", "open", "--limit", "100",
        "--json", "number,title,author,labels,url,createdAt,updatedAt,"
                  "statusCheckRollup,mergeStateStatus,isDraft,autoMergeRequest,"
                  "headRefName,baseRefName,mergeable"
    ])
    if code != 0:
        print(f"ERROR listing PRs: {err}", file=sys.stderr)
        return []
    return json.loads(out or "[]")


def classify_pr(pr):
    """
    Classify a PR and determine the correct action.
    Returns: (action, reason, details)
    """
    title = pr["title"].lower()
    author = pr.get("author", {}).get("login", "")
    labels = [l["name"] for l in pr.get("labels", [])]
    checks = pr.get("statusCheckRollup", []) or []
    mergeable = pr.get("mergeable", "UNKNOWN")
    is_draft = pr.get("isDraft", False)
    has_auto_merge = pr.get("autoMergeRequest") is not None
    created_at = pr.get("createdAt", "")
    branch = pr.get("headRefName", "")

    # ── Draft PRs: skip ──────────────────────────────────────────
    if is_draft:
        return "SKIP", "Draft PR", {}

    # ── Check CI status ──────────────────────────────────────────
    required_checks = {"validate", "lint", "opa-policy", "test", "build", "supply-chain"}
    check_results = {}
    for c in checks:
        name = c.get("name") or c.get("context", "")
        state = c.get("state") or c.get("conclusion") or "UNKNOWN"
        if name in required_checks:
            check_results[name] = state.upper()

    required_passing = (
        len(check_results) > 0 and
        all(check_results.get(c) == "SUCCESS" for c in required_checks if c in check_results)
    )
    has_required_failures = any(
        check_results.get(c) in ("FAILURE", "ERROR")
        for c in required_checks if c in check_results
    )

    # ── human-review-required label ───────────────────────────────
    if "human-review-required" in labels:
        # Check if this is a known safe major version upgrade
        for pkg, is_safe in MAJOR_VERSION_SAFE.items():
            if pkg.lower() in title and is_safe:
                return "REMOVE_HUMAN_REVIEW_AND_MERGE", f"Major version upgrade assessed as low-risk: {pkg}", {}
        # Check for unsafe versions that should be closed
        for pkg, info in UNSAFE_DOCKER_VERSIONS.items():
            must_contain = info.get("title_must_contain", pkg)
            if must_contain not in title:
                continue
            for pattern in info["unsafe_patterns"]:
                if pattern in title:
                    return "CLOSE_UNSAFE", info["reason"], {
                        "pkg": pkg, "safe": info["safe_replacement"]
                    }
        # Genuinely needs human review (e.g. nvidia/cuda)
        return "HUMAN_REVIEW", "Requires human assessment (major version or unknown risk)", {}

    # ── Unsafe versions (not yet labeled) ────────────────────────
    for pkg, info in UNSAFE_DOCKER_VERSIONS.items():
        must_contain = info.get("title_must_contain", pkg)
        if must_contain not in title:
            continue  # Avoid false positives (e.g. nginx matching node patterns)
        for pattern in info["unsafe_patterns"]:
            if pattern in title:
                return "CLOSE_UNSAFE", info["reason"], {
                    "pkg": pkg, "safe": info["safe_replacement"]
                }

    # ── Dependabot PRs ───────────────────────────────────────────
    is_dependabot = author in ("dependabot[bot]", "app/dependabot")
    if is_dependabot:
        if mergeable == "CONFLICTING":
            return "NEEDS_REBASE", "Branch has conflicts with main", {}
        if has_required_failures:
            failing = [k for k, v in check_results.items() if v in ("FAILURE", "ERROR")]
            return "NEEDS_CI_FIX", f"Required CI checks failing: {failing}", {}
        if required_passing and not has_auto_merge:
            return "ENABLE_AUTO_MERGE", "All required CI checks pass, auto-merge not yet enabled", {}
        if required_passing and has_auto_merge:
            return "ALREADY_HANDLED", "Auto-merge already enabled, waiting for CI", {}
        if not check_results:
            return "NEEDS_REBASE", "No CI checks found — branch may be stale, needs rebase", {}
        return "MONITOR", "CI in progress", {}

    # ── Bot PRs (autonomous-bot, auto-fix-ci, etc.) ──────────────
    is_bot_pr = (
        author in ("app/github-actions", "github-actions[bot]")
        or branch.startswith("bot/")
        or "automated" in labels
        or "auto-merge" in labels
    )
    if is_bot_pr:
        if has_required_failures:
            failing = [k for k, v in check_results.items() if v in ("FAILURE", "ERROR")]
            return "BOT_PR_CI_FAILED", f"Bot PR CI failing: {failing}", {}
        if required_passing and not has_auto_merge:
            return "ENABLE_AUTO_MERGE", "Bot PR CI passes but auto-merge not enabled", {}
        if required_passing and has_auto_merge:
            return "ALREADY_HANDLED", "Bot PR: auto-merge enabled, waiting", {}
        return "MONITOR", "Bot PR CI in progress", {}

    # ── Stale PRs (> 60 days no update) ──────────────────────────
    if created_at:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days > 60:
                return "STALE", f"PR is {age_days} days old with no recent activity", {"age_days": age_days}
        except Exception:
            pass

    # ── Default: monitor ─────────────────────────────────────────
    return "MONITOR", "No action needed at this time", {}


def process_pr(pr, action, reason, details):
    """Execute the determined action on a PR."""
    number = pr["number"]
    title = pr["title"]
    author = pr.get("author", {}).get("login", "")
    is_dependabot = author in ("dependabot[bot]", "app/dependabot")

    print(f"\n  PR #{number}: {title[:65]}")
    print(f"  Action: {action} — {reason}")

    if DRY_RUN:
        print(f"  [DRY RUN] Would execute: {action}")
        return {"pr": number, "action": action, "reason": reason, "executed": False}

    result = {"pr": number, "action": action, "reason": reason, "executed": True}

    if action == "ENABLE_AUTO_MERGE":
        code, out, err = gh(["pr", "merge", str(number), "--auto", "--squash",
                              "--repo", REPO])
        if code == 0:
            print(f"  ✅ Auto-merge enabled")
        else:
            print(f"  ⚠️  Auto-merge failed: {err[:120]}")
            result["error"] = err[:120]

    elif action == "REMOVE_HUMAN_REVIEW_AND_MERGE":
        gh(["pr", "edit", str(number), "--remove-label", "human-review-required",
            "--repo", REPO])
        gh(["pr", "edit", str(number), "--add-label", "automated", "--repo", REPO])
        code, out, err = gh(["pr", "merge", str(number), "--auto", "--squash",
                              "--repo", REPO])
        if code == 0:
            print(f"  ✅ Removed human-review label, auto-merge enabled")
        else:
            print(f"  ⚠️  Auto-merge failed: {err[:120]}")
            result["error"] = err[:120]

    elif action == "NEEDS_REBASE":
        if is_dependabot:
            gh(["pr", "comment", str(number), "--body", "@dependabot rebase",
                "--repo", REPO])
            print(f"  ✅ Triggered @dependabot rebase")
        else:
            gh(["pr", "comment", str(number),
                "--body", "This PR has conflicts with main. Please rebase.",
                "--repo", REPO])
            print(f"  ✅ Commented: needs rebase")

    elif action == "NEEDS_CI_FIX":
        branch = pr.get("headRefName", "")
        code2, run_out, _ = gh(["run", "list", "--repo", REPO,
                                 "--branch", branch,
                                 "--json", "databaseId,conclusion",
                                 "--limit", "1"])
        if code2 == 0 and run_out:
            try:
                runs = json.loads(run_out)
                if runs and runs[0].get("conclusion") in ("failure", "cancelled"):
                    gh(["run", "rerun", str(runs[0]["databaseId"]),
                        "--failed", "--repo", REPO])
                    print(f"  ✅ Re-ran failed CI run")
                    return result
            except Exception:
                pass
        gh(["pr", "comment", str(number),
            "--body", f"CI fix needed: {reason}. Re-running checks.",
            "--repo", REPO])
        print(f"  ✅ Commented CI fix needed")

    elif action == "CLOSE_UNSAFE":
        pkg = details.get("pkg", "")
        safe = details.get("safe", "")
        msg = (f"Closing: {reason} "
               f"Safe replacement: `{safe}`. "
               f"A corrected PR will be created automatically.")
        gh(["pr", "close", str(number), "--comment", msg, "--repo", REPO])
        print(f"  ✅ Closed unsafe version PR")

    elif action == "BOT_PR_CI_FAILED":
        branch = pr.get("headRefName", "")
        code2, run_out, _ = gh(["run", "list", "--repo", REPO,
                                 "--branch", branch,
                                 "--json", "databaseId,conclusion",
                                 "--limit", "1"])
        if code2 == 0 and run_out:
            try:
                runs = json.loads(run_out)
                if runs and runs[0].get("conclusion") in ("failure", "cancelled"):
                    gh(["run", "rerun", str(runs[0]["databaseId"]),
                        "--failed", "--repo", REPO])
                    print(f"  ✅ Re-ran failed CI on bot PR")
                    return result
            except Exception:
                pass
        print(f"  ⚠️  Could not re-run CI (no failed run found)")

    elif action == "STALE":
        age = details.get("age_days", 0)
        if age > 60:
            gh(["pr", "close", str(number),
                "--comment", f"Closing stale PR ({age} days old, no recent activity).",
                "--repo", REPO])
            print(f"  ✅ Closed stale PR ({age}d)")
        else:
            gh(["pr", "comment", str(number),
                "--body", f"This PR has been open for {age} days. It will be closed after 60 days of inactivity.",
                "--repo", REPO])
            print(f"  ✅ Warned stale PR ({age}d)")

    elif action in ("SKIP", "MONITOR", "ALREADY_HANDLED", "HUMAN_REVIEW"):
        print(f"  ℹ️  No action taken")
        result["executed"] = False

    return result


def main():
    print(f"=== PR Intelligence Engine ===")
    print(f"Repo: {REPO}")
    print(f"Dry run: {DRY_RUN}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()

    prs = get_all_open_prs()
    print(f"Found {len(prs)} open PRs")

    results = []
    action_summary = {}

    for pr in prs:
        action, reason, details = classify_pr(pr)
        action_summary[action] = action_summary.get(action, 0) + 1
        result = process_pr(pr, action, reason, details)
        results.append(result)

    print(f"\n=== Summary ===")
    for action, count in sorted(action_summary.items()):
        print(f"  {action}: {count}")

    print(f"\nTotal PRs processed: {len(results)}")
    executed = sum(1 for r in results if r.get("executed"))
    print(f"Actions executed: {executed}")

    # Output for GitHub Actions
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"prs_processed={len(results)}\n")
            f.write(f"actions_executed={executed}\n")
            f.write(f"results_json={json.dumps(results)}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
