#!/usr/bin/env python3
"""Autonomous Bot — Phase 5: Auto-merge PR with human gate + branch cleanup.
Defense Matrix Layer 4: Human-in-the-Loop Gate + Auto-delete merged branches
"""
import json, os, time, urllib.request

token = os.environ.get("GITHUB_TOKEN", "")
repo = os.environ.get("GITHUB_REPOSITORY", "")
pr_number = os.environ.get("PR_NUMBER", "0")
dry_run = os.environ.get("DRY_RUN", "false") == "true"
problems_json = os.environ.get("PROBLEMS_JSON", "[]")

if not pr_number or pr_number == "0":
    print("No PR to merge.")
    exit(0)

try:
    problems = json.loads(problems_json)
except Exception:
    problems = []

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
    except urllib.error.HTTPError as e:
        return {"error": str(e.code), "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}

# ── Human-in-the-loop gate check ────────────────────────────────────────────
human_required_problems = [
    p for p in problems
    if p.get("risk", {}).get("requires_human_review", False)
]

if human_required_problems:
    print(f"\nHUMAN REVIEW REQUIRED for {len(human_required_problems)} problem(s):")
    for p in human_required_problems:
        print(f"  - {p['title']}: {p['risk']['ai_assessment']}")

    # Add label and comment to PR
    gh_api(f"/issues/{pr_number}/labels", method="POST", data={"labels": ["requires-human-review", "human-in-the-loop"]})
    comment_body = "## Human Review Required\n\nThis PR was created by the Autonomous Bot but contains changes that require human review:\n\n"
    for p in human_required_problems:
        comment_body += f"- **{p['title']}** (Risk: {p['risk']['risk_level']} {p['risk']['risk_score']}/100)\n"
        comment_body += f"  - {p['risk']['ai_assessment']}\n\n"
    comment_body += "\ncc: @indestructiblemachinen\n"
    gh_api(f"/issues/{pr_number}/comments", method="POST", data={"body": comment_body})

    print("\nPR labeled as requiring human review. Auto-merge blocked.")
    exit(0)

# ── All problems are auto-fixable — proceed with auto-merge ─────────────────
print(f"\nAll {len(problems)} problem(s) are safe for auto-merge. Proceeding...")

max_wait, poll_interval, elapsed = 25 * 60, 30, 0
branch_name = None

while elapsed < max_wait:
    pr = gh_api(f"/pulls/{pr_number}")
    if not pr.get("number"):
        print("PR not found or already merged.")
        break

    state = pr.get("state", "")
    mergeable_state = pr.get("mergeable_state", "unknown")
    branch_name = pr.get("head", {}).get("ref", "")
    print(f"[{elapsed}s] state={state}, mergeable_state={mergeable_state}, branch={branch_name}")

    if state == "closed":
        print("PR is already closed/merged.")
        # Still try to delete the branch
        break

    if mergeable_state == "clean":
        if dry_run:
            print(f"[DRY RUN] Would merge PR #{pr_number} (squash) and delete branch '{branch_name}'")
            break

        merge_result = gh_api(f"/pulls/{pr_number}/merge", method="PUT", data={
            "merge_method": "squash",
            "commit_title": f"fix(bot): autonomous fixes (PR #{pr_number})",
            "commit_message": (
                "Automatically merged by Autonomous Bot after all CI checks passed.\n"
                "Squash merge per eco-base best practices.\n\n"
                f"Problems fixed: {len(problems)}\n"
                "Risk assessment: All problems cleared for auto-merge.\n"
            ),
        })

        if merge_result.get("merged"):
            print(f"PR #{pr_number} successfully merged via squash!")
            break
        elif merge_result.get("error") == "405":
            print("Auto-merge already enabled via GitHub — will merge automatically.")
            break
        else:
            print(f"Merge result: {merge_result}")
            break

    elif mergeable_state in ("blocked", "behind", "dirty"):
        print(f"PR cannot be merged: {mergeable_state}.")
        gh_api(f"/issues/{pr_number}/comments", method="POST", data={
            "body": f"Auto-merge blocked: PR is in `{mergeable_state}` state.\n\nPlease resolve conflicts or wait for required checks to pass."
        })
        break

    time.sleep(poll_interval)
    elapsed += poll_interval

# ── Auto-delete merged branch ────────────────────────────────────────────────
if branch_name and branch_name.startswith(("bot/", "fix/", "feat/", "chore/", "dependabot/")):
    if dry_run:
        print(f"[DRY RUN] Would delete branch '{branch_name}'")
    else:
        # Verify PR is merged before deleting
        pr_check = gh_api(f"/pulls/{pr_number}")
        if pr_check.get("merged") or pr_check.get("state") == "closed":
            delete_result = gh_api(f"/git/refs/heads/{branch_name}", method="DELETE")
            if not delete_result.get("error"):
                print(f"Branch '{branch_name}' deleted successfully.")
            else:
                print(f"Branch deletion result: {delete_result}")
        else:
            print(f"PR not yet merged — skipping branch deletion.")
else:
    print(f"Branch '{branch_name}' does not match bot pattern — skipping deletion.")

if elapsed >= max_wait:
    print(f"Timeout after {max_wait}s.")
