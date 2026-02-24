package autoecops.governance

# AutoEcoOps High-Governance Engine — OPA Policy
# Defines the authoritative governance rules for PR merge decisions.
# Used by engine.py and the CI opa-policy gate.
#
# Governance Tiers:
#   TIER-3: Safety/correctness issue → deny merge, escalate
#   TIER-2: Style/quality suggestion → allow merge, log
#   TIER-1: Mechanical fix → allow merge, log suggestion
#
# Failure Response Levels:
#   L1: retry CI
#   L2: AI diagnosis
#   L3: external validation
#   L4: sandbox simulation
#   L5: final safeguard (human review required)

import future.keywords.if
import future.keywords.in

# ─── Required CI Checks ───────────────────────────────────────────────────────

required_checks := {
    "validate",
    "lint",
    "test",
    "build",
    "opa-policy",
    "supply-chain",
}

# Checks that are expected to be skipped — not a failure
expected_skip_checks := {
    "auto-fix",
    "Supabase Preview",
    "request-codacy-review",
    "Deploy Preview",
}

# ─── AI/Bot Escalation Patterns ───────────────────────────────────────────────

escalation_keywords := [
    "does not exist",
    "non-existent",
    "invalid tag",
    "should be reconsidered",
    "cannot be pulled",
    "image not found",
    "security vulnerability",
    "breaking change",
    "critical",
]

# ─── Merge Decision Rules ─────────────────────────────────────────────────────

# deny merge if any required check has failed
deny_merge[reason] {
    input.check_runs[check_name].conclusion == "failure"
    check_name in required_checks
    reason := sprintf("Required check '%v' failed", [check_name])
}

# deny merge if any required check is still pending
deny_merge[reason] {
    input.check_runs[check_name].status != "completed"
    check_name in required_checks
    reason := sprintf("Required check '%v' is still pending", [check_name])
}

# deny merge if bot governance has TIER-3 escalation
deny_merge[reason] {
    input.bot_governance.has_escalation == true
    reason := sprintf("TIER-3 AI/Bot escalation: %v", [input.bot_governance.reason])
}

# deny merge if PR is in dirty state (merge conflict)
deny_merge[reason] {
    input.pr.mergeable_state == "dirty"
    reason := "PR has merge conflicts (dirty state)"
}

# deny merge if PR is a draft
deny_merge[reason] {
    input.pr.is_draft == true
    reason := "PR is a draft"
}

# ─── Risk Score Rules ─────────────────────────────────────────────────────────

# Risk score components (0-100 total)
risk_score_components := {
    "bot_escalation": 40,
    "failed_required_check": 15,
    "major_version_bump": 20,
    "dirty_state": 10,
}

risk_score := score {
    bot_score := 40 if input.bot_governance.has_escalation else 0
    failed_count := count({name | input.check_runs[name].conclusion == "failure"; name in required_checks})
    check_score := failed_count * 15
    dirty_score := 10 if input.pr.mergeable_state == "dirty" else 0
    score := min([bot_score + check_score + dirty_score, 100])
}

# ─── Failure Response Level ───────────────────────────────────────────────────

# Determine which failure response level to activate
failure_response_level := level {
    count(deny_merge) > 0
    risk_score >= 50
    level := "L4"
} else := level {
    count(deny_merge) > 0
    risk_score >= 30
    level := "L3"
} else := level {
    count(deny_merge) > 0
    level := "L1"
} else := "NONE"

# ─── Final Decision ───────────────────────────────────────────────────────────

allow_merge if {
    count(deny_merge) == 0
}

decision := "MERGE" if {
    allow_merge
}

decision := "DENY" if {
    not allow_merge
}

# ─── Governance Summary ───────────────────────────────────────────────────────

governance_summary := {
    "decision": decision,
    "deny_reasons": deny_merge,
    "risk_score": risk_score,
    "failure_response_level": failure_response_level,
    "allow_merge": allow_merge,
}
