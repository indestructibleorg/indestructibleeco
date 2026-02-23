"""eco-base AI Service configuration — environment-driven, zero hardcoded secrets.

URI: eco-base://backend/ai/config
All environment variables use the ECO_* prefix for namespace isolation.
"""

import os
from typing import List


class Settings:
    # ── Application ───────────────────────────────────────────────────
    environment: str = os.getenv("ECO_ENVIRONMENT", "development")
    http_port: int = int(os.getenv("ECO_AI_HTTP_PORT", "8001"))
    grpc_port: int = int(os.getenv("ECO_AI_GRPC_PORT", "8000"))
    log_level: str = os.getenv("ECO_LOG_LEVEL", "info")

    # ── Inference Models ──────────────────────────────────────────────
    ai_models: List[str] = os.getenv("ECO_AI_MODELS", "vllm,ollama,tgi,sglang").split(",")

    # ── Redis / Celery ────────────────────────────────────────────────
    redis_url: str = os.getenv("ECO_REDIS_URL", "redis://localhost:6379")
    celery_broker: str = os.getenv("ECO_CELERY_BROKER", "redis://localhost:6379/0")
    celery_backend: str = os.getenv("ECO_CELERY_BACKEND", "redis://localhost:6379/1")

    # ── Vector Alignment ──────────────────────────────────────────────
    vector_dim: int = int(os.getenv("ECO_VECTOR_DIM", "1024"))
    alignment_model: str = os.getenv("ECO_ALIGNMENT_MODEL", "BAAI/bge-large-en-v1.5")
    alignment_tolerance: float = float(os.getenv("ECO_ALIGNMENT_TOLERANCE", "0.001"))

    # ── FAISS Index ───────────────────────────────────────────────────
    faiss_enabled: bool = os.getenv("ECO_FAISS_ENABLED", "true").lower() == "true"
    faiss_index_type: str = os.getenv("ECO_FAISS_INDEX_TYPE", "IVFFlat")
    faiss_nprobe: int = int(os.getenv("ECO_FAISS_NPROBE", "16"))
    faiss_nlist: int = int(os.getenv("ECO_FAISS_NLIST", "256"))
    faiss_use_gpu: bool = os.getenv("ECO_FAISS_USE_GPU", "false").lower() == "true"
    faiss_persist_dir: str = os.getenv("ECO_FAISS_PERSIST_DIR", "/tmp/eco-faiss")

    # ── Elasticsearch Index ───────────────────────────────────────────
    es_enabled: bool = os.getenv("ECO_ES_ENABLED", "false").lower() == "true"
    es_hosts: List[str] = os.getenv("ECO_ES_HOSTS", "http://localhost:9200").split(",")
    es_index_prefix: str = os.getenv("ECO_ES_INDEX_PREFIX", "eco-vectors")
    es_username: str = os.getenv("ECO_ES_USERNAME", "")
    es_password: str = os.getenv("ECO_ES_PASSWORD", "")
    es_verify_certs: bool = os.getenv("ECO_ES_VERIFY_CERTS", "true").lower() == "true"
    es_timeout: int = int(os.getenv("ECO_ES_TIMEOUT", "30"))
    es_max_retries: int = int(os.getenv("ECO_ES_MAX_RETRIES", "3"))

    # ── Neo4j Index ───────────────────────────────────────────────────
    neo4j_enabled: bool = os.getenv("ECO_NEO4J_ENABLED", "false").lower() == "true"
    neo4j_uri: str = os.getenv("ECO_NEO4J_URI", "bolt://localhost:7687")
    neo4j_username: str = os.getenv("ECO_NEO4J_USERNAME", "neo4j")
    neo4j_password: str = os.getenv("ECO_NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("ECO_NEO4J_DATABASE", "neo4j")
    neo4j_max_connection_pool_size: int = int(os.getenv("ECO_NEO4J_POOL_SIZE", "50"))

    # ── CORS ──────────────────────────────────────────────────────────
    cors_origins: List[str] = os.getenv(
        "ECO_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")

    # ── Service Discovery ─────────────────────────────────────────────
    consul_endpoint: str = os.getenv("ECO_CONSUL_ENDPOINT", "http://localhost:8500")

    # ── Tracing ───────────────────────────────────────────────────────
    jaeger_endpoint: str = os.getenv(
        "ECO_JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
    )


settings = Settings()
