package mno.governance.policies.autonomy

import future.keywords.in

# Autonomy Policy for MachineNativeOps
# Enforces autonomy level requirements and progression rules

# Default decision is deny
default allow = false

# Allow if all autonomy rules pass
allow {
    input.resource.type == "module"
    module_autonomy_valid(input.resource)
}

allow {
    input.resource.type == "operation"
    operation_autonomy_valid(input.resource)
}

allow {
    input.resource.type == "component"
    component_autonomy_valid(input.resource)
}

# Module autonomy validation
module_autonomy_valid(module) {
    has_autonomy_level(module)
    autonomy_level_valid(module.autonomy_level)
    autonomy_matches_dependencies(module)
    autonomy_progression_allowed(module)
}

# Operation autonomy validation
operation_autonomy_valid(operation) {
    has_required_autonomy(operation)
    operation_complies_with_module_level(operation)
    human_intervention_respected(operation)
}

# Component autonomy validation
component_autonomy_valid(component) {
    component_autonomy_level_defined(component)
    component_autonomy_within_module_range(component)
}

# Validation helpers
has_autonomy_level(module) {
    module.autonomy_level
}

autonomy_level_valid(level) {
    valid_levels := ["L1", "L2", "L3", "L4", "L5", "Global Layer"]
    level in valid_levels
}

autonomy_matches_dependencies(module) {
    module_level := get_level_value(module.autonomy_level)
    max_dep := max_dependency_autonomy(module)
    module_level >= max_dep
}

autonomy_progression_allowed(module) {
    current_level := get_level_value(module.autonomy_level)
    previous_level := get_level_value(module.previous_autonomy_level)
    current_level >= previous_level
    current_level - previous_level <= 2
}

has_required_autonomy(operation) {
    operation.required_autonomy_level
    valid_op_levels := ["L1", "L2", "L3", "L4", "L5"]
    operation.required_autonomy_level in valid_op_levels
}

operation_complies_with_module_level(operation) {
    req_level := get_level_value(operation.required_autonomy_level)
    mod_level := get_level_value(operation.module_autonomy_level)
    req_level <= mod_level
}

human_intervention_respected(operation) {
    operation.autonomy_level != "L5"
}

human_intervention_respected(operation) {
    operation.autonomy_level == "L5"
    operation.human_intervention == false
}

component_autonomy_level_defined(component) {
    component.autonomy_level
}

component_autonomy_within_module_range(component) {
    component_level := get_level_value(component.autonomy_level)
    min_level := get_level_value(component.module_min_autonomy)
    max_level := get_level_value(component.module_max_autonomy)
    component_level >= min_level
    component_level <= max_level
}

# Helper: get max dependency autonomy level
max_dependency_autonomy(module) := result {
    module.dependencies
    count(module.dependencies) > 0
    dep_levels := [get_level_value(dep.autonomy_level) | some dep in module.dependencies]
    result := max(dep_levels)
} else := 0

# Helper: convert autonomy level to numeric value
get_level_value(level) := 1 {
    level == "L1"
}

get_level_value(level) := 2 {
    level == "L2"
}

get_level_value(level) := 3 {
    level == "L3"
}

get_level_value(level) := 4 {
    level == "L4"
}

get_level_value(level) := 5 {
    level == "L5"
}

get_level_value(level) := 10 {
    level == "Global Layer"
}

get_level_value(level) := 0 {
    not level
}

# Autonomy level requirements by module
autonomy_requirements := {
    "01-core": {"min": "L1", "max": "L2"},
    "02-intelligence": {"min": "L2", "max": "L3"},
    "03-governance": {"min": "L3", "max": "L4"},
    "04-autonomous": {"min": "L4", "max": "L5"},
    "05-observability": {"min": "L4", "max": "L5"},
    "06-security": {"min": "Global Layer", "max": "Global Layer"}
}

check_module_autonomy_range(module_id, level) {
    requirements := autonomy_requirements[module_id]
    level_value := get_level_value(level)
    min_value := get_level_value(requirements.min)
    max_value := get_level_value(requirements.max)
    level_value >= min_value
    level_value <= max_value
}

# Violation messages
deny[msg] {
    input.resource.type == "module"
    not has_autonomy_level(input.resource)
    msg := "Module must have an autonomy level"
}

deny[msg] {
    input.resource.type == "module"
    not autonomy_level_valid(input.resource.autonomy_level)
    msg := sprintf("Invalid autonomy level '%s', must be L1-L5 or Global Layer", [
        input.resource.autonomy_level
    ])
}

deny[msg] {
    input.resource.type == "module"
    not autonomy_matches_dependencies(input.resource)
    msg := sprintf("Module autonomy level must be >= dependency levels, got %s but dependencies require higher", [
        input.resource.autonomy_level
    ])
}

deny[msg] {
    input.resource.type == "module"
    not autonomy_progression_allowed(input.resource)
    msg := "Autonomy level progression too aggressive (max 2 levels at a time)"
}

deny[msg] {
    input.resource.type == "operation"
    not has_required_autonomy(input.resource)
    msg := "Operation must specify required autonomy level"
}

deny[msg] {
    input.resource.type == "operation"
    not operation_complies_with_module_level(input.resource)
    msg := sprintf("Operation requires %s but module only supports %s", [
        input.resource.required_autonomy_level,
        input.resource.module_autonomy_level
    ])
}

deny[msg] {
    input.resource.type == "operation"
    input.resource.autonomy_level == "L5"
    input.resource.human_intervention == true
    msg := "L5 operations must not require human intervention"
}

# Module-specific autonomy checks
deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "01-core"
    not check_module_autonomy_range("01-core", input.resource.autonomy_level)
    msg := "01-core module must have autonomy level L1-L2"
}

deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "02-intelligence"
    not check_module_autonomy_range("02-intelligence", input.resource.autonomy_level)
    msg := "02-intelligence module must have autonomy level L2-L3"
}

deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "03-governance"
    not check_module_autonomy_range("03-governance", input.resource.autonomy_level)
    msg := "03-governance module must have autonomy level L3-L4"
}

deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "04-autonomous"
    not check_module_autonomy_range("04-autonomous", input.resource.autonomy_level)
    msg := "04-autonomous module must have autonomy level L4-L5"
}

deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "05-observability"
    not check_module_autonomy_range("05-observability", input.resource.autonomy_level)
    msg := "05-observability module must have autonomy level L4-L5"
}

deny[msg] {
    input.resource.type == "module"
    input.resource.module_id == "06-security"
    not check_module_autonomy_range("06-security", input.resource.autonomy_level)
    msg := "06-security module must have autonomy level Global Layer"
}

# Autonomy progression tracking
autonomy_progression_metrics(modules) := result {
    result := {
        "total_modules": count(modules),
        "average_autonomy_level": avg_autonomy_level(modules),
        "l5_modules": count_l5_modules(modules),
        "global_layer_modules": count_global_modules(modules)
    }
}

avg_autonomy_level(modules) := result {
    count(modules) > 0
    levels := [get_level_value(m.autonomy_level) | some m in modules]
    result := sum(levels) / count(modules)
} else := 0

count_l5_modules(modules) := result {
    l5_mods := [m | some m in modules; m.autonomy_level == "L5"]
    result := count(l5_mods)
}

count_global_modules(modules) := result {
    global_mods := [m | some m in modules; m.autonomy_level == "Global Layer"]
    result := count(global_mods)
}

# Global Layer autonomy veto
global_autonomy_veto(module_change) {
    module_change.new_autonomy_level == "Global Layer"
    module_change.module_id != "06-security"
}

deny[msg] {
    input.resource.type == "module_change"
    global_autonomy_veto(input.resource)
    msg := sprintf("Global Layer VETO: Only module 06-security can have Global Layer autonomy, got %s", [
        input.resource.module_id
    ])
}

# Autonomous operation requirements
autonomous_operation_requirements := {
    "L1": {"requires_supervision": true, "human_in_loop": true},
    "L2": {"requires_supervision": true, "human_in_loop": false},
    "L3": {"requires_supervision": false, "human_in_loop": false},
    "L4": {"requires_supervision": false, "human_in_loop": false},
    "L5": {"requires_supervision": false, "human_in_loop": false}
}

check_operation_requirements(operation) {
    requirements := autonomous_operation_requirements[operation.autonomy_level]
    operation.requires_supervision == requirements.requires_supervision
    operation.human_in_loop == requirements.human_in_loop
}