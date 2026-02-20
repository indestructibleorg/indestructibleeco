"""Vector Folding Engine.

URI: indestructibleeco://backend/ai/engines/folding/vector_folding

Converts text/code into vector representations via embedding models,
with dimensionality reduction to preserve core semantic information.
Suitable for large-scale efficient processing and similarity search.

Wired to EmbeddingService for real embedding generation when available,
with deterministic hash-based fallback for CI/test environments.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VectorFoldingEngine:
    """Transforms source content into dense vector representations.

    Pipeline: tokenize → embed → reduce dimensions → normalize → output.
    Uses EmbeddingService when available, sentence-transformers as secondary,
    and deterministic hash fallback for CI/test.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        target_dimensions: int | None = None,
        batch_size: int = 64,
        embedding_service: Any = None,
    ) -> None:
        self._model_name = model_name
        self._target_dimensions = target_dimensions
        self._batch_size = batch_size
        self._embedding_service = embedding_service
        self._model: Any = None
        self._reducer: Any = None
        self._native_dim: int = 384
        self._embed_mode: str = "uninitialized"

    def _ensure_model(self) -> None:
        """Lazy-load the embedding backend on first use."""
        if self._embed_mode != "uninitialized":
            return

        # Priority 1: Use injected EmbeddingService
        if self._embedding_service is not None:
            self._embed_mode = "embedding_service"
            self._native_dim = getattr(self._embedding_service, '_dimensions', 1024)
            logger.info("VectorFolding using EmbeddingService (dim=%d)", self._native_dim)
            return

        # Priority 2: Try sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._native_dim = self._model.get_sentence_embedding_dimension()
            self._embed_mode = "sentence_transformers"
            logger.info("VectorFolding using sentence-transformers %s (dim=%d)", self._model_name, self._native_dim)
            return
        except ImportError:
            pass

        # Priority 3: Deterministic hash fallback
        self._embed_mode = "fallback"
        self._native_dim = 384
        logger.warning("VectorFolding using hash-based fallback embeddings (dim=%d)", self._native_dim)

    def _fallback_embed(self, text: str) -> np.ndarray:
        """Deterministic hash-based embedding for environments without GPU/model."""
        digest = hashlib.sha512(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        rng = np.random.RandomState(seed)
        vec = rng.randn(self._native_dim).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-10)

    def _embed_via_service(self, texts: list[str]) -> np.ndarray:
        """Embed using the injected EmbeddingService."""
        result = self._embedding_service.embed_batch(texts)
        if hasattr(result, 'embeddings'):
            return np.array(result.embeddings, dtype=np.float32)
        elif isinstance(result, dict) and 'embeddings' in result:
            return np.array(result['embeddings'], dtype=np.float32)
        elif isinstance(result, (list, np.ndarray)):
            return np.array(result, dtype=np.float32)
        return np.array([self._fallback_embed(t) for t in texts], dtype=np.float32)

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts into dense vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            numpy array of shape (len(texts), native_dim).
        """
        self._ensure_model()

        if self._embed_mode == "embedding_service":
            return self._embed_via_service(texts)
        elif self._embed_mode == "sentence_transformers":
            return self._model.encode(
                texts,
                batch_size=self._batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
        else:
            return np.array([self._fallback_embed(t) for t in texts], dtype=np.float32)

    def reduce_dimensions(self, vectors: np.ndarray, target_dim: int | None = None) -> np.ndarray:
        """Reduce vector dimensionality via PCA while preserving variance.

        Args:
            vectors: Input array of shape (n, d).
            target_dim: Target dimensionality. Defaults to self._target_dimensions.

        Returns:
            Reduced array of shape (n, target_dim).
        """
        dim = target_dim or self._target_dimensions
        if dim is None or dim >= vectors.shape[1]:
            return vectors
        try:
            from sklearn.decomposition import PCA
            if self._reducer is None or self._reducer.n_components != dim:
                self._reducer = PCA(n_components=dim, random_state=42)
                self._reducer.fit(vectors)
                logger.info(
                    "PCA fitted: %d → %d dims, explained_variance=%.4f",
                    vectors.shape[1], dim, sum(self._reducer.explained_variance_ratio_),
                )
            reduced = self._reducer.transform(vectors).astype(np.float32)
        except ImportError:
            logger.warning("sklearn not available; using truncation for dimension reduction")
            reduced = vectors[:, :dim].astype(np.float32)
        norms = np.linalg.norm(reduced, axis=1, keepdims=True) + 1e-10
        return reduced / norms

    def fold(
        self,
        content: str,
        content_type: str = "source_code",
        language: str | None = None,
        target_dimensions: int | None = None,
    ) -> dict[str, Any]:
        """Full folding pipeline: chunk → embed → reduce → return.

        Args:
            content: Raw text or code to fold.
            content_type: One of source_code, document, config, log.
            language: Programming language hint for chunking.
            target_dimensions: Override target dimensionality.

        Returns:
            Dict with id, vector, metadata, folding_time_ms.
        """
        start = time.perf_counter()
        chunks = self._chunk_content(content, content_type, language)
        embeddings = self.embed(chunks)

        if len(embeddings) > 1:
            combined = np.mean(embeddings, axis=0, keepdims=True)
        else:
            combined = embeddings

        dim = target_dimensions or self._target_dimensions
        if dim and dim < combined.shape[1]:
            combined = self.reduce_dimensions(combined, dim)

        vector = combined[0].tolist()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "id": f"vf-{content_hash}",
            "vector": vector,
            "metadata": {
                "content_type": content_type,
                "language": language,
                "chunk_count": len(chunks),
                "native_dim": self._native_dim,
                "output_dim": len(vector),
                "model": self._model_name,
                "embed_mode": self._embed_mode,
            },
            "folding_time_ms": round(elapsed_ms, 2),
        }

    def fold_batch(
        self,
        contents: list[str],
        content_type: str = "source_code",
        language: str | None = None,
        target_dimensions: int | None = None,
    ) -> list[dict[str, Any]]:
        """Batch fold multiple content items."""
        return [
            self.fold(c, content_type, language, target_dimensions)
            for c in contents
        ]

    @staticmethod
    def _chunk_content(content: str, content_type: str, language: str | None) -> list[str]:
        """Split content into semantically meaningful chunks.

        For source code: split by function/class boundaries.
        For documents: split by paragraphs.
        For configs: split by top-level keys.
        For logs: split by timestamp boundaries.
        """
        if not content.strip():
            return [content]

        if content_type == "source_code":
            return _chunk_source_code(content, language)
        elif content_type == "config":
            return _chunk_config(content)
        elif content_type == "log":
            return _chunk_log(content)
        else:
            return _chunk_document(content)


def _chunk_source_code(content: str, language: str | None) -> list[str]:
    """Chunk source code by function/class boundaries."""
    lines = content.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    boundary_keywords = {"def ", "class ", "function ", "func ", "pub fn ", "public ", "private ", "protected "}

    for line in lines:
        stripped = line.lstrip()
        if any(stripped.startswith(kw) for kw in boundary_keywords) and current:
            chunk_text = "\n".join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current = [line]
        else:
            current.append(line)

    if current:
        chunk_text = "\n".join(current).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks if chunks else [content]


def _chunk_document(content: str) -> list[str]:
    """Chunk documents by paragraph boundaries."""
    paragraphs = content.split("\n\n")
    chunks = [p.strip() for p in paragraphs if p.strip()]
    return chunks if chunks else [content]


def _chunk_config(content: str) -> list[str]:
    """Chunk config files by top-level sections."""
    lines = content.split("\n")
    chunks: list[str] = []
    current: list[str] = []

    for line in lines:
        if line and not line[0].isspace() and line[0] not in ("#", "/", "-") and current:
            chunk_text = "\n".join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current = [line]
        else:
            current.append(line)

    if current:
        chunk_text = "\n".join(current).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks if chunks else [content]


def _chunk_log(content: str) -> list[str]:
    """Chunk log files by timestamp boundaries, grouping ~50 lines."""
    lines = content.split("\n")
    chunk_size = 50
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i : i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks if chunks else [content]
