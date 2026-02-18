# Workflow Patterns

## Sequential Workflows

For complex tasks, break operations into clear, sequential steps with explicit dependency chains:

```json
{
  "actions": [
    { "id": "understand", "name": "Build Mental Model", "type": "shell", "depends_on": [] },
    { "id": "retrieve", "name": "Fetch Data", "type": "api", "depends_on": ["understand"] },
    { "id": "analyze", "name": "Root Cause Analysis", "type": "transform", "depends_on": ["retrieve"] },
    { "id": "reason", "name": "Solution Derivation", "type": "transform", "depends_on": ["analyze"] },
    { "id": "repair", "name": "Apply Fix", "type": "shell", "depends_on": ["reason"] },
    { "id": "verify", "name": "Verify Fix", "type": "validate", "depends_on": ["repair"] }
  ]
}
```

This maps directly to the IndestructibleEco execution methodology:
Understanding → Retrieval → Analysis → Reasoning → One-Stop Repair

## Conditional Workflows

For tasks with branching logic, use separate action chains:

```json
{
  "actions": [
    { "id": "classify", "name": "Classify Failure Type", "type": "transform", "depends_on": [] },
    { "id": "repair-yaml", "name": "Repair YAML Syntax", "type": "shell", "depends_on": ["classify"] },
    { "id": "repair-docker", "name": "Repair Dockerfile", "type": "shell", "depends_on": ["classify"] },
    { "id": "repair-identity", "name": "Repair Identity Refs", "type": "shell", "depends_on": ["classify"] },
    { "id": "verify", "name": "Verify All Repairs", "type": "validate", "depends_on": ["repair-yaml", "repair-docker", "repair-identity"] }
  ]
}
```

The verify action waits for all repair branches to complete before running.

## Parallel Retrieval

When multiple data sources are independent, parallelize retrieval:

```json
{
  "actions": [
    { "id": "understand", "depends_on": [] },
    { "id": "retrieve-logs", "depends_on": ["understand"] },
    { "id": "retrieve-workflow", "depends_on": ["understand"] },
    { "id": "retrieve-dockerfile", "depends_on": ["understand"] },
    { "id": "analyze", "depends_on": ["retrieve-logs", "retrieve-workflow", "retrieve-dockerfile"] }
  ]
}
```

## Self-Healing Loop

For automated repair skills, always include verification and monitoring:

```json
{
  "actions": [
    { "id": "diagnose", "type": "transform", "depends_on": [] },
    { "id": "consolidate", "type": "transform", "depends_on": ["diagnose"] },
    { "id": "integrate", "type": "shell", "depends_on": ["consolidate"] },
    { "id": "verify", "type": "validate", "depends_on": ["integrate"] },
    { "id": "monitor", "type": "shell", "depends_on": ["verify"] }
  ]
}
```

Within One-Stop Repair: consolidate (merge changes) always precedes integrate (apply to system).