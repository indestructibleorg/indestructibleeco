"""Unit tests for ai/prompts and ai/vectordb modules."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# PromptTemplate
# ---------------------------------------------------------------------------

class TestPromptTemplate:
    def test_render_basic(self) -> None:
        from src.ai.prompts import PromptTemplate
        t = PromptTemplate(
            name="test",
            template="Hello {{name}}, you are {{role}}.",
            version="1.0",
            description="test template",
        )
        result = t.render(name="Alice", role="admin")
        assert result == "Hello Alice, you are admin."

    def test_render_missing_variable_raises(self) -> None:
        from src.ai.prompts import PromptTemplate
        t = PromptTemplate(
            name="test",
            template="Hello {{name}}.",
            version="1.0",
            description="test",
        )
        with pytest.raises((KeyError, Exception)):
            t.render()  # missing 'name'

    def test_render_extra_variables_ignored(self) -> None:
        from src.ai.prompts import PromptTemplate
        t = PromptTemplate(
            name="test",
            template="Hello {{name}}.",
            version="1.0",
            description="test",
        )
        result = t.render(name="Bob", extra="ignored")
        assert "Bob" in result

    def test_template_metadata(self) -> None:
        from src.ai.prompts import PromptTemplate
        t = PromptTemplate(
            name="my_template",
            template="{{content}}",
            version="2.1",
            description="A test template",
        )
        assert t.name == "my_template"
        assert t.version == "2.1"
        assert t.description == "A test template"


# ---------------------------------------------------------------------------
# PromptTemplateManager
# ---------------------------------------------------------------------------

class TestPromptTemplateManager:
    def test_register_and_get(self) -> None:
        from src.ai.prompts import PromptTemplateManager, PromptTemplate
        mgr = PromptTemplateManager()
        t = PromptTemplate(name="custom", template="{{x}}", version="1.0", description="custom")
        mgr.register(t)
        retrieved = mgr.get("custom")
        assert retrieved is not None
        assert retrieved.name == "custom"

    def test_get_nonexistent_returns_none(self) -> None:
        from src.ai.prompts import PromptTemplateManager
        mgr = PromptTemplateManager()
        result = mgr.get("nonexistent_xyz")
        assert result is None

    def test_list_templates(self) -> None:
        from src.ai.prompts import PromptTemplateManager
        mgr = PromptTemplateManager()
        templates = mgr.list_templates()
        assert isinstance(templates, list)

    def test_default_templates_registered(self) -> None:
        from src.ai.prompts import PromptTemplateManager
        mgr = PromptTemplateManager()
        # Should have default templates like 'code_review', 'data_analysis', etc.
        templates = mgr.list_templates()
        assert len(templates) > 0

    def test_render_by_name(self) -> None:
        from src.ai.prompts import PromptTemplateManager, PromptTemplate
        mgr = PromptTemplateManager()
        t = PromptTemplate(name="greeting", template="Hi {{user}}!", version="1.0", description="greeting")
        mgr.register(t)
        result = mgr.render("greeting", user="Charlie")
        assert result == "Hi Charlie!"

    def test_render_nonexistent_raises(self) -> None:
        from src.ai.prompts import PromptTemplateManager
        mgr = PromptTemplateManager()
        with pytest.raises((KeyError, ValueError, AttributeError)):
            mgr.render("nonexistent_xyz", x="y")

    def test_get_prompt_manager_singleton(self) -> None:
        from src.ai.prompts import get_prompt_manager
        mgr1 = get_prompt_manager()
        mgr2 = get_prompt_manager()
        assert mgr1 is mgr2

    def test_overwrite_existing_template(self) -> None:
        from src.ai.prompts import PromptTemplateManager, PromptTemplate
        mgr = PromptTemplateManager()
        t1 = PromptTemplate(name="dup", template="v1: {{x}}", version="1.0", description="v1")
        t2 = PromptTemplate(name="dup", template="v2: {{x}}", version="2.0", description="v2")
        mgr.register(t1)
        mgr.register(t2)
        retrieved = mgr.get("dup")
        assert retrieved.version == "2.0"


# ---------------------------------------------------------------------------
# VectorDBManager — mock chromadb
# ---------------------------------------------------------------------------

class TestVectorDBManager:
    def _make_mock_collection(self):
        col = MagicMock()
        col.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[{"source": "api"}, {"source": "api"}]],
        }
        col.get.return_value = {
            "ids": ["id1"],
            "documents": ["doc1"],
            "metadatas": [{"source": "api"}],
        }
        col.count.return_value = 5
        return col

    def _make_mock_client(self, col=None):
        if col is None:
            col = self._make_mock_collection()
        client = MagicMock()
        client.get_or_create_collection.return_value = col
        client.get_collection.return_value = col
        client.list_collections.return_value = [
            MagicMock(name="test_collection"),
        ]
        client.delete_collection = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_upsert_success(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_col = self._make_mock_collection()
        mock_client = self._make_mock_client(mock_col)

        with patch.object(mgr, "_get_client", return_value=mock_client):
            with patch.object(mgr, "_embed_texts", return_value=[[0.1] * 384, [0.2] * 384]):
                result = await mgr.upsert(
                    collection="test",
                    documents=["doc1", "doc2"],
                    metadata=[{"source": "api"}, {"source": "api"}],
                    ids=["id1", "id2"],
                )
        assert result["status"] == "success"
        assert result["upserted_count"] == 2

    @pytest.mark.asyncio
    async def test_upsert_auto_generates_ids(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_col = self._make_mock_collection()
        mock_client = self._make_mock_client(mock_col)

        with patch.object(mgr, "_get_client", return_value=mock_client):
            with patch.object(mgr, "_embed_texts", return_value=[[0.1] * 384]):
                result = await mgr.upsert(
                    collection="test",
                    documents=["doc1"],
                    metadata=[],
                    ids=[],
                )
        assert len(result["ids"]) == 1

    @pytest.mark.asyncio
    async def test_search_success(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_col = self._make_mock_collection()
        mock_client = self._make_mock_client(mock_col)

        with patch.object(mgr, "_get_client", return_value=mock_client):
            with patch.object(mgr, "_embed_texts", return_value=[[0.1] * 384]):
                result = await mgr.search(
                    collection="test",
                    query="find me",
                    top_k=2,
                )
        assert "results" in result
        assert "total_results" in result
        assert result["total_results"] >= 0

    @pytest.mark.asyncio
    async def test_search_collection_not_found_returns_empty(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Collection not found")

        with patch.object(mgr, "_get_client", return_value=mock_client):
            result = await mgr.search(
                collection="nonexistent",
                query="find me",
                top_k=5,
            )
        # Should return error dict with empty results, not raise
        assert "results" in result
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_list_collections(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_client = self._make_mock_client()

        with patch.object(mgr, "_get_client", return_value=mock_client):
            result = await mgr.list_collections()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_delete_collection_returns_none(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_client = self._make_mock_client()

        with patch.object(mgr, "_get_client", return_value=mock_client):
            result = await mgr.delete_collection(collection="test")
        # delete_collection returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_semantic_search_with_threshold(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_col = self._make_mock_collection()
        # Adjust mock to return distances that map to similarity scores
        mock_col.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["high similarity doc", "low similarity doc"]],
            "distances": [[0.1, 0.9]],  # similarity: 0.9 and 0.1
            "metadatas": [[{"source": "api"}, {"source": "api"}]],
        }
        mock_client = self._make_mock_client(mock_col)

        with patch.object(mgr, "_get_client", return_value=mock_client):
            with patch.object(mgr, "_embed_texts", return_value=[[0.1] * 384]):
                result = await mgr.semantic_search(
                    collection_name="test",
                    query="find me",
                    top_k=5,
                    threshold=0.5,  # only keep similarity >= 0.5
                )
        # Only the first result (similarity=0.9) should pass the threshold
        assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_add_documents_wraps_upsert(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        mgr = VectorDBManager()
        mock_col = self._make_mock_collection()
        mock_client = self._make_mock_client(mock_col)

        with patch.object(mgr, "_get_client", return_value=mock_client):
            with patch.object(mgr, "_embed_texts", return_value=[[0.1] * 384]):
                result = await mgr.add_documents(
                    collection_name="test",
                    documents=["doc1"],
                    metadatas=[{"source": "test"}],
                    ids=["id1"],
                )
        assert result["status"] == "success"

    def test_embed_texts_fallback_without_sentence_transformers(self) -> None:
        """When sentence_transformers is not installed, hash-based embeddings are used."""
        from src.ai.vectordb.manager import VectorDBManager
        import sys
        mgr = VectorDBManager()
        with patch.dict(sys.modules, {"sentence_transformers": None}):
            embeddings = mgr._embed_texts(["hello world", "test text"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        # Verify normalization (unit vector)
        norm = sum(v**2 for v in embeddings[0]) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_embed_texts_deterministic(self) -> None:
        """Same text should always produce the same embedding."""
        from src.ai.vectordb.manager import VectorDBManager
        import sys
        mgr = VectorDBManager()
        with patch.dict(sys.modules, {"sentence_transformers": None}):
            e1 = mgr._embed_texts(["deterministic text"])
            e2 = mgr._embed_texts(["deterministic text"])
        assert e1 == e2
