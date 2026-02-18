"""Ranking Algorithm Engine.

Sorts results by relevance using BM25 text scoring, vector reranking,
and hybrid fusion strategies. Optimizes precision for search and
recommendation systems.
"""
from __future__ import annotations

import logging
import math
import time
from collections import Counter
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RankingEngine:
    """Multi-strategy ranking with score fusion.

    Strategies:
    - BM25: Probabilistic text relevance scoring
    - Vector: Cosine similarity reranking
    - Hybrid: Reciprocal Rank Fusion (RRF) of BM25 + vector
    """

    def __init__(self, bm25_k1: float = 1.5, bm25_b: float = 0.75, rrf_k: int = 60) -> None:
        self._k1 = bm25_k1
        self._b = bm25_b
        self._rrf_k = rrf_k

    def rank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        strategy: str = "hybrid",
        query_vector: list[float] | None = None,
        top_k: int = 20,
    ) -> dict[str, Any]:
        """Rank candidates by relevance to query.

        Args:
            query: Text query string.
            candidates: List of dicts with id, text, and optional vector.
            strategy: One of bm25, vector, hybrid.
            query_vector: Pre-computed query embedding for vector ranking.
            top_k: Maximum results to return.

        Returns:
            Dict with ranked results and scoring metadata.
        """
        start = time.perf_counter()

        if strategy == "bm25":
            scored = self._bm25_rank(query, candidates)
        elif strategy == "vector":
            if query_vector is None:
                raise ValueError("query_vector required for vector ranking strategy")
            scored = self._vector_rank(query_vector, candidates)
        elif strategy == "hybrid":
            bm25_scored = self._bm25_rank(query, candidates)
            if query_vector is not None:
                vector_scored = self._vector_rank(query_vector, candidates)
                scored = self._reciprocal_rank_fusion(bm25_scored, vector_scored)
            else:
                scored = bm25_scored
        else:
            raise ValueError(f"Unsupported ranking strategy: {strategy}")

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:top_k]
        for i, r in enumerate(results):
            r["rank"] = i + 1

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "results": results,
            "metadata": {
                "strategy": strategy,
                "total_candidates": len(candidates),
                "returned": len(results),
                "query_time_ms": round(elapsed_ms, 2),
            },
        }

    def _bm25_rank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score candidates using BM25 algorithm."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return [{"id": c["id"], "score": 0.0} for c in candidates]

        doc_texts = [c.get("text", "") for c in candidates]
        doc_tokens = [self._tokenize(t) for t in doc_texts]
        doc_lengths = [len(t) for t in doc_tokens]
        avg_dl = sum(doc_lengths) / max(len(doc_lengths), 1)

        n_docs = len(candidates)
        df: Counter[str] = Counter()
        for tokens in doc_tokens:
            seen = set(tokens)
            for term in seen:
                df[term] += 1

        results = []
        for idx, candidate in enumerate(candidates):
            score = 0.0
            tf_counter = Counter(doc_tokens[idx])
            dl = doc_lengths[idx]

            for term in query_terms:
                if term not in tf_counter:
                    continue
                tf = tf_counter[term]
                doc_freq = df.get(term, 0)
                idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                tf_norm = (tf * (self._k1 + 1)) / (tf + self._k1 * (1 - self._b + self._b * dl / max(avg_dl, 1)))
                score += idf * tf_norm

            results.append({"id": candidate["id"], "score": round(score, 6)})

        return results

    @staticmethod
    def _vector_rank(query_vector: list[float], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score candidates using cosine similarity with query vector."""
        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query) + 1e-10
        query_normalized = query / query_norm

        results = []
        for candidate in candidates:
            vec = candidate.get("vector")
            if vec is None:
                results.append({"id": candidate["id"], "score": 0.0})
                continue
            cvec = np.array(vec, dtype=np.float32)
            cvec_norm = np.linalg.norm(cvec) + 1e-10
            similarity = float(np.dot(query_normalized, cvec / cvec_norm))
            results.append({"id": candidate["id"], "score": round(similarity, 6)})

        return results

    def _reciprocal_rank_fusion(
        self,
        ranking_a: list[dict[str, Any]],
        ranking_b: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Fuse two rankings using Reciprocal Rank Fusion (RRF).

        RRF score = Σ 1/(k + rank_i) for each ranking list.
        """
        sorted_a = sorted(ranking_a, key=lambda x: x["score"], reverse=True)
        sorted_b = sorted(ranking_b, key=lambda x: x["score"], reverse=True)

        rrf_scores: dict[str, float] = {}

        for rank, item in enumerate(sorted_a, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (self._rrf_k + rank)

        for rank, item in enumerate(sorted_b, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (self._rrf_k + rank)

        return [{"id": doc_id, "score": round(score, 6)} for doc_id, score in rrf_scores.items()]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowercase tokenizer with stopword removal."""
        stopwords = frozenset({
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "above", "below", "between", "and", "but", "or",
            "not", "no", "nor", "so", "yet", "both", "either", "neither", "each",
            "every", "all", "any", "few", "more", "most", "other", "some", "such",
            "than", "too", "very", "just", "about", "it", "its", "this", "that",
        })
        tokens = []
        for word in text.lower().split():
            cleaned = "".join(c for c in word if c.isalnum())
            if cleaned and cleaned not in stopwords and len(cleaned) > 1:
                tokens.append(cleaned)
        return tokens