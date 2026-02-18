"""Centralized configuration for AI Engine Service."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI service configuration loaded from environment variables."""

    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Data stores
    database_url: str = "postgresql://eco_admin:eco_dev_secret@localhost:5432/indestructibleeco"
    redis_url: str = "redis://localhost:6379"
    elasticsearch_url: str = "http://localhost:9200"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "eco_graph_secret"
    kafka_brokers: str = "localhost:9092"

    # FAISS
    faiss_index_path: str = "/data/faiss"
    faiss_dimension: int = 1024
    faiss_nprobe: int = 32

    # Vector model
    vector_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimensions: int = 384
    vector_tolerance_min: float = 0.0001
    vector_tolerance_max: float = 0.005

    # gRPC
    grpc_port: int = 50051

    # Rate limiting
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 60

    model_config = {"env_prefix": "ECO_", "env_file": ".env", "extra": "ignore"}


settings = Settings()