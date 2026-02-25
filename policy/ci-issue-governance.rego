package ci_issue_governance

import future.keywords.if
import future.keywords.in

# 預設拒絕
default allow = false

# 允許自動修復的條件
allow if {
    input.action == "auto-repair"
    input.gate in ["lint", "validate", "test"]
    input.risk_score < 30
    input.idempotency_key != ""
}

# 拒絕無冪等性保護的修復
deny[msg] if {
    input.action == "auto-repair"
    not input.idempotency_key
    msg := "Auto-repair must include an idempotency key to prevent infinite loops."
}

# 拒絕高風險修復 (例如 build 失敗)
deny[msg] if {
    input.gate == "build"
    input.risk_score > 50
    msg := "High-risk build failure requires manual verification or L5 escalation."
}

# 規則：lint 失敗必須自動轉為 style issue
gate_to_issue_rules[gate] := "style" if {
    gate == "lint"
}

gate_to_issue_rules[gate] := "validation" if {
    gate == "validate"
}
