#!/usr/bin/env node
/**
 * Skill Validator — Validates skill.json manifests against IndestructibleEco governance spec.
 * Usage: node validate.js [skill-dir]
 *
 * URI: indestructibleeco://tools/skill-creator/validate
 */
const fs = require("fs");
const path = require("path");

const VALID_CATEGORIES = ["ci-cd-repair", "code-generation", "code-analysis", "deployment", "monitoring", "security", "testing"];
const VALID_TRIGGER_TYPES = ["webhook", "schedule", "event", "manual"];
const VALID_ACTION_TYPES = ["shell", "api", "transform", "validate", "deploy"];
const VALID_PARAM_TYPES = ["string", "number", "boolean", "object", "array"];
const VALID_LIFECYCLE = ["active", "deprecated", "sunset", "archived"];
const UUID_V1_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const URI_RE = /^indestructibleeco:\/\//;
const URN_RE = /^urn:indestructibleeco:/;

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

  // ID format + directory match
  if (manifest.id) {
    if (!/^[a-z0-9-]+$/.test(manifest.id)) errors.push(`ID must be kebab-case: ${manifest.id}`);
    if (/^-|-$|--/.test(manifest.id)) errors.push(`ID has invalid hyphens: ${manifest.id}`);
    if (manifest.id.length > 64) errors.push(`ID too long (${manifest.id.length} chars, max 64)`);
    if (path.basename(skillDir) !== manifest.id) {
      errors.push(`ID '${manifest.id}' does not match directory name '${path.basename(skillDir)}'`);
    }
  }

  // Version
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

  // Actions — DAG validation
  if (Array.isArray(manifest.actions)) {
    const actionIds = new Set();
    const allIds = new Set(manifest.actions.filter(a => a && a.id).map(a => a.id));

    manifest.actions.forEach((a, i) => {
      if (!a.id) errors.push(`Action[${i}]: missing id`);
      else if (actionIds.has(a.id)) errors.push(`Action[${i}]: duplicate id '${a.id}'`);
      else actionIds.add(a.id);

      if (!a.type) errors.push(`Action[${i}]: missing type`);
      else if (!VALID_ACTION_TYPES.includes(a.type)) errors.push(`Action[${i}]: invalid type '${a.type}'`);

      if (Array.isArray(a.depends_on)) {
        a.depends_on.forEach(dep => {
          if (!allIds.has(dep)) {
            errors.push(`Action '${a.id}': dependency '${dep}' not found in actions`);
          }
        });
      }

      // Retry
      if (a.retry && typeof a.retry === "object") {
        if (a.retry.max_attempts !== undefined && (typeof a.retry.max_attempts !== "number" || a.retry.max_attempts < 0)) {
          errors.push(`Action '${a.id}': retry.max_attempts must be non-negative integer`);
        }
      }
    });

    // Cycle detection (topological sort)
    const visited = new Set();
    const visiting = new Set();
    function hasCycle(id) {
      if (visiting.has(id)) return true;
      if (visited.has(id)) return false;
      visiting.add(id);
      const action = manifest.actions.find(a => a.id === id);
      if (action && Array.isArray(action.depends_on)) {
        for (const dep of action.depends_on) {
          if (hasCycle(dep)) return true;
        }
      }
      visiting.delete(id);
      visited.add(id);
      return false;
    }
    for (const id of allIds) {
      if (hasCycle(id)) {
        errors.push(`Action DAG contains a cycle involving '${id}'`);
        break;
      }
    }
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

  // Governance block
  if (!manifest.governance || typeof manifest.governance !== "object") {
    errors.push("Missing governance block");
  } else {
    if (!manifest.governance.owner) errors.push("Governance: missing owner");
    if (!Array.isArray(manifest.governance.approval_chain) || manifest.governance.approval_chain.length === 0) {
      errors.push("Governance: missing or empty approval_chain");
    }
    if (!Array.isArray(manifest.governance.compliance_tags)) {
      warnings.push("Governance: missing compliance_tags");
    }
    if (manifest.governance.lifecycle_policy && !VALID_LIFECYCLE.includes(manifest.governance.lifecycle_policy)) {
      errors.push(`Governance: invalid lifecycle_policy '${manifest.governance.lifecycle_policy}'`);
    }
  }

  // Metadata block (governance identity)
  if (!manifest.metadata || typeof manifest.metadata !== "object") {
    errors.push("Missing metadata block");
  } else {
    const m = manifest.metadata;
    if (!m.unique_id) errors.push("Metadata: missing unique_id");
    else if (!UUID_V1_RE.test(m.unique_id)) warnings.push(`Metadata: unique_id does not match UUID v1 pattern`);

    if (!m.uri) errors.push("Metadata: missing uri");
    else if (!URI_RE.test(m.uri)) errors.push(`Metadata: uri must start with 'indestructibleeco://'`);

    if (!m.urn) errors.push("Metadata: missing urn");
    else if (!URN_RE.test(m.urn)) errors.push(`Metadata: urn must start with 'urn:indestructibleeco:'`);

    if (!m.schema_version) warnings.push("Metadata: missing schema_version");
    if (!m.generated_by) warnings.push("Metadata: missing generated_by");
    if (!m.created_at) warnings.push("Metadata: missing created_at");
  }

  return { valid: errors.length === 0, errors, warnings, manifest };
}

// --- CLI ---
const skillDir = process.argv[2] || path.join(__dirname, "..", "skills");
if (fs.existsSync(skillDir) && fs.statSync(skillDir).isDirectory()) {
  const hasManifest = fs.existsSync(path.join(skillDir, "skill.json"));
  const dirs = hasManifest ? [skillDir] : fs.readdirSync(skillDir)
    .map(d => path.join(skillDir, d))
    .filter(d => fs.statSync(d).isDirectory() && fs.existsSync(path.join(d, "skill.json")));

  if (dirs.length === 0) {
    console.log("No skills found to validate.");
    process.exit(0);
  }

  let allValid = true;
  dirs.forEach(dir => {
    const name = path.basename(dir);
    const result = validate(dir);
    const icon = result.valid ? "✓" : "✗";
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