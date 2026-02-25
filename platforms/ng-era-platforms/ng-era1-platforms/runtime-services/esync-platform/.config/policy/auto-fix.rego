package esync.platform.autofix

# Auto-fix policy definitions for automated remediation

allow_fix[issue_id] {
    issue := input.issue
    fixable_issues[issue_id]
    
    # Check if issue is in allowlist
    not in_allowlist(issue_id)
    
    # Check severity
    issue.severity in ["low", "medium"]
}

# Define fixable issues
fixable_issues["actions_hardening"] {
    input.issue.category == "github_actions"
    input.issue.type == "missing_permissions"
}

fixable_issues["lint_format"] {
    input.issue.category == "code_quality"
    input.issue.type == "formatting"
}

fixable_issues["deps_go"] {
    input.issue.category == "dependencies"
    input.issue.language == "go"
}

fixable_issues["deps_node"] {
    input.issue.category == "dependencies"
    input.issue.language == "node"
}

fixable_issues["docker_base"] {
    input.issue.category == "docker"
    input.issue.type == "outdated_base"
}

fixable_issues["openapi_fix"] {
    input.issue.category == "api"
    input.issue.type == "openapi_violation"
}

fixable_issues["helm_sync"] {
    input.issue.category == "helm"
    input.issue.type == "field_mismatch"
}

fixable_issues["kustomize_sync"] {
    input.issue.category == "kustomize"
    input.issue.type == "field_mismatch"
}

# Check if in allowlist
in_allowlist[issue_id] {
    allowlist := data.auto_fix.allowlist
    allowlist[_] == issue_id
}

# Auto-fix strategies
fix_strategy[issue_id] = "actions_hardening" {
    fixable_issues["actions_hardening"]
}

fix_strategy[issue_id] = "lint_format" {
    fixable_issues["lint_format"]
}

fix_strategy[issue_id] = "dependency_update" {
    fixable_issues["deps_go"]
}

fix_strategy[issue_id] = "dependency_update" {
    fixable_issues["deps_node"]
}

fix_strategy[issue_id] = "docker_base_update" {
    fixable_issues["docker_base"]
}

fix_strategy[issue_id] = "openapi_repair" {
    fixable_issues["openapi_fix"]
}

fix_strategy[issue_id] = "helm_sync" {
    fixable_issues["helm_sync"]
}

fix_strategy[issue_id] = "kustomize_sync" {
    fixable_issues["kustomize_sync"]
}