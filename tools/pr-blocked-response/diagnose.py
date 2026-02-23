#!/usr/bin/env python3
"""
PR Blocked Response — Fully Autonomous Self-Healing Engine v3
eco-base: zero human intervention, zero external platform dependency.

Design principles:
  1. ONLY internal CI checks matter (validate/lint/test/build/opa-policy/supply-chain)
  2. External checks (Codacy/SonarCloud/CodeQL/Trivy/Copilot) are IGNORED — never block
  3. strict_required_status_checks_policy=false → BEHIND is no longer a hard blocker
  4. All decisions made autonomously — no human escalation path
  5. Idempotent: safe to run every 15 minutes

AI/Bot Review Governance (policy/ai_bot_review.rego implemented here):
  TIER-1 (Auto-fix):   Mechanical comment (version mismatch in comment) → apply suggestion
  TIER-2 (Info only):  Style/quality suggestion → log, ignore, proceed with merge
  TIER-3 (Escalate):   Safety/correctness issue (non-existent tag, CVE, breaking change)
                       → keep human-review-required label, post explanation comment

Skipped Check Policy (policy/skipped_check_response.rego implemented here):
  Expected skips:      auto-fix, Supabase Preview, request-codacy-review → ignore, not blocking
  Unexpected skips:    required check skipped → treat as pending, re-trigger CI
  All other skips:     external/informational → ignore completely

Decision tree per PR:
  human-review-required label?  → evaluate AI/bot comments for TIER-3 escalations
                                   if no TIER-3 found → remove label and proceed
  All 6 required checks PASS?   → merge immediately (squash, --admin)
  Checks still IN_PROGRESS?     → enable auto-merge and wait
  DIRTY (conflict)?             → @dependabot rebase
  BEHIND?                       → update-branch (non-blocking with strict=false)
  Required check FAILED?        → re-trigger CI + enable auto-merge
  Required check SKIPPED?       → treat as pending, re-trigger CI
"""
import os, json, subprocess, sys, re, urllib.request, urllib.error

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

# Expected skips — these are NEVER blocking, even if conclusion=skipped
EXPECTED_SKIPS = {
    "auto-fix",           # Only runs on main branch failures
    "Supabase Preview",   # Only runs when branch is linked to Supabase
    "request-codacy-review",  # Only runs when codacy-review label is present
    "Auto-label New Issues",
}

# AI/Bot actors whose review comments are evaluated by governance policy
AI_BOT_ACTORS = {
    # GitHub Copilot review (inline review comments use login "Copilot")
    "Copilot",
    "copilot-pull-request-reviewer[bot]",
    "copilot-pull-request-reviewer",
    # CodeRabbit
    "coderabbitai[bot]",
    "coderabbitai",
    # Qodo
    "qodo-merge-pro[bot]",
    "qodo-merge-pro",
    # Codacy
    "codacy-production[bot]",
    "codacy-production",
    # SonarCloud
    "sonarqubecloud[bot]",
    "sonarqubecloud",
    # GitHub Advanced Security
    "github-advanced-security[bot]",
}

# TIER-3 escalation patterns — safety/correctness issues requiring human judgment
ESCALATION_PATTERNS = [
    r"does not exist",
    r"non-existent",
    r"invalid tag",
    r"tag not found",
    r"breaking change",
    r"security vulnerability",
    r"CVE-\d{4}-\d+",
    r"should be reconsidered",
    r"cannot be pulled",
    r"image not found",
    r"cuda \d+\.\d+ does not exist",
]

# TIER-1 auto-fix patterns — mechanical, safe to apply automatically
AUTO_FIX_PATTERNS = [
    r"comment.*still references",
    r"comment.*should be updated",
    r"documentation mismatch",
    r"typo",
]


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


def get_pr_review_comments(pr_num):
    """Get inline review comments (suggestions on specific lines)."""
    data = gh_api(f"/repos/{REPO}/pulls/{pr_num}/comments?per_page=100")
    return data if isinstance(data, list) else []


def get_pr_issue_comments(pr_num):
    """Get general PR comments (bot summaries, etc.)."""
    data = gh_api(f"/repos/{REPO}/issues/{pr_num}/comments?per_page=100")
    return data if isinstance(data, list) else []


def get_pr_reviews(pr_num):
    """Get formal PR reviews (APPROVED/CHANGES_REQUESTED/COMMENTED)."""
    data = gh_api(f"/repos/{REPO}/pulls/{pr_num}/reviews?per_page=100")
    return data if isinstance(data, list) else []


# ── AI/Bot governance ─────────────────────────────────────────────────────────

def is_escalation_comment(body):
    """TIER-3: Does this comment body indicate a safety/correctness issue?"""
    body_lower = body.lower()
    for pattern in ESCALATION_PATTERNS:
        if re.search(pattern, body_lower, re.IGNORECASE):
            return True
    return False


def is_auto_fix_comment(body):
    """TIER-1: Does this comment body indicate a safe mechanical fix?"""
    body_lower = body.lower()
    for pattern in AUTO_FIX_PATTERNS:
        if re.search(pattern, body_lower, re.IGNORECASE):
            return True
    return False


def evaluate_ai_bot_comments(pr_num):
    """
    Evaluate all AI/Bot comments on a PR using the governance policy.

    Returns:
        (has_escalation, escalation_reasons, auto_fix_suggestions)
        - has_escalation: True if any TIER-3 comment found
        - escalation_reasons: list of (actor, snippet) for TIER-3 comments
        - auto_fix_suggestions: list of (actor, body, suggestion) for TIER-1
    """
    all_comments = []

    # Collect inline review comments from AI/bots
    review_comments = get_pr_review_comments(pr_num)
    for c in review_comments:
        actor = c.get("user", {}).get("login", "")
        if actor in AI_BOT_ACTORS:
            all_comments.append({
                "actor": actor,
                "body": c.get("body", ""),
                "path": c.get("path", ""),
                "suggestion": c.get("body", "") if "```suggestion" in c.get("body", "") else None,
                "type": "review_comment",
            })

    # Collect general issue comments from AI/bots
    issue_comments = get_pr_issue_comments(pr_num)
    for c in issue_comments:
        actor = c.get("user", {}).get("login", "")
        if actor in AI_BOT_ACTORS:
            all_comments.append({
                "actor": actor,
                "body": c.get("body", ""),
                "path": None,
                "suggestion": None,
                "type": "issue_comment",
            })

    # Collect formal reviews from AI/bots
    reviews = get_pr_reviews(pr_num)
    for r in reviews:
        actor = r.get("user", {}).get("login", "")
        if actor in AI_BOT_ACTORS:
            body = r.get("body", "")
            if body:
                all_comments.append({
                    "actor": actor,
                    "body": body,
                    "path": None,
                    "suggestion": None,
                    "type": "review",
                })

    has_escalation = False
    escalation_reasons = []
    auto_fix_suggestions = []

    for comment in all_comments:
        body = comment["body"]
        actor = comment["actor"]

        if is_escalation_comment(body):
            has_escalation = True
            escalation_reasons.append((actor, body[:200]))
            print(f"  [BOT-TIER3] {actor}: {body[:120]}")
        elif is_auto_fix_comment(body) and comment.get("suggestion"):
            auto_fix_suggestions.append(comment)
            print(f"  [BOT-TIER1] Auto-fixable suggestion from {actor}")
        else:
            # TIER-2: informational only
            print(f"  [BOT-TIER2] Informational comment from {actor} — ignored")

    return has_escalation, escalation_reasons, auto_fix_suggestions


def post_escalation_explanation(pr_num, escalation_reasons):
    """Post a comment explaining why the PR remains in human-review-required."""
    reasons_text = "\n".join(
        f"- **{actor}**: {snippet[:150]}..."
        for actor, snippet in escalation_reasons
    )
    body = (
        "## Autonomous PR Engine — Human Review Required\n\n"
        "This PR remains in `human-review-required` state because an AI/Bot reviewer "
        "identified a **TIER-3 safety/correctness issue** that requires human judgment:\n\n"
        f"{reasons_text}\n\n"
        "**To proceed:** Resolve the above concern and remove the `human-review-required` "
        "label, or confirm it is safe by commenting `/approve-anyway`.\n\n"
        "_This comment was posted automatically by the eco-base autonomous PR engine._"
    )
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO, "--body", body])
    if r.returncode == 0:
        print(f"  [BOT-ESCALATE] Posted escalation explanation on PR #{pr_num}")


def apply_auto_fix_suggestions(pr_num, suggestions):
    """
    Apply TIER-1 auto-fix suggestions (e.g., update version comment in Dockerfile).
    Currently: log the suggestion for audit trail. Full auto-apply requires
    parsing the suggestion block and committing the change.
    """
    for s in suggestions:
        print(f"  [BOT-AUTOFIX] Suggestion from {s['actor']} on {s.get('path', 'N/A')}: "
              f"{s['body'][:100]}")
    # NOTE: Full auto-apply of suggestion blocks is deferred to a future iteration.
    # The governance policy is enforced; TIER-1 suggestions are logged in audit trail.


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


def add_label(pr_num, label):
    gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--add-label", label])


# ── Core classification ───────────────────────────────────────────────────────

def classify_checks(check_runs):
    """
    Classify CI state based ONLY on internal required checks.
    External checks are completely ignored.
    Skipped expected checks are treated as passing.
    Skipped required checks are treated as pending (re-trigger needed).

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

        if conclusion == "success" or conclusion == "neutral":
            passing.add(name)
        elif conclusion == "skipped":
            # Required check skipped unexpectedly → treat as pending, re-trigger
            if name in REQUIRED_CHECKS:
                print(f"  [SKIPPED-REQUIRED] {name} was skipped — treating as pending")
                pending.append(name)
            else:
                # Expected skip for non-required check → treat as passing
                passing.add(name)
        elif status in ("queued", "in_progress", "waiting", "pending"):
            pending.append(name)
        elif conclusion in ("failure", "error", "timed_out", "action_required", "cancelled"):
            failing.append(name)

    # Missing required checks = not yet triggered = pending
    for name in REQUIRED_CHECKS:
        if name not in latest:
            pending.append(name)

    all_pass    = REQUIRED_CHECKS.issubset(passing)
    any_pending = len(pending) > 0
    return passing, failing, pending, all_pass, any_pending


# ── Main PR processor ─────────────────────────────────────────────────────────

def process_pr(pr_num, pr_title, pr_branch, head_sha, merge_status, labels):
    label_names = {l["name"] for l in labels} if labels else set()

    # ── Human-review-required: evaluate AI/bot comments ──────────────────────
    if "human-review-required" in label_names:
        print(f"  [HUMAN-REVIEW] Evaluating AI/bot comments for TIER-3 escalations...")
        has_escalation, escalation_reasons, auto_fix_suggestions = \
            evaluate_ai_bot_comments(pr_num)

        if has_escalation:
            # TIER-3: keep label, post explanation, do not merge
            print(f"  [TIER-3] Safety/correctness issue found — keeping human-review-required")
            post_escalation_explanation(pr_num, escalation_reasons)
            # Apply any TIER-1 auto-fix suggestions that coexist
            if auto_fix_suggestions:
                apply_auto_fix_suggestions(pr_num, auto_fix_suggestions)
            return

        # No TIER-3 escalation found → remove human-review-required and proceed
        print(f"  [TIER-2/NONE] No safety issues found — removing human-review-required")
        remove_label(pr_num, "human-review-required")
        if auto_fix_suggestions:
            apply_auto_fix_suggestions(pr_num, auto_fix_suggestions)
        # Fall through to normal merge logic below

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
        pr_num       = pr["number"]
        pr_title     = pr.get("title", "")
        pr_branch    = pr.get("headRefName", "")
        head_sha     = pr.get("headRefOid", "")
        merge_status = pr.get("mergeStateStatus", "UNKNOWN")
        labels       = pr.get("labels", [])

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
