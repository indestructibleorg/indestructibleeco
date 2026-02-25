package esync.platform.naming

# Conftest policy for naming convention validation
# This validates Kubernetes manifests and other config files

deny[msg] {
    input.kind == "Deployment"
    name := input.metadata.name
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    not re_match(pattern, name)
    msg := sprintf("Deployment name '%s' does not match naming pattern", [name])
}

deny[msg] {
    input.kind == "Service"
    name := input.metadata.name
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    not re_match(pattern, name)
    msg := sprintf("Service name '%s' does not match naming pattern", [name])
}

deny[msg] {
    input.kind == "Ingress"
    name := input.metadata.name
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    not re_match(pattern, name)
    msg := sprintf("Ingress name '%s' does not match naming pattern", [name])
}

deny[msg] {
    input.kind == "ConfigMap"
    name := input.metadata.name
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    not re_match(pattern, name)
    msg := sprintf("ConfigMap name '%s' does not match naming pattern", [name])
}

deny[msg] {
    input.kind == "Secret"
    name := input.metadata.name
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    not re_match(pattern, name)
    msg := sprintf("Secret name '%s' does not match naming pattern", [name])
}

# Required labels
warn[msg] {
    not input.metadata.labels.environment
    msg := "Missing required label: environment"
}

warn[msg] {
    not input.metadata.labels.component
    msg := "Missing required label: component"
}

warn[msg] {
    not input.metadata.labels.version
    msg := "Missing required label: version"
}

# Required annotations for certain resources
warn[msg] {
    input.kind == "Deployment"
    not input.metadata.annotations
    msg := "Deployment should have annotations for documentation"
}