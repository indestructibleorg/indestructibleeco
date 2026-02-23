"""Governance Engine — GL enforcement, audit trail, schema validation.

URI: eco-base://backend/ai/src/governance

Enforces:
- UUID v1 for all identifiers
- URI/URN dual identification on all resources
- .qyaml 4-block governance compliance (via YAML parsing)
- Vector alignment via BAAI/bge-large-en-v1.5
- Persistent audit log (append-only JSONL file + in-memory ring buffer)
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import settings

logger = logging.getLogger("governance")

_REQUIRED_BLOCKS = frozenset([
    "document_metadata",
    "governance_info",
    "registry_binding",
    "vector_alignment_map",
])

_REQUIRED_METADATA_FIELDS = frozenset([
    "unique_id", "uri", "urn", "target_system",
    "schema_version", "generated_by", "created_at",
])

_GOVERNANCE_REQUIRED_FIELDS = frozenset([
    "owner", "compliance_tags", "lifecycle_policy",
])

_REGISTRY_REQUIRED_FIELDS = frozenset([
    "service_endpoint", "health_check_path",
])

_VECTOR_REQUIRED_FIELDS = frozenset([
    "alignment_model", "coherence_vector_dim",
])


class AuditPersistence:
    """Append-only JSONL audit log writer with rotation."""

    def __init__(self, log_dir: str = "", max_file_bytes: int = 10 * 1024 * 1024) -> None:
        self._log_dir = log_dir or os.environ.get(
            "ECO_AUDIT_LOG_DIR",
            os.path.join(os.getcwd(), ".eco-audit"),
        )
        self._max_file_bytes = max_file_bytes
        self._current_file: Optional[Any] = None
        self._current_path: Optional[Path] = None
        self._initialized = False

    def _ensure_dir(self) -> None:
        if not self._initialized:
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)
            self._initialized = True

    def _rotate_if_needed(self) -> None:
        if self._current_path and self._current_path.exists():
            if self._current_path.stat().st_size >= self._max_file_bytes:
                if self._current_file:
                    self._current_file.close()
                    self._current_file = None
                    self._current_path = None

    def _get_file(self) -> Any:
        self._ensure_dir()
        self._rotate_if_needed()
        if self._current_file is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            uid = uuid.uuid1().hex[:8]
            fname = f"audit-{ts}-{uid}.jsonl"
            self._current_path = Path(self._log_dir) / fname
            self._current_file = open(self._current_path, "a", encoding="utf-8")
        return self._current_file

    def append(self, entry: Dict[str, Any]) -> None:
        try:
            fh = self._get_file()
            fh.write(json.dumps(entry, default=str) + "\n")
            fh.flush()
        except Exception as exc:
            logger.warning(f"Audit persistence write failed: {exc}")

    def close(self) -> None:
        if self._current_file:
            try:
                self._current_file.close()
            except Exception:
                pass
            self._current_file = None


class GovernanceEngine:
    """Central governance enforcement for AI service."""

    def __init__(self, audit_dir: str = "", persist: bool = True) -> None:
        self._engine_map: Dict[str, str] = {
            "vllm": "vllm_adapter",
            "ollama": "ollama_adapter",
            "tgi": "tgi_adapter",
            "sglang": "sglang_adapter",
            "tensorrt": "tensorrt_adapter",
            "deepspeed": "deepspeed_adapter",
            "lmdeploy": "lmdeploy_adapter",
        }
        self._audit_log: List[Dict[str, Any]] = []
        self._persist = persist
        self._persistence: Optional[AuditPersistence] = None
        if persist:
            self._persistence = AuditPersistence(log_dir=audit_dir)

    def resolve_engine(self, model_id: str) -> str:
        """Resolve model_id to engine adapter name."""
        provider = model_id.split("-")[0] if "-" in model_id else model_id
        engine = self._engine_map.get(provider)
        if not engine:
            engine = self._engine_map.get(settings.ai_models[0], "vllm_adapter")
        self._audit("engine_resolve", {"model_id": model_id, "engine": engine})
        return engine

    def validate_qyaml(self, content: str) -> Dict[str, Any]:
        """Validate .qyaml content against governance schema using YAML parsing.

        Performs structural validation by parsing YAML into a dict tree,
        then checking for required blocks, fields, and semantic constraints.
        Falls back to string-based checks only if YAML parsing fails entirely.
        """
        errors: List[Dict[str, str]] = []
        parsed: Optional[Dict[str, Any]] = None

        # --- Phase 1: Parse YAML ---
        try:
            docs = list(yaml.safe_load_all(content))
            if not docs:
                errors.append({
                    "path": "/",
                    "message": "Empty YAML document",
                    "severity": "error",
                })
            else:
                parsed = {}
                for doc in docs:
                    if isinstance(doc, dict):
                        parsed.update(doc)
        except yaml.YAMLError as exc:
            errors.append({
                "path": "/",
                "message": f"YAML parse error: {exc}",
                "severity": "error",
            })

        # --- Phase 2: Structural block validation ---
        if parsed is not None:
            for block in _REQUIRED_BLOCKS:
                if block not in parsed:
                    errors.append({
                        "path": block,
                        "message": f"Missing mandatory governance block: {block}",
                        "severity": "error",
                    })

            # --- Phase 3: Field-level validation per block ---
            doc_meta = parsed.get("document_metadata")
            if isinstance(doc_meta, dict):
                for field in _REQUIRED_METADATA_FIELDS:
                    if field not in doc_meta:
                        errors.append({
                            "path": f"document_metadata.{field}",
                            "message": f"Missing required field: {field}",
                            "severity": "error",
                        })
                # URI format check
                uri_val = doc_meta.get("uri", "")
                if uri_val and not str(uri_val).startswith("eco-base://"):
                    errors.append({
                        "path": "document_metadata.uri",
                        "message": f"URI must start with 'eco-base://', got: {uri_val}",
                        "severity": "error",
                    })
                # URN format check
                urn_val = doc_meta.get("urn", "")
                if urn_val and not str(urn_val).startswith("urn:eco-base:"):
                    errors.append({
                        "path": "document_metadata.urn",
                        "message": f"URN must start with 'urn:eco-base:', got: {urn_val}",
                        "severity": "error",
                    })
                # UUID v1 format check
                uid_val = doc_meta.get("unique_id", "")
                if uid_val:
                    try:
                        parsed_uuid = uuid.UUID(str(uid_val))
                        if parsed_uuid.version != 1:
                            errors.append({
                                "path": "document_metadata.unique_id",
                                "message": f"unique_id must be UUID v1, got version {parsed_uuid.version}",
                                "severity": "warning",
                            })
                    except (ValueError, AttributeError):
                        errors.append({
                            "path": "document_metadata.unique_id",
                            "message": f"unique_id is not a valid UUID: {uid_val}",
                            "severity": "error",
                        })
                # schema_version check
                sv = doc_meta.get("schema_version", "")
                if sv and sv not in ("v1", "v2"):
                    errors.append({
                        "path": "document_metadata.schema_version",
                        "message": f"Unsupported schema_version: {sv}",
                        "severity": "warning",
                    })
            elif "document_metadata" in (parsed or {}):
                errors.append({
                    "path": "document_metadata",
                    "message": "document_metadata must be a mapping",
                    "severity": "error",
                })

            gov_info = parsed.get("governance_info")
            if isinstance(gov_info, dict):
                for field in _GOVERNANCE_REQUIRED_FIELDS:
                    if field not in gov_info:
                        errors.append({
                            "path": f"governance_info.{field}",
                            "message": f"Missing required field: {field}",
                            "severity": "error",
                        })

            reg_bind = parsed.get("registry_binding")
            if isinstance(reg_bind, dict):
                for field in _REGISTRY_REQUIRED_FIELDS:
                    if field not in reg_bind:
                        errors.append({
                            "path": f"registry_binding.{field}",
                            "message": f"Missing required field: {field}",
                            "severity": "error",
                        })

            vec_map = parsed.get("vector_alignment_map")
            if isinstance(vec_map, dict):
                for field in _VECTOR_REQUIRED_FIELDS:
                    if field not in vec_map:
                        errors.append({
                            "path": f"vector_alignment_map.{field}",
                            "message": f"Missing required field: {field}",
                            "severity": "error",
                        })

        # --- Phase 4: GKE compatibility (string-level) ---
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("%YAML"):
                errors.append({
                    "path": f"line:{i}",
                    "message": "GKE incompatible: %YAML directive detected \u2014 must be removed",
                    "severity": "error",
                })

        # --- Phase 5: Semantic warnings (parsed or fallback string) ---
        if parsed is not None:
            if not any(
                "eco-base://" in str(v)
                for v in _deep_values(parsed)
            ):
                errors.append({
                    "path": "metadata.uri",
                    "message": "No URI identifier found in document",
                    "severity": "warning",
                })
            if not any(
                "urn:eco-base:" in str(v)
                for v in _deep_values(parsed)
            ):
                errors.append({
                    "path": "metadata.urn",
                    "message": "No URN identifier found in document",
                    "severity": "warning",
                })
        else:
            if "eco-base://" not in content:
                errors.append({
                    "path": "metadata.uri",
                    "message": "No URI identifier found",
                    "severity": "warning",
                })
            if "urn:eco-base:" not in content:
                errors.append({
                    "path": "metadata.urn",
                    "message": "No URN identifier found",
                    "severity": "warning",
                })

        valid = len([e for e in errors if e["severity"] == "error"]) == 0
        self._audit("qyaml_validate", {"valid": valid, "error_count": len(errors)})

        return {"valid": valid, "errors": errors}

    def stamp_governance(
        self,
        name: str,
        namespace: str = "eco-base",
        kind: str = "Deployment",
        target_system: str = "gke-production",
        cross_layer_binding: Optional[List[str]] = None,
        function_keywords: Optional[List[str]] = None,
        owner: str = "platform-team",
    ) -> Dict[str, Any]:
        """Generate complete governance stamp with UUID v1, URI, URN."""
        uid = uuid.uuid1()
        uri = f"eco-base://k8s/{namespace}/{kind.lower()}/{name}"
        urn = f"urn:eco-base:k8s:{namespace}:{kind.lower()}:{name}:{uid}"
        bindings = cross_layer_binding or []
        keywords = function_keywords or [name, kind.lower()]

        stamp = {
            "document_metadata": {
                "unique_id": str(uid),
                "uri": uri,
                "urn": urn,
                "target_system": target_system,
                "cross_layer_binding": bindings,
                "schema_version": "v1",
                "generated_by": "yaml-toolkit-v1",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "governance_info": {
                "owner": owner,
                "approval_chain": [owner],
                "compliance_tags": ["zero-trust", "soc2", "internal"],
                "lifecycle_policy": "active",
            },
            "registry_binding": {
                "service_endpoint": f"http://{name}.{namespace}.svc.cluster.local",
                "discovery_protocol": "consul",
                "health_check_path": "/health",
                "registry_ttl": 30,
            },
            "vector_alignment_map": {
                "alignment_model": settings.alignment_model,
                "coherence_vector_dim": settings.vector_dim,
                "function_keyword": keywords,
                "contextual_binding": f"{name} -> [{', '.join(bindings)}]",
            },
        }

        self._audit("governance_stamp", {"uid": str(uid), "name": name, "kind": kind})
        return stamp

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return audit trail."""
        return self._audit_log.copy()

    def close(self) -> None:
        """Flush and close persistent audit log."""
        if self._persistence:
            self._persistence.close()

    def _audit(self, action: str, details: Dict[str, Any]) -> None:
        """Record audit entry with UUID v1 timestamp — in-memory + persistent."""
        entry = {
            "id": str(uuid.uuid1()),
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uri": f"eco-base://governance/audit/{action}",
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
        if self._persistence:
            self._persistence.append(entry)
        logger.info(f"AUDIT: {action} — {details}")


def _deep_values(obj: Any) -> List[Any]:
    """Recursively extract all leaf values from nested dict/list."""
    results: List[Any] = []
    if isinstance(obj, dict):
        for v in obj.values():
            results.extend(_deep_values(v))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_deep_values(item))
    else:
        results.append(obj)
    return results
