# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
<!--
@gl-layer ECO-90-META
@gl-module engine/governance/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Governance Layer - Stage 5

## Overview

The Governance Layer enforces policies, evaluates rules, resolves semantic anchors, and maintains audit trails for compliance.

## Components

### GovernanceEngine
Core governance engine orchestrating all governance operations.

**Features:**
- Policy enforcement
- Anchor resolution integration
- Rule evaluation coordination
- Event streaming for audit

### RuleEvaluator
Policy rule evaluator with multiple rule types.

**Rule Types:**
- `required`: Field must be present
- `forbidden`: Field must be absent
- `pattern`: Value must match regex pattern
- `range`: Numeric value within range
- `enum`: Value must be in allowed set
- `custom`: Custom evaluator function

### AnchorResolver (GL)
Semantic anchor resolver for governance layer.

**Features:**
- $anchor definition extraction
- $ref usage tracking
- Reference validation
- Resolution with audit trail

### EventsWriter
Governance event stream writer for compliance.

**Features:**
- Event streaming to file
- Event filtering by type/stage/component
- Statistics generation
- JSON and NDJSON export

## Usage

```typescript
import { GovernanceEngine, RuleEvaluator, EventsWriter } from './governance';

// Enforce governance
const glEngine = new GovernanceEngine();
const result = await glEngine.enforce(config, 'production');

// Evaluate rules
const ruleEvaluator = new RuleEvaluator();
const evalResult = await ruleEvaluator.evaluate(config, 'production');

// Write events
const eventsWriter = new EventsWriter({ outputPath: './artifacts/gl-events.jsonl' });
await eventsWriter.write(events);
```

## Evidence Records

All governance operations generate evidence records with:
- Policy and rule evaluation results
- Anchor resolution status
- Event streaming confirmation
- Violation tracking