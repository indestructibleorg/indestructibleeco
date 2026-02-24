#!/usr/bin/env python3
"""SLO Breach Issue Creator with dedup guard.

Checks both open AND recently closed (48h) issues before creating a new one.
Used by dora-metrics.yaml to prevent duplicate SLO breach issues.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

token = os.environ["GITHUB_TOKEN"]
repo = os.environ["GITHUB_REPOSITORY"]
cfr = os.environ.get("CFR_PCT", "unknown")

TITLE = f"SLO Breach: CFR {cfr}% exceeds 5% threshold"
LABELS = "slo-breach,dora,incident"
COOLDOWN_HOURS = 48

headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def gh_get(path: str):
    url = f"https://api.github.com/repos/{repo}{path}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {path}: {e}")
        return []


def normalize(s: str) -> str:
    """Strip dates and special chars for fuzzy title matching."""
    import re
    s = re.sub(r"\d+\.?\d*%", "", s)  # strip percentages
    s = re.sub(r"\d{4}-\d{2}-\d{2}", "", s)
    s = re.sub(r"[^a-zA-Z0-9 ]", "", s)
    return " ".join(s.split()).lower()


# 1. Check open issues
open_issues = gh_get(f"/issues?labels={LABELS}&state=open&per_page=50")
if isinstance(open_issues, list):
    norm_title = normalize(TITLE)
    for issue in open_issues:
        if normalize(issue.get("title", "")) == norm_title:
            print(f"DEDUP: SLO breach issue already open: #{issue['number']}")
            exit(0)

# 2. Check recently closed issues (48h cooldown)
closed_issues = gh_get(f"/issues?labels={LABELS}&state=closed&per_page=20&sort=updated&direction=desc")
if isinstance(closed_issues, list):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=COOLDOWN_HOURS)
    norm_title = normalize(TITLE)
    for issue in closed_issues:
        closed_at = issue.get("closed_at", "")
        if closed_at:
            closed_dt = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
            if closed_dt > cutoff and normalize(issue.get("title", "")) == norm_title:
                print(f"DEDUP: SLO breach issue #{issue['number']} closed within {COOLDOWN_HOURS}h, skipping")
                exit(0)

# 3. Create new issue
body = f"""## SLO Breach: Change Failure Rate Exceeded

**Threshold:** 5%
**Current CFR:** {cfr}%

The Change Failure Rate has exceeded the SLO threshold. This means more than 5% of deployments to main are failing.

### Recommended Actions
1. Review recent failed CI/CD runs
2. Check if recent merges introduced regressions
3. Consider pausing auto-merge until CFR returns below 5%

### DORA Reference
- Elite: ≤5% CFR
- High: ≤10% CFR
- Medium: ≤15% CFR
- Low: >15% CFR

cc: @indestructiblemachinen
"""

data = json.dumps({
    "title": TITLE,
    "body": body,
    "labels": LABELS.split(","),
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/issues",
    data=data,
    method="POST",
    headers={**headers, "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req) as r:
        issue = json.loads(r.read())
    print(f"Created SLO breach issue: #{issue['number']}")
except Exception as e:
    print(f"Failed to create issue: {e}")
