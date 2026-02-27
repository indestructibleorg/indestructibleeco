#!/usr/bin/env python3
"""
Universal Issue Dedup Guard — prevents duplicate issue creation.

Usage (from GitHub Actions):
  python3 tools/issue-dedup/dedup.py \
    --title "Issue title to check" \
    --labels "label1,label2" \
    --cooldown-hours 48

Exit codes:
  0 = No duplicate found → safe to create
  1 = Duplicate exists (open or recently closed) → DO NOT create

Also writes result to $GITHUB_OUTPUT:
  dedup_result=create   (safe to create)
  dedup_result=skip     (duplicate exists)
  existing_issue=N      (issue number if duplicate found)
"""
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta


def gh_api(path: str, token: str, repo: str) -> list | dict:
    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, encoding='utf-8') as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {path}: {e}")
        return []


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching — strip dates, emojis, whitespace."""
    import re
    # Remove date patterns like 2026-02-24, 2026-02-24T01:22Z
    t = re.sub(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?Z?)?", "", title)
    # Remove common emojis
    t = re.sub(r"[🚨⚠️✅❌🔴🟡🟢💀🔥]", "", t)
    # Remove percentage values like 11.0%, 16.0%
    t = re.sub(r"\d+\.?\d*%", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    # Remove trailing " —" or " -"
    t = re.sub(r"\s*[—\-]\s*$", "", t)
    return t.lower()


def find_duplicate(
    title: str,
    labels: list[str],
    token: str,
    repo: str,
    cooldown_hours: int,
) -> int | None:
    """
    Check for duplicate issues:
    1. Open issues with matching normalized title
    2. Recently closed issues (within cooldown_hours) with matching normalized title
    
    Returns issue number if duplicate found, None otherwise.
    """
    norm_title = normalize_title(title)
    
    # Check open issues
    label_query = ",".join(labels) if labels else ""
    open_path = f"/issues?state=open&per_page=100"
    if label_query:
        open_path += f"&labels={label_query}"
    
    open_issues = gh_api(open_path, token, repo)
    if isinstance(open_issues, list):
        for issue in open_issues:
            if normalize_title(issue.get("title", "")) == norm_title:
                return issue["number"]
    
    # Check recently closed issues (within cooldown window)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
    closed_path = f"/issues?state=closed&per_page=50&sort=updated&direction=desc"
    if label_query:
        closed_path += f"&labels={label_query}"
    
    closed_issues = gh_api(closed_path, token, repo)
    if isinstance(closed_issues, list):
        for issue in closed_issues:
            closed_at = issue.get("closed_at", "")
            if closed_at:
                try:
                    closed_time = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                    if closed_time > cutoff:
                        if normalize_title(issue.get("title", "")) == norm_title:
                            return issue["number"]
                except (ValueError, TypeError):
                    pass
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Universal Issue Dedup Guard")
    parser.add_argument("--title", required=True, help="Issue title to check")
    parser.add_argument("--labels", default="", help="Comma-separated labels to filter")
    parser.add_argument("--cooldown-hours", type=int, default=48,
                        help="Hours to look back in closed issues (default: 48)")
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    
    if not token or not repo:
        print("ERROR: GITHUB_TOKEN and GITHUB_REPOSITORY must be set")
        sys.exit(1)
    
    labels = [l.strip() for l in args.labels.split(",") if l.strip()]
    
    existing = find_duplicate(args.title, labels, token, repo, args.cooldown_hours)
    
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    
    if existing:
        print(f"DEDUP: Duplicate found → #{existing} (skipping creation)")
        if output_file:
            with open(output_file, "a", encoding='utf-8') as f:
                f.write(f"dedup_result=skip\n")
                f.write(f"existing_issue={existing}\n")
        sys.exit(1)
    else:
        print(f"DEDUP: No duplicate found → safe to create")
        if output_file:
            with open(output_file, "a", encoding='utf-8') as f:
                f.write(f"dedup_result=create\n")
                f.write(f"existing_issue=0\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
