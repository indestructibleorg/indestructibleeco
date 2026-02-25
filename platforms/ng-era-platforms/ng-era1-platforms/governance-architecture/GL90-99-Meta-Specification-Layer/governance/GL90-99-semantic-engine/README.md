# GL Semantic Core Engine

A fully functional semantic engine that transforms YAML specifications into computable, reasonaable, indexable, and foldable semantic structures.

## Overview

The Semantic Core Engine implements a complete semantic computing system with 6 phases:

### ⭐ Phase 2: Semantic Folding (語意折疊)
Transforms YAML semantic structures into computable semantic nodes with:
- **Feature Extraction**: Extracts semantic features from domains, capabilities, resources, labels
- **Vector Generation**: Creates 128-dimensional semantic vectors using bit vector compression
- **Semantic Relations**: Builds graph of relationships between semantic entities

### ⭐ Phase 3: Semantic Parameterization (語意參數化)
Provides queryable, referencable, composable semantic API:
- `get_semantics(id)` - Query semantic definitions by ID
- `get_domain(id)` - Access domain semantics
- `get_capability(id)` - Access capability semantics
- `get_resource(id)` - Access resource semantics
- `get_label(id)` - Access label semantics
- `compose_semantics(ids)` - Combine multiple semantic definitions

### ⭐ Phase 4: Semantic Indexing (語意索引)
Implements millisecond-level semantic queries:
- **ID-based Index**: O(1) lookup by node ID
- **Feature-based Index**: Find nodes by semantic features
- **Hierarchical Index**: Domain → Capability → Resource mappings
- **Vector Index**: Semantic similarity search

### ⭐ Phase 5: Semantic Optimization (語意性能優化)
Optimizes query performance with:
- **Bit Vector Compression**: Features compressed for O(1) bitwise operations
- **Semantic Cache**: Frequently accessed queries cached
- **Precomputation**: Semantic overlaps, conflicts, and mappings precomputed
- **Performance**: O(1) and O(log n) operations achieved

### ⭐ Phase 6: Semantic Engine Integration (語意引擎化)
Unified API with comprehensive capabilities:
- **Query Methods**: `query()`, `query_by_feature()`, `query_related()`, `semantic_search()`
- **Inference Methods**: `infer_capabilities()`, `infer_resources()`, `infer_labels()`
- **Validation Methods**: `validate_conflict()`, `validate_duplicate()`, `validate_consistency()`, `validate_completeness()`
- **Mapping Methods**: `map_internal_to_ui()`, `map_platform_to_api()`, `map_component_to_functional()`

## Installation

```bash
pip install pyyaml flask numpy
```

## Quick Start

### Python API

```python
from semantic_engine import SemanticEngine

# Initialize engine
engine = SemanticEngine(embedding_dim=128)

# Load specification
graph = engine.load_specification_from_file('semantic-unification-spec.yaml')

# Query semantic nodes
domain = engine.get_domain("runtime")
print(domain['description'])  # "運行時環境與執行引擎"

# Query by features
nodes = engine.query_by_feature("execution")
for node in nodes:
    print(f"{node['type']}: {node['id']}")

# Inference
capabilities = engine.infer_capabilities("api")
for cap in capabilities:
    print(f"Capability: {cap['capability_id']}")
```

### REST API

Start the server:
```bash
python -c "from semantic_engine.api_server import app; app.run(host='0.0.0.0', port=3333)"
```

#### API Endpoints

**Health Check**
```bash
curl [EXTERNAL_URL_REMOVED]
```

**Load Specification**
```bash
curl -X POST [EXTERNAL_URL_REMOVED] \
  -H "Content-Type: application/json" \
  -d '{"specification": "<yaml_content>"}'
```

**Query Semantic Node**
```bash
curl "[EXTERNAL_URL_REMOVED]
```

**Query by Feature**
```bash
curl "[EXTERNAL_URL_REMOVED]
```

**Infer Capabilities**
```bash
curl "[EXTERNAL_URL_REMOVED]
```

**Validate Conflict**
```bash
curl -X POST [EXTERNAL_URL_REMOVED] \
  -H "Content-Type: application/json" \
  -d '{"node_a_id": "domain.runtime", "node_b_id": "domain.api"}'
```

## Architecture

```
semantic_engine/
├── __init__.py              # Package initialization
├── semantic_models.py        # Core data structures
├── semantic_folding.py        # Phase 2: Folding engine
├── semantic_parameterization.py  # Phase 3: Parameterization
├── semantic_indexing.py       # Phase 4: Indexing engine
├── semantic_inference.py     # Phase 6: Inference engine
├── semantic_engine.py        # Phase 6: Main unified API
└── api_server.py            # REST API server
```

## Performance

- **Query by ID**: O(1)
- **Query by Feature**: O(1)
- **Semantic Search**: O(n) with indexing optimizations
- **Inference**: O(1) with precomputation
- **Validation**: O(1) with precomputed caches

## Statistics

From the test run with semantic-unification-spec.yaml:
- **Graph Nodes**: 32
- **Graph Edges**: 6
- **Indexed Features**: 112
- **Indexed Vectors**: 32
- **Folding Cache Size**: 118
- **Inference Cache Size**: 0 (fresh run)

## Example Output

```
✓ Loaded specification: 32 semantic nodes, 6 edges
✓ Phase 2 Folding: Domain and capability nodes with vectors
✓ Phase 3 Parameterization: All get_domain, get_capability, get_resource, get_label working
✓ Phase 4 Indexing: Feature and semantic search operational
✓ Phase 5 Optimization: 118 features cached, 112 feature co-occurrence entries precomputed
✓ Phase 6 Integration: Full unified API working with inference and validation
```

## License

GL Semantic Core Platform v1.0.0

## Contributing

This is part of the MachineNativeOps GL Platform Enterprise Architecture.