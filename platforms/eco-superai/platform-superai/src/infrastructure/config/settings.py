"""
SuperAI Platform - Centralized Configuration Management
Pydantic Settings with multi-environment support, validation, and secret management.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = "postgresql+asyncpg://superai:superai_secret@localhost:5432/superai_db"
    url_sync: str = "postgresql://superai:superai_secret@localhost:5432/superai_db"
    pool_size: int = Field(default=20, ge=5, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=5)
    pool_recycle: int = Field(default=3600, ge=300)
    echo: bool = False
    echo_pool: bool = False


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = "redis://localhost:6379/0"
    password: str = "superai_redis_secret"
    max_connections: int = Field(default=50, ge=10)
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)
    retry_on_timeout: bool = True
    decode_responses: bool = True


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY_")

    broker_url: str = "amqp://superai:superai_secret@localhost:5672//"
    result_backend: str = "redis://localhost:6379/1"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 3600
    task_soft_time_limit: int = 3300
    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int = 1000


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = "change-me-in-production-use-openssl-rand-hex-64"
    algorithm: str = "HS256"
    expiration_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_expiration_days: int = Field(default=7, ge=1, le=30)
    issuer: str = "superai-platform"
    audience: str = "superai-users"


class ElasticsearchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ELASTICSEARCH_")

    url: str = "http://localhost:9200"
    index_prefix: str = "superai"
    number_of_shards: int = 1
    number_of_replicas: int = 0
    request_timeout: int = 30


class QuantumSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QUANTUM_")

    backend: str = "aer_simulator"
    shots: int = Field(default=1024, ge=1, le=100000)
    optimization_level: int = Field(default=1, ge=0, le=3)
    ibm_token: str = ""
    ibm_instance: str = ""
    max_circuits_per_batch: int = Field(default=100, ge=1)
    resilience_level: int = Field(default=1, ge=0, le=2)


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_")

    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    chromadb_host: str = "localhost"
    chromadb_port: int = 8100
    vector_dimension: int = 1536
    max_tokens: int = 4096
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_k_results: int = Field(default=10, ge=1, le=100)


class MonitoringSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONITORING_")

    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_port: int = 3000
    jaeger_endpoint: str = "http://localhost:4317"
    tracing_enabled: bool = True
    tracing_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    metrics_prefix: str = "superai"


class CORSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CORS_")

    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    allowed_headers: list[str] = ["*"]
    allow_credentials: bool = True
    max_age: int = 600


class Settings(BaseSettings):
    """Master configuration aggregating all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "SuperAI Platform"
    app_version: str = "1.0.0"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    app_port: int = Field(default=8094, ge=1024, le=65535)
    app_workers: int = Field(default=4, ge=1, le=32)
    app_host: str = "0.0.0.0"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-64"
    log_level: str = "info"
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent

    # --- Sub-settings ---
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    jwt: JWTSettings = JWTSettings()
    elasticsearch: ElasticsearchSettings = ElasticsearchSettings()
    quantum: QuantumSettings = QuantumSettings()
    ai: AISettings = AISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    cors: CORSSettings = CORSSettings()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.lower()

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env == Environment.PRODUCTION:
            if self.secret_key == "change-me-in-production-use-openssl-rand-hex-64":
                raise ValueError("SECRET_KEY must be changed in production")
            if self.app_debug:
                raise ValueError("DEBUG must be False in production")
            if self.jwt.secret_key == "change-me-in-production-use-openssl-rand-hex-64":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.app_env == Environment.TESTING


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()