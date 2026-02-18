"""IndestructibleEco AI Service configuration — environment-driven, zero hardcoded secrets.

URI: indestructibleeco://backend/ai/config
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
    alignment_model: str = os.getenv("ECO_ALIGNMENT_MODEL", "quantum-bert-xxl-v1")
    alignment_tolerance: float = float(os.getenv("ECO_ALIGNMENT_TOLERANCE", "0.001"))

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