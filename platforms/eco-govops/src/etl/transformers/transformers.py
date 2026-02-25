"""Concrete transformer implementations for the GovOps ETL pipeline.

Transformers receive Records from extractors, apply mutations (normalisation,
enrichment, filtering, validation), and yield transformed Records downstream.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: etl-transformers
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import structlog

from etl.extractors.base_extractor import Record

logger = structlog.get_logger(__name__)


class BaseTransformer(ABC):
    """Abstract base class for all data transformers."""

    def __init__(self, name: str = "base-transformer") -> None:
        self.name = name
        self._log = logger.bind(transformer=name)
        self._records_in: int = 0
        self._records_out: int = 0
        self._errors: int = 0

    @abstractmethod
    async def transform(self, record: Record) -> Record | None:
        """Transform a single record.

        Return ``None`` to filter the record out of the pipeline.
        """
        ...

    async def transform_batch(self, records: list[Record]) -> list[Record]:
        """Transform a batch of records, filtering out ``None`` results."""
        results: list[Record] = []
        for record in records:
            self._records_in += 1
            try:
                transformed = await self.transform(record)
                if transformed is not None:
                    results.append(transformed)
                    self._records_out += 1
            except Exception as exc:
                self._errors += 1
                self._log.warning("transform_error", error=str(exc))
        return results

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            "transformer": self.name,
            "records_in": self._records_in,
            "records_out": self._records_out,
            "errors": self._errors,
            "drop_rate": round(
                1 - (self._records_out / max(self._records_in, 1)), 4
            ),
        }


class DataTransformer(BaseTransformer):
    """General-purpose data normalisation transformer.

    Applies field mappings, type coercions, and default values.
    """

    def __init__(
        self,
        field_mappings: dict[str, str] | None = None,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name="data-transformer")
        self._field_mappings = field_mappings or {}
        self._defaults = defaults or {}

    async def transform(self, record: Record) -> Record | None:
        data = dict(record.data)

        # Apply field mappings (rename keys)
        for old_key, new_key in self._field_mappings.items():
            if old_key in data:
                data[new_key] = data.pop(old_key)

        # Apply defaults for missing keys
        for key, default in self._defaults.items():
            data.setdefault(key, default)

        # Add transform metadata
        return record.with_data(data).with_metadata(
            {"transformed_at": datetime.now(timezone.utc).isoformat()}
        )


class DataValidator(BaseTransformer):
    """Validates records against a set of required fields and type constraints.

    Records failing validation are filtered out (return ``None``).
    """

    def __init__(
        self,
        required_fields: list[str] | None = None,
        field_types: dict[str, type] | None = None,
    ) -> None:
        super().__init__(name="data-validator")
        self._required_fields = required_fields or []
        self._field_types = field_types or {}

    async def transform(self, record: Record) -> Record | None:
        data = record.data

        # Check required fields
        for field in self._required_fields:
            if field not in data:
                self._log.debug("validation_missing_field", field=field)
                return None

        # Check field types
        for field, expected_type in self._field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                self._log.debug(
                    "validation_type_mismatch",
                    field=field,
                    expected=expected_type.__name__,
                    actual=type(data[field]).__name__,
                )
                return None

        return record.with_metadata({"validated": True})


class GovernanceTransformer(BaseTransformer):
    """Enriches records with governance metadata (GL layer, compliance status).

    Normalises governance-specific fields and computes derived attributes.
    """

    def __init__(self) -> None:
        super().__init__(name="governance-transformer")

    async def transform(self, record: Record) -> Record | None:
        data = dict(record.data)

        # Normalise compliance status
        status = data.get("compliance_status", "unknown")
        if isinstance(status, str):
            data["compliance_status"] = status.lower().strip()

        # Normalise GL layer
        gl_layer = data.get("gl_layer", "")
        if gl_layer and not gl_layer.startswith("GL"):
            data["gl_layer"] = f"GL{gl_layer}"

        # Compute governance flags
        data["is_compliant"] = data.get("compliance_status") in ("compliant", "exempt")
        data["needs_action"] = data.get("compliance_status") in (
            "non_compliant",
            "partially_compliant",
        )

        return record.with_data(data).with_metadata(
            {"governance_enriched": True}
        )
