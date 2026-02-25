# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
<!--
@gl-layer ECO-90-META
@gl-module engine/loader/docs
@gl-semantic-anchor ECO-90-META-DOC
@gl-evidence-required false
-->

# Loader Stage - Stage 1

## Overview

The Loader Stage is responsible for loading DSL configuration files from various sources, including the file system and Git repositories, then merging them into a unified index.

## Components

### FsLoader
File system loader with recursive directory traversal.

**Features:**
- Recursive directory loading
- Ignore patterns support
- SHA256 hash generation for files
- Error handling for missing directories

**Usage:**
```typescript
import { FsLoader } from './loader/fs_loader';

const loader = new FsLoader('./dsl', { 
  ignore: ['node_modules', '.git'] 
});
const result = await loader.load();
```

### GitLoader
Git repository loader supporting branches, tags, and commits.

**Features:**
- Clone Git repositories
- Load specific branches/tags/commits
- Extract Git metadata
- Clean up after loading

**Usage:**
```typescript
import { GitLoader } from './loader/git_loader';

const loader = new GitLoader({
  url: '[EXTERNAL_URL_REMOVED]
  branch: 'main',
  commit: 'abc123'
});
const result = await loader.load();
```

### MergeIndex
Index merger with configurable conflict resolution strategies.

**Merge Strategies:**
- `error`: Fail on conflicts
- `first`: Use first value (source priority)
- `last`: Use last value (override priority)
- `newest`: Use value with newest timestamp
- `custom`: Use custom resolver function

**Usage:**
```typescript
import { MergeIndex } from './loader/merge_index';

const merger = new MergeIndex({ strategy: 'last' });
const result = await merger.merge([index1, index2, index3]);
```

## Evidence Records

All loader operations generate evidence records with:
- Source information (directory URL)
- File counts and hashes
- Error tracking
- Performance metrics

## Output

**LoadResult:**
- `status`: 'success' | 'error' | 'warning'
- `files`: Map<string, any> - Loaded configuration data
- `errors`: string[] - Any errors encountered
- `evidence`: EvidenceRecord[] - Complete evidence chain
