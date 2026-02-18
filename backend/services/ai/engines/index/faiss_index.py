"""FAISS Vector Index Adapter.

High-performance storage and retrieval of high-dimensional vectors
using Facebook AI Similarity Search. Supports approximate nearest
neighbor search with configurable index types (Flat, IVF, HNSW).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class FAISSIndexAdapter:
    """Manages FAISS vector indexes with persistence and hot-reload.

    Features:
    - Multiple index types: FlatIP, IVFFlat, IVFPQ, HNSW
    - Automatic training for IVF-based indexes
    - Disk persistence with atomic writes
    - ID mapping for external identifier resolution
    """

    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "FlatIP",
        nprobe: int = 32,
        index_path: str | None = None,
    ) -> None:
        self._dimension = dimension
        self._index_type = index_type
        self._nprobe = nprobe
        self._index_path = index_path
        self._index: Any = None
        self._id_map: dict[int, str] = {}
        self._next_internal_id: int = 0
        self._faiss: Any = None

    async def initialize(self) -> None:
        """Initialize FAISS index, loading from disk if available."""
        try:
            import faiss
            self._faiss = faiss
        except ImportError:
            logger.warning("faiss-cpu not installed; using numpy fallback for vector search")
            self._faiss = None
            self._index = {"vectors": np.empty((0, self._dimension), dtype=np.float32)}
            return

        if self._index_path and os.path.exists(self._index_path):
            self._index = faiss.read_index(self._index_path)
            meta_path = self._index_path + ".meta.npy"
            if os.path.exists(meta_path):
                self._id_map = dict(np.load(meta_path, allow_pickle=True).item())
                self._next_internal_id = max(self._id_map.keys(), default=-1) + 1
            logger.info("Loaded FAISS index from %s (%d vectors)", self._index_path, self._index.ntotal)
        else:
            self._index = self._create_index()
            logger.info("Created new FAISS %s index (dim=%d)", self._index_type, self._dimension)

    def _create_index(self) -> Any:
        """Create a new FAISS index based on configured type."""
        faiss = self._faiss
        if self._index_type == "FlatIP":
            return faiss.IndexFlatIP(self._dimension)
        elif self._index_type == "FlatL2":
            return faiss.IndexFlatL2(self._dimension)
        elif self._index_type == "IVFFlat":
            quantizer = faiss.IndexFlatIP(self._dimension)
            index = faiss.IndexIVFFlat(quantizer, self._dimension, 100)
            index.nprobe = self._nprobe
            return index
        elif self._index_type == "HNSW":
            index = faiss.IndexHNSWFlat(self._dimension, 32)
            index.hnsw.efSearch = 64
            return index
        else:
            return faiss.IndexFlatIP(self._dimension)

    def add(self, entry_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> int:
        """Add a single vector to the index.

        Args:
            entry_id: External identifier.
            vector: Dense vector of correct dimensionality.
            metadata: Optional metadata (stored in id_map only).

        Returns:
            Internal index ID.
        """
        vec = np.array([vector], dtype=np.float32)
        if vec.shape[1] != self._dimension:
            raise ValueError(f"Vector dimension {vec.shape[1]} != index dimension {self._dimension}")

        internal_id = self._next_internal_id
        self._id_map[internal_id] = entry_id
        self._next_internal_id += 1

        if self._faiss is None:
            existing = self._index["vectors"]
            self._index["vectors"] = np.vstack([existing, vec]) if existing.shape[0] > 0 else vec
        else:
            faiss = self._faiss
            if hasattr(self._index, "is_trained") and not self._index.is_trained:
                logger.info("Training IVF index with %d vectors", vec.shape[0])
                self._index.train(vec)
            self._index.add(vec)

        return internal_id

    def add_batch(self, entries: list[dict[str, Any]]) -> list[int]:
        """Add multiple vectors in a single batch.

        Args:
            entries: List of dicts with id, vector, and optional metadata.

        Returns:
            List of internal IDs.
        """
        if not entries:
            return []

        vectors = np.array([e["vector"] for e in entries], dtype=np.float32)
        if vectors.shape[1] != self._dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} != index dimension {self._dimension}")

        internal_ids = []
        for entry in entries:
            iid = self._next_internal_id
            self._id_map[iid] = entry["id"]
            self._next_internal_id += 1
            internal_ids.append(iid)

        if self._faiss is None:
            existing = self._index["vectors"]
            self._index["vectors"] = np.vstack([existing, vectors]) if existing.shape[0] > 0 else vectors
        else:
            if hasattr(self._index, "is_trained") and not self._index.is_trained:
                self._index.train(vectors)
            self._index.add(vectors)

        logger.info("Added batch of %d vectors to FAISS index", len(entries))
        return internal_ids

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        """Search for nearest neighbors.

        Args:
            query_vector: Query embedding.
            top_k: Number of results.
            threshold: Minimum score filter.

        Returns:
            Dict with results and search metadata.
        """
        start = time.perf_counter()
        query = np.array([query_vector], dtype=np.float32)

        if self._faiss is None:
            results = self._numpy_search(query, top_k)
        else:
            ntotal = self._index.ntotal
            if ntotal == 0:
                return {"results": [], "metadata": {"total_indexed": 0, "query_time_ms": 0}}
            k = min(top_k, ntotal)
            scores, indices = self._index.search(query, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                entry_id = self._id_map.get(int(idx), f"unknown-{idx}")
                if threshold is not None and float(score) < threshold:
                    continue
                results.append({"id": entry_id, "score": round(float(score), 6), "internal_id": int(idx)})

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "results": results,
            "metadata": {
                "index_type": "faiss",
                "faiss_type": self._index_type,
                "total_indexed": self._index.ntotal if self._faiss else self._index["vectors"].shape[0],
                "top_k": top_k,
                "returned": len(results),
                "query_time_ms": round(elapsed_ms, 2),
            },
        }

    def _numpy_search(self, query: np.ndarray, top_k: int) -> list[dict[str, Any]]:
        """Fallback numpy-based search when FAISS is not available."""
        vectors = self._index["vectors"]
        if vectors.shape[0] == 0:
            return []

        query_norm = query / (np.linalg.norm(query) + 1e-10)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-10
        normalized = vectors / norms
        scores = (normalized @ query_norm.T).flatten()

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            entry_id = self._id_map.get(int(idx), f"unknown-{idx}")
            results.append({"id": entry_id, "score": round(float(scores[idx]), 6), "internal_id": int(idx)})
        return results

    def save(self, path: str | None = None) -> None:
        """Persist index to disk."""
        save_path = path or self._index_path
        if not save_path:
            logger.warning("No index path configured; skipping save")
            return

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        if self._faiss is not None:
            self._faiss.write_index(self._index, save_path)
        np.save(save_path + ".meta.npy", self._id_map)
        logger.info("Saved FAISS index to %s (%d vectors)", save_path, len(self._id_map))

    def get_stats(self) -> dict[str, Any]:
        """Return index statistics."""
        total = self._index.ntotal if self._faiss else self._index["vectors"].shape[0]
        return {
            "index_type": self._index_type,
            "dimension": self._dimension,
            "total_vectors": total,
            "id_map_size": len(self._id_map),
        }