# Skill Definition Format v1.0

## Overview

A **Skill** is a self-contained, declarative automation unit within the IndestructibleEco platform. Each skill defines triggers, actions, inputs, outputs, and governance metadata in a single JSON manifest.

## File Structure

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
├── tests/              # Skill test cases
│   └── test_skill.py
└── README.md           # Skill documentation
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
    "schema_version": "1.0.0",
    "target_system": "string",
    "generated_by": "string",
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

## Lifecycle

- `active`: Skill is available for execution
- `deprecated`: Skill works but users should migrate
- `sunset`: Skill will be removed in next major version
- `archived`: Skill is read-only, cannot be executed