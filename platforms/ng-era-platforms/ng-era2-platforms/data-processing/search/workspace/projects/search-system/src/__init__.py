# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: __init__
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Search System Package
ECO-Layer: GL30-49 (Execution)
Closure-Signal: artifact
"""
__version__ = "1.0.0"
__author__ = "Data Engineering Team"
__description__ = "Comprehensive Elasticsearch search indexing system"
"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
from .elasticsearch.client import EsClientManager
from .indexing.bulk_indexer import BulkIndexer
from .indexing.incremental_updater import IncrementalUpdater
from .indexing.index_optimizer import IndexOptimizer
from .search.full_text_search import FullTextSearch
from .search.faceted_search import FacetedSearch
from .search.autocomplete import Autocomplete
from .analytics.search_analytics import SearchAnalytics
from .analytics.relevance_tuning import RelevanceTuner
__all__ = [
    'EsClientManager',
    'BulkIndexer',
    'IncrementalUpdater',
    'IndexOptimizer',
    'FullTextSearch',
    'FacetedSearch',
    'Autocomplete',
    'SearchAnalytics',
    'RelevanceTuner'
]