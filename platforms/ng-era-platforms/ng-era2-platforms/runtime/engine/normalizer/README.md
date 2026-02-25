<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

<!--
@gl-layer ECO-90-META
@gl-module engine/normalizer/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Normalizer Stage - Stage 3

## Overview

The Normalizer Stage normalizes configuration data by applying environment-specific values, defaults, and module-level configurations.

## Components

### EnvMerger
Environment configuration merger with deep merge support.

**Features:**
- Deep merge of nested objects
- Override tracking
- Environment-specific overrides
- Conflict resolution

**Usage:**
```typescript
import { EnvMerger } from './normalizer/env_merger';

const merger = new EnvMerger();
const result = await merger.merge(baseConfig, envConfig, 'production');
```

### DefaultsApplier
Default value applier based on schema definitions.

**Features:**
- Extract defaults from JSON Schema
- Apply to missing fields
- Nested object support
- Type validation

**Usage:**
```typescript
import { DefaultsApplier } from './normalizer/defaults_applier';

const applier = new DefaultsApplier();
const result = await applier.apply(data, schema);
```

### ModuleDefaults
Module-level default configuration manager.

**Features:**
- Batch processing of modules
- Module-specific defaults
- Override tracking
- Validation

**Usage:**
```typescript
import { ModuleDefaults } from './normalizer/module_defaults';

const manager = new ModuleDefaults();
const result = await manager.applyDefaults(config, moduleRegistry);
```

## Evidence Records

All normalizer operations generate evidence records with:
- Merge operations tracking
- Override paths
- Applied defaults
- Performance metrics

## Output

**NormalizerResult:**
- `status`: 'success' | 'error' | 'warning'
- `data`: any - Normalized configuration data
- `errors`: string[] - Any errors encountered
- `evidence`: EvidenceRecord[] - Complete evidence chain
