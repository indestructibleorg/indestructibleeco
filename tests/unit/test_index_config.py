"""Unit tests for index engine configuration (Step 21)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFaissConfig:
    def test_faiss_defaults(self):
        from backend.ai.src.config import Settings
        s = Settings()
        assert s.faiss_enabled is True
        assert s.faiss_index_type == "IVFFlat"
        assert s.faiss_nprobe == 16
        assert s.faiss_nlist == 256
        assert s.faiss_use_gpu is False
        assert s.faiss_persist_dir == "/tmp/eco-faiss"

    def test_faiss_env_override(self, monkeypatch):
        monkeypatch.setenv("ECO_FAISS_ENABLED", "false")
        monkeypatch.setenv("ECO_FAISS_INDEX_TYPE", "HNSW")
        monkeypatch.setenv("ECO_FAISS_NPROBE", "32")
        from importlib import reload
        import backend.ai.src.config as cfg
        reload(cfg)
        s = cfg.Settings()
        assert s.faiss_enabled is False
        assert s.faiss_index_type == "HNSW"
        assert s.faiss_nprobe == 32
        reload(cfg)  # restore


class TestElasticsearchConfig:
    def test_es_defaults(self):
        from backend.ai.src.config import Settings
        s = Settings()
        assert s.es_enabled is False
        assert s.es_hosts == ["http://localhost:9200"]
        assert s.es_index_prefix == "eco-vectors"
        assert s.es_timeout == 30
        assert s.es_max_retries == 3
        assert s.es_verify_certs is True

    def test_es_env_override(self, monkeypatch):
        monkeypatch.setenv("ECO_ES_ENABLED", "true")
        monkeypatch.setenv("ECO_ES_HOSTS", "http://es1:9200,http://es2:9200")
        from importlib import reload
        import backend.ai.src.config as cfg
        reload(cfg)
        s = cfg.Settings()
        assert s.es_enabled is True
        assert len(s.es_hosts) == 2
        reload(cfg)


class TestNeo4jConfig:
    def test_neo4j_defaults(self):
        from backend.ai.src.config import Settings
        s = Settings()
        assert s.neo4j_enabled is False
        assert s.neo4j_uri == "bolt://localhost:7687"
        assert s.neo4j_username == "neo4j"
        assert s.neo4j_database == "neo4j"
        assert s.neo4j_max_connection_pool_size == 50

    def test_neo4j_env_override(self, monkeypatch):
        monkeypatch.setenv("ECO_NEO4J_ENABLED", "true")
        monkeypatch.setenv("ECO_NEO4J_URI", "bolt://neo4j-prod:7687")
        monkeypatch.setenv("ECO_NEO4J_POOL_SIZE", "100")
        from importlib import reload
        import backend.ai.src.config as cfg
        reload(cfg)
        s = cfg.Settings()
        assert s.neo4j_enabled is True
        assert s.neo4j_uri == "bolt://neo4j-prod:7687"
        assert s.neo4j_max_connection_pool_size == 100
        reload(cfg)


class TestExistingConfigPreserved:
    def test_core_settings(self):
        from backend.ai.src.config import Settings
        s = Settings()
        assert s.http_port == 8001
        assert s.grpc_port == 8000
        assert s.vector_dim == 1024
        assert s.alignment_model == "BAAI/bge-large-en-v1.5"
        assert s.redis_url == "redis://localhost:6379"
