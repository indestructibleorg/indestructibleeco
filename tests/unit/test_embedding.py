"""Unit tests for EmbeddingService."""
import pytest
import math

from backend.ai.src.services.embedding import (
    EmbeddingResult,
    EmbeddingService,
    SimilarityResult,
    DEFAULT_EMBEDDING_DIM,
    MAX_BATCH_SIZE,
    MAX_EMBEDDING_DIM,
    MIN_EMBEDDING_DIM,
)


@pytest.fixture
def svc():
    return EmbeddingService(engine_manager=None, default_dimensions=64)


class TestEmbeddingResult:
    def test_creation(self):
        result = EmbeddingResult(
            embeddings=[[0.1, 0.2]],
            model_id="test",
            dimensions=2,
            total_tokens=5,
            latency_ms=1.5,
        )
        assert len(result.embeddings) == 1
        assert result.model_id == "test"
        assert result.dimensions == 2

    def test_to_dict(self):
        result = EmbeddingResult(embeddings=[[0.1]], model_id="m", dimensions=1)
        d = result.to_dict()
        assert "uri" in d
        assert "urn" in d
        assert d["model_id"] == "m"
        assert d["uri"].startswith("indestructibleeco://")


class TestSimilarityResult:
    def test_creation(self):
        result = SimilarityResult(
            text_a="hello",
            text_b="world",
            cosine_similarity=0.85,
            euclidean_distance=0.55,
        )
        assert result.cosine_similarity == 0.85

    def test_to_dict(self):
        result = SimilarityResult(
            text_a="a" * 200,
            text_b="b",
            cosine_similarity=0.9,
            euclidean_distance=0.3,
        )
        d = result.to_dict()
        assert len(d["text_a"]) <= 100
        assert d["cosine_similarity"] == 0.9


class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_embed_single(self, svc):
        result = await svc.embed("Hello world")
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 64
        assert result.total_tokens > 0
        assert result.latency_ms >= 0
        assert svc.total_requests == 1

    @pytest.mark.asyncio
    async def test_embed_batch(self, svc):
        texts = ["Hello", "World", "Test"]
        result = await svc.embed_batch(texts=texts, dimensions=64)
        assert len(result.embeddings) == 3
        for emb in result.embeddings:
            assert len(emb) == 64
        assert result.total_tokens > 0
        assert svc.total_vectors == 3

    @pytest.mark.asyncio
    async def test_embed_deterministic(self, svc):
        result1 = await svc.embed("Hello world", dimensions=64)
        result2 = await svc.embed("Hello world", dimensions=64)
        assert result1.embeddings[0] == result2.embeddings[0]

    @pytest.mark.asyncio
    async def test_embed_different_texts(self, svc):
        result1 = await svc.embed("Hello", dimensions=64)
        result2 = await svc.embed("Goodbye", dimensions=64)
        assert result1.embeddings[0] != result2.embeddings[0]

    @pytest.mark.asyncio
    async def test_embed_normalized(self, svc):
        result = await svc.embed("Test normalization", dimensions=64)
        vec = result.embeddings[0]
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_embed_empty_raises(self, svc):
        with pytest.raises(ValueError, match="Empty"):
            await svc.embed_batch(texts=[], dimensions=64)

    @pytest.mark.asyncio
    async def test_embed_dim_too_small(self, svc):
        with pytest.raises(ValueError, match="out of range"):
            await svc.embed_batch(texts=["test"], dimensions=10)

    @pytest.mark.asyncio
    async def test_embed_dim_too_large(self, svc):
        with pytest.raises(ValueError, match="out of range"):
            await svc.embed_batch(texts=["test"], dimensions=10000)

    @pytest.mark.asyncio
    async def test_embed_batch_too_large(self, svc):
        texts = [f"text-{i}" for i in range(MAX_BATCH_SIZE + 1)]
        with pytest.raises(ValueError, match="exceeds maximum"):
            await svc.embed_batch(texts=texts, dimensions=64)

    @pytest.mark.asyncio
    async def test_similarity(self, svc):
        result = await svc.similarity("Hello world", "Hello world", dimensions=64)
        assert isinstance(result, SimilarityResult)
        assert result.cosine_similarity > 0.99
        assert result.euclidean_distance < 0.01

    @pytest.mark.asyncio
    async def test_similarity_different(self, svc):
        result = await svc.similarity("cat", "quantum physics", dimensions=64)
        assert isinstance(result, SimilarityResult)
        assert result.cosine_similarity < 0.99

    @pytest.mark.asyncio
    async def test_reduce_dimensions(self, svc):
        result = await svc.embed_batch(texts=["hello", "world"], dimensions=128)
        reduced = await svc.reduce_dimensions(result.embeddings, target_dim=64)
        assert len(reduced) == 2
        assert len(reduced[0]) == 64
        norm = math.sqrt(sum(v * v for v in reduced[0]))
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_reduce_noop_if_smaller(self, svc):
        result = await svc.embed_batch(texts=["hello"], dimensions=64)
        reduced = await svc.reduce_dimensions(result.embeddings, target_dim=128)
        assert reduced == result.embeddings

    @pytest.mark.asyncio
    async def test_reduce_empty(self, svc):
        reduced = await svc.reduce_dimensions([], target_dim=32)
        assert reduced == []

    @pytest.mark.asyncio
    async def test_reduce_invalid_dim(self, svc):
        with pytest.raises(ValueError, match="target_dim"):
            await svc.reduce_dimensions([[0.1, 0.2]], target_dim=0)

    @pytest.mark.asyncio
    async def test_stats(self, svc):
        await svc.embed("test", dimensions=64)
        stats = svc.get_stats()
        assert stats["total_requests"] == 1
        assert stats["total_vectors"] == 1
        assert stats["total_tokens"] > 0
        assert stats["engine_available"] is False

    @pytest.mark.asyncio
    async def test_cosine_similarity_static(self):
        cos = EmbeddingService._cosine_similarity([1, 0, 0], [1, 0, 0])
        assert abs(cos - 1.0) < 1e-6

        cos = EmbeddingService._cosine_similarity([1, 0, 0], [0, 1, 0])
        assert abs(cos) < 1e-6

    @pytest.mark.asyncio
    async def test_euclidean_distance_static(self):
        dist = EmbeddingService._euclidean_distance([0, 0], [3, 4])
        assert abs(dist - 5.0) < 1e-6

    @pytest.mark.asyncio
    async def test_dimension_mismatch(self):
        with pytest.raises(ValueError, match="mismatch"):
            EmbeddingService._cosine_similarity([1, 0], [1, 0, 0])

        with pytest.raises(ValueError, match="mismatch"):
            EmbeddingService._euclidean_distance([1], [1, 2])