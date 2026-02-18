# Output Patterns

Use these patterns when skills need to produce consistent, structured output.

## Structured Report Pattern

For skills that produce diagnostic or repair reports:

```json
{
  "outputs": [
    { "name": "root_cause", "type": "string", "required": true, "description": "Identified root cause" },
    { "name": "fix_applied", "type": "boolean", "required": true, "description": "Whether fix was applied" },
    { "name": "verification_status", "type": "string", "required": true, "description": "success|failure|timeout" },
    { "name": "patch_diff", "type": "string", "required": false, "description": "Unified diff of changes" },
    { "name": "error_taxonomy", "type": "object", "required": false, "description": "Classified error details" }
  ]
}
```

## Error Taxonomy Pattern

For skills that classify errors into categories:

```json
{
  "error_taxonomy": {
    "category": "yaml-syntax | dockerfile-path | identity-drift | governance-missing | schema-violation",
    "severity": "error | warning",
    "file": "path/to/file",
    "line": 71,
    "message": "Human-readable description",
    "auto_fixable": true,
    "fix_strategy": "heredoc-replacement | path-correction | block-injection | reference-update"
  }
}
```

## Governance Stamp Pattern

All skill outputs must carry governance metadata:

```json
{
  "governance_stamp": {
    "unique_id": "UUID v1",
    "uri": "indestructibleeco://skills/<skill-id>/output/<run-id>",
    "urn": "urn:indestructibleeco:skills:<skill-id>:output:<run-id>:<uuid>",
    "generated_by": "skill-creator-v1",
    "created_at": "ISO 8601",
    "schema_version": "1.0.0"
  }
}
```

## Patch Output Pattern

For skills that generate code modifications:

```
--- a/.github/workflows/ci.yaml
+++ b/.github/workflows/ci.yaml
@@ -68,4 +68,6 @@
-        python3 -c "
-        from src.config import Settings
+        cat > /tmp/test.py << 'PYEOF'
+        import sys
+        sys.path.insert(0, '.')
+        from src.config import Settings
+        PYEOF
+        python3 /tmp/test.py
```

Patches must be in unified diff format, applicable via `git apply`.