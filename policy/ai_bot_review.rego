package eco_base.ai_bot_review

# ── AI/Bot Review Governance Policy ──────────────────────────────────────────
# URI: eco-base://policy/ai-bot-review
# Purpose: Define which AI/Bot review comments require action, which are
#          informational only, and which trigger auto-fix vs human escalation.
#
# Governance Tiers:
#   TIER-1 (Auto-fix):     Comment identifies a concrete, safe, mechanical fix
#                          (e.g., update a version comment to match FROM line)
#   TIER-2 (Informational): Comment is a style/quality suggestion with no
#                           safety implication — log and ignore
#   TIER-3 (Escalate):     Comment identifies a safety/correctness issue that
#                           requires human judgment (e.g., non-existent image tag,
#                           breaking API change, security vulnerability)
#
# Bots covered:
#   - copilot-pull-request-reviewer[bot]
#   - coderabbit-ai[bot]
#   - qodo-merge-pro[bot]
#   - codacy-production[bot]
#   - sonarqubecloud[bot]
#   - github-advanced-security[bot]
# ─────────────────────────────────────────────────────────────────────────────

import future.keywords.in

# ── Known AI/Bot actors ───────────────────────────────────────────────────────
ai_bot_actors := {
    "copilot-pull-request-reviewer",
    "coderabbit-ai",
    "qodo-merge-pro",
    "codacy-production",
    "sonarqubecloud",
    "github-advanced-security",
}

# ── TIER-3: Escalation triggers (safety/correctness issues) ──────────────────
# These patterns in a bot comment body indicate the PR should remain in
# human-review-required state until a human confirms it is safe.
escalation_patterns := {
    "does not exist",
    "non-existent",
    "invalid tag",
    "tag not found",
    "breaking change",
    "security vulnerability",
    "CVE-",
    "should be reconsidered",
    "critical",
    "cannot be pulled",
    "image not found",
}

# A bot comment is an escalation trigger if it contains any escalation pattern
is_escalation_comment(body) {
    some pattern in escalation_patterns
    contains(lower(body), lower(pattern))
}

# ── TIER-1: Auto-fixable patterns ────────────────────────────────────────────
# These patterns indicate a mechanical fix is safe to apply automatically.
# The auto-fix engine will apply the suggestion block if present.
auto_fix_patterns := {
    "comment.*still references",
    "comment.*should be updated",
    "documentation mismatch",
    "typo",
    "whitespace",
    "trailing newline",
    "missing newline",
}

# ── Policy decisions ──────────────────────────────────────────────────────────

# DENY merge if any bot comment is a TIER-3 escalation
deny[msg] {
    some comment in input.bot_comments
    actor := comment.user.login
    # Strip [bot] suffix for matching
    actor_clean := trim_suffix(actor, "[bot]")
    actor_clean in ai_bot_actors
    is_escalation_comment(comment.body)
    msg := sprintf(
        "Bot %s flagged a safety/correctness issue: %s",
        [actor, substring(comment.body, 0, 120)]
    )
}

# WARN (informational only) for TIER-2 style/quality comments
warn[msg] {
    some comment in input.bot_comments
    actor := comment.user.login
    actor_clean := trim_suffix(actor, "[bot]")
    actor_clean in ai_bot_actors
    not is_escalation_comment(comment.body)
    msg := sprintf(
        "Bot %s left a non-blocking suggestion (informational): %s",
        [actor, substring(comment.body, 0, 80)]
    )
}
