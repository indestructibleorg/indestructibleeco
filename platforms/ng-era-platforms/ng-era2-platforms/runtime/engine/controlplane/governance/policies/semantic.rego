package mno.governance.policies.semantic

import future.keywords.in

# Semantic Policy for MachineNativeOps
# Ensures semantic consistency across modules and components

# Default decision is deny
default allow = false

# Allow if all semantic rules pass
allow {
    input.resource.type == "module"
    module_semantic_valid(input.resource)
}

allow {
    input.resource.type == "semantic_mapping"
    semantic_mapping_valid(input.resource)
}

allow {
    input.resource.type == "component"
    component_semantic_valid(input.resource)
}

# Module semantic validation
module_semantic_valid(module) {
    has_namespace(module)
    has_semantic_mappings(module)
    semantic_health_acceptable(module)
    no_semantic_conflicts(module)
}

# Check if module has a namespace
has_namespace(module) {
    module.namespace
    valid_namespace_format(module.namespace)
}

# Check if module has semantic mappings
has_semantic_mappings(module) {
    module.semantic_mappings
    count(module.semantic_mappings) > 0
}

# Check semantic health score
semantic_health_acceptable(module) {
    module.semantic_health_score >= 80
}

# Check for semantic conflicts
no_semantic_conflicts(module) {
    not has_duplicate_concepts(module)
}

# Component semantic validation
component_semantic_valid(component) {
    has_component_semantic_mapping(component)
    component_in_namespace(component)
}

# Semantic mapping validation
semantic_mapping_valid(mapping) {
    has_concept(mapping)
    has_mapping(mapping)
    mapping_format_valid(mapping)
}

# Validation helpers
valid_namespace_format(namespace) {
    regex.match("^mno-[a-z][a-z-]*$", namespace)
}

has_duplicate_concepts(module) {
    count(module.semantic_mappings) > 1
    mappings := module.semantic_mappings
    some i, j
    mappings[i].concept == mappings[j].concept
    mappings[i].mapping != mappings[j].mapping
    i != j
}

has_component_semantic_mapping(component) {
    component.semantic_mapping
}

component_in_namespace(component) {
    startswith(component.semantic_mapping, "mno-")
}

has_concept(mapping) {
    mapping.concept
    count(mapping.concept) > 0
}

has_mapping(mapping) {
    mapping.mapping
    count(mapping.mapping) > 0
}

mapping_format_valid(mapping) {
    startswith(mapping.mapping, "mno-")
}

# Violation messages
deny[msg] {
    input.resource.type == "module"
    not has_namespace(input.resource)
    msg := "Module must have a namespace"
}

deny[msg] {
    input.resource.type == "module"
    not valid_namespace_format(input.resource.namespace)
    msg := sprintf("Module namespace '%s' must follow mno-name format", [input.resource.namespace])
}

deny[msg] {
    input.resource.type == "module"
    not has_semantic_mappings(input.resource)
    msg := "Module must have at least one semantic mapping"
}

deny[msg] {
    input.resource.type == "module"
    not semantic_health_acceptable(input.resource)
    msg := sprintf("Module semantic health score %v is below minimum threshold of 80", [
        input.resource.semantic_health_score
    ])
}

deny[msg] {
    input.resource.type == "module"
    has_duplicate_concepts(input.resource)
    msg := "Module has duplicate concepts with different mappings"
}

deny[msg] {
    input.resource.type == "component"
    not has_component_semantic_mapping(input.resource)
    msg := "Component must have a semantic mapping"
}

deny[msg] {
    input.resource.type == "semantic_mapping"
    not has_concept(input.resource)
    msg := "Semantic mapping must have a concept"
}

deny[msg] {
    input.resource.type == "semantic_mapping"
    not has_mapping(input.resource)
    msg := "Semantic mapping must have a mapping"
}

deny[msg] {
    input.resource.type == "semantic_mapping"
    not mapping_format_valid(input.resource)
    msg := sprintf("Semantic mapping '%s' must follow mno-name format", [input.resource.mapping])
}

# Global Layer semantic consistency
global_layer_consistent(modules) {
    no_namespace_conflicts(modules)
    semantic_fragments_below_threshold(modules)
}

# Check for namespace conflicts
no_namespace_conflicts(modules) {
    not namespace_conflict_exists(modules)
}

namespace_conflict_exists(modules) {
    some i, j
    modules[i].module_id != modules[j].module_id
    modules[i].namespace == modules[j].namespace
    i != j
}

# Check semantic fragmentation
semantic_fragments_below_threshold(modules) {
    total_modules := count(modules)
    total_modules > 0
    semantic_health_scores := [score | some m in modules; score := m.semantic_health_score]
    avg_health := sum(semantic_health_scores) / total_modules
    avg_health >= 90
}

# Semantic health score calculation
calculate_semantic_health(module) := score {
    base_score := 100
    
    # Deduct for missing semantic mappings
    mapping_deduction := count_missing_mappings(module) * 5
    
    # Deduct for semantic conflicts
    conflict_deduction := count_semantic_conflicts(module) * 10
    
    # Deduct for namespace violations
    namespace_deduction := namespace_violation_score(module) * 15
    
    score := base_score - mapping_deduction - conflict_deduction - namespace_deduction
}

count_missing_mappings(module) := result {
    expected_mappings := 3
    actual_mappings := count(module.semantic_mappings)
    actual_mappings < expected_mappings
    result := expected_mappings - actual_mappings
} else := 0

count_semantic_conflicts(module) := result {
    has_duplicate_concepts(module)
    result := 1
} else := 0

namespace_violation_score(module) := 1 {
    not valid_namespace_format(module.namespace)
} else := 0