"""Search layer for the Governance Operations Platform.

Provides in-memory indexing, full-text search, faceted querying, and
analytical capabilities across all governed modules.  The three main
subsystems are:

* **Indexer** -- builds and maintains the primary and secondary indexes
  that back all search operations.  Supports secondary indexes by
  ``gl_layer``, ``ng_era``, and ``compliance_status`` as well as simple
  tokenised full-text search on module name and path.
* **Searcher** -- executes queries against the index with filtering,
  pagination, faceted counts, and full-text matching.
* **Analyzers** -- run analytical passes over the index to surface
  compliance trends, hash drift patterns, and scan coverage gaps.

Usage::

    from search import ModuleIndex, ModuleSearcher, ComplianceAnalyzer

    index = ModuleIndex()
    index.build_index(modules)

    searcher = ModuleSearcher(index)
    results = searcher.search(SearchQuery(text="auth"))

    analyzer = ComplianceAnalyzer()
    report = analyzer.analyze(index)

@GL-governed
@GL-layer: GL30-49
@GL-semantic: search-layer
"""
from __future__ import annotations

from search.indexer import (
    IndexEntry,
    IndexStats,
    IndexStatus,
    ModuleIndex,
    SecondaryIndex,
    TokenIndex,
)
from search.searcher import (
    FacetCounts,
    ModuleSearcher,
    SearchFilters,
    SearchQuery,
    SearchResult,
    SortField,
    SortOrder,
)
from search.analyzers import (
    AnalysisFinding,
    AnalysisReport,
    AnalysisSeverity,
    BaseAnalyzer,
    ComplianceAnalyzer,
    CoverageAnalyzer,
    DriftAnalyzer,
)

__version__ = "1.0.0"

__all__: list[str] = [
    # Indexer
    "IndexEntry",
    "IndexStats",
    "IndexStatus",
    "ModuleIndex",
    "SecondaryIndex",
    "TokenIndex",
    # Searcher
    "FacetCounts",
    "ModuleSearcher",
    "SearchFilters",
    "SearchQuery",
    "SearchResult",
    "SortField",
    "SortOrder",
    # Analyzers
    "AnalysisFinding",
    "AnalysisReport",
    "AnalysisSeverity",
    "BaseAnalyzer",
    "ComplianceAnalyzer",
    "CoverageAnalyzer",
    "DriftAnalyzer",
]
