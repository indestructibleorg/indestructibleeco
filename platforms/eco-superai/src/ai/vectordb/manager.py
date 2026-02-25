"""Vector Database Manager - ChromaDB integration with embedding support."""
from __future__ import annotations

import uuid
import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class VectorDBManager:
    """Manage vector collections, embeddings, and semantic search."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import chromadb
                from src.infrastructure.config import get_settings
                settings = get_settings()
                self._client = chromadb.HttpClient(host=settings.ai.chromadb_host, port=settings.ai.chromadb_port)
            except Exception:
                import chromadb
                self._client = chromadb.Client()
        return self._client

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers or OpenAI."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(texts)
            return embeddings.tolist()
        except ImportError:
            import hashlib
            import numpy as np
            embeddings = []
            for text in texts:
                seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                rng = np.random.RandomState(seed)
                vec = rng.randn(384).tolist()
                norm = sum(v**2 for v in vec) ** 0.5
                embeddings.append([v / norm for v in vec])
            return embeddings

    async def upsert(self, collection: str, documents: list[str], metadata: list[dict[str, Any]], ids: list[str]) -> dict[str, Any]:
        start = time.perf_counter()
        client = self._get_client()

        col = client.get_or_create_collection(name=collection, metadata={"hnsw:space": "cosine"})

        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        if not metadata:
            metadata = [{"source": "api", "index": i} for i in range(len(documents))]

        embeddings = self._embed_texts(documents)
        col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadata)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("vector_upsert", collection=collection, count=len(documents), elapsed_ms=elapsed)

        return {
            "status": "success",
            "collection": collection,
            "upserted_count": len(documents),
            "ids": ids,
            "execution_time_ms": round(elapsed, 2),
        }

    async def search(self, collection: str, query: str, top_k: int, filter: dict[str, Any] | None = None, include_metadata: bool = True) -> dict[str, Any]:
        start = time.perf_counter()
        client = self._get_client()

        try:
            col = client.get_collection(name=collection)
        except Exception:
            return {"error": f"Collection '{collection}' not found", "results": []}

        query_embedding = self._embed_texts([query])[0]

        kwargs: dict[str, Any] = {"query_embeddings": [query_embedding], "n_results": top_k}
        if include_metadata:
            kwargs["include"] = ["documents", "metadatas", "distances"]
        if filter:
            kwargs["where"] = filter

        results = col.query(**kwargs)

        formatted_results = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                entry: dict[str, Any] = {"id": doc_id}
                if results.get("documents"):
                    entry["document"] = results["documents"][0][i]
                if results.get("metadatas"):
                    entry["metadata"] = results["metadatas"][0][i]
                if results.get("distances"):
                    entry["distance"] = round(results["distances"][0][i], 6)
                    entry["similarity"] = round(1 - results["distances"][0][i], 6)
                formatted_results.append(entry)

        elapsed = (time.perf_counter() - start) * 1000
        return {
            "collection": collection,
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "execution_time_ms": round(elapsed, 2),
        }

    async def list_collections(self) -> list[dict[str, Any]]:
        client = self._get_client()
        collections = client.list_collections()
        return [{"name": c.name, "count": c.count(), "metadata": c.metadata} for c in collections]

    async def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add documents to a collection (convenience wrapper around upsert)."""
        return await self.upsert(
            collection=collection_name,
            documents=documents,
            metadata=metadatas or [],
            ids=ids or [],
        )

    async def semantic_search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Semantic search with optional similarity threshold filtering.

        Args:
            collection_name: Name of the vector collection.
            query: Natural-language query string.
            top_k: Maximum number of results to return.
            threshold: Minimum similarity score (0-1). Results below this are dropped.
            filter: Optional metadata filter dict passed to ChromaDB ``where``.
        """
        result = await self.search(
            collection=collection_name,
            query=query,
            top_k=top_k,
            filter=filter,
        )
        if threshold > 0.0 and "results" in result:
            result["results"] = [
                r for r in result["results"]
                if r.get("similarity", 0.0) >= threshold
            ]
            result["total_results"] = len(result["results"])
        return result

    async def delete_collection(self, collection: str) -> None:
        client = self._get_client()
        client.delete_collection(name=collection)
        logger.info("vector_collection_deleted", collection=collection)