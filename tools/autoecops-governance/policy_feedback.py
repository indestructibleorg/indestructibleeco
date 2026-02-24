#!/usr/bin/env python3
"""
AutoEcoOps Policy Feedback Loop
================================
Analyzes historical audit trails and proposes OPA policy updates via PR.

This implements the "dynamic adaptation" mechanism from the governance directive:
  - Scan audit trails for false-positive TIER-3 escalations
  - Identify patterns that were escalated but later resolved as safe
  - Propose policy allowlist updates via automated PR
  - Maintain a learning history to prevent regression

Usage:
  python3 policy_feedback.py                    # analyze and propose
  python3 policy_feedback.py --dry-run          # analyze only, no PR
  python3 policy_feedback.py --min-occurrences 3  # require 3+ occurrences before proposing
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = os.environ.get("GITHUB_REPOSITORY", "indestructibleorg/eco-base")
ARTIFACTS_DIR = Path(os.environ.get("ARTIFACTS_DIR", "artifacts"))
AUDIT_DIR = ARTIFACTS_DIR / "audit"
POLICY_FILE = Path("policy/ai_bot_review.rego")
LEARNING_HISTORY_FILE = ARTIFACTS_DIR / "policy-learning-history.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str).encode()
    return hashlib.sha256(serialized).hexdigest()


def gh_cli(args: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def load_audit_trails() -> list[dict]:
    """Load all audit trail JSON files from the artifacts directory."""
    trails = []
    if not AUDIT_DIR.exists():
        return trails
    for f in AUDIT_DIR.glob("pr-*-audit.json"):
        try:
            data = json.loads(f.read_text())
            trails.append(data)
        except Exception as e:
            print(f"  WARN: Could not load {f}: {e}")
    return trails


def extract_escalation_patterns(trails: list[dict]) -> dict[str, list[dict]]:
    """
    Extract TIER-3 escalation patterns from audit trails.
    Returns a dict mapping pattern → list of occurrences.
    """
    patterns: dict[str, list[dict]] = {}

    for trail in trails:
        audit = trail.get("audit", {})
        steps = audit.get("steps", [])

        for step in steps:
            if step.get("step") != "bot_governance_evaluated":
                continue
            data = step.get("data", {})
            if not data.get("has_escalation"):
                continue

            # Find the final action — if it was eventually merged, it was a false positive
            final_action = next(
                (p["value"] for p in trail.get("properties", [])
                 if "final_action" in p.get("name", "")),
                ""
            )
            if final_action not in ("MERGED", "AUTO_MERGE_ENABLED"):
                continue

            # Extract the escalation body excerpts
            for comment in data.get("comments", []):
                if comment.get("tier") != "TIER-3":
                    continue
                body = comment.get("body_excerpt", "")
                actor = comment.get("actor", "")
                key = f"{actor}:{body[:80]}"
                if key not in patterns:
                    patterns[key] = []
                patterns[key].append({
                    "pr_number": trail.get("metadata", {}).get("component", {}).get("version", ""),
                    "actor": actor,
                    "body_excerpt": body,
                    "final_action": final_action,
                    "trail_hash": trail.get("audit", {}).get("audit_hash", "")[:16],
                })

    return patterns


def load_learning_history() -> dict:
    """Load the policy learning history."""
    if LEARNING_HISTORY_FILE.exists():
        try:
            return json.loads(LEARNING_HISTORY_FILE.read_text())
        except Exception:
            pass
    return {"allowlisted_patterns": [], "proposed_prs": [], "last_updated": ""}


def save_learning_history(history: dict):
    """Save the policy learning history."""
    LEARNING_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history["last_updated"] = now_utc()
    LEARNING_HISTORY_FILE.write_text(json.dumps(history, indent=2))


def propose_policy_update(patterns: dict[str, list[dict]],
                          min_occurrences: int,
                          dry_run: bool) -> bool:
    """
    Propose OPA policy updates for patterns that appear to be false positives.
    Returns True if a PR was created.
    """
    history = load_learning_history()
    already_allowlisted = set(history.get("allowlisted_patterns", []))

    candidates = [
        (key, occurrences)
        for key, occurrences in patterns.items()
        if len(occurrences) >= min_occurrences
        and key not in already_allowlisted
    ]

    if not candidates:
        print("  No new false-positive patterns to propose.")
        return False

    print(f"  Found {len(candidates)} candidate pattern(s) for allowlisting:")
    for key, occurrences in candidates:
        print(f"    - '{key[:60]}' ({len(occurrences)} occurrences)")

    if dry_run:
        print("  DRY_RUN: would propose policy update PR")
        return False

    # Read current policy file
    if not POLICY_FILE.exists():
        print(f"  ERROR: Policy file not found: {POLICY_FILE}")
        return False

    current_policy = POLICY_FILE.read_text()

    # Generate allowlist additions
    new_allowlist_entries = []
    for key, occurrences in candidates:
        actor, body = key.split(":", 1)
        # Escape for Rego string
        safe_body = body.replace('"', '\\"')[:60]
        new_allowlist_entries.append(
            f'    # Auto-learned: {len(occurrences)} occurrences resolved as safe\n'
            f'    "{safe_body}",'
        )

    # Insert into policy (find the allowlist section)
    if "# LEARNED_ALLOWLIST_START" in current_policy:
        insert_marker = "# LEARNED_ALLOWLIST_START"
        insertion = "\n".join(new_allowlist_entries) + "\n"
        updated_policy = current_policy.replace(
            insert_marker,
            insert_marker + "\n" + insertion
        )
    else:
        # Append allowlist section at end
        allowlist_block = (
            "\n\n# ─── Learned Allowlist (auto-generated by policy_feedback.py) ───\n"
            "# LEARNED_ALLOWLIST_START\n"
            "learned_false_positive_patterns := [\n"
            + "\n".join(new_allowlist_entries) + "\n"
            "]\n\n"
            "# A TIER-3 comment is a false positive if its body matches a learned pattern\n"
            "is_learned_false_positive(body) if {\n"
            "    some pattern in learned_false_positive_patterns\n"
            "    contains(lower(body), lower(pattern))\n"
            "}\n"
        )
        updated_policy = current_policy + allowlist_block

    # Create branch and commit
    branch = f"chore/policy-feedback-{int(datetime.now(timezone.utc).timestamp())}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    POLICY_FILE.write_text(updated_policy)
    subprocess.run(["git", "add", str(POLICY_FILE)], check=True)
    subprocess.run([
        "git", "commit", "-m",
        f"chore(policy): auto-learn {len(candidates)} false-positive pattern(s)\n\n"
        f"Patterns learned from audit trail analysis:\n"
        + "\n".join(f"- {key[:60]}" for key, _ in candidates)
    ], check=True)
    subprocess.run(["git", "push", "origin", branch], check=True)

    # Create PR
    pr_body = (
        "## AutoEcoOps Policy Feedback Loop\n\n"
        "This PR was automatically generated by the policy feedback loop.\n\n"
        "### Patterns Proposed for Allowlisting\n\n"
        "These TIER-3 escalation patterns were observed in audit trails but "
        "were subsequently resolved as safe (PR was merged):\n\n"
        + "\n".join(
            f"- `{key[:80]}` ({len(occ)} occurrences)"
            for key, occ in candidates
        )
        + "\n\n"
        "### Evidence\n\n"
        "Audit trail hashes:\n"
        + "\n".join(
            f"- `{occ[0]['trail_hash']}`"
            for _, occ in candidates
        )
        + "\n\n"
        "*AutoEcoOps High-Governance Engine v1.0 — Policy Feedback Loop*"
    )

    code, out, err = gh_cli([
        "pr", "create",
        "--repo", REPO,
        "--title", f"chore(policy): auto-learn {len(candidates)} false-positive pattern(s)",
        "--body", pr_body,
        "--head", branch,
        "--base", "main",
    ])

    if code == 0:
        print(f"  ✅ Policy update PR created: {out}")
        # Update learning history
        history["allowlisted_patterns"].extend(key for key, _ in candidates)
        history["proposed_prs"].append({
            "pr_url": out,
            "patterns": [key for key, _ in candidates],
            "proposed_at": now_utc(),
        })
        save_learning_history(history)
        return True
    else:
        print(f"  ERROR: Could not create PR: {err[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="AutoEcoOps Policy Feedback Loop")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-occurrences", type=int, default=2,
                        help="Minimum occurrences before proposing allowlist")
    args = parser.parse_args()

    print(f"AutoEcoOps Policy Feedback Loop")
    print(f"Repo: {REPO}")
    print(f"Dry run: {args.dry_run}")
    print(f"Min occurrences: {args.min_occurrences}")
    print(f"Audit dir: {AUDIT_DIR}")
    print()

    trails = load_audit_trails()
    print(f"Loaded {len(trails)} audit trail(s)")

    if not trails:
        print("No audit trails found. Nothing to analyze.")
        return 0

    patterns = extract_escalation_patterns(trails)
    print(f"Extracted {len(patterns)} escalation pattern(s)")

    propose_policy_update(patterns, args.min_occurrences, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
