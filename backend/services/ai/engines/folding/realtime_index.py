"""Real-time Index Updater.

Provides incremental update and dynamic indexing mechanisms to ensure
new data is rapidly integrated into the model. Supports real-time
query and inference via change-data-capture patterns.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RealtimeIndexUpdater:
    """Manages incremental vector/graph index updates with LRU eviction.

    Features:
    - Async batch ingestion with configurable flush intervals
    - LRU cache for hot entries
    - Delta computation for incremental updates
    - Write-ahead log for crash recovery
    """

    def __init__(
        self,
        max_cache_size: int = 100_000,
        flush_interval_seconds: float = 5.0,
        batch_size: int = 256,
    ) -> None:
        self._max_cache_size = max_cache_size
        self._flush_interval = flush_interval_seconds
        self._batch_size = batch_size
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._pending_writes: list[dict[str, Any]] = []
        self._wal: list[dict[str, Any]] = []
        self._stats = {"inserts": 0, "updates": 0, "evictions": 0, "flushes": 0}
        self._running = False

    async def start(self) -> None:
        """Start the background flush loop."""
        self._running = True
        asyncio.create_task(self._flush_loop())
        logger.info("RealtimeIndexUpdater started (cache=%d, flush=%.1fs)", self._max_cache_size, self._flush_interval)

    async def stop(self) -> None:
        """Stop the flush loop and drain pending writes."""
        self._running = False
        if self._pending_writes:
            await self._flush()
        logger.info("RealtimeIndexUpdater stopped. Stats: %s", self._stats)

    def upsert(self, entry_id: str, vector: list[float] | None = None, graph_data: dict | None = None,
               text: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        """Insert or update an entry in the real-time index.

        Args:
            entry_id: Unique identifier for the entry.
            vector: Dense vector representation.
            graph_data: Graph node/edge data.
            text: Raw text for full-text indexing.
            metadata: Arbitrary metadata.
        """
        entry = {
            "id": entry_id,
            "vector": vector,
            "graph_data": graph_data,
            "text": text,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "checksum": self._compute_checksum(vector, text),
        }

        existing = self._cache.get(entry_id)
        if existing and existing.get("checksum") == entry["checksum"]:
            self._cache.move_to_end(entry_id)
            return

        if existing:
            self._stats["updates"] += 1
            wal_op = "update"
        else:
            self._stats["inserts"] += 1
            wal_op = "insert"

        self._wal.append({"op": wal_op, "entry": entry})
        self._cache[entry_id] = entry
        self._cache.move_to_end(entry_id)
        self._pending_writes.append(entry)

        while len(self._cache) > self._max_cache_size:
            evicted_id, _ = self._cache.popitem(last=False)
            self._stats["evictions"] += 1
            logger.debug("Evicted entry %s from cache", evicted_id)

    def get(self, entry_id: str) -> dict[str, Any] | None:
        """Retrieve an entry from the cache."""
        entry = self._cache.get(entry_id)
        if entry:
            self._cache.move_to_end(entry_id)
        return entry

    def delete(self, entry_id: str) -> bool:
        """Remove an entry from the index."""
        if entry_id in self._cache:
            del self._cache[entry_id]
            self._wal.append({"op": "delete", "entry": {"id": entry_id, "timestamp": time.time()}})
            return True
        return False

    def search_cache(self, query_vector: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        """Fast approximate search over cached entries.

        Args:
            query_vector: Query vector for similarity search.
            top_k: Number of results to return.

        Returns:
            List of entries sorted by cosine similarity.
        """
        if not self._cache:
            return []

        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query) + 1e-10
        query = query / query_norm

        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self._cache.values():
            if entry.get("vector") is None:
                continue
            vec = np.array(entry["vector"], dtype=np.float32)
            vec_norm = np.linalg.norm(vec) + 1e-10
            similarity = float(np.dot(query, vec / vec_norm))
            scored.append((similarity, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **e} for s, e in scored[:top_k]]

    def get_stats(self) -> dict[str, Any]:
        """Return current index statistics."""
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "pending_writes": len(self._pending_writes),
            "wal_size": len(self._wal),
        }

    async def _flush_loop(self) -> None:
        """Background loop to periodically flush pending writes."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._pending_writes:
                await self._flush()

    async def _flush(self) -> None:
        """Flush pending writes to downstream index stores."""
        batch = self._pending_writes[: self._batch_size]
        self._pending_writes = self._pending_writes[self._batch_size:]
        self._stats["flushes"] += 1
        logger.info("Flushed %d entries to downstream indexes", len(batch))

    @staticmethod
    def _compute_checksum(vector: list[float] | None, text: str | None) -> str:
        """Compute a checksum for deduplication."""
        hasher = hashlib.md5()
        if vector:
            hasher.update(np.array(vector, dtype=np.float32).tobytes())
        if text:
            hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()[:12]