package eco_base.skipped_check_response

# ── Skipped Architecture Content Response Policy ─────────────────────────────
# URI: eco-base://policy/skipped-check-response
# Purpose: Define what happens when a check is skipped (conclusion=skipped)
#          rather than passed or failed. Skipped checks are NOT failures and
#          MUST NOT block merge.
#
# Skipped check categories and their responses:
#
# CATEGORY A — Conditional skips (expected, by design):
#   auto-fix:           Only runs on main branch failures. Skipped on PRs = correct.
#   Supabase Preview:   Only runs when branch is linked to Supabase. Skipped = correct.
#   request-codacy-review: Only runs when codacy-review label is present. Skipped = correct.
#
# CATEGORY B — External service skips (not required for merge):
#   Supabase Preview:   External service, not a required check.
#   Cloudflare Pages:   External deploy preview, informational only.
#
# CATEGORY C — Unexpected skips (required check was skipped):
#   If a REQUIRED check (validate/lint/test/build/opa-policy/supply-chain) is
#   skipped, this is treated as PENDING (not failure) and CI is re-triggered.
# ─────────────────────────────────────────────────────────────────────────────

import future.keywords.in

# Checks that are expected to be skipped — never block merge
expected_skips := {
    "auto-fix",
    "Supabase Preview",
    "request-codacy-review",
    "Auto-label New Issues",
}

# Required checks — if skipped unexpectedly, re-trigger CI
required_checks := {
    "validate",
    "lint",
    "test",
    "build",
    "opa-policy",
    "supply-chain",
}

# A skipped check is acceptable if it is in the expected_skips set
acceptable_skip(name) {
    name in expected_skips
}

# A skipped check is acceptable if it is NOT a required check
acceptable_skip(name) {
    not name in required_checks
}

# DENY if a required check was unexpectedly skipped
# (This signals CI was not triggered properly — re-trigger is needed)
deny[msg] {
    some check in input.check_runs
    check.conclusion == "skipped"
    check.name in required_checks
    msg := sprintf(
        "Required check '%s' was skipped unexpectedly — CI re-trigger needed",
        [check.name]
    )
}

# ALLOW (informational) for expected skips
allow[msg] {
    some check in input.check_runs
    check.conclusion == "skipped"
    acceptable_skip(check.name)
    msg := sprintf(
        "Check '%s' skipped as expected — not required for merge",
        [check.name]
    )
}
