"""Hybrid Index Router.

Fuses multiple index types to dynamically select the optimal retrieval
path based on query characteristics. Balances speed and accuracy by
routing vector queries to FAISS, text queries to Elasticsearch, and
relational queries to Neo4j.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .faiss_index import FAISSIndexAdapter
from .neo4j_index import Neo4jIndexAdapter
from .elasticsearch_index import ElasticsearchIndexAdapter

logger = logging.getLogger(__name__)


class HybridIndexRouter:
    """Routes queries to optimal index backends and fuses results.

    Routing logic:
    - Vector-only queries → FAISS (lowest latency)
    - Text-only queries → Elasticsearch (BM25 + fuzzy)
    - Graph/relational queries → Neo4j (pattern matching)
    - Hybrid queries → parallel fan-out + Reciprocal Rank Fusion
    """

    def __init__(
        self,
        faiss: FAISSIndexAdapter,
        neo4j: Neo4jIndexAdapter,
        elasticsearch: ElasticsearchIndexAdapter,
        rrf_k: int = 60,
    ) -> None:
        self._faiss = faiss
        self._neo4j = neo4j
        self._es = elasticsearch
        self._rrf_k = rrf_k

    async def search(
        self,
        query_text: str | None = None,
        query_vector: list[float] | None = None,
        graph_query: str | None = None,
        top_k: int = 10,
        index_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a hybrid search across multiple index backends.

        Args:
            query_text: Full-text search query.
            query_vector: Dense vector for similarity search.
            graph_query: Graph traversal or pattern query.
            top_k: Maximum results per backend.
            index_types: Explicit list of backends to query (faiss, neo4j, elasticsearch).
            filters: Additional filters (content_type, language, etc.).

        Returns:
            Fused results with per-backend metadata.
        """
        start = time.perf_counter()
        filters = filters or {}

        backends = index_types or self._auto_route(query_text, query_vector, graph_query)
        tasks: dict[str, asyncio.Task[dict[str, Any]]] = {}

        if "faiss" in backends and query_vector:
            tasks["faiss"] = asyncio.create_task(self._search_faiss(query_vector, top_k))

        if "elasticsearch" in backends and (query_text or query_vector):
            tasks["elasticsearch"] = asyncio.create_task(
                self._search_elasticsearch(query_text, query_vector, top_k, filters)
            )

        if "neo4j" in backends and (graph_query or query_text):
            search_term = graph_query or query_text or ""
            tasks["neo4j"] = asyncio.create_task(
                self._search_neo4j(search_term, top_k, filters.get("node_type"))
            )

        backend_results: dict[str, dict[str, Any]] = {}
        if tasks:
            done = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for backend_name, result in zip(tasks.keys(), done):
                if isinstance(result, Exception):
                    logger.error("Backend %s failed: %s", backend_name, result)
                    backend_results[backend_name] = {"results": [], "metadata": {"error": str(result)}}
                else:
                    backend_results[backend_name] = result

        if len(backend_results) > 1:
            fused = self._reciprocal_rank_fusion(backend_results, top_k)
        elif len(backend_results) == 1:
            single = next(iter(backend_results.values()))
            fused = single.get("results", [])[:top_k]
        else:
            fused = []

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "results": fused,
            "metadata": {
                "index_type": "hybrid",
                "backends_queried": list(backend_results.keys()),
                "total_returned": len(fused),
                "query_time_ms": round(elapsed_ms, 2),
                "backend_metadata": {k: v.get("metadata", {}) for k, v in backend_results.items()},
            },
        }

    async def ingest(
        self,
        entry_id: str,
        content: str,
        vector: list[float] | None = None,
        graph_data: dict[str, Any] | None = None,
        content_type: str = "source_code",
        language: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        """Ingest data into all applicable index backends.

        Args:
            entry_id: Unique identifier.
            content: Raw text content.
            vector: Dense vector embedding.
            graph_data: Graph structure (nodes/edges).
            content_type: Content classification.
            language: Programming language.
            metadata: Arbitrary metadata.

        Returns:
            Dict mapping backend name to success status.
        """
        results: dict[str, bool] = {}

        if vector:
            try:
                self._faiss.add(entry_id, vector, metadata)
                results["faiss"] = True
            except Exception as e:
                logger.error("FAISS ingest failed for %s: %s", entry_id, e)
                results["faiss"] = False

        try:
            success = await self._es.index_document(
                entry_id=entry_id,
                content=content,
                content_type=content_type,
                language=language,
                vector=vector,
                metadata=metadata,
            )
            results["elasticsearch"] = success
        except Exception as e:
            logger.error("Elasticsearch ingest failed for %s: %s", entry_id, e)
            results["elasticsearch"] = False

        if graph_data:
            try:
                counts = await self._neo4j.ingest_graph(graph_data)
                results["neo4j"] = counts.get("nodes", 0) > 0
            except Exception as e:
                logger.error("Neo4j ingest failed for %s: %s", entry_id, e)
                results["neo4j"] = False

        return results

    async def get_stats(self) -> dict[str, Any]:
        """Aggregate statistics from all backends."""
        faiss_stats = self._faiss.get_stats()
        neo4j_stats = await self._neo4j.get_stats()
        es_stats = await self._es.get_stats()

        return {
            "faiss": faiss_stats,
            "neo4j": neo4j_stats,
            "elasticsearch": es_stats,
        }

    @staticmethod
    def _auto_route(
        query_text: str | None,
        query_vector: list[float] | None,
        graph_query: str | None,
    ) -> list[str]:
        """Automatically determine which backends to query."""
        backends = []
        if query_vector:
            backends.append("faiss")
        if query_text:
            backends.append("elasticsearch")
        if graph_query:
            backends.append("neo4j")
        if not backends:
            backends = ["elasticsearch"]
        return backends

    async def _search_faiss(self, query_vector: list[float], top_k: int) -> dict[str, Any]:
        """Execute FAISS vector search."""
        return self._faiss.search(query_vector, top_k)

    async def _search_elasticsearch(
        self, query_text: str | None, query_vector: list[float] | None, top_k: int, filters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute Elasticsearch search."""
        return await self._es.search(
            query_text=query_text,
            query_vector=query_vector,
            top_k=top_k,
            content_type=filters.get("content_type"),
            language=filters.get("language"),
        )

    async def _search_neo4j(self, query: str, top_k: int, node_type: str | None) -> dict[str, Any]:
        """Execute Neo4j graph search."""
        return await self._neo4j.search(query=query, top_k=top_k, node_type=node_type)

    def _reciprocal_rank_fusion(
        self, backend_results: dict[str, dict[str, Any]], top_k: int,
    ) -> list[dict[str, Any]]:
        """Fuse results from multiple backends using RRF.

        RRF score = Σ 1/(k + rank_i) across all ranking lists.
        """
        rrf_scores: dict[str, float] = {}
        entry_data: dict[str, dict[str, Any]] = {}

        for backend_name, result in backend_results.items():
            ranked = result.get("results", [])
            for rank, item in enumerate(ranked, 1):
                doc_id = item.get("id", "")
                if not doc_id:
                    continue
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (self._rrf_k + rank)
                if doc_id not in entry_data:
                    entry_data[doc_id] = {**item, "sources": [backend_name]}
                else:
                    entry_data[doc_id]["sources"].append(backend_name)

        fused = []
        for doc_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            entry = entry_data[doc_id]
            entry["score"] = round(score, 6)
            entry["id"] = doc_id
            fused.append(entry)

        return fused