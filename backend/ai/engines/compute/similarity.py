"""Similarity Computation Engine.

Quantifies semantic association between data points using vector distance
metrics and graph path analysis. Supports cosine similarity, euclidean
distance, dot product, and graph-based proximity measures.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """Computes pairwise and batch similarity across multiple metrics.

    Supports:
    - Cosine similarity (angular distance)
    - Euclidean distance (L2 norm)
    - Dot product (unnormalized inner product)
    - Jaccard similarity (set overlap)
    """

    def compute(
        self,
        query_vector: list[float],
        candidate_vectors: list[list[float]],
        candidate_ids: list[str],
        metric: str = "cosine",
        top_k: int = 10,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        """Compute similarity between query and candidates.

        Args:
            query_vector: Query embedding.
            candidate_vectors: List of candidate embeddings.
            candidate_ids: Corresponding IDs for candidates.
            metric: Distance metric (cosine, euclidean, dot_product).
            top_k: Maximum results to return.
            threshold: Minimum similarity score filter.

        Returns:
            Dict with results list and computation metadata.
        """
        start = time.perf_counter()

        query = np.array(query_vector, dtype=np.float32)
        candidates = np.array(candidate_vectors, dtype=np.float32)

        if metric == "cosine":
            scores = self._cosine_similarity(query, candidates)
        elif metric == "euclidean":
            scores = self._euclidean_similarity(query, candidates)
        elif metric == "dot_product":
            scores = self._dot_product(query, candidates)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        indices = np.argsort(scores)[::-1]

        results = []
        for idx in indices:
            score = float(scores[idx])
            if threshold is not None and score < threshold:
                continue
            results.append({
                "id": candidate_ids[idx],
                "score": round(score, 6),
                "rank": len(results) + 1,
            })
            if len(results) >= top_k:
                break

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "results": results,
            "metadata": {
                "metric": metric,
                "total_candidates": len(candidate_vectors),
                "returned": len(results),
                "query_time_ms": round(elapsed_ms, 2),
            },
        }

    def pairwise_matrix(
        self,
        vectors: list[list[float]],
        metric: str = "cosine",
    ) -> np.ndarray:
        """Compute full pairwise similarity matrix.

        Args:
            vectors: List of vectors.
            metric: Distance metric.

        Returns:
            NxN similarity matrix as numpy array.
        """
        mat = np.array(vectors, dtype=np.float32)
        n = mat.shape[0]

        if metric == "cosine":
            norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-10
            normalized = mat / norms
            return normalized @ normalized.T
        elif metric == "euclidean":
            dists = np.sqrt(np.sum((mat[:, None] - mat[None, :]) ** 2, axis=2))
            return 1.0 / (1.0 + dists)
        elif metric == "dot_product":
            return mat @ mat.T
        else:
            raise ValueError(f"Unsupported metric: {metric}")

    @staticmethod
    def _cosine_similarity(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all candidates."""
        query_norm = np.linalg.norm(query) + 1e-10
        candidate_norms = np.linalg.norm(candidates, axis=1) + 1e-10
        return (candidates @ query) / (candidate_norms * query_norm)

    @staticmethod
    def _euclidean_similarity(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        """Convert euclidean distance to similarity score (inverse)."""
        distances = np.sqrt(np.sum((candidates - query) ** 2, axis=1))
        return 1.0 / (1.0 + distances)

    @staticmethod
    def _dot_product(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        """Compute raw dot product scores."""
        return candidates @ query