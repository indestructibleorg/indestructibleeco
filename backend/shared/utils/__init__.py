"""Shared utilities for eco-base platform."""

from uuid import UUID, uuid1
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json


def new_uuid() -> UUID:
    """Generate UUID v1 (time-based, sortable, traceable)."""
    return uuid1()


def new_uuid_str() -> str:
    """Generate UUID v1 as string."""
    return str(uuid1())


def build_uri(domain: str, kind: str, name: str) -> str:
    """Build eco-base URI.

    Format: eco-base://{domain}/{kind}/{name}
    Example: eco-base://k8s/deployment/api-service
    """
    return f"eco-base://{domain}/{kind}/{name}"


def build_urn(domain: str, kind: str, name: str, uid: UUID) -> str:
    """Build eco-base URN.

    Format: urn:eco-base:{domain}:{kind}:{name}:{uuid}
    Example: urn:eco-base:k8s:deployment:api-service:550e8400-e29b-41d4-a716-446655440000
    """
    return f"urn:eco-base:{domain}:{kind}:{name}:{uid}"


def build_k8s_uri(namespace: str, kind: str, name: str) -> str:
    """Build K8s resource URI.

    Format: eco-base://k8s/{namespace}/{kind}/{name}
    """
    return f"eco-base://k8s/{namespace}/{kind}/{name}"


def build_k8s_urn(namespace: str, kind: str, name: str, uid: UUID) -> str:
    """Build K8s resource URN.

    Format: urn:eco-base:k8s:{namespace}:{kind}:{name}:{uuid}
    """
    return f"urn:eco-base:k8s:{namespace}:{kind}:{name}:{uid}"


def governance_stamp() -> Dict[str, Any]:
    """Generate a governance metadata stamp for .qyaml documents."""
    uid = uuid1()
    return {
        "unique_id": str(uid),
        "uri": build_uri("governance", "stamp", str(uid)),
        "urn": build_urn("governance", "stamp", "qyaml", uid),
        "schema_version": "v1",
        "generated_by": "yaml-toolkit-v1",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def compute_content_hash(content: str) -> str:
    """SHA-256 hash of content for integrity verification."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_qyaml_metadata(
    name: str,
    namespace: str,
    kind: str,
    target_system: str,
    owner: str = "platform-team",
    cross_layer_binding: Optional[List[str]] = None,
    compliance_tags: Optional[List[str]] = None,
    function_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build complete .qyaml governance metadata block.

    Returns the four mandatory governance blocks:
    - document_metadata
    - governance_info
    - registry_binding
    - vector_alignment_map
    """
    uid = uuid1()
    uri = build_k8s_uri(namespace, kind, name)
    urn = build_k8s_urn(namespace, kind, name, uid)

    return {
        "document_metadata": {
            "unique_id": str(uid),
            "uri": uri,
            "urn": urn,
            "target_system": target_system,
            "cross_layer_binding": cross_layer_binding or [],
            "schema_version": "v1",
            "generated_by": "yaml-toolkit-v1",
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
        "governance_info": {
            "owner": owner,
            "approval_chain": [owner],
            "compliance_tags": compliance_tags or ["zero-trust", "internal"],
            "lifecycle_policy": "active",
        },
        "registry_binding": {
            "service_endpoint": f"http://{name}.{namespace}.svc.cluster.local",
            "discovery_protocol": "consul",
            "health_check_path": "/health",
            "registry_ttl": 30,
        },
        "vector_alignment_map": {
            "alignment_model": "BAAI/bge-large-en-v1.5",
            "coherence_vector_dim": 1024,
            "function_keyword": function_keywords or [name, kind, namespace],
            "contextual_binding": f"{name} -> [{', '.join(cross_layer_binding or [])}]",
        },
    }