package esync.platform.naming

# Resource naming policy: ^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\d+.\d+.\d+(-[A-Za-z0-9]+)?$
# Examples:
# - prod-esync-api-deploy-v1.0.0
# - dev-esync-worker-svc-v2.1.3-canary
# - staging-esync-config-cm-v1.0.0

deny[reason] {
    # Check if resource has a name
    input.review.object.metadata.name
    
    # Get the name
    name := input.review.object.metadata.name
    
    # Define the regex pattern
    pattern := "^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\\d+\\.\\d+\\.\\d+(-[A-Za-z0-9]+)?$"
    
    # Check if it matches
    not re_match(pattern, name)
    
    reason := sprintf("Resource name '%s' does not match naming pattern. Expected format: ^(dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-vX.X.X(-suffix)?$", [name])
}

# Label policy
deny_labels[reason] {
    not input.review.object.metadata.labels.environment
    reason := "Resource must have 'environment' label (dev/staging/prod)"
}

deny_labels[reason] {
    not input.review.object.metadata.labels.component
    reason := "Resource must have 'component' label"
}

deny_labels[reason] {
    not input.review.object.metadata.labels.version
    reason := "Resource must have 'version' label"
}

# Annotation policy
warn_annotations[msg] {
    not input.review.object.metadata.annotations
    msg := "Resource should have annotations for better documentation"
}