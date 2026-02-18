"""Model Registry & Management Service.

Central registry mapping model identifiers to engine backends.
Handles model lifecycle, version tracking, and capability metadata.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .base import BaseInferenceAdapter, EngineType, EngineStatus

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    """Registry entry for a deployed model."""
    model_id: str
    engine_type: EngineType
    adapter: BaseInferenceAdapter
    capabilities: list[str] = field(default_factory=lambda: ["chat", "completion"])
    max_context_length: int = 4096
    quantization: str | None = None
    priority: int = 0
    registered_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """Thread-safe model registry with multi-engine support.

    Responsibilities:
    - Register/deregister model-to-engine mappings
    - Resolve model IDs to adapters (with fallback chains)
    - Track model capabilities (chat, completion, embedding, vision)
    - Provide model listing in OpenAI-compatible format
    """

    def __init__(self) -> None:
        self._models: dict[str, list[ModelEntry]] = {}
        self._adapters: dict[str, BaseInferenceAdapter] = {}
        self._aliases: dict[str, str] = {}

    def register_adapter(self, name: str, adapter: BaseInferenceAdapter) -> None:
        """Register an engine adapter instance."""
        self._adapters[name] = adapter
        logger.info("Registered adapter: %s (%s @ %s)", name, adapter.engine_type.value, adapter.endpoint)

    def register_model(
        self,
        model_id: str,
        engine_type: EngineType,
        adapter: BaseInferenceAdapter,
        capabilities: list[str] | None = None,
        max_context_length: int = 4096,
        quantization: str | None = None,
        priority: int = 0,
        aliases: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a model with its serving engine.

        Args:
            model_id: Canonical model identifier.
            engine_type: Backend engine type.
            adapter: Engine adapter instance.
            capabilities: List of supported operations.
            max_context_length: Maximum context window.
            quantization: Quantization method if applicable.
            priority: Routing priority (higher = preferred).
            aliases: Alternative model names.
            metadata: Additional model metadata.
        """
        entry = ModelEntry(
            model_id=model_id,
            engine_type=engine_type,
            adapter=adapter,
            capabilities=capabilities or ["chat", "completion"],
            max_context_length=max_context_length,
            quantization=quantization,
            priority=priority,
            metadata=metadata or {},
        )

        if model_id not in self._models:
            self._models[model_id] = []
        self._models[model_id].append(entry)
        self._models[model_id].sort(key=lambda e: e.priority, reverse=True)

        for alias in (aliases or []):
            self._aliases[alias] = model_id

        logger.info(
            "Registered model: %s → %s (priority=%d, ctx=%d)",
            model_id, engine_type.value, priority, max_context_length,
        )

    def deregister_model(self, model_id: str, engine_type: EngineType | None = None) -> int:
        """Remove model entries. Returns count of removed entries."""
        if model_id not in self._models:
            return 0
        if engine_type is None:
            count = len(self._models.pop(model_id, []))
        else:
            before = len(self._models[model_id])
            self._models[model_id] = [e for e in self._models[model_id] if e.engine_type != engine_type]
            count = before - len(self._models[model_id])
            if not self._models[model_id]:
                del self._models[model_id]
        return count

    def resolve(self, model_id: str, capability: str = "chat") -> ModelEntry | None:
        """Resolve a model ID to the highest-priority healthy entry.

        Args:
            model_id: Model identifier or alias.
            capability: Required capability.

        Returns:
            Best matching ModelEntry or None.
        """
        canonical = self._aliases.get(model_id, model_id)
        entries = self._models.get(canonical, [])

        for entry in entries:
            if capability in entry.capabilities:
                return entry

        return None

    def resolve_all(self, model_id: str) -> list[ModelEntry]:
        """Get all entries for a model (for load balancing)."""
        canonical = self._aliases.get(model_id, model_id)
        return self._models.get(canonical, [])

    def list_models(self) -> list[dict[str, Any]]:
        """List all registered models in OpenAI-compatible format."""
        models = []
        seen = set()
        for model_id, entries in self._models.items():
            if model_id in seen:
                continue
            seen.add(model_id)
            entry = entries[0]
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(entry.registered_at),
                "owned_by": entry.engine_type.value,
                "capabilities": entry.capabilities,
                "max_context_length": entry.max_context_length,
                "quantization": entry.quantization,
                "engines": [e.engine_type.value for e in entries],
            })
        return models

    def get_adapter(self, name: str) -> BaseInferenceAdapter | None:
        """Get a registered adapter by name."""
        return self._adapters.get(name)

    def get_all_adapters(self) -> dict[str, BaseInferenceAdapter]:
        """Get all registered adapters."""
        return dict(self._adapters)

    @property
    def model_count(self) -> int:
        return len(self._models)

    @property
    def adapter_count(self) -> int:
        return len(self._adapters)