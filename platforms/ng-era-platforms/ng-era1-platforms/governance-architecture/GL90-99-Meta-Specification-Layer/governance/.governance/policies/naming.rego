package gl.governance.naming

import future.keywords.in
import future.keywords.if
import future.keywords.contains

# =============================================================================
# GL Naming Governance Policy v1.0
# OPA Rego Policy for Resource Naming Conventions
# =============================================================================

default allow := false

# Resource naming pattern
resource_pattern := `^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret|pvc|hpa|pdb|sa|role|rb|cj|job)-v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$`

# Kubernetes naming constraints
k8s_name_pattern := `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
k8s_max_length := 63

# Environment prefixes
valid_environments := {"dev", "staging", "prod", "test", "qa"}

# Resource type suffixes
valid_suffixes := {
    "deploy": "Deployment",
    "svc": "Service",
    "ing": "Ingress",
    "cm": "ConfigMap",
    "secret": "Secret",
    "pvc": "PersistentVolumeClaim",
    "hpa": "HorizontalPodAutoscaler",
    "pdb": "PodDisruptionBudget",
    "sa": "ServiceAccount",
    "role": "Role",
    "rb": "RoleBinding",
    "cj": "CronJob",
    "job": "Job"
}

# =============================================================================
# Main Policy Rules
# =============================================================================

# Allow if name is compliant
allow if {
    is_compliant
}

# Check overall compliance
is_compliant if {
    valid_k8s_name
    valid_resource_pattern
    valid_labels
}

# Validate Kubernetes naming rules
valid_k8s_name if {
    name := input.metadata.name
    regex.match(k8s_name_pattern, name)
    count(name) <= k8s_max_length
}

# Validate resource naming pattern
valid_resource_pattern if {
    name := input.metadata.name
    regex.match(resource_pattern, name)
}

# Validate required labels
valid_labels if {
    input.metadata.labels["app.kubernetes.io/name"]
    input.metadata.labels["app.kubernetes.io/version"]
    input.metadata.labels["gl.governance.level"]
}

# =============================================================================
# Violation Detection
# =============================================================================

violations contains msg if {
    not valid_k8s_name
    name := input.metadata.name
    msg := sprintf("VIOLATION: Resource name '%s' does not comply with K8s naming rules (pattern: %s, max length: %d)", [name, k8s_name_pattern, k8s_max_length])
}

violations contains msg if {
    not valid_resource_pattern
    name := input.metadata.name
    msg := sprintf("VIOLATION: Resource name '%s' does not match GL naming convention: %s", [name, resource_pattern])
}

violations contains msg if {
    not input.metadata.labels["app.kubernetes.io/name"]
    msg := sprintf("VIOLATION: Resource '%s' missing required label 'app.kubernetes.io/name'", [input.metadata.name])
}

violations contains msg if {
    not input.metadata.labels["app.kubernetes.io/version"]
    msg := sprintf("VIOLATION: Resource '%s' missing required label 'app.kubernetes.io/version'", [input.metadata.name])
}

violations contains msg if {
    not input.metadata.labels["gl.governance.level"]
    msg := sprintf("VIOLATION: Resource '%s' missing required label 'gl.governance.level'", [input.metadata.name])
}

# =============================================================================
# Warnings (Non-blocking)
# =============================================================================

warnings contains msg if {
    not input.metadata.labels["app.kubernetes.io/component"]
    msg := sprintf("WARNING: Resource '%s' missing recommended label 'app.kubernetes.io/component'", [input.metadata.name])
}

warnings contains msg if {
    not input.metadata.labels["app.kubernetes.io/managed-by"]
    msg := sprintf("WARNING: Resource '%s' missing recommended label 'app.kubernetes.io/managed-by'", [input.metadata.name])
}

warnings contains msg if {
    not input.metadata.annotations["gl.governance.last-audit"]
    msg := sprintf("WARNING: Resource '%s' has no governance audit timestamp", [input.metadata.name])
}

# =============================================================================
# Name Suggestions
# =============================================================================

# Generate compliant name suggestion
suggest_name := suggestion if {
    current := input.metadata.name
    parts := split(current, "-")
    count(parts) >= 2
    
    env := parts[0]
    env in valid_environments
    
    base_name := concat("-", array.slice(parts, 1, count(parts)))
    kind := lower(input.kind)
    suffix := get_suffix(kind)
    
    suggestion := sprintf("%s-%s-%s-v1.0.0", [env, base_name, suffix])
}

# Get appropriate suffix for resource kind
get_suffix(kind) := suffix if {
    suffix := [s | some s, k in valid_suffixes; lower(k) == kind][0]
} else := "resource"

# =============================================================================
# Compliance Metrics
# =============================================================================

compliance_score := score if {
    total_checks := 5
    passed_checks := count([1 |
        some check in [valid_k8s_name, valid_resource_pattern, valid_labels]
        check == true
    ])
    score := (passed_checks / total_checks) * 100
}

# =============================================================================
# Audit Trail
# =============================================================================

audit_record := {
    "timestamp": time.now_ns(),
    "resource": input.metadata.name,
    "namespace": input.metadata.namespace,
    "kind": input.kind,
    "compliant": is_compliant,
    "violations": violations,
    "warnings": warnings,
    "compliance_score": compliance_score,
    "suggestion": suggest_name
}
