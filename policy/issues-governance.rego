# AutoEcoOps Issues Governance Policy v1.0
# ==========================================
# OPA policy for Issues lifecycle decisions.
# Governs: triage classification, auto-close eligibility,
#          security escalation, duplicate detection, stale management.
#
# TIER Rules:
#   TIER-1: Noise/informational — auto-close immediately
#   TIER-2: Operational — auto-close when underlying cause resolved
#   TIER-3: Security/Critical — NEVER auto-close, require human review

package autoecops.issues

import future.keywords.if
import future.keywords.in
import future.keywords.every

# ─── Constants ────────────────────────────────────────────────────────────────

# Issues that are safe to auto-close when their linked PR is merged
auto_closeable_types := {
    "pr-blocked",
    "supabase-failure",
    "ci-failure",
    "deploy-failure",
    "stale-notification",
}

# Issues that must NEVER be auto-closed without human review
protected_types := {
    "security",
    "critical",
    "cve",
}

# Labels that exempt an issue from stale management
stale_exempt_labels := {
    "pinned",
    "security",
    "critical",
    "in-progress",
    "blocked",
    "human-review-required",
}

# Labels that indicate an issue is a duplicate candidate
noise_patterns := [
    "[auto]",
    "[bot]",
    "🚨 [auto-sync]",
]

# ─── TIER Classification ──────────────────────────────────────────────────────

# TIER-1: Pure noise — auto-generated, no human action needed
tier1_issue if {
    lower_title := lower(input.title)
    some pattern in noise_patterns
    contains(lower_title, pattern)
    input.issue_type in {"pr-blocked", "supabase-failure", "ci-failure"}
    input.linked_pr_merged == true
}

tier1_issue if {
    input.issue_type == "pr-blocked"
    input.linked_pr_state == "closed"
}

# TIER-2: Operational — auto-close when resolved
tier2_issue if {
    not tier1_issue
    not tier3_issue
    input.issue_type in auto_closeable_types
    input.auto_closeable == true
}

tier2_issue if {
    not tier1_issue
    not tier3_issue
    input.issue_type in auto_closeable_types
    input.days_since_update > 14
    not stale_exempt(input)
}

# TIER-3: Security/Critical — human review required
tier3_issue if {
    some label in input.labels
    label in protected_types
}

tier3_issue if {
    lower_title := lower(input.title)
    some keyword in ["cve-", "vulnerability", "rce", "sqli", "xss", "secret exposed", "credential leak"]
    contains(lower_title, keyword)
}

tier3_issue if {
    input.severity == "critical"
}

# ─── Auto-close Decision ─────────────────────────────────────────────────────

# allow_auto_close: true if the issue can be automatically closed
allow_auto_close if {
    tier1_issue
    not tier3_issue
}

allow_auto_close if {
    tier2_issue
    not tier3_issue
}

# deny_auto_close: reasons why an issue must NOT be auto-closed
deny_auto_close[reason] if {
    tier3_issue
    reason := "TIER-3: Security/critical issue requires human review before closing"
}

deny_auto_close[reason] if {
    some label in input.labels
    label in stale_exempt_labels
    reason := sprintf("Issue has exempt label '%v' — stale management disabled", [label])
}

deny_auto_close[reason] if {
    input.issue_type == "security"
    reason := "Security issues must be manually reviewed and resolved"
}

# ─── Duplicate Detection ─────────────────────────────────────────────────────

# is_duplicate: true if this issue matches a known duplicate pattern
is_duplicate if {
    input.duplicate_of != null
    input.duplicate_of > 0
}

is_duplicate if {
    # Same title pattern as an older issue (normalized)
    input.normalized_title == input.existing_normalized_title
    input.number > input.existing_number
}

# ─── Stale Management ────────────────────────────────────────────────────────

stale_exempt(issue) if {
    some label in issue.labels
    label in stale_exempt_labels
}

should_mark_stale if {
    not stale_exempt(input)
    not tier3_issue
    input.days_since_update > 7
    not "stale" in input.labels
}

should_close_stale if {
    "stale" in input.labels
    not stale_exempt(input)
    not tier3_issue
    input.days_since_update > 21
}

# ─── Label Recommendations ───────────────────────────────────────────────────

recommended_labels[label] if {
    input.issue_type == "supabase-failure"
    label in ["bug", "ci/cd", "incident", "deployment", "supabase"]
}

recommended_labels[label] if {
    input.issue_type == "pr-blocked"
    label in ["bug", "ci/cd", "blocked", "needs-attention"]
}

recommended_labels[label] if {
    input.issue_type == "security"
    label in ["security", "high-priority"]
}

recommended_labels[label] if {
    input.issue_type == "ci-failure"
    label in ["bug", "ci/cd"]
}

recommended_labels[label] if {
    input.issue_type == "deploy-failure"
    label in ["bug", "deployment"]
}

# ─── Decision Summary ────────────────────────────────────────────────────────

decision := {
    "tier": tier,
    "allow_auto_close": allow_auto_close,
    "deny_reasons": deny_reasons,
    "should_mark_stale": should_mark_stale,
    "should_close_stale": should_close_stale,
    "is_duplicate": is_duplicate,
    "recommended_labels": recommended_labels,
    "requires_human_review": tier3_issue,
} if {
    tier := tier_value
    deny_reasons := {r | deny_auto_close[r]}
    allow_auto_close := allow_auto_close_value
    should_mark_stale := should_mark_stale_value
    should_close_stale := should_close_stale_value
    is_duplicate := is_duplicate_value
    recommended_labels := {l | recommended_labels[l]}
}

# Helper: compute tier as string
tier_value := "TIER-3" if { tier3_issue }
tier_value := "TIER-2" if { not tier3_issue; tier2_issue }
tier_value := "TIER-1" if { not tier3_issue; not tier2_issue; tier1_issue }
tier_value := "TIER-0" if { not tier3_issue; not tier2_issue; not tier1_issue }

# Helper: safe boolean defaults
allow_auto_close_value := true if { allow_auto_close }
allow_auto_close_value := false if { not allow_auto_close }

should_mark_stale_value := true if { should_mark_stale }
should_mark_stale_value := false if { not should_mark_stale }

should_close_stale_value := true if { should_close_stale }
should_close_stale_value := false if { not should_close_stale }

is_duplicate_value := true if { is_duplicate }
is_duplicate_value := false if { not is_duplicate }
