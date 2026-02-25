# @GL-layer: GQS-L0
package machinenativeops.naming

# Default deny
default allow = false

# Naming policy for Kubernetes resources
allow {
    input.kind == kind
    resource_name_pattern(input.metadata.name, kind)
    resource_labels_present(input.metadata.labels, kind)
}

# Naming pattern: (dev|staging|prod)-[a-z0-9-]+-(deploy|svc|ing|cm|secret)-v\d+.\d+.\d+(-[A-Za-z0-9]+)?
resource_name_pattern(name, kind) {
    kind == "Deployment"
    regex.match("^(dev|staging|prod)-[a-z0-9-]+-deploy-v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9]+)?$", name)
}

resource_name_pattern(name, kind) {
    kind == "Service"
    regex.match("^(dev|staging|prod)-[a-z0-9-]+-svc-v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9]+)?$", name)
}

resource_name_pattern(name, kind) {
    kind == "Ingress"
    regex.match("^(dev|staging|prod)-[a-z0-9-]+-ing-v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9]+)?$", name)
}

resource_name_pattern(name, kind) {
    kind == "ConfigMap"
    regex.match("^(dev|staging|prod)-[a-z0-9-]+-cm-v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9]+)?$", name)
}

resource_name_pattern(name, kind) {
    kind == "Secret"
    regex.match("^(dev|staging|prod)-[a-z0-9-]+-secret-v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9]+)?$", name)
}

# Required labels for all resources
resource_labels_present(labels, kind) {
    labels["app.kubernetes.io/name"]
    labels["app.kubernetes.io/version"]
    labels["app.kubernetes.io/managed-by"]
    labels["machinenativeops.gl/environment"]
    labels["machinenativeops.gl/tier"]
}

# Violation message
violation[msg] {
    not allow
    msg := sprintf("Resource %s of kind %s violates naming policy", [input.metadata.name, input.kind])
}