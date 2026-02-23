#!/usr/bin/env python3
"""Autonomous Bot — Phase 5: Auto-merge PR when CI passes."""
import json, os, time, urllib.request

token = os.environ.get("GITHUB_TOKEN", "")
repo = os.environ.get("GITHUB_REPOSITORY", "")
pr_number = os.environ.get("PR_NUMBER", "0")
dry_run = os.environ.get("DRY_RUN", "false") == "true"

if not pr_number or pr_number == "0":
    print("No PR to merge.")
    exit(0)

def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers, method=method, data=json.dumps(data).encode() if data else None)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e.code), "body": e.read().decode()}
    except Exception as e:
        return {}

print(f"Monitoring PR #{pr_number} for CI completion...")
max_wait, poll_interval, elapsed = 25 * 60, 30, 0

while elapsed < max_wait:
    pr = gh_api(f"/pulls/{pr_number}")
    if not pr.get("number"):
        print("PR not found or already merged.")
        break
    state = pr.get("state", "")
    mergeable_state = pr.get("mergeable_state", "unknown")
    print(f"[{elapsed}s] state={state}, mergeable_state={mergeable_state}")
    if state == "closed":
        print("PR is already closed/merged.")
        break
    if mergeable_state == "clean":
        if dry_run:
            print(f"[DRY RUN] Would merge PR #{pr_number} (squash)")
            break
        merge_result = gh_api(f"/pulls/{pr_number}/merge", method="PUT", data={
            "merge_method": "squash",
            "commit_title": f"fix(bot): autonomous fixes (PR #{pr_number})",
            "commit_message": "Automatically merged by Autonomous Bot after all CI checks passed.\nSquash merge per eco-base best practices.",
        })
        if merge_result.get("merged"):
            print(f"PR #{pr_number} successfully merged via squash!")
            break
        elif merge_result.get("error") == "405":
            print("Auto-merge already enabled via GraphQL — GitHub will merge automatically.")
            break
        else:
            print(f"Merge result: {merge_result}")
            break
    elif mergeable_state in ("blocked", "behind", "dirty"):
        print(f"PR cannot be merged: {mergeable_state}.")
        gh_api(f"/issues/{pr_number}/comments", method="POST", data={
            "body": f"Auto-merge blocked: PR is in `{mergeable_state}` state. Manual review required."})
        break
    time.sleep(poll_interval)
    elapsed += poll_interval

if elapsed >= max_wait:
    print(f"Timeout after {max_wait}s.")
