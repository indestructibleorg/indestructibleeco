"""Governance module indexer — builds and maintains an in-memory search index.

Provides the ``ModuleIndexer`` class that manages a thread-safe, in-memory
index of governance modules.  Each module is represented by an ``IndexEntry``
Pydantic model capturing its identity, governance layer, compliance posture,
and associated tags.  The indexer supports incremental updates (single-module
add / remove) as well as full rebuilds.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: search-indexing
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class IndexStatus(StrEnum):
    """Lifecycle state of the search index."""

    EMPTY = "empty"
    BUILDING = "building"
    READY = "ready"
    REBUILDING = "rebuilding"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class IndexEntry(BaseModel):
    """A single record stored in the governance module search index.

    Attributes:
        module_id: Globally-unique module identifier.
        name: Human-readable module name.
        path: Filesystem or repository path.
        gl_layer: Governance Layer designation (e.g. ``"GL30-49"``).
        ng_era: Naming-generation era tag (e.g. ``"Era-2"``).
        compliance_status: Current compliance posture string.
        tags: Free-form tags for categorisation and search.
        last_updated: Timestamp of the most recent index write (UTC).
    """

    module_id: str
    name: str
    path: str
    gl_layer: str
    ng_era: str
    compliance_status: str = "unknown"
    tags: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}


class IndexStats(BaseModel):
    """Aggregate statistics about the current index contents."""

    total_entries: int = 0
    status: IndexStatus = IndexStatus.EMPTY
    entries_by_gl_layer: dict[str, int] = Field(default_factory=dict)
    entries_by_compliance: dict[str, int] = Field(default_factory=dict)
    last_rebuild_at: datetime | None = None
    last_update_at: datetime | None = None


# ---------------------------------------------------------------------------
# Indexer
# ---------------------------------------------------------------------------

class ModuleIndexer:
    """Builds and maintains a thread-safe, in-memory search index of
    governance modules.

    The index is a simple ``dict[str, IndexEntry]`` keyed by ``module_id``.
    All mutating operations are serialised through an :class:`asyncio.Lock`
    so the indexer is safe for concurrent use within a single event loop.
    """

    def __init__(self) -> None:
        self._entries: dict[str, IndexEntry] = {}
        self._lock = asyncio.Lock()
        self._status: IndexStatus = IndexStatus.EMPTY
        self._last_rebuild_at: datetime | None = None
        self._last_update_at: datetime | None = None
        logger.info("module_indexer_initialised")

    # -- public read API ----------------------------------------------------

    @property
    def entry_count(self) -> int:
        """Return the number of entries currently in the index."""
        return len(self._entries)

    @property
    def status(self) -> IndexStatus:
        """Return the current lifecycle status of the index."""
        return self._status

    def get_all_entries(self) -> list[IndexEntry]:
        """Return a snapshot of every entry in the index."""
        return list(self._entries.values())

    def get_entry(self, module_id: str) -> IndexEntry | None:
        """Look up a single entry by *module_id*."""
        return self._entries.get(module_id)

    async def get_stats(self) -> IndexStats:
        """Compute and return aggregate statistics about the index.

        Returns:
            An ``IndexStats`` instance summarising the current state.
        """
        async with self._lock:
            by_layer: dict[str, int] = {}
            by_compliance: dict[str, int] = {}

            for entry in self._entries.values():
                by_layer[entry.gl_layer] = by_layer.get(entry.gl_layer, 0) + 1
                by_compliance[entry.compliance_status] = (
                    by_compliance.get(entry.compliance_status, 0) + 1
                )

            stats = IndexStats(
                total_entries=len(self._entries),
                status=self._status,
                entries_by_gl_layer=by_layer,
                entries_by_compliance=by_compliance,
                last_rebuild_at=self._last_rebuild_at,
                last_update_at=self._last_update_at,
            )

        logger.debug("index_stats_computed", total=stats.total_entries)
        return stats

    # -- public write API ---------------------------------------------------

    async def index_module(
        self,
        module_id: str,
        name: str,
        path: str,
        gl_layer: str,
        ng_era: str,
        compliance_status: str = "unknown",
        tags: list[str] | None = None,
    ) -> IndexEntry:
        """Add or update a single module in the index.

        If an entry with the same *module_id* already exists it is replaced.

        Returns:
            The newly created ``IndexEntry``.
        """
        entry = IndexEntry(
            module_id=module_id,
            name=name,
            path=path,
            gl_layer=gl_layer,
            ng_era=ng_era,
            compliance_status=compliance_status,
            tags=tags or [],
            last_updated=datetime.now(timezone.utc),
        )

        async with self._lock:
            is_update = module_id in self._entries
            self._entries[module_id] = entry
            self._last_update_at = entry.last_updated
            if self._status == IndexStatus.EMPTY:
                self._status = IndexStatus.READY

        action = "updated" if is_update else "indexed"
        logger.info(
            f"module_{action}",
            module_id=module_id,
            name=name,
            gl_layer=gl_layer,
            compliance_status=compliance_status,
        )
        return entry

    async def remove_module(self, module_id: str) -> bool:
        """Remove a module from the index by its *module_id*.

        Returns:
            ``True`` if the module was present and removed, ``False`` otherwise.
        """
        async with self._lock:
            if module_id not in self._entries:
                logger.warning("remove_module_not_found", module_id=module_id)
                return False
            del self._entries[module_id]
            self._last_update_at = datetime.now(timezone.utc)
            if not self._entries:
                self._status = IndexStatus.EMPTY

        logger.info("module_removed", module_id=module_id)
        return True

    async def rebuild_index(self, modules: list[dict[str, Any]]) -> int:
        """Drop the entire index and rebuild it from *modules*.

        Each dict in *modules* must contain at minimum the keys accepted by
        :meth:`index_module`.

        Args:
            modules: Sequence of module data dicts to populate the index.

        Returns:
            The number of entries indexed after the rebuild.
        """
        async with self._lock:
            self._status = IndexStatus.REBUILDING
            self._entries.clear()

        logger.info("index_rebuild_started", module_count=len(modules))
        indexed = 0

        for mod in modules:
            try:
                await self.index_module(
                    module_id=mod["module_id"],
                    name=mod["name"],
                    path=mod["path"],
                    gl_layer=mod["gl_layer"],
                    ng_era=mod["ng_era"],
                    compliance_status=mod.get("compliance_status", "unknown"),
                    tags=mod.get("tags", []),
                )
                indexed += 1
            except (KeyError, ValueError) as exc:
                logger.error(
                    "index_rebuild_entry_failed",
                    module=mod.get("module_id", "<unknown>"),
                    error=str(exc),
                )

        async with self._lock:
            self._status = IndexStatus.READY if indexed > 0 else IndexStatus.EMPTY
            self._last_rebuild_at = datetime.now(timezone.utc)

        logger.info("index_rebuild_complete", indexed=indexed, total=len(modules))
        return indexed
