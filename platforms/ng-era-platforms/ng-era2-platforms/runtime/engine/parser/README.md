<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

<!--
@gl-layer ECO-90-META
@gl-module engine/parser/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Parser Stage - Stage 2

## Overview

The Parser Stage parses raw file contents into structured data objects, supporting YAML and JSON formats with advanced features like anchor resolution.

## Components

### YamlParser
YAML parser with full js-yaml support.

**Features:**
- Parse YAML files
- Support for anchors and aliases
- Warning collection
- Schema validation

**Usage:**
```typescript
import { YamlParser } from './parser/yaml_parser';

const parser = new YamlParser();
const result = await parser.parse(yamlContent, 'config.yaml');
```

### JsonPassthrough
JSON parser for pre-parsed JSON objects.

**Features:**
- Validate JSON objects
- Type checking
- Error reporting

**Usage:**
```typescript
import { JsonPassthroughParser } from './parser/json_passthrough';

const parser = new JsonPassthroughParser();
const result = await parser.parse(jsonObject, 'config.json');
```

### AnchorResolver
YAML anchor and alias resolver.

**Features:**
- Extract anchor definitions
- Track anchor usage
- Validate references
- Resolve with audit trail

**Usage:**
```typescript
import { AnchorResolver } from './parser/anchor_resolver';

const resolver = new AnchorResolver();
const resolved = await resolver.resolve(parsedData);
```

## Evidence Records

All parser operations generate evidence records with:
- File path and content size
- Parsing warnings
- Anchor definitions and usage
- Performance metrics

## Output

**ParseResult:**
- `status`: 'success' | 'error' | 'warning'
- `data`: any - Parsed structured data
- `errors`: string[] - Any errors encountered
- `evidence`: EvidenceRecord[] - Complete evidence chain
