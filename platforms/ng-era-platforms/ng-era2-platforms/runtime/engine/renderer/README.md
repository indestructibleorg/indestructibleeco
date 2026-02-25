<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

<!--
@gl-layer ECO-90-META
@gl-module engine/renderer/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Renderer Stage - Stage 6

## Overview

The Renderer Stage renders configuration data into artifacts using template engines, maps modules to artifacts, and writes them to the filesystem with integrity verification.

## Components

### TemplateEngine
Jinja2 template engine using Nunjucks.

**Features:**
- Nunjucks template rendering
- Custom filters (to_yaml, to_json, sha256, base64, etc.)
- Custom macros
- Global variables

**Usage:**
```typescript
import { TemplateEngine } from './renderer/template_engine';

const engine = new TemplateEngine({
  templatePaths: ['./templates', './modules'],
  filters: new Map([['custom', (val) => transform(val)]])
});
const result = await engine.render('config.yaml.j2', data, 'output.yaml');
```

### ModuleMapper
Module to artifact mapper with dependency resolution.

**Features:**
- Dependency graph resolution
- Topological sorting
- Module mapping
- Circular dependency detection

**Usage:**
```typescript
import { ModuleMapper } from './renderer/module_mapper';

const mapper = new ModuleMapper();
const artifacts = await mapper.mapModules(config, moduleRegistry);
```

### ArtifactWriter
Artifact writer with SHA256 hash generation.

**Features:**
- Write artifacts to filesystem
- Generate SHA256 hashes
- Integrity verification
- Atomic writes

**Usage:**
```typescript
import { ArtifactWriter } from './renderer/artifact_writer';

const writer = new ArtifactWriter();
const result = await writer.write(artifactPath, content, outputPath);
```

## Evidence Records

All renderer operations generate evidence records with:
- Template and artifact paths
- Rendering metadata
- Hash verification
- Performance metrics

## Output

**RenderResult:**
- `status`: 'success' | 'error' | 'warning'
- `content`: string - Rendered content
- `outputPath`: string - Path where artifact was written
- `errors`: string[] - Any errors encountered
- `evidence`: EvidenceRecord[] - Complete evidence chain
