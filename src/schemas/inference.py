"""Inference schemas — OpenAI-compatible chat/completion/embedding contracts.

URI: indestructibleeco://src/schemas/inference

Contracts defined by: tests/unit/test_schemas.py
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str = "default"
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=131072)
    stream: bool = False
    stop: Optional[List[str]] = None
    seed: Optional[int] = None
    engine: Optional[str] = None
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo
    system_fingerprint: Optional[str] = None


class CompletionRequest(BaseModel):
    """Legacy completion request (non-chat)."""

    model: str = "default"
    prompt: Union[str, List[str]] = ""
    max_tokens: int = Field(default=2048, ge=1, le=131072)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    stop: Optional[List[str]] = None
    engine: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Embedding request — single string or list of strings."""

    input: Union[str, List[str]]
    model: str = "default"
    encoding_format: str = "float"
    dimensions: Optional[int] = None


class BatchInferenceRequest(BaseModel):
    """Batch of chat completion requests."""

    batch_id: str = Field(default_factory=lambda: f"batch-{uuid.uuid4().hex[:12]}")
    requests: List[ChatCompletionRequest]
    priority: str = "normal"


class StreamChunk(BaseModel):
    """Single chunk in a streaming response."""

    id: str = ""
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = ""
    choices: List[Dict[str, Any]] = Field(default_factory=list)