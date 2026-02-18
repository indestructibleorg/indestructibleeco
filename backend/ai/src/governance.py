"""Governance Engine — GL enforcement, audit trail, schema validation.

Enforces:
- UUID v1 for all identifiers
- URI/URN dual identification on all resources
- .qyaml 4-block governance compliance
- Vector alignment via quantum-bert-xxl-v1
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger("governance")


class GovernanceEngine:
    """Central governance enforcement for AI service."""

    def __init__(self):
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

    def resolve_engine(self, model_id: str) -> str:
        """Resolve model_id to engine adapter name."""
        provider = model_id.split("-")[0] if "-" in model_id else model_id
        engine = self._engine_map.get(provider)
        if not engine:
            engine = self._engine_map.get(settings.ai_models[0], "vllm_adapter")
        self._audit("engine_resolve", {"model_id": model_id, "engine": engine})
        return engine

    def validate_qyaml(self, content: str) -> Dict[str, Any]:
        """Validate .qyaml content against governance schema."""
        errors: List[Dict[str, str]] = []

        required_blocks = [
            "document_metadata",
            "governance_info",
            "registry_binding",
            "vector_alignment_map",
        ]
        for block in required_blocks:
            if f"{block}:" not in content:
                errors.append({
                    "path": block,
                    "message": f"Missing mandatory governance block: {block}",
                    "severity": "error",
                })

        required_fields = [
            "unique_id", "uri", "urn", "target_system",
            "schema_version", "generated_by", "created_at",
        ]
        for field in required_fields:
            if f"{field}:" not in content:
                errors.append({
                    "path": f"document_metadata.{field}",
                    "message": f"Missing required field: {field}",
                    "severity": "error",
                })

        if "%YAML" in content:
            errors.append({
                "path": "header",
                "message": "GKE incompatible: %YAML directive detected — must be removed",
                "severity": "error",
            })

        if "indestructibleeco://" not in content:
            errors.append({
                "path": "metadata.uri",
                "message": "No URI identifier found",
                "severity": "warning",
            })

        if "urn:indestructibleeco:" not in content:
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
        namespace: str = "indestructibleeco",
        kind: str = "Deployment",
        target_system: str = "gke-production",
        cross_layer_binding: Optional[List[str]] = None,
        function_keywords: Optional[List[str]] = None,
        owner: str = "platform-team",
    ) -> Dict[str, Any]:
        """Generate complete governance stamp with UUID v1, URI, URN."""
        uid = uuid.uuid1()
        uri = f"indestructibleeco://k8s/{namespace}/{kind.lower()}/{name}"
        urn = f"urn:indestructibleeco:k8s:{namespace}:{kind.lower()}:{name}:{uid}"
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

    def _audit(self, action: str, details: Dict[str, Any]) -> None:
        """Record audit entry with UUID v1 timestamp."""
        entry = {
            "id": str(uuid.uuid1()),
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uri": f"indestructibleeco://governance/audit/{action}",
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
        logger.info(f"AUDIT: {action} — {details}")