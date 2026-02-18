#!/usr/bin/env node
/**
 * Skill Validator - Validates skill.json manifests against the SKILL.md spec.
 * Usage: node validate.js [skill-dir]
 */
const fs = require("fs");
const path = require("path");

const VALID_CATEGORIES = ["ci-cd-repair", "code-generation", "code-analysis", "deployment", "monitoring", "security", "testing"];
const VALID_TRIGGER_TYPES = ["webhook", "schedule", "event", "manual"];
const VALID_ACTION_TYPES = ["shell", "api", "transform", "validate", "deploy"];
const VALID_PARAM_TYPES = ["string", "number", "boolean", "object", "array"];
const VALID_LIFECYCLE = ["active", "deprecated", "sunset", "archived"];

function validate(skillDir) {
  const errors = [];
  const warnings = [];
  const manifestPath = path.join(skillDir, "skill.json");

  if (!fs.existsSync(manifestPath)) {
    errors.push(`skill.json not found in ${skillDir}`);
    return { valid: false, errors, warnings };
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
  } catch (e) {
    errors.push(`Invalid JSON: ${e.message}`);
    return { valid: false, errors, warnings };
  }

  // Required top-level fields
  for (const field of ["id", "name", "version", "description", "category", "triggers", "actions", "inputs", "outputs"]) {
    if (!(field in manifest)) errors.push(`Missing required field: ${field}`);
  }

  // ID format
  if (manifest.id && !/^[a-z0-9-]+$/.test(manifest.id)) {
    errors.push(`ID must be kebab-case: ${manifest.id}`);
  }

  // Version format
  if (manifest.version && !/^\d+\.\d+\.\d+/.test(manifest.version)) {
    errors.push(`Version must be semver: ${manifest.version}`);
  }

  // Category
  if (manifest.category && !VALID_CATEGORIES.includes(manifest.category)) {
    errors.push(`Invalid category: ${manifest.category}. Must be one of: ${VALID_CATEGORIES.join(", ")}`);
  }

  // Triggers
  if (Array.isArray(manifest.triggers)) {
    manifest.triggers.forEach((t, i) => {
      if (!t.type) errors.push(`Trigger[${i}]: missing type`);
      else if (!VALID_TRIGGER_TYPES.includes(t.type)) errors.push(`Trigger[${i}]: invalid type '${t.type}'`);
    });
  }

  // Actions - DAG validation
  if (Array.isArray(manifest.actions)) {
    const actionIds = new Set();
    manifest.actions.forEach((a, i) => {
      if (!a.id) errors.push(`Action[${i}]: missing id`);
      else if (actionIds.has(a.id)) errors.push(`Action[${i}]: duplicate id '${a.id}'`);
      else actionIds.add(a.id);

      if (!a.type) errors.push(`Action[${i}]: missing type`);
      else if (!VALID_ACTION_TYPES.includes(a.type)) errors.push(`Action[${i}]: invalid type '${a.type}'`);

      if (a.depends_on) {
        a.depends_on.forEach(dep => {
          if (!actionIds.has(dep) && !manifest.actions.some(x => x.id === dep)) {
            warnings.push(`Action '${a.id}': dependency '${dep}' not yet defined (check ordering)`);
          }
        });
      }
    });
  }

  // Inputs/Outputs
  for (const section of ["inputs", "outputs"]) {
    if (Array.isArray(manifest[section])) {
      manifest[section].forEach((p, i) => {
        if (!p.name) errors.push(`${section}[${i}]: missing name`);
        if (!p.type) errors.push(`${section}[${i}]: missing type`);
        else if (!VALID_PARAM_TYPES.includes(p.type)) errors.push(`${section}[${i}]: invalid type '${p.type}'`);
      });
    }
  }

  // Governance
  if (manifest.governance) {
    if (!manifest.governance.owner) warnings.push("Governance: missing owner");
    if (manifest.governance.lifecycle_policy && !VALID_LIFECYCLE.includes(manifest.governance.lifecycle_policy)) {
      errors.push(`Invalid lifecycle_policy: ${manifest.governance.lifecycle_policy}`);
    }
  } else {
    warnings.push("Missing governance block");
  }

  // Metadata
  if (manifest.metadata) {
    if (!manifest.metadata.unique_id) warnings.push("Metadata: missing unique_id");
    if (!manifest.metadata.schema_version) warnings.push("Metadata: missing schema_version");
  } else {
    warnings.push("Missing metadata block");
  }

  return { valid: errors.length === 0, errors, warnings, manifest };
}

// CLI execution
const skillDir = process.argv[2] || path.join(__dirname, "..", "skills");
if (fs.existsSync(skillDir) && fs.statSync(skillDir).isDirectory()) {
  const hasManifest = fs.existsSync(path.join(skillDir, "skill.json"));
  const dirs = hasManifest ? [skillDir] : fs.readdirSync(skillDir)
    .map(d => path.join(skillDir, d))
    .filter(d => fs.statSync(d).isDirectory() && fs.existsSync(path.join(d, "skill.json")));

  let allValid = true;
  dirs.forEach(dir => {
    const name = path.basename(dir);
    const result = validate(dir);
    const icon = result.valid ? "✅" : "❌";
    console.log(`${icon} ${name}: ${result.errors.length} errors, ${result.warnings.length} warnings`);
    result.errors.forEach(e => console.log(`   ERROR: ${e}`));
    result.warnings.forEach(w => console.log(`   WARN:  ${w}`));
    if (!result.valid) allValid = false;
  });

  process.exit(allValid ? 0 : 1);
} else {
  console.error(`Directory not found: ${skillDir}`);
  process.exit(1);
}