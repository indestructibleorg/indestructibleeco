package indestructibleeco.qyaml

import future.keywords.in

deny[msg] {
    not input.document_metadata
    msg := "Missing mandatory block: document_metadata"
}

deny[msg] {
    not input.governance_info
    msg := "Missing mandatory block: governance_info"
}

deny[msg] {
    not input.registry_binding
    msg := "Missing mandatory block: registry_binding"
}

deny[msg] {
    not input.vector_alignment_map
    msg := "Missing mandatory block: vector_alignment_map"
}

deny[msg] {
    not input.document_metadata.unique_id
    msg := "Missing required field: document_metadata.unique_id"
}

deny[msg] {
    uri := input.document_metadata.uri
    not startswith(uri, "indestructibleeco://")
    msg := sprintf("Invalid URI format: %s", [uri])
}

deny[msg] {
    urn := input.document_metadata.urn
    not startswith(urn, "urn:indestructibleeco:")
    msg := sprintf("Invalid URN format: %s", [urn])
}

deny[msg] {
    ns := input.metadata.namespace
    ns != "indestructibleeco"
    ns != "indestructibleeco-staging"
    msg := sprintf("Invalid namespace: %s", [ns])
}

deny[msg] {
    some container in input.spec.template.spec.containers
    image := container.image
    not startswith(image, "ghcr.io/indestructibleorg/")
    msg := sprintf("Unapproved image registry: %s", [image])
}

deny[msg] {
    some container in input.spec.template.spec.containers
    name := container.name
    not startswith(name, "eco-")
    msg := sprintf("Container name %s must start with eco-", [name])
}

deny[msg] {
    some container in input.spec.template.spec.containers
    not container.resources.limits
    msg := sprintf("Container %s missing resource limits", [container.name])
}

deny[msg] {
    some container in input.spec.template.spec.containers
    not container.livenessProbe
    msg := sprintf("Container %s missing liveness probe", [container.name])
}

warn[msg] {
    sv := input.document_metadata.schema_version
    sv != "1.0"
    msg := sprintf("Non-standard schema_version: %s", [sv])
}
