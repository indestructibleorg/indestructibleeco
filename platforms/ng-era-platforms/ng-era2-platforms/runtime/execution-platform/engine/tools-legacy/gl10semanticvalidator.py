# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: archive-tools
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#
# @ECO-governed
# @ECO-layer: gl-platform.governance
# @ECO-semantic: gl10semanticvalidator
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL10 Phase2 Semantic Validator
Validates semantic terms and functional dimensions for GL10-29 layer
Updated to support new project-docs directory structure
"""
# MNGA-002: Import organization needs review
import json
import sys
import glob
import os
# Run from repo root
base = "."
# Try multiple possible schema locations
schema_paths = [
    os.path.join(base, "schemas", "GL10-phase2-schema.json"),
    os.path.join(base, "GL10-phase2-schema.json"),
    os.path.join(base, "project-docs", "gl-gl-platform.governance", "schemas", "GL10-phase2-schema.json"),
]
schema = None
for schema_path in schema_paths:
    try:
        with open(schema_path, encoding='utf-8') as _f:
            schema = json.load(_f)
        print(f"Found schema at: {schema_path}", file=sys.stderr)
        break
    except Exception:
        continue
if schema is None:
    print(f"Warning: Schema not found, tried: {schema_paths}", file=sys.stderr)
    # Continue without schema validation
# Collect artifacts - look for GL17-GL24 files (semantic terms and functional dimensions)
# Search in multiple locations
search_paths = [
    # Root directory (legacy)
    os.path.join(base, "GL1[7-9]*.json"),
    os.path.join(base, "GL2[0-4]*.json"),
    # New project-docs location
    os.path.join(base, "project-docs", "gl-gl-platform.governance", "semantic-terms", "GL1[7-9]*.json"),
    os.path.join(base, "project-docs", "gl-gl-platform.governance", "semantic-terms", "GL2[0-4]*.json"),
]
files = []
for pattern in search_paths:
    files.extend(glob.glob(pattern))
# Remove duplicates
files = list(set(files))
print(f"Found {len(files)} GL semantic term files", file=sys.stderr)
for f in files:
    print(f"  - {f}", file=sys.stderr)
semantic_terms = set()
functional_dims = set()
artifact_terms = []
for f in files:
    try:
        with open(f, encoding='utf-8') as _f:
            data = json.load(_f)
    except Exception as e:
        print(f"Warning: Could not parse {f}: {e}", file=sys.stderr)
        continue
    st = data.get("semanticterms", [])
    fd = data.get("functionaldimensions", [])
    artifact_terms.append({"file": f, "semanticterms": st, "functional_dimensions": fd})
    semantic_terms.update([s.lower() for s in st])
    functional_dims.update([d.lower() for d in fd])
# Required semantic and functional dimensions
required_semantic = ["process", "standard", "monitoring", "resource allocation"]
required_functional = ["process optimization", "resource scheduling", "risk control", "operational supervision"]
# Check missing
missing_sem = [r for r in required_semantic if r.lower() not in semantic_terms]
missing_func = [r for r in required_functional if r.lower() not in functional_dims]
# Calculate semantic consistency: percentage of artifacts containing required_semantic
total_artifacts = len(files) if files else 1
match_counts = 0
for a in artifact_terms:
    terms = [t.lower() for t in a.get("semanticterms", [])]
    dims = [d.lower() for d in a.get("functional_dimensions", [])]
    if any(req in terms for req in required_semantic) or any(req in dims for req in required_functional):
        match_counts += 1
consistency = match_counts / total_artifacts
# Output result and blocking conditions (threshold 0.75)
result = {
    "missingsemantic": missing_sem,
    "missingfunctional": missing_func,
    "semantic_consistency": round(consistency, 2),
    "total_artifacts": total_artifacts,
    "matched_artifacts": match_counts,
    "files_found": files
}
print(json.dumps(result))
# Exit with error if missing items or consistency below threshold
if missing_sem or missing_func or consistency < 0.75:
    sys.exit(2)
sys.exit(0)