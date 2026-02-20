"""Unit tests for Vector Folding + Realtime Index upgrades (Step 20)."""
import json
import os
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.ai.engines.folding.vector_folding import VectorFoldingEngine
from backend.ai.engines.folding.realtime_index import RealtimeIndexUpdater, WALWriter


class MockEmbeddingService:
    """Mock EmbeddingService that returns deterministic vectors."""
    _dimensions = 128

    def embed_batch(self, texts):
        vecs = []
        for t in texts:
            seed = hash(t) % (2**31)
            rng = np.random.RandomState(seed)
            v = rng.randn(self._dimensions).astype(np.float32)
            v = v / (np.linalg.norm(v) + 1e-10)
            vecs.append(v.tolist())
        return {"embeddings": vecs}


class TestVectorFoldingWithService:
    def test_embed_via_service(self):
        svc = MockEmbeddingService()
        engine = VectorFoldingEngine(embedding_service=svc)
        result = engine.embed(["hello world"])
        assert result.shape == (1, 128)

    def test_fold_via_service(self):
        svc = MockEmbeddingService()
        engine = VectorFoldingEngine(embedding_service=svc)
        result = engine.fold("def foo(): pass", content_type="source_code")
        assert "vector" in result
        assert len(result["vector"]) == 128
        assert result["metadata"]["embed_mode"] == "embedding_service"

    def test_fold_batch_via_service(self):
        svc = MockEmbeddingService()
        engine = VectorFoldingEngine(embedding_service=svc)
        results = engine.fold_batch(["text1", "text2"], content_type="document")
        assert len(results) == 2
        assert all("vector" in r for r in results)

    def test_deterministic_same_input(self):
        svc = MockEmbeddingService()
        engine = VectorFoldingEngine(embedding_service=svc)
        r1 = engine.fold("same text")
        r2 = engine.fold("same text")
        assert r1["id"] == r2["id"]
        assert np.allclose(r1["vector"], r2["vector"])


class TestVectorFoldingFallback:
    def test_fallback_mode(self):
        engine = VectorFoldingEngine()
        result = engine.fold("test content")
        assert result["metadata"]["embed_mode"] == "fallback"
        assert len(result["vector"]) == 384

    def test_fallback_deterministic(self):
        engine = VectorFoldingEngine()
        r1 = engine.embed(["hello"])
        r2 = engine.embed(["hello"])
        assert np.allclose(r1, r2)

    def test_different_inputs_different_vectors(self):
        engine = VectorFoldingEngine()
        r1 = engine.embed(["hello"])
        r2 = engine.embed(["world"])
        assert not np.allclose(r1, r2)


class TestVectorFoldingChunking:
    def test_source_code_chunking(self):
        code = "import os\n\ndef foo():\n    pass\n\ndef bar():\n    pass"
        engine = VectorFoldingEngine()
        result = engine.fold(code, content_type="source_code")
        assert result["metadata"]["chunk_count"] >= 2

    def test_document_chunking(self):
        doc = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        engine = VectorFoldingEngine()
        result = engine.fold(doc, content_type="document")
        assert result["metadata"]["chunk_count"] == 3

    def test_empty_content(self):
        engine = VectorFoldingEngine()
        result = engine.fold("")
        assert "vector" in result


class TestWALWriter:
    def test_wal_creates_file(self, tmp_path):
        wal = WALWriter(wal_dir=str(tmp_path))
        wal.append("insert", {"id": "test-1", "data": "hello"})
        wal.close()
        files = list(tmp_path.glob("wal-*.jsonl"))
        assert len(files) == 1

    def test_wal_writes_json_lines(self, tmp_path):
        wal = WALWriter(wal_dir=str(tmp_path))
        wal.append("insert", {"id": "test-1"})
        wal.append("update", {"id": "test-2"})
        wal.close()
        files = list(tmp_path.glob("wal-*.jsonl"))
        with open(files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 2
        for line in lines:
            parsed = json.loads(line)
            assert "op" in parsed
            assert "entry" in parsed

    def test_wal_replay(self, tmp_path):
        wal = WALWriter(wal_dir=str(tmp_path))
        wal.append("insert", {"id": "a"})
        wal.append("insert", {"id": "b"})
        wal.close()
        wal2 = WALWriter(wal_dir=str(tmp_path))
        entries = wal2.replay()
        assert len(entries) == 2
        wal2.close()

    def test_wal_entries_count(self, tmp_path):
        wal = WALWriter(wal_dir=str(tmp_path))
        wal.append("insert", {"id": "x"})
        wal.append("insert", {"id": "y"})
        assert wal.entries_written == 2
        wal.close()


class TestRealtimeIndexWAL:
    def test_upsert_writes_wal(self, tmp_path):
        idx = RealtimeIndexUpdater(wal_dir=str(tmp_path), enable_wal=True)
        idx.upsert("e1", vector=[1.0, 2.0, 3.0], text="hello")
        idx.upsert("e2", vector=[4.0, 5.0, 6.0], text="world")
        stats = idx.get_stats()
        assert stats["wal_entries"] == 2
        assert stats["inserts"] == 2

    def test_recover_from_wal(self, tmp_path):
        idx1 = RealtimeIndexUpdater(wal_dir=str(tmp_path), enable_wal=True)
        idx1.upsert("e1", vector=[1.0, 2.0], text="hello")
        idx1.upsert("e2", vector=[3.0, 4.0], text="world")
        # Simulate crash: create new instance
        idx2 = RealtimeIndexUpdater(wal_dir=str(tmp_path), enable_wal=True)
        recovered = idx2.recover_from_wal()
        assert recovered == 2
        assert idx2.get("e1") is not None
        assert idx2.get("e2") is not None

    def test_delete_in_wal_recovery(self, tmp_path):
        idx1 = RealtimeIndexUpdater(wal_dir=str(tmp_path), enable_wal=True)
        idx1.upsert("e1", vector=[1.0], text="a")
        idx1.upsert("e2", vector=[2.0], text="b")
        idx1.delete("e1")
        idx2 = RealtimeIndexUpdater(wal_dir=str(tmp_path), enable_wal=True)
        idx2.recover_from_wal()
        assert idx2.get("e1") is None
        assert idx2.get("e2") is not None

    def test_no_wal_mode(self):
        idx = RealtimeIndexUpdater(enable_wal=False)
        idx.upsert("e1", vector=[1.0], text="test")
        assert idx.get("e1") is not None
        stats = idx.get_stats()
        assert stats["wal_entries"] == 0

    def test_search_cache(self):
        idx = RealtimeIndexUpdater(enable_wal=False)
        idx.upsert("e1", vector=[1.0, 0.0, 0.0])
        idx.upsert("e2", vector=[0.0, 1.0, 0.0])
        results = idx.search_cache([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "e1"
