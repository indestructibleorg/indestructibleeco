package mno.governance.policies.security

import future.keywords.in

# Security Policy for MachineNativeOps
# Enforces security policies, secret management, and vulnerability requirements

# Default decision is deny
default allow = false

# Allow if all security rules pass
allow {
    input.resource.type == "artifact"
    artifact_security_valid(input.resource)
}

allow {
    input.resource.type == "deployment"
    deployment_security_valid(input.resource)
}

allow {
    input.resource.type == "secret"
    secret_management_valid(input.resource)
}

allow {
    input.resource.type == "dependency"
    dependency_security_valid(input.resource)
}

# Artifact security validation
artifact_security_valid(artifact) {
    has_sbom(artifact)
    has_provenance(artifact)
    is_signed(artifact)
    no_critical_vulnerabilities(artifact)
}

# Deployment security validation
deployment_security_valid(deployment) {
    secrets_encrypted(deployment)
    no_secrets_in_config(deployment)
    compliance_verified(deployment)
}

# Secret management validation
secret_management_valid(secret) {
    secret_encrypted(secret)
    secret_rotated(secret)
    secret_access_limited(secret)
}

# Dependency security validation
dependency_security_valid(dependency) {
    dependency_scanned(dependency)
    no_high_vulnerabilities(dependency)
    dependency_approved(dependency)
}

# Validation helpers
has_sbom(artifact) {
    artifact.sbom
    artifact.sbom.version
}

has_provenance(artifact) {
    artifact.provenance
    artifact.provenance.slsa_level >= 3
}

is_signed(artifact) {
    artifact.signature
    artifact.signature.type == "cosign"
}

no_critical_vulnerabilities(artifact) {
    not has_critical_vulnerability(artifact)
}

secrets_encrypted(deployment) {
    all_secret_encrypted(deployment)
}

all_secret_encrypted(deployment) {
    deployment.secrets[_].encrypted == true
}

no_secrets_in_config(deployment) {
    not contains_secrets(deployment.config)
}

compliance_verified(deployment) {
    deployment.compliance_checks.passed == true
}

secret_encrypted(secret) {
    secret.encryption_algorithm
    valid_encryption_algorithms := ["AES-256-GCM", "ChaCha20-Poly1305"]
    secret.encryption_algorithm in valid_encryption_algorithms
}

secret_rotated(secret) {
    secret.last_rotated
    secret.rotation_period_days <= 90
}

secret_access_limited(secret) {
    secret.access_principles
    count(secret.access_principles) > 0
}

dependency_scanned(dependency) {
    dependency.scan_date
    dependency.vulnerabilities
}

no_high_vulnerabilities(dependency) {
    not has_high_vulnerability(dependency)
}

dependency_approved(dependency) {
    dependency.approved == true
    dependency.approved_by
}

# Helper: check if config contains secrets
contains_secrets(config) {
    some key
    config[key]
    regex.match("(?i)(password|secret|token|key|credential)", key)
}

contains_secrets(config) {
    some key
    value := config[key]
    is_string(value)
    regex.match("[A-Za-z0-9+/]{32,}={0,2}", value)  # Base64 pattern
}

# Violation messages
deny[msg] {
    input.resource.type == "artifact"
    not has_sbom(input.resource)
    msg := "Artifact must have an SBOM"
}

deny[msg] {
    input.resource.type == "artifact"
    not has_provenance(input.resource)
    msg := "Artifact must have SLSA Level 3+ provenance"
}

deny[msg] {
    input.resource.type == "artifact"
    not is_signed(input.resource)
    msg := "Artifact must be signed with Cosign"
}

deny[msg] {
    input.resource.type == "artifact"
    has_critical_vulnerability(input.resource)
    vuln := get_critical_vulnerability(input.resource)
    msg := sprintf("Artifact has critical vulnerability: %s", [vuln])
}

deny[msg] {
    input.resource.type == "deployment"
    not secrets_encrypted(input.resource)
    msg := "All secrets must be encrypted"
}

deny[msg] {
    input.resource.type == "deployment"
    contains_secrets(input.resource.config)
    msg := "Deployment configuration must not contain secrets"
}

deny[msg] {
    input.resource.type == "deployment"
    not compliance_verified(input.resource)
    msg := "Deployment must pass all compliance checks"
}

deny[msg] {
    input.resource.type == "secret"
    not secret_encrypted(input.resource)
    msg := "Secret must be encrypted with AES-256-GCM or ChaCha20-Poly1305"
}

deny[msg] {
    input.resource.type == "secret"
    not secret_rotated(input.resource)
    msg := "Secret must be rotated within 90 days"
}

deny[msg] {
    input.resource.type == "dependency"
    not dependency_scanned(input.resource)
    msg := "Dependency must be security scanned"
}

deny[msg] {
    input.resource.type == "dependency"
    has_high_vulnerability(input.resource)
    vuln := get_high_vulnerability(input.resource)
    msg := sprintf("Dependency has high severity vulnerability: %s", [vuln])
}

# Helper functions
has_critical_vulnerability(artifact) {
    artifact.vulnerabilities[_].severity == "critical"
}

get_critical_vulnerability(artifact) := result {
    some vuln in artifact.vulnerabilities
    vuln.severity == "critical"
    result := sprintf("%s (CVE-%s)", [vuln.name, vuln.cve_id])
}

has_high_vulnerability(dependency) {
    dependency.vulnerabilities[_].severity == "high"
}

get_high_vulnerability(dependency) := result {
    some vuln in dependency.vulnerabilities
    vuln.severity == "high"
    result := sprintf("%s (CVE-%s)", [vuln.name, vuln.cve_id])
}

# Supply chain security policies
supply_chain_policy_valid(artifact) {
    artifact.source_repository
    artifact.build_environment
    artifact.build_environment.trusted == true
    artifact.source_repository.branch_protected == true
}

deny[msg] {
    input.resource.type == "artifact"
    not supply_chain_policy_valid(input.resource)
    msg := "Artifact must be built from trusted environment and protected branch"
}

# Secret detection policy
no_secrets_in_code(code) {
    not contains_secret_patterns(code)
}

contains_secret_patterns(code) {
    regex.match("(?i)(password\\s*=\\s*['&quot;]\\w+['&quot;])", code)
}

contains_secret_patterns(code) {
    regex.match("(?i)(secret\\s*=\\s*['&quot;]\\w+['&quot;])", code)
}

contains_secret_patterns(code) {
    regex.match("(?i)(token\\s*=\\s*['&quot;]\\w+['&quot;])", code)
}

contains_secret_patterns(code) {
    regex.match("(?i)(api[_-]?key\\s*=\\s*['&quot;]\\w+['&quot;])", code)
}

deny[msg] {
    input.resource.type == "code"
    contains_secret_patterns(input.resource.content)
    msg := "Code contains potential secret patterns"
}

# Image security policies
image_security_valid(image) {
    image.scanned == true
    image.base_image_trusted == true
    not image.has_critical_vulnerabilities
}

deny[msg] {
    input.resource.type == "image"
    not image_security_valid(input.resource)
    msg := "Container image must be scanned and free of critical vulnerabilities"
}

# Global Layer security veto
security_veto_required(change) {
    change.type == "security_policy_change"
    change.decreases_security_level == true
    not change.has_exception_approval
}

deny[msg] {
    input.resource.type == "policy_change"
    security_veto_required(input.resource)
    msg := "Global Layer VETO: Security policy changes that decrease security level require exception approval"
}