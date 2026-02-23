"""Embedding Service — Vector embedding generation via engine adapters.

Supports batch embedding, dimension reduction, similarity computation,
and integration with the vector alignment pipeline.

Default model: BAAI/bge-large-en-v1.5 (1024-dim, multilingual, Apache-2.0)
  HuggingFace: https://huggingface.co/BAAI/bge-large-en-v1.5
  Strong MTEB benchmark performance; supports Chinese and English.

Fallback chain:
  1. Engine adapter (vLLM / TGI / Ollama via /v1/embeddings)
  2. sentence-transformers local inference (requires ``pip install sentence-transformers``)
  3. Deterministic hash-based vectors (offline, no GPU/network — semantically meaningless)

URI: eco-base://backend/ai/services/embedding
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_DIM = 1024
MAX_EMBEDDING_DIM = 4096
MIN_EMBEDDING_DIM = 64
MAX_BATCH_SIZE = 256

# Real model: BAAI/bge-large-en-v1.5 — 1024-dim multilingual embedding model
# Apache-2.0 license; replaces the previously fictitious "quantum-bert-xxl-v1".
DEFAULT_MODEL = "BAAI/bge-large-en-v1.5"

# Lightweight alternative for resource-constrained / CPU-only environments
_FALLBACK_ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, Apache-2.0


class EmbeddingResult:
    """Result of an embedding operation."""

    __slots__ = (
        "request_id", "embeddings", "model_id", "dimensions",
        "total_tokens", "latency_ms", "created_at",
    )

    def __init__(
        self,
        embeddings: Optional[List[List[float]]] = None,
        model_id: str = DEFAULT_MODEL,
        dimensions: int = DEFAULT_EMBEDDING_DIM,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        self.request_id = str(uuid.uuid1())
        self.embeddings = embeddings or []
        self.model_id = model_id
        self.dimensions = dimensions
        self.total_tokens = total_tokens
        self.latency_ms = latency_ms
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "embeddings": self.embeddings,
            "model_id": self.model_id,
            "dimensions": self.dimensions,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "created_at": self.created_at,
            "uri": f"eco-base://ai/embedding/{self.request_id}",
            "urn": f"urn:eco-base:ai:embedding:{self.model_id}:{self.request_id}",
        }


class SimilarityResult:
    """Result of a similarity computation."""

    __slots__ = ("text_a", "text_b", "cosine_similarity", "euclidean_distance", "model_id")

    def __init__(
        self,
        text_a: str,
        text_b: str,
        cosine_similarity: float,
        euclidean_distance: float,
        model_id: str = DEFAULT_MODEL,
    ) -> None:
        self.text_a = text_a
        self.text_b = text_b
        self.cosine_similarity = cosine_similarity
        self.euclidean_distance = euclidean_distance
        self.model_id = model_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_a": self.text_a[:100],
            "text_b": self.text_b[:100],
            "cosine_similarity": round(self.cosine_similarity, 6),
            "euclidean_distance": round(self.euclidean_distance, 6),
            "model_id": self.model_id,
        }


class EmbeddingService:
    """Generates vector embeddings via engine adapters with local fallback.

    In production, dispatches to engine endpoints that support /v1/embeddings
    (vLLM, TGI, Ollama). Falls back to sentence-transformers local inference,
    then to deterministic hash-based vectors when no engine is available.

    Features:
        - Batch embedding with configurable dimensions
        - Dimension reduction via PCA-like projection
        - Cosine similarity and Euclidean distance
        - Integration with EngineManager connection pools
        - Prometheus-compatible metrics
    """

    def __init__(
        self,
        engine_manager: Any = None,
        default_model: str = DEFAULT_MODEL,
        default_dimensions: int = DEFAULT_EMBEDDING_DIM,
    ) -> None:
        self._engine_manager = engine_manager
        self._default_model = default_model
        self._default_dimensions = default_dimensions
        self._st_model: Any = None  # cached sentence-transformers model

        # Metrics
        self.total_requests: int = 0
        self.total_tokens: int = 0
        self.total_errors: int = 0
        self.total_vectors: int = 0

    async def embed(
        self,
        text: str,
        model_id: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> EmbeddingResult:
        """Generate embedding for a single text."""
        return await self.embed_batch(
            texts=[text],
            model_id=model_id,
            dimensions=dimensions,
        )

    async def embed_batch(
        self,
        texts: List[str],
        model_id: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> EmbeddingResult:
        """Generate embeddings for a batch of texts.

        Dispatches to engine if available, otherwise falls back through
        sentence-transformers local inference and finally hash-based vectors.
        """
        model = model_id or self._default_model
        dim = dimensions or self._default_dimensions
        self.total_requests += 1

        if len(texts) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(texts)} exceeds maximum {MAX_BATCH_SIZE}")
        if dim < MIN_EMBEDDING_DIM or dim > MAX_EMBEDDING_DIM:
            raise ValueError(f"Dimensions {dim} out of range [{MIN_EMBEDDING_DIM}, {MAX_EMBEDDING_DIM}]")
        if not texts:
            raise ValueError("Empty text list")

        start = time.monotonic()

        try:
            result = await self._embed_via_engine(texts, model, dim)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning("Engine embedding failed, using fallback: %s", exc)

        embeddings, total_tokens = self._embed_fallback(texts, dim)
        elapsed = (time.monotonic() - start) * 1000

        self.total_tokens += total_tokens
        self.total_vectors += len(embeddings)

        return EmbeddingResult(
            embeddings=embeddings,
            model_id=model,
            dimensions=dim,
            total_tokens=total_tokens,
            latency_ms=elapsed,
        )

    async def similarity(
        self,
        text_a: str,
        text_b: str,
        model_id: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> SimilarityResult:
        """Compute similarity between two texts."""
        model = model_id or self._default_model
        result = await self.embed_batch(
            texts=[text_a, text_b],
            model_id=model,
            dimensions=dimensions,
        )

        vec_a = result.embeddings[0]
        vec_b = result.embeddings[1]

        cos_sim = self._cosine_similarity(vec_a, vec_b)
        euc_dist = self._euclidean_distance(vec_a, vec_b)

        return SimilarityResult(
            text_a=text_a,
            text_b=text_b,
            cosine_similarity=cos_sim,
            euclidean_distance=euc_dist,
            model_id=model,
        )

    async def reduce_dimensions(
        self,
        embeddings: List[List[float]],
        target_dim: int,
    ) -> List[List[float]]:
        """Reduce embedding dimensions via deterministic projection.

        Uses a seeded random projection matrix for reproducibility.
        """
        if not embeddings:
            return []

        source_dim = len(embeddings[0])
        if target_dim >= source_dim:
            return embeddings
        if target_dim < 1:
            raise ValueError("target_dim must be >= 1")

        projection = self._build_projection_matrix(source_dim, target_dim)
        reduced: List[List[float]] = []

        for vec in embeddings:
            new_vec = [0.0] * target_dim
            for j in range(target_dim):
                val = 0.0
                for i in range(source_dim):
                    val += vec[i] * projection[i][j]
                new_vec[j] = val

            norm = math.sqrt(sum(v * v for v in new_vec))
            if norm > 0:
                new_vec = [v / norm for v in new_vec]
            reduced.append([round(v, 6) for v in new_vec])

        return reduced

    def get_stats(self) -> Dict[str, Any]:
        """Return embedding service statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "total_vectors": self.total_vectors,
            "default_model": self._default_model,
            "default_dimensions": self._default_dimensions,
            "engine_available": self._engine_manager is not None,
        }

    async def _embed_via_engine(
        self,
        texts: List[str],
        model_id: str,
        dimensions: int,
    ) -> Optional[EmbeddingResult]:
        """Attempt to generate embeddings via an engine adapter."""
        if self._engine_manager is None:
            return None

        pool = getattr(self._engine_manager, "_pool", None)
        if pool is None:
            return None

        engine_name = self._resolve_embedding_engine()
        if engine_name is None:
            return None

        endpoints = getattr(self._engine_manager, "_endpoints", {})
        url = endpoints.get(engine_name)
        if not url:
            return None

        client = pool.get_client(engine_name, url)
        start = time.monotonic()

        payload = {
            "input": texts,
            "model": model_id,
            "encoding_format": "float",
        }
        if dimensions != DEFAULT_EMBEDDING_DIM:
            payload["dimensions"] = dimensions

        path = "/v1/embeddings"
        if engine_name == "ollama":
            path = "/api/embeddings"
            payload = {"model": model_id, "prompt": texts[0] if len(texts) == 1 else " ".join(texts)}

        resp = await client.post(path, json=payload)
        resp.raise_for_status()
        data = resp.json()

        embeddings: List[List[float]] = []
        total_tokens = 0

        if "data" in data:
            for item in data["data"]:
                vec = item.get("embedding", [])
                if len(vec) > dimensions:
                    vec = vec[:dimensions]
                embeddings.append([round(v, 6) for v in vec])
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", sum(len(t.split()) for t in texts))
        elif "embedding" in data:
            vec = data["embedding"]
            if len(vec) > dimensions:
                vec = vec[:dimensions]
            embeddings.append([round(v, 6) for v in vec])
            total_tokens = len(texts[0].split())

        elapsed = (time.monotonic() - start) * 1000
        self.total_tokens += total_tokens
        self.total_vectors += len(embeddings)

        return EmbeddingResult(
            embeddings=embeddings,
            model_id=model_id,
            dimensions=dimensions,
            total_tokens=total_tokens,
            latency_ms=elapsed,
        )

    def _resolve_embedding_engine(self) -> Optional[str]:
        """Find an engine that supports embeddings."""
        if self._engine_manager is None:
            return None

        preferred = ["ollama", "tgi", "vllm"]
        available = set(self._engine_manager.list_available_engines())

        for engine in preferred:
            if engine in available:
                return engine

        return next(iter(available), None)

    def _embed_fallback(
        self,
        texts: List[str],
        dimensions: int,
    ) -> Tuple[List[List[float]], int]:
        """Embedding fallback chain.

        Priority:
          1. sentence-transformers local inference
             (requires ``pip install sentence-transformers``)
          2. Deterministic hash-based vectors (offline, no dependencies)

        The hash-based path guarantees the service remains functional without
        any network access or GPU, but produces semantically meaningless vectors.
        It is intended only for unit-test / CI environments where a real model
        is not available.
        """
        # --- Attempt 1: local sentence-transformers ---
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]

            # Use lightweight model for dims <= 384, full model otherwise
            st_model_name = _FALLBACK_ST_MODEL if dimensions <= 384 else DEFAULT_MODEL
            cached = self._st_model
            if cached is None or getattr(cached, "_eco_model_name", None) != st_model_name:
                logger.info("Loading sentence-transformers model: %s", st_model_name)
                self._st_model = SentenceTransformer(st_model_name)
                self._st_model._eco_model_name = st_model_name  # type: ignore[attr-defined]

            raw = self._st_model.encode(texts, normalize_embeddings=True)
            embeddings: List[List[float]] = []
            total_tokens = 0
            for i, vec in enumerate(raw):
                total_tokens += len(texts[i].split())
                v: List[float] = list(vec[:dimensions]) if len(vec) >= dimensions else list(vec)
                # Pad with zeros if model native dim < requested dim
                if len(v) < dimensions:
                    v += [0.0] * (dimensions - len(v))
                embeddings.append([round(float(x), 6) for x in v])
            return embeddings, total_tokens

        except Exception as exc:  # noqa: BLE001
            logger.debug("sentence-transformers unavailable, using hash fallback: %s", exc)

        # --- Attempt 2: deterministic hash-based fallback (offline) ---
        # WARNING: these vectors carry NO semantic meaning.
        # They are deterministic (same text → same vector) and L2-normalised,
        # but cosine similarity between unrelated texts will be near-random.
        embeddings = []
        total_tokens = 0

        for text in texts:
            tokens = text.split()
            total_tokens += len(tokens)

            seed = int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)
            rng = random.Random(seed)

            vec = [rng.gauss(0, 1) / math.sqrt(dimensions) for _ in range(dimensions)]
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]

            embeddings.append([round(v, 6) for v in vec])

        return embeddings, total_tokens

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            raise ValueError(f"Dimension mismatch: {len(a)} vs {len(b)}")

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    @staticmethod
    def _euclidean_distance(a: List[float], b: List[float]) -> float:
        """Compute Euclidean distance between two vectors."""
        if len(a) != len(b):
            raise ValueError(f"Dimension mismatch: {len(a)} vs {len(b)}")

        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    @staticmethod
    def _build_projection_matrix(source_dim: int, target_dim: int) -> List[List[float]]:
        """Build a deterministic random projection matrix."""
        rng = random.Random(42)
        scale = 1.0 / math.sqrt(target_dim)
        matrix: List[List[float]] = []
        for _ in range(source_dim):
            row = [rng.gauss(0, scale) for _ in range(target_dim)]
            matrix.append(row)
        return matrix
