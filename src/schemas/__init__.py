"""IndestructibleEco v1.0 — Pydantic Schemas Package.

URI: indestructibleeco://src/schemas
"""

from .auth import APIKeyCreate, APIKeyInfo, APIKeyResult, UserRole
from .inference import (
    BatchInferenceRequest,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ChatRole,
    CompletionRequest,
    EmbeddingRequest,
    StreamChunk,
    UsageInfo,
)
from .models import (
    ModelCapability,
    ModelFormat,
    ModelHardwareRequirements,
    ModelInfo,
    ModelRegisterRequest,
    ModelStatus,
    QuantizationConfig,
)

__all__ = [
    "APIKeyCreate",
    "APIKeyInfo",
    "APIKeyResult",
    "UserRole",
    "BatchInferenceRequest",
    "ChatCompletionChoice",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatMessage",
    "ChatRole",
    "CompletionRequest",
    "EmbeddingRequest",
    "StreamChunk",
    "UsageInfo",
    "ModelCapability",
    "ModelFormat",
    "ModelHardwareRequirements",
    "ModelInfo",
    "ModelRegisterRequest",
    "ModelStatus",
    "QuantizationConfig",
]