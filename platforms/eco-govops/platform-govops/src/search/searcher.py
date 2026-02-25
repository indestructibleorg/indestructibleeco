"""Search engine for the governance module index.

Provides the ``ModuleSearcher`` class that queries the in-memory index built by
:class:`~search.indexer.ModuleIndexer`.  Supports free-text matching, multi-
dimensional filtering, sorting, pagination, and faceted result aggregation.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: search-query
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from search.indexer import IndexEntry, ModuleIndexer

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SortField(StrEnum):
    """Fields available for sorting search results."""

    NAME = "name"
    PATH = "path"
    GL_LAYER = "gl_layer"
    COMPLIANCE_STATUS = "compliance_status"
    LAST_UPDATED = "last_updated"


class SortOrder(StrEnum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


# ---------------------------------------------------------------------------
# Query / result models
# ---------------------------------------------------------------------------

class SearchFilters(BaseModel):
    """Optional filters applied to narrow search results.

    Every field that is ``None`` is ignored during filtering.  When multiple
    fields are set, they are combined with logical AND.
    """

    gl_layer: str | None = None
    ng_era: str | None = None
    compliance_status: str | None = None
    severity: str | None = None
    tags: list[str] | None = None


class SearchQuery(BaseModel):
    """Describes a search request against the governance module index.

    Attributes:
        text: Free-text substring matched case-insensitively against
            ``name``, ``path``, and ``tags``.
        filters: Structured dimension filters (AND-combined).
        sort_by: Field to sort results on.
        sort_order: Ascending or descending.
        limit: Maximum entries to return (page size).
        offset: Number of entries to skip (for pagination).
    """

    text: str = ""
    filters: SearchFilters = Field(default_factory=SearchFilters)
    sort_by: SortField = SortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class FacetCounts(BaseModel):
    """Aggregated counts used for faceted navigation in search UIs."""

    by_gl_layer: dict[str, int] = Field(default_factory=dict)
    by_compliance_status: dict[str, int] = Field(default_factory=dict)
    by_ng_era: dict[str, int] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Container returned by every search operation.

    Attributes:
        entries: The page of matching ``IndexEntry`` instances.
        total_count: Total matches *before* pagination.
        query_time_ms: Wall-clock time spent executing the query.
        facets: Aggregated counts across the **full** (un-paginated) result
            set, suitable for building faceted navigation.
    """

    entries: list[IndexEntry] = Field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0
    facets: FacetCounts = Field(default_factory=FacetCounts)


# ---------------------------------------------------------------------------
# Searcher
# ---------------------------------------------------------------------------

class ModuleSearcher:
    """Queries the governance module search index.

    The searcher is a stateless read-only facade that operates against a
    :class:`ModuleIndexer` reference.  All public methods are ``async`` so
    they can be composed within async request handlers without blocking.
    """

    def __init__(self, indexer: ModuleIndexer) -> None:
        self._indexer = indexer
        logger.info("module_searcher_initialised")

    # -- primary search -----------------------------------------------------

    async def search(self, query: SearchQuery) -> SearchResult:
        """Execute a search query and return paginated, faceted results.

        Args:
            query: The search parameters.

        Returns:
            A ``SearchResult`` containing the matching page, total count,
            timing information, and facet aggregations.
        """
        start = time.monotonic()

        all_entries = self._indexer.get_all_entries()
        matched = self._apply_text_filter(all_entries, query.text)
        matched = self._apply_structured_filters(matched, query.filters)

        facets = self._compute_facets(matched)

        matched = self._sort_entries(matched, query.sort_by, query.sort_order)
        total_count = len(matched)
        page = matched[query.offset : query.offset + query.limit]

        elapsed_ms = (time.monotonic() - start) * 1000.0

        logger.info(
            "search_executed",
            text=query.text or "<none>",
            total=total_count,
            returned=len(page),
            query_time_ms=round(elapsed_ms, 2),
        )

        return SearchResult(
            entries=page,
            total_count=total_count,
            query_time_ms=round(elapsed_ms, 2),
            facets=facets,
        )

    # -- convenience look-ups -----------------------------------------------

    async def find_by_id(self, module_id: str) -> IndexEntry | None:
        """Look up a single module by its unique identifier.

        Returns:
            The matching ``IndexEntry``, or ``None`` if not found.
        """
        entry = self._indexer.get_entry(module_id)
        if entry is None:
            logger.debug("find_by_id_miss", module_id=module_id)
        return entry

    async def find_by_path(self, path: str) -> list[IndexEntry]:
        """Return all entries whose ``path`` contains the given substring.

        The match is case-insensitive.
        """
        needle = path.lower()
        results = [
            e for e in self._indexer.get_all_entries()
            if needle in e.path.lower()
        ]
        logger.debug("find_by_path", path=path, matches=len(results))
        return results

    async def find_non_compliant(self) -> list[IndexEntry]:
        """Return every entry whose compliance status is ``non_compliant``.

        This is a convenience shortcut used by dashboards and alerting.
        """
        results = [
            e for e in self._indexer.get_all_entries()
            if e.compliance_status == "non_compliant"
        ]
        logger.info("find_non_compliant", count=len(results))
        return results

    async def find_by_gl_layer(self, gl_layer: str) -> list[IndexEntry]:
        """Return all entries assigned to the specified governance layer.

        The match is exact and case-sensitive (GL layer codes are canonical).
        """
        results = [
            e for e in self._indexer.get_all_entries()
            if e.gl_layer == gl_layer
        ]
        logger.debug("find_by_gl_layer", gl_layer=gl_layer, matches=len(results))
        return results

    # -- private helpers ----------------------------------------------------

    @staticmethod
    def _apply_text_filter(
        entries: list[IndexEntry],
        text: str,
    ) -> list[IndexEntry]:
        """Case-insensitive substring match on name, path, and tags."""
        if not text:
            return entries

        needle = text.lower()
        return [
            e for e in entries
            if (
                needle in e.name.lower()
                or needle in e.path.lower()
                or any(needle in tag.lower() for tag in e.tags)
            )
        ]

    @staticmethod
    def _apply_structured_filters(
        entries: list[IndexEntry],
        filters: SearchFilters,
    ) -> list[IndexEntry]:
        """Apply the structured dimension filters (AND semantics)."""
        result = entries

        if filters.gl_layer is not None:
            result = [e for e in result if e.gl_layer == filters.gl_layer]

        if filters.ng_era is not None:
            result = [e for e in result if e.ng_era == filters.ng_era]

        if filters.compliance_status is not None:
            result = [
                e for e in result
                if e.compliance_status == filters.compliance_status
            ]

        if filters.tags:
            tag_set = {t.lower() for t in filters.tags}
            result = [
                e for e in result
                if tag_set.intersection(t.lower() for t in e.tags)
            ]

        return result

    @staticmethod
    def _sort_entries(
        entries: list[IndexEntry],
        sort_by: SortField,
        sort_order: SortOrder,
    ) -> list[IndexEntry]:
        """Sort *entries* by the requested field and direction."""
        reverse = sort_order == SortOrder.DESC
        key_fn = {
            SortField.NAME: lambda e: e.name.lower(),
            SortField.PATH: lambda e: e.path.lower(),
            SortField.GL_LAYER: lambda e: e.gl_layer,
            SortField.COMPLIANCE_STATUS: lambda e: e.compliance_status,
            SortField.LAST_UPDATED: lambda e: e.last_updated,
        }[sort_by]
        return sorted(entries, key=key_fn, reverse=reverse)

    @staticmethod
    def _compute_facets(entries: list[IndexEntry]) -> FacetCounts:
        """Build facet counts from the full (un-paginated) result set."""
        by_layer: dict[str, int] = {}
        by_compliance: dict[str, int] = {}
        by_era: dict[str, int] = {}

        for entry in entries:
            by_layer[entry.gl_layer] = by_layer.get(entry.gl_layer, 0) + 1
            by_compliance[entry.compliance_status] = (
                by_compliance.get(entry.compliance_status, 0) + 1
            )
            by_era[entry.ng_era] = by_era.get(entry.ng_era, 0) + 1

        return FacetCounts(
            by_gl_layer=by_layer,
            by_compliance_status=by_compliance,
            by_ng_era=by_era,
        )
