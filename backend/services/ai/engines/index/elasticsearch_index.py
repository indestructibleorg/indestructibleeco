"""Elasticsearch Text Index Adapter.

Full-text retrieval on raw content with BM25 scoring, combined with
folding results to improve recall. Supports fuzzy matching, aggregations,
and custom analyzers for code-aware tokenization.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ElasticsearchIndexAdapter:
    """Manages Elasticsearch indexes for full-text and hybrid search.

    Features:
    - Async client with connection pooling
    - Custom analyzers for source code tokenization
    - Dense vector field support (kNN search)
    - Bulk ingestion with automatic batching
    """

    INDEX_SETTINGS = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "code_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "word_delimiter_graph", "flatten_graph"],
                    }
                }
            },
        },
        "mappings": {
            "properties": {
                "entry_id": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "code_analyzer"},
                "content_type": {"type": "keyword"},
                "language": {"type": "keyword"},
                "metadata": {"type": "object", "enabled": False},
                "vector": {"type": "dense_vector", "dims": 384, "index": True, "similarity": "cosine"},
                "timestamp": {"type": "date", "format": "epoch_millis"},
            }
        },
    }

    def __init__(
        self,
        url: str = "http://localhost:9200",
        index_name: str = "eco_code_index",
        vector_dims: int = 384,
    ) -> None:
        self._url = url
        self._index_name = index_name
        self._vector_dims = vector_dims
        self._client: Any = None

    async def initialize(self) -> None:
        """Initialize Elasticsearch async client and ensure index exists."""
        try:
            from elasticsearch import AsyncElasticsearch
            self._client = AsyncElasticsearch(self._url)
            info = await self._client.info()
            logger.info("Elasticsearch connected: %s (version=%s)", self._url, info["version"]["number"])

            exists = await self._client.indices.exists(index=self._index_name)
            if not exists:
                settings = self.INDEX_SETTINGS.copy()
                settings["mappings"]["properties"]["vector"]["dims"] = self._vector_dims
                await self._client.indices.create(index=self._index_name, body=settings)
                logger.info("Created index: %s", self._index_name)
        except ImportError:
            logger.warning("elasticsearch[async] not installed; text index operating in mock mode")
            self._client = None
        except Exception as e:
            logger.warning("Elasticsearch connection failed: %s; operating in mock mode", e)
            self._client = None

    async def close(self) -> None:
        """Close the Elasticsearch client."""
        if self._client:
            await self._client.close()
            logger.info("Elasticsearch client closed")

    async def index_document(
        self,
        entry_id: str,
        content: str,
        content_type: str = "source_code",
        language: str | None = None,
        vector: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Index a single document.

        Args:
            entry_id: Unique document identifier.
            content: Full text content.
            content_type: Content classification.
            language: Programming language.
            vector: Optional dense vector for kNN search.
            metadata: Arbitrary metadata.

        Returns:
            True if indexing succeeded.
        """
        if not self._client:
            return False

        doc: dict[str, Any] = {
            "entry_id": entry_id,
            "content": content,
            "content_type": content_type,
            "metadata": metadata or {},
            "timestamp": int(time.time() * 1000),
        }
        if language:
            doc["language"] = language
        if vector:
            doc["vector"] = vector

        result = await self._client.index(index=self._index_name, id=entry_id, document=doc)
        return result.get("result") in ("created", "updated")

    async def bulk_index(self, documents: list[dict[str, Any]]) -> dict[str, int]:
        """Bulk index multiple documents.

        Args:
            documents: List of dicts with entry_id, content, and optional fields.

        Returns:
            Dict with success and error counts.
        """
        if not self._client or not documents:
            return {"success": 0, "errors": 0}

        actions = []
        for doc in documents:
            actions.append({"index": {"_index": self._index_name, "_id": doc["entry_id"]}})
            body: dict[str, Any] = {
                "entry_id": doc["entry_id"],
                "content": doc.get("content", ""),
                "content_type": doc.get("content_type", "source_code"),
                "metadata": doc.get("metadata", {}),
                "timestamp": int(time.time() * 1000),
            }
            if doc.get("language"):
                body["language"] = doc["language"]
            if doc.get("vector"):
                body["vector"] = doc["vector"]
            actions.append(body)

        result = await self._client.bulk(operations=actions, refresh="wait_for")
        errors = sum(1 for item in result.get("items", []) if item.get("index", {}).get("error"))
        success = len(documents) - errors

        logger.info("Bulk indexed %d documents (%d errors)", success, errors)
        return {"success": success, "errors": errors}

    async def search(
        self,
        query_text: str | None = None,
        query_vector: list[float] | None = None,
        top_k: int = 10,
        content_type: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Search documents by text, vector, or both.

        Args:
            query_text: Full-text search query.
            query_vector: Dense vector for kNN search.
            top_k: Maximum results.
            content_type: Filter by content type.
            language: Filter by language.

        Returns:
            Dict with results and search metadata.
        """
        start = time.perf_counter()

        if not self._client:
            return {"results": [], "metadata": {"index_type": "elasticsearch", "mode": "mock"}}

        body: dict[str, Any] = {"size": top_k}
        filters: list[dict[str, Any]] = []

        if content_type:
            filters.append({"term": {"content_type": content_type}})
        if language:
            filters.append({"term": {"language": language}})

        if query_vector and query_text:
            body["query"] = {
                "bool": {
                    "must": [{"match": {"content": {"query": query_text, "fuzziness": "AUTO"}}}],
                    "filter": filters,
                }
            }
            body["knn"] = {
                "field": "vector",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": top_k * 10,
            }
        elif query_vector:
            body["knn"] = {
                "field": "vector",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": top_k * 10,
            }
            if filters:
                body["knn"]["filter"] = {"bool": {"filter": filters}}
        elif query_text:
            body["query"] = {
                "bool": {
                    "must": [{"match": {"content": {"query": query_text, "fuzziness": "AUTO"}}}],
                    "filter": filters,
                }
            }
        else:
            body["query"] = {"bool": {"filter": filters}} if filters else {"match_all": {}}

        response = await self._client.search(index=self._index_name, body=body)

        results = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append({
                "id": source.get("entry_id", hit["_id"]),
                "score": round(float(hit.get("_score", 0)), 6),
                "content_type": source.get("content_type"),
                "language": source.get("language"),
                "snippet": source.get("content", "")[:200],
            })

        elapsed_ms = (time.perf_counter() - start) * 1000
        total = response.get("hits", {}).get("total", {})
        total_count = total.get("value", 0) if isinstance(total, dict) else int(total)

        return {
            "results": results,
            "metadata": {
                "index_type": "elasticsearch",
                "total_hits": total_count,
                "returned": len(results),
                "query_time_ms": round(elapsed_ms, 2),
            },
        }

    async def delete_document(self, entry_id: str) -> bool:
        """Delete a document by ID."""
        if not self._client:
            return False
        try:
            result = await self._client.delete(index=self._index_name, id=entry_id)
            return result.get("result") == "deleted"
        except Exception:
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Return index statistics."""
        if not self._client:
            return {"mode": "mock", "doc_count": 0}

        stats = await self._client.indices.stats(index=self._index_name)
        total = stats.get("_all", {}).get("primaries", {})
        return {
            "mode": "connected",
            "url": self._url,
            "index": self._index_name,
            "doc_count": total.get("docs", {}).get("count", 0),
            "store_size_bytes": total.get("store", {}).get("size_in_bytes", 0),
        }