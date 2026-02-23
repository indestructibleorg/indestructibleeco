"""Lightweight AI Service proto stubs (no grpc dependency required).

URI: eco-base://backend/shared/proto/generated/ai_service_pb2

Matches the message definitions in backend/shared/proto/ai_service.proto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GenerateRequest:
    model_id: str = ""
    prompt: str = ""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = False


@dataclass
class GenerateResponse:
    request_id: str = ""
    text: str = ""
    model_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0


@dataclass
class StreamChunk:
    request_id: str = ""
    delta: str = ""
    finish_reason: str = ""
    index: int = 0


@dataclass
class EmbeddingRequest:
    texts: List[str] = field(default_factory=list)
    model_id: str = "BAAI/bge-large-en-v1.5"
    dimensions: int = 1024


@dataclass
class EmbeddingResponse:
    request_id: str = ""
    embeddings: List[List[float]] = field(default_factory=list)
    model_id: str = ""
    dimensions: int = 0
    total_tokens: int = 0


@dataclass
class HealthCheckRequest:
    service: str = ""


@dataclass
class HealthCheckResponse:
    status: str = "SERVING"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
