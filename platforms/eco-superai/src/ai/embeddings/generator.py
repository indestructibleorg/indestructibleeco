"""Embedding generator with multi-model support."""
from __future__ import annotations

import time
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingGenerator:
    """Generate text embeddings using various models."""

    async def generate(self, texts: list[str], model: str = "text-embedding-3-small") -> dict[str, Any]:
        start = time.perf_counter()

        try:
            from openai import AsyncOpenAI
            from src.infrastructure.config import get_settings
            settings = get_settings()
            client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
            response = await client.embeddings.create(input=texts, model=model)
            embeddings = [item.embedding for item in response.data]
            elapsed = (time.perf_counter() - start) * 1000
            return {
                "embeddings": embeddings,
                "model": model,
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "count": len(embeddings),
                "usage": {"total_tokens": response.usage.total_tokens},
                "execution_time_ms": round(elapsed, 2),
            }
        except Exception:
            # Fallback: sentence-transformers or deterministic hash
            try:
                from sentence_transformers import SentenceTransformer
                st_model = SentenceTransformer("all-MiniLM-L6-v2")
                embeddings = st_model.encode(texts).tolist()
            except ImportError:
                import hashlib
                embeddings = []
                for text in texts:
                    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                    rng = np.random.RandomState(seed)
                    vec = rng.randn(384)
                    vec = (vec / np.linalg.norm(vec)).tolist()
                    embeddings.append(vec)

            elapsed = (time.perf_counter() - start) * 1000
            return {
                "embeddings": embeddings,
                "model": "fallback",
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "count": len(embeddings),
                "execution_time_ms": round(elapsed, 2),
            }