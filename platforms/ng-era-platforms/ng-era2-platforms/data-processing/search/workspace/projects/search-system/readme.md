<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Search Indexing System
**ECO-Layer: GL30-49 (Execution)**
**Closure-Signal: manifest, artifact**

## Overview

Comprehensive Elasticsearch-based search indexing system with full-text search, faceted search, autocomplete, bulk indexing, incremental updates, and search analytics.

## Features

### Core Capabilities
- **Bulk Indexing**: Batch document indexing with retry logic
- **Incremental Updates**: Change detection with hash-based comparison
- **Index Optimization**: Automatic segment merging and optimization
- **Full-Text Search**: Multi-field search with highlighting
- **Faceted Search**: Multi-dimensional filtering and aggregation
- **Autocomplete**: Real-time search suggestions with edge n-grams
- **Relevance Tuning**: Field weights and boost functions
- **Search Analytics**: Query logging, click tracking, trends analysis

### Configuration
- **Analyzers**: Custom text and autocomplete analyzers
- **Tokenizers**: Standard tokenizer, edge n-gram tokenizer
- **Filters**: Lowercase, stop words, snowball stemming
- **Mappings**: Optimized index mappings with multi-fields
- **Settings**: Shard/replica configuration, refresh intervals

## Installation

```bash
pip install elasticsearch==8.11.0
```

## Usage

### Initialize Client

```python
from src.elasticsearch.client import EsClientManager

client = EsClientManager({
    'hosts': ['[EXTERNAL_URL_REMOVED]],
    'timeout': 30,
    'username': 'elastic',
    'password': 'your-password'
})
```

### Bulk Indexing

```python
from src.indexing.bulk_indexer import BulkIndexer

indexer = BulkIndexer(client, {'batch_size': 1000})
results = indexer.index_documents('documents', documents)
print(f"Indexed: {results['indexed']}, Failed: {results['failed']}")
```

### Full-Text Search

```python
from src.search.full_text_search import FullTextSearch

fts = FullTextSearch(client, {'default_fields': ['title', 'description']})
results = fts.search('documents', 'search query', page=1, page_size=20)
print(f"Found {results['hits']} results")
```

### Faceted Search

```python
from src.search.faceted_search import FacetedSearch

facets = FacetedSearch(client, {'facet_fields': ['category', 'tags']})
results = facets.search('documents', 'query', filters={'category': 'tech'})
print(f"Facets: {results['facets']}")
```

### Autocomplete

```python
from src.search.autocomplete import Autocomplete

ac = Autocomplete(client, {
    'max_suggestions': 10,
    'source_fields': ['id', 'title'],
    'suggestion_fields': ['title', 'tags']
})
suggestions = ac.suggest('documents', 'sea')
print(f"Suggestions: {suggestions}")
```

### Search Analytics

```python
from src.analytics.search_analytics import SearchAnalytics

analytics = SearchAnalytics(client, {'analytics_index': 'search_analytics'})
analytics.log_search_query('documents', 'query', 100, 50)
trends = analytics.get_search_trends(hours=24)
print(f"Trends: {trends}")
```

## Configuration Files

- `config/index-mapping.yaml`: Index mappings and analyzers
- `config/search-config.yaml`: Search and analytics configuration
- `source_fields` (autocomplete): controls which fields are returned in autocomplete results.
- `suggestion_fields` (autocomplete): list of fields used for suggestion generation.
- `max_suggestions` (autocomplete): maximum number of suggestions to return.

## GL Framework Integration

- GL00-09: Governance policies
- GL30-49: Execution layer (core services)
- GL50-59: Observability layer (analytics)
- GL90-99: Meta layer (validation)

## Compliance

- GDPR compliant (query logging with anonymization)
- SOC2 compliant (audit trails and evidence generation)
