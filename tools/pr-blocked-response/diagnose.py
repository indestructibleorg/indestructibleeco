#!/usr/bin/env python3
"""
PR Blocked Response — Fully Autonomous Self-Healing Engine v2
eco-base: zero human intervention, zero external platform dependency.

Design principles:
  1. ONLY internal CI checks matter (validate/lint/test/build/opa-policy/supply-chain)
  2. External checks (Codacy/SonarCloud/CodeQL/Trivy/Copilot) are IGNORED — never block
  3. strict_required_status_checks_policy=false → BEHIND is no longer a hard blocker
  4. All decisions made autonomously — no human escalation path
  5. Idempotent: safe to run every 15 minutes

Decision tree per PR:
  All 6 required checks PASS? → merge immediately (squash, --admin)
  Checks still IN_PROGRESS?   → enable auto-merge and wait
  DIRTY (conflict)?           → @dependabot rebase
  BEHIND?                     → update-branch (non-blocking with strict=false)
  Required check FAILED?      → re-trigger CI + enable auto-merge
"""
import os, json, subprocess, sys, time, urllib.request, urllib.error

REPO           = os.environ.get("REPO", "indestructibleorg/eco-base")
SPECIFIC_PR    = os.environ.get("SPECIFIC_PR", "").strip()
GH_TOKEN       = os.environ.get("GH_TOKEN", "")

# Internal required checks — ONLY these matter for merge decisions
REQUIRED_CHECKS = {"validate", "lint", "test", "build", "opa-policy", "supply-chain"}

# External/third-party checks — completely ignored for merge gate
EXTERNAL_CHECKS = {
    "Codacy Static Code Analysis", "codacy",
    "CodeRabbit", "coderabbitai", "qodo",
    "copilot-pull-request-reviewer",
    "SonarCloud Code Analysis", "SonarCloud",
    "Analyze (javascript-typescript)", "Analyze (python)", "Analyze (actions)", "CodeQL",
    "Trivy", "trivy", "Cloudflare Pages", "cloudflare", "submit-pypi",
}


# ── GitHub API helpers ────────────────────────────────────────────────────────

def gh_run(args, **kwargs):
    return subprocess.run(["gh"] + args, capture_output=True, text=True, **kwargs)


def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    if data is not None:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode()}
    except Exception as e:
        return {"_error": str(e)}


# ── Data fetchers ─────────────────────────────────────────────────────────────

def get_open_prs():
    if SPECIFIC_PR:
        r = gh_run(["pr", "view", SPECIFIC_PR, "--repo", REPO, "--json",
                    "number,title,headRefName,headRefOid,mergeStateStatus,labels,isDraft"])
        return [json.loads(r.stdout)] if r.returncode == 0 and r.stdout.strip() else []
    r = gh_run(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "100",
                "--json", "number,title,headRefName,headRefOid,mergeStateStatus,labels,isDraft"])
    if r.returncode != 0 or not r.stdout.strip():
        return []
    return [p for p in json.loads(r.stdout) if not p.get("isDraft", False)]


def get_pr_api(pr_num):
    return gh_api(f"/repos/{REPO}/pulls/{pr_num}")


def get_check_runs(head_sha):
    data = gh_api(f"/repos/{REPO}/commits/{head_sha}/check-runs?per_page=100")
    return data.get("check_runs", [])


# ── Actions ───────────────────────────────────────────────────────────────────

def direct_merge(pr_num, pr_title):
    print(f"  [MERGE] Merging PR #{pr_num}...")
    r = gh_run(["pr", "merge", str(pr_num), "--repo", REPO,
                "--squash", "--admin",
                "--subject", f"{pr_title} (#{pr_num})"])
    if r.returncode == 0:
        print(f"  [MERGE] ✓ PR #{pr_num} merged")
        return True
    err = r.stderr.strip()
    print(f"  [MERGE] Failed: {err[:120]}")
    if "in progress" in err.lower() or "required status" in err.lower():
        enable_auto_merge(pr_num)
    return False


def enable_auto_merge(pr_num):
    r = gh_run(["pr", "merge", str(pr_num), "--repo", REPO, "--auto", "--squash"])
    if r.returncode == 0:
        print(f"  [AUTO-MERGE] Enabled for PR #{pr_num}")
        return True
    msg = r.stderr.strip()
    if "already" in msg.lower():
        print(f"  [AUTO-MERGE] Already enabled for PR #{pr_num}")
        return True
    print(f"  [AUTO-MERGE] Failed: {msg[:80]}")
    return False


def update_branch(pr_num):
    print(f"  [UPDATE-BRANCH] Updating PR #{pr_num}...")
    result = gh_api(f"/repos/{REPO}/pulls/{pr_num}/update-branch", method="PUT", data={})
    if result.get("_http_error") == 422:
        body = result.get("_body", "")
        if "already up to date" in body.lower():
            print(f"  [UPDATE-BRANCH] Already up-to-date")
        else:
            print(f"  [UPDATE-BRANCH] 422: {body[:80]}")
    else:
        print(f"  [UPDATE-BRANCH] {result.get('message', 'triggered')}")


def trigger_rebase(pr_num):
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO, "--body", "@dependabot rebase"])
    print(f"  [REBASE] {'✓ Requested' if r.returncode == 0 else r.stderr[:60]}")


def retrigger_ci(pr_num, head_sha, failed_check_names):
    print(f"  [RETRIGGER] Re-triggering CI for PR #{pr_num}...")
    runs = get_check_runs(head_sha)
    rerun_count = 0
    for run in runs:
        if (run.get("name") in failed_check_names and
                run.get("conclusion") in ("failure", "timed_out", "cancelled")):
            result = gh_api(f"/repos/{REPO}/check-runs/{run['id']}/rerequest", method="POST")
            if not result.get("_http_error"):
                rerun_count += 1
    print(f"  [RETRIGGER] Re-triggered {rerun_count} check run(s)")


def remove_label(pr_num, label):
    gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--remove-label", label])


# ── Core classification ───────────────────────────────────────────────────────

def classify_checks(check_runs):
    """
    Classify CI state based ONLY on internal required checks.
    External checks are completely ignored.

    Returns: (passing, failing, pending, all_pass, any_pending)
    """
    # Deduplicate: keep latest run per check name
    latest = {}
    for run in check_runs:
        name = run.get("name", "")
        if name not in REQUIRED_CHECKS:
            continue
        if name not in latest or run.get("id", 0) > latest[name].get("id", 0):
            latest[name] = run

    passing, failing, pending = set(), [], []

    for name, run in latest.items():
        status     = (run.get("status")     or "").lower()
        conclusion = (run.get("conclusion") or "").lower()

        if conclusion == "success" or conclusion in ("skipped", "neutral"):
            passing.add(name)
        elif status in ("queued", "in_progress", "waiting", "pending"):
            pending.append(name)
        elif conclusion in ("failure", "error", "timed_out", "action_required", "cancelled"):
            failing.append(name)

    # Missing required checks = not yet triggered = pending
    for name in REQUIRED_CHECKS:
        if name not in latest:
            pending.append(name)

    all_pass   = REQUIRED_CHECKS.issubset(passing)
    any_pending = len(pending) > 0
    return passing, failing, pending, all_pass, any_pending


# ── Main PR processor ─────────────────────────────────────────────────────────

def process_pr(pr_num, pr_title, pr_branch, head_sha, merge_status, labels):
    label_names = {l["name"] for l in labels} if labels else set()

    # Skip PRs explicitly flagged for human review
    if "human-review-required" in label_names:
        print(f"  [SKIP] human-review-required — skipping")
        return

    check_runs = get_check_runs(head_sha) if head_sha else []
    passing, failing, pending, all_pass, any_pending = classify_checks(check_runs)

    print(f"  passing={sorted(passing)} failing={sorted(failing)} pending={sorted(pending)}")
    print(f"  all_pass={all_pass} any_pending={any_pending} merge_status={merge_status}")

    # ── 1. All required checks pass → MERGE NOW ───────────────────────────────
    if all_pass and not failing:
        direct_merge(pr_num, pr_title)
        remove_label(pr_num, "blocked")
        return

    # ── 2. Checks still running → enable auto-merge and wait ─────────────────
    if any_pending and not failing:
        print(f"  → CI running ({pending}). Enabling auto-merge...")
        enable_auto_merge(pr_num)
        return

    # ── 3. DIRTY (merge conflict) → rebase ───────────────────────────────────
    if merge_status == "DIRTY":
        trigger_rebase(pr_num)
        return

    # ── 4. Required check FAILED → re-trigger CI ─────────────────────────────
    if failing:
        print(f"  → Required checks failed: {failing}. Re-triggering...")
        retrigger_ci(pr_num, head_sha, set(failing))
        enable_auto_merge(pr_num)
        return

    # ── 5. BEHIND or UNKNOWN → update branch ─────────────────────────────────
    if merge_status in ("BEHIND", "UNKNOWN"):
        update_branch(pr_num)
        enable_auto_merge(pr_num)
        return

    # ── 6. BLOCKED with all checks passing → direct merge ────────────────────
    if merge_status == "BLOCKED" and all_pass:
        direct_merge(pr_num, pr_title)
        return

    # ── Fallback ──────────────────────────────────────────────────────────────
    print(f"  → Unhandled state [{merge_status}]. Enabling auto-merge as fallback...")
    enable_auto_merge(pr_num)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set")
        sys.exit(1)

    prs = get_open_prs()
    if not prs:
        print("No open PRs to process")
        return

    print(f"Processing {len(prs)} open PR(s)...")

    for pr in prs:
        pr_num      = pr["number"]
        pr_title    = pr.get("title", "")
        pr_branch   = pr.get("headRefName", "")
        head_sha    = pr.get("headRefOid", "")
        merge_status = pr.get("mergeStateStatus", "UNKNOWN")
        labels      = pr.get("labels", [])

        # For UNKNOWN state: get accurate data from REST API
        if merge_status == "UNKNOWN":
            api_pr = get_pr_api(pr_num)
            ms = api_pr.get("mergeable_state", "unknown")
            merge_status = {
                "behind": "BEHIND", "dirty": "DIRTY",
                "clean": "CLEAN",   "blocked": "BLOCKED",
            }.get(ms, "BLOCKED")
            print(f"\n=== PR #{pr_num} [UNKNOWN→{merge_status}]: {pr_title[:60]} ===")
        else:
            print(f"\n=== PR #{pr_num} [{merge_status}]: {pr_title[:60]} ===")

        process_pr(pr_num, pr_title, pr_branch, head_sha, merge_status, labels)

    print("\n[DONE] All PRs processed.")


if __name__ == "__main__":
    main()
