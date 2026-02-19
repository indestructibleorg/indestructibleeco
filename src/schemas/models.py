"""Model management schemas — registration, capabilities, hardware requirements.

URI: indestructibleeco://src/schemas/models

Contracts defined by: tests/unit/test_schemas.py, tests/unit/test_registry.py
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelFormat(str, Enum):
    SAFETENSORS = "safetensors"
    GGUF = "gguf"
    GPTQ = "gptq"
    AWQ = "awq"
    PYTORCH = "pytorch"
    ONNX = "onnx"


class ModelCapability(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CODE_GENERATION = "code_generation"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    REASONING = "reasoning"


class ModelStatus(str, Enum):
    REGISTERED = "registered"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    UNLOADING = "unloading"
    RETIRED = "retired"


class QuantizationConfig(BaseModel):
    method: str = "none"
    bits: int = 16
    group_size: Optional[int] = None
    desc_act: bool = False


class ModelHardwareRequirements(BaseModel):
    min_gpu_memory_gb: float = 0.0
    recommended_gpu_memory_gb: float = 0.0
    min_gpu_count: int = 1
    min_cpu_cores: int = 4
    min_ram_gb: float = 16.0


class ModelRegisterRequest(BaseModel):
    """Request to register a new model in the registry."""

    model_id: str
    source: str = ""
    format: ModelFormat = ModelFormat.SAFETENSORS
    capabilities: List[ModelCapability] = Field(default_factory=lambda: [ModelCapability.CHAT])
    compatible_engines: List[str] = Field(default_factory=lambda: ["vllm"])
    context_length: int = 4096
    parameters_billion: Optional[float] = None
    quantization: Optional[QuantizationConfig] = None
    hardware: Optional[ModelHardwareRequirements] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    """Full model information returned by the registry."""

    model_id: str
    source: str = ""
    format: ModelFormat = ModelFormat.SAFETENSORS
    capabilities: List[ModelCapability] = Field(default_factory=list)
    compatible_engines: List[str] = Field(default_factory=list)
    context_length: int = 4096
    parameters_billion: Optional[float] = None
    quantization: Optional[QuantizationConfig] = None
    hardware: Optional[ModelHardwareRequirements] = None
    status: ModelStatus = ModelStatus.REGISTERED
    loaded_on_engines: List[str] = Field(default_factory=list)
    registered_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)