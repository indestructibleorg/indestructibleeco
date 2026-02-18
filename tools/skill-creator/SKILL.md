---
name: skill-creator
description: Skill authoring, validation, and lifecycle management for IndestructibleEco platform automation units. Use when creating, updating, or validating skills that extend platform CI/CD, governance, inference routing, or deployment capabilities.
license: Apache-2.0
---

# Skill Creator

Skill authoring and lifecycle management for IndestructibleEco platform automation units.

## About Skills

Skills are modular, self-contained automation packages within the IndestructibleEco platform. Each skill defines triggers, actions, inputs, outputs, and governance metadata in a single JSON manifest (`skill.json`). Skills execute as DAGs — actions run in dependency order with retry, rollback, and audit trail.

### What Skills Provide

1. **Automated workflows** — Multi-step procedures triggered by events, schedules, or manual dispatch
2. **Tool integrations** — Shell commands, API calls, data transforms, schema validation, deployment operations
3. **Governance compliance** — Every skill carries UUID v1 identifiers, URI/URN dual identification, and compliance tags
4. **Self-healing loops** — Skills can detect failures, diagnose root causes, apply patches, and verify fixes

## Skill Structure

```
skills/<skill-name>/
├── skill.json          # Skill manifest (required)
├── actions/            # Action scripts and templates
│   ├── analyze.sh
│   ├── repair.sh
│   └── validate.sh
├── schemas/            # Input/output JSON schemas
│   ├── input.schema.json
│   └── output.schema.json
└── tests/              # Skill test cases
    └── test_skill.py
```

## Manifest Schema (skill.json)

```json
{
  "id": "string (unique, kebab-case)",
  "name": "string (human-readable)",
  "version": "string (semver)",
  "description": "string",
  "category": "ci-cd-repair | code-generation | code-analysis | deployment | monitoring | security | testing",
  "triggers": [
    {
      "type": "webhook | schedule | event | manual",
      "config": {}
    }
  ],
  "actions": [
    {
      "id": "string (unique within skill)",
      "name": "string",
      "type": "shell | api | transform | validate | deploy",
      "config": {},
      "depends_on": ["action-id"],
      "retry": { "max_attempts": 3, "backoff_ms": 1000 }
    }
  ],
  "inputs": [
    {
      "name": "string",
      "type": "string | number | boolean | object | array",
      "required": true,
      "default": null,
      "description": "string"
    }
  ],
  "outputs": [
    {
      "name": "string",
      "type": "string | number | boolean | object | array",
      "required": true,
      "description": "string"
    }
  ],
  "governance": {
    "owner": "string",
    "approval_chain": ["string"],
    "compliance_tags": ["string"],
    "lifecycle_policy": "active | deprecated | sunset | archived"
  },
  "metadata": {
    "unique_id": "UUID v1",
    "uri": "indestructibleeco://skills/<skill-id>",
    "urn": "urn:indestructibleeco:skills:<skill-id>:<uuid>",
    "schema_version": "1.0.0",
    "target_system": "string",
    "generated_by": "skill-creator-v1",
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601"
  }
}
```

## Action Types

| Type | Description | Config Fields |
|------|-------------|---------------|
| `shell` | Execute shell command | `command`, `working_dir`, `env`, `timeout_seconds` |
| `api` | HTTP API call | `method`, `url`, `headers`, `body`, `expected_status` |
| `transform` | Data transformation | `input_path`, `output_path`, `jq_filter` |
| `validate` | Schema/rule validation | `schema_path`, `rules`, `fail_on_warning` |
| `deploy` | Deployment operation | `target`, `strategy`, `rollback_on_failure` |

## Execution Model

1. Actions execute in dependency order (DAG)
2. Failed actions trigger retry with exponential backoff
3. All actions must succeed for skill completion
4. Outputs are captured and stored as artifacts
5. Governance metadata is attached to all artifacts

## Skill Creation Process

1. Define skill scope and action DAG
2. Initialize skill directory (`scripts/init_skill.py <skill-name>`)
3. Implement action scripts in `actions/`
4. Define input/output schemas in `schemas/`
5. Write `skill.json` manifest
6. Validate (`scripts/quick_validate.py <skill-name>`)
7. Test with real inputs
8. Iterate until all actions pass end-to-end

## Design Patterns

### Sequential Workflows

For multi-step processes, define explicit dependency chains:

```json
{
  "actions": [
    { "id": "understand", "depends_on": [] },
    { "id": "retrieve", "depends_on": ["understand"] },
    { "id": "analyze", "depends_on": ["retrieve"] },
    { "id": "reason", "depends_on": ["analyze"] },
    { "id": "repair", "depends_on": ["reason"] },
    { "id": "verify", "depends_on": ["repair"] }
  ]
}
```

### Parallel Retrieval

When multiple data sources are independent, parallelize:

```json
{
  "actions": [
    { "id": "understand", "depends_on": [] },
    { "id": "retrieve-logs", "depends_on": ["understand"] },
    { "id": "retrieve-workflow", "depends_on": ["understand"] },
    { "id": "analyze", "depends_on": ["retrieve-logs", "retrieve-workflow"] }
  ]
}
```

### Self-Healing Loop

For automated repair skills, include verification:

```json
{
  "actions": [
    { "id": "diagnose", "depends_on": [] },
    { "id": "patch", "depends_on": ["diagnose"] },
    { "id": "verify", "depends_on": ["patch"] },
    { "id": "monitor", "depends_on": ["verify"] }
  ]
}
```

## References

- `references/workflows.md` — Sequential and conditional workflow patterns
- `references/output-patterns.md` — Template and example output patterns
- `references/progressive-disclosure-patterns.md` — Content splitting strategies

## Lifecycle

- `active` — Skill is available for execution
- `deprecated` — Skill works but users should migrate
- `sunset` — Skill will be removed in next major version
- `archived` — Skill is read-only, cannot be executed