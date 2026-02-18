"""AI Service configuration — environment-driven, zero hardcoded secrets."""

import os
from typing import List


class Settings:
    environment: str = os.getenv("NODE_ENV", "development")
    http_port: int = int(os.getenv("HTTP_PORT", "8001"))
    grpc_port: int = int(os.getenv("GRPC_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Models
    ai_models: List[str] = os.getenv("AI_MODELS", "vllm,ollama,tgi,sglang").split(",")

    # Redis / Celery
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    celery_broker: str = os.getenv("CELERY_BROKER", "redis://localhost:6379/0")
    celery_backend: str = os.getenv("CELERY_BACKEND", "redis://localhost:6379/1")

    # Vector Alignment
    vector_dim: int = int(os.getenv("VECTOR_DIM", "1024"))
    alignment_model: str = os.getenv("ALIGNMENT_MODEL", "quantum-bert-xxl-v1")
    alignment_tolerance: float = float(os.getenv("ALIGNMENT_TOLERANCE", "0.001"))

    # CORS
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")

    # Service Discovery
    consul_endpoint: str = os.getenv("CONSUL_ENDPOINT", "http://localhost:8500")

    # Tracing
    jaeger_endpoint: str = os.getenv(
        "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
    )


settings = Settings()