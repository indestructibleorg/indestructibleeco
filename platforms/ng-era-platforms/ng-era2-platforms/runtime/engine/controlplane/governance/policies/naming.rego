package mno.governance.policies.naming

import future.keywords.in

# Naming Policy for MachineNativeOps
# Enforces kebab-case naming conventions and namespace governance

# Default decision is deny
default allow = false

# Allow if all naming rules pass
allow {
    input.resource.type == "file"
    file_naming_valid(input.resource.name)
}

allow {
    input.resource.type == "directory"
    directory_naming_valid(input.resource.name)
}

allow {
    input.resource.type == "module"
    module_naming_valid(input.resource)
}

allow {
    input.resource.type == "interface"
    interface_naming_valid(input.resource)
}

allow {
    input.resource.type == "component"
    component_naming_valid(input.resource)
}

# File naming validation: must be kebab-case
file_naming_valid(name) {
    not has_space(name)
    not has_underscore(name)
    not regex.match("[A-Z]", name)
    has_valid_extension(name)
}

# Directory naming validation: must be kebab-case
directory_naming_valid(name) {
    not has_space(name)
    not has_underscore(name)
    not regex.match("[A-Z]", name)
}

# Module naming validation: must follow XX-name pattern
module_naming_valid(module) {
    regex.match("^\\d{2}-[a-z][a-z-]*$", module.module_id)
    regex.match("^mno-[a-z][a-z-]*$", module.namespace)
}

# Interface naming validation
interface_naming_valid(interface) {
    kebab_case(interface.name)
    valid_interface_type(interface.type)
}

# Component naming validation
component_naming_valid(component) {
    kebab_case(component.name)
    valid_component_type(component.type)
}

# Helper: check if string is kebab-case
kebab_case(s) {
    not has_space(s)
    not has_underscore(s)
    not regex.match("[A-Z]", s)
}

# Helper: check for space
has_space(s) {
    contains(s, " ")
}

# Helper: check for underscore
has_underscore(s) {
    contains(s, "_")
}

# Helper: check if file has valid extension
has_valid_extension(filename) {
    parts := split(filename, ".")
    count(parts) > 1
}

# Helper: valid interface types
valid_interface_type(t) {
    valid_types := ["api", "service", "data", "workflow"]
    t in valid_types
}

# Helper: valid component types
valid_component_type(t) {
    valid_types := ["service", "library", "tool", "framework"]
    t in valid_types
}

# Violation messages
deny[msg] {
    input.resource.type == "file"
    not file_naming_valid(input.resource.name)
    msg := sprintf("File name '%s' must be kebab-case", [input.resource.name])
}

deny[msg] {
    input.resource.type == "directory"
    not directory_naming_valid(input.resource.name)
    msg := sprintf("Directory name '%s' must be kebab-case", [input.resource.name])
}

deny[msg] {
    input.resource.type == "module"
    not module_naming_valid(input.resource)
    msg := sprintf("Module must have module_id in format XX-name and namespace in format mno-name, got '%s' and '%s'", [
        input.resource.module_id,
        input.resource.namespace
    ])
}

# Semantic namespace validation
valid_namespace(namespace) {
    regex.match("^mno-[a-z][a-z-]*$", namespace)
}

# Reserved namespaces that require special approval
reserved_namespaces := [
    "mno-core",
    "mno-intelligence",
    "mno-governance",
    "mno-autonomous",
    "mno-observability",
    "mno-security"
]

deny[msg] {
    input.resource.type == "module"
    not valid_namespace(input.resource.namespace)
    msg := sprintf("Invalid namespace '%s', must follow mno-name format", [input.resource.namespace])
}

deny[msg] {
    input.resource.type == "module"
    input.resource.namespace in reserved_namespaces
    input.resource.module_id != get_module_id_for_namespace(input.resource.namespace)
    msg := sprintf("Namespace '%s' is reserved for module %s", [
        input.resource.namespace,
        get_module_id_for_namespace(input.resource.namespace)
    ])
}

# Helper: map reserved namespaces to module IDs
get_module_id_for_namespace(namespace) := "01-core" {
    namespace == "mno-core"
}

get_module_id_for_namespace(namespace) := "02-intelligence" {
    namespace == "mno-intelligence"
}

get_module_id_for_namespace(namespace) := "03-governance" {
    namespace == "mno-governance"
}

get_module_id_for_namespace(namespace) := "04-autonomous" {
    namespace == "mno-autonomous"
}

get_module_id_for_namespace(namespace) := "05-observability" {
    namespace == "mno-observability"
}

get_module_id_for_namespace(namespace) := "06-security" {
    namespace == "mno-security"
}