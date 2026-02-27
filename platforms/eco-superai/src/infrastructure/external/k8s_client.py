"""Kubernetes client -- async cluster introspection and workload management.

Provides a fully async interface for Kubernetes operations.  All blocking
``kubernetes-client`` calls are dispatched to a thread-pool via
``asyncio.to_thread`` so they never block the event loop.

When the ``kubernetes`` package is not installed (or the cluster config is
unreachable) every method degrades gracefully -- returning empty collections
or descriptive error dicts -- so the rest of the platform can operate without
a live cluster.
"""
from __future__ import annotations

import asyncio
import logging
import os
import yaml
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentinel for missing kubernetes package
# ---------------------------------------------------------------------------
_K8S_AVAILABLE = False
_k8s_client_module: Any = None
_k8s_config_module: Any = None

try:
    from kubernetes import client as _k8s_client_module  # type: ignore[no-redef]
    from kubernetes import config as _k8s_config_module  # type: ignore[no-redef]
    from kubernetes.client.rest import ApiException  # type: ignore[import-untyped]

    _K8S_AVAILABLE = True
except ImportError:  # pragma: no cover
    # Create a stand-in so type-checkers and runtime both work.

    class ApiException(Exception):  # type: ignore[no-redef]
        """Stub raised when kubernetes is absent."""

        def __init__(self, status: int = 0, reason: str = "") -> None:
            self.status = status
            self.reason = reason
            super().__init__(reason)


# ===================================================================
# K8sClient
# ===================================================================

class K8sClient:
    """Lightweight async Kubernetes API client for admin operations.

    Uses the official ``kubernetes`` Python package when available.
    All underlying synchronous API calls are executed inside
    ``asyncio.to_thread`` to keep the async event loop responsive.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._available: bool = False
        self._in_cluster: bool = False
        self._init_client()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        """Load kubeconfig or in-cluster config.  Never raises."""
        if not _K8S_AVAILABLE:
            logger.warning(
                "kubernetes package not installed -- "
                "K8sClient will return empty/fallback results"
            )
            return

        try:
            sa_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
            if os.path.exists(sa_token_path):
                _k8s_config_module.load_incluster_config()
                self._in_cluster = True
            else:
                _k8s_config_module.load_kube_config()
                self._in_cluster = False

            self._client = _k8s_client_module
            self._available = True
            logger.info(
                "k8s_client_initialized",
                extra={"in_cluster": self._in_cluster},
            )
        except Exception as exc:
            logger.warning(
                "k8s_client_unavailable",
                extra={"error": str(exc)},
            )
            self._available = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the kubernetes API is reachable."""
        return self._available

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Return cluster health summary.

        Queries all nodes and reports readiness.  Returns a descriptive
        dict even when the cluster is unreachable.
        """
        if not self._available:
            return {
                "status": "unavailable",
                "message": "Kubernetes client not configured or package not installed",
            }
        try:
            nodes = await self.list_nodes()
            ready_count = sum(1 for n in nodes if n.get("ready") == "True")
            total = len(nodes)
            status = "healthy" if ready_count == total else "degraded"
            return {
                "status": status,
                "total_nodes": total,
                "ready_nodes": ready_count,
                "nodes": nodes,
            }
        except Exception as exc:
            logger.error("k8s_health_check_failed", extra={"error": str(exc)})
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    # Namespace operations
    # ------------------------------------------------------------------

    async def list_namespaces(self) -> list[dict[str, Any]]:
        """Return all namespaces in the cluster."""
        if not self._available:
            return []

        def _call() -> list[dict[str, Any]]:
            v1 = self._client.CoreV1Api()
            ns_list = v1.list_namespace()
            return [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created_at": (
                        ns.metadata.creation_timestamp.isoformat()
                        if ns.metadata.creation_timestamp
                        else None
                    ),
                    "labels": dict(ns.metadata.labels or {}),
                }
                for ns in ns_list.items
            ]

        try:
            return await asyncio.to_thread(_call)
        except ApiException as exc:
            logger.error("k8s_list_namespaces_failed", extra={"status": exc.status, "reason": exc.reason})
            return []
        except Exception as exc:
            logger.error("k8s_list_namespaces_failed", extra={"error": str(exc)})
            return []

    # ------------------------------------------------------------------
    # Pod operations
    # ------------------------------------------------------------------

    async def list_pods(self, namespace: str = "default") -> list[dict[str, Any]]:
        """List pods in *namespace*."""
        if not self._available:
            return []

        def _call() -> list[dict[str, Any]]:
            v1 = self._client.CoreV1Api()
            pod_list = v1.list_namespaced_pod(namespace=namespace)
            results: list[dict[str, Any]] = []
            for pod in pod_list.items:
                container_statuses = pod.status.container_statuses or []
                containers = []
                for c in pod.spec.containers:
                    ready = any(
                        cs.name == c.name and cs.ready for cs in container_statuses
                    )
                    containers.append(
                        {
                            "name": c.name,
                            "image": c.image,
                            "ready": ready,
                        }
                    )
                results.append(
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "node": pod.spec.node_name,
                        "ip": pod.status.pod_ip,
                        "containers": containers,
                        "created_at": (
                            pod.metadata.creation_timestamp.isoformat()
                            if pod.metadata.creation_timestamp
                            else None
                        ),
                    }
                )
            return results

        try:
            return await asyncio.to_thread(_call)
        except ApiException as exc:
            logger.error("k8s_list_pods_failed", extra={"namespace": namespace, "status": exc.status})
            return []
        except Exception as exc:
            logger.error("k8s_list_pods_failed", extra={"error": str(exc)})
            return []

    # ------------------------------------------------------------------
    # Deployment operations
    # ------------------------------------------------------------------

    async def list_deployments(self, namespace: str = "default") -> list[dict[str, Any]]:
        """List deployments in *namespace*."""
        if not self._available:
            return []

        def _call() -> list[dict[str, Any]]:
            apps = self._client.AppsV1Api()
            dep_list = apps.list_namespaced_deployment(namespace=namespace)
            return [
                {
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "replicas": dep.spec.replicas,
                    "ready_replicas": dep.status.ready_replicas or 0,
                    "available_replicas": dep.status.available_replicas or 0,
                    "unavailable_replicas": dep.status.unavailable_replicas or 0,
                    "strategy": (
                        dep.spec.strategy.type if dep.spec.strategy else "Unknown"
                    ),
                    "images": [
                        c.image for c in dep.spec.template.spec.containers
                    ],
                    "conditions": [
                        {
                            "type": cond.type,
                            "status": cond.status,
                            "reason": cond.reason,
                            "message": cond.message,
                        }
                        for cond in (dep.status.conditions or [])
                    ],
                    "created_at": (
                        dep.metadata.creation_timestamp.isoformat()
                        if dep.metadata.creation_timestamp
                        else None
                    ),
                }
                for dep in dep_list.items
            ]

        try:
            return await asyncio.to_thread(_call)
        except ApiException as exc:
            logger.error("k8s_list_deployments_failed", extra={"namespace": namespace, "status": exc.status})
            return []
        except Exception as exc:
            logger.error("k8s_list_deployments_failed", extra={"error": str(exc)})
            return []

    async def get_deployment_status(
        self, name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """Return detailed status for a single deployment."""
        if not self._available:
            return {"error": "Kubernetes client not available"}

        def _call() -> dict[str, Any]:
            apps = self._client.AppsV1Api()
            dep = apps.read_namespaced_deployment(name=name, namespace=namespace)
            conditions = [
                {
                    "type": cond.type,
                    "status": cond.status,
                    "reason": cond.reason,
                    "message": cond.message,
                    "last_transition": (
                        cond.last_transition_time.isoformat()
                        if cond.last_transition_time
                        else None
                    ),
                }
                for cond in (dep.status.conditions or [])
            ]
            return {
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "ready_replicas": dep.status.ready_replicas or 0,
                "available_replicas": dep.status.available_replicas or 0,
                "unavailable_replicas": dep.status.unavailable_replicas or 0,
                "updated_replicas": dep.status.updated_replicas or 0,
                "strategy": (
                    dep.spec.strategy.type if dep.spec.strategy else "Unknown"
                ),
                "images": [
                    c.image for c in dep.spec.template.spec.containers
                ],
                "conditions": conditions,
                "observed_generation": dep.status.observed_generation,
                "created_at": (
                    dep.metadata.creation_timestamp.isoformat()
                    if dep.metadata.creation_timestamp
                    else None
                ),
            }

        try:
            return await asyncio.to_thread(_call)
        except ApiException as exc:
            logger.error(
                "k8s_get_deployment_status_failed",
                extra={"resource_name": name, "namespace": namespace, "status": exc.status},
            )
            return {"error": f"API error {exc.status}: {exc.reason}"}
        except Exception as exc:
            logger.error("k8s_get_deployment_status_failed", extra={"error": str(exc)})
            return {"error": str(exc)}

    async def scale_deployment(
        self, name: str, replicas: int, namespace: str = "default"
    ) -> dict[str, Any]:
        """Scale a deployment to *replicas* replicas."""
        if not self._available:
            return {"error": "Kubernetes client not available"}

        if replicas < 0:
            return {"error": "Replica count must be non-negative"}

        def _call() -> dict[str, Any]:
            apps = self._client.AppsV1Api()
            body = {"spec": {"replicas": replicas}}
            result = apps.patch_namespaced_deployment_scale(
                name=name, namespace=namespace, body=body,
            )
            return {
                "name": name,
                "namespace": namespace,
                "replicas": result.spec.replicas,
                "status": "scaled",
            }

        try:
            resp = await asyncio.to_thread(_call)
            logger.info(
                "deployment_scaled",
                extra={"resource_name": name, "namespace": namespace, "replicas": replicas},
            )
            return resp
        except ApiException as exc:
            logger.error(
                "k8s_scale_deployment_failed",
                extra={"resource_name": name, "namespace": namespace, "status": exc.status},
            )
            return {"error": f"API error {exc.status}: {exc.reason}"}
        except Exception as exc:
            logger.error("k8s_scale_deployment_failed", extra={"error": str(exc)})
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Manifest operations
    # ------------------------------------------------------------------

    async def apply_manifest(
        self, manifest: str | dict[str, Any], namespace: str = "default"
    ) -> dict[str, Any]:
        """Apply a Kubernetes manifest (YAML string or parsed dict).

        Supports ``Deployment``, ``Service``, ``ConfigMap``, ``Namespace``,
        and ``Pod`` kinds.  Returns the API server response summary or an
        error dict.
        """
        if not self._available:
            return {"error": "Kubernetes client not available"}

        # Parse YAML string into dict if needed
        if isinstance(manifest, str):
            try:
                manifest = yaml.safe_load(manifest)
            except yaml.YAMLError as exc:
                return {"error": f"Invalid YAML: {exc}"}

        if not isinstance(manifest, dict):
            return {"error": "Manifest must be a YAML string or dict"}

        kind = manifest.get("kind", "")
        metadata = manifest.get("metadata", {})
        resource_name = metadata.get("name", "unknown")
        resource_namespace = metadata.get("namespace", namespace)

        def _apply() -> dict[str, Any]:
            if kind == "Deployment":
                api = self._client.AppsV1Api()
                try:
                    result = api.create_namespaced_deployment(
                        namespace=resource_namespace, body=manifest,
                    )
                    return {
                        "action": "created",
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": result.metadata.namespace,
                    }
                except ApiException as exc:
                    if exc.status == 409:
                        result = api.patch_namespaced_deployment(
                            name=resource_name,
                            namespace=resource_namespace,
                            body=manifest,
                        )
                        return {
                            "action": "patched",
                            "kind": kind,
                            "name": result.metadata.name,
                            "namespace": result.metadata.namespace,
                        }
                    raise

            elif kind == "Service":
                api = self._client.CoreV1Api()
                try:
                    result = api.create_namespaced_service(
                        namespace=resource_namespace, body=manifest,
                    )
                    return {
                        "action": "created",
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": result.metadata.namespace,
                    }
                except ApiException as exc:
                    if exc.status == 409:
                        result = api.patch_namespaced_service(
                            name=resource_name,
                            namespace=resource_namespace,
                            body=manifest,
                        )
                        return {
                            "action": "patched",
                            "kind": kind,
                            "name": result.metadata.name,
                            "namespace": result.metadata.namespace,
                        }
                    raise

            elif kind == "ConfigMap":
                api = self._client.CoreV1Api()
                try:
                    result = api.create_namespaced_config_map(
                        namespace=resource_namespace, body=manifest,
                    )
                    return {
                        "action": "created",
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": result.metadata.namespace,
                    }
                except ApiException as exc:
                    if exc.status == 409:
                        result = api.patch_namespaced_config_map(
                            name=resource_name,
                            namespace=resource_namespace,
                            body=manifest,
                        )
                        return {
                            "action": "patched",
                            "kind": kind,
                            "name": result.metadata.name,
                            "namespace": result.metadata.namespace,
                        }
                    raise

            elif kind == "Namespace":
                api = self._client.CoreV1Api()
                try:
                    result = api.create_namespace(body=manifest)
                    return {
                        "action": "created",
                        "kind": kind,
                        "name": result.metadata.name,
                    }
                except ApiException as exc:
                    if exc.status == 409:
                        result = api.patch_namespace(
                            name=resource_name, body=manifest,
                        )
                        return {
                            "action": "patched",
                            "kind": kind,
                            "name": result.metadata.name,
                        }
                    raise

            elif kind == "Pod":
                api = self._client.CoreV1Api()
                try:
                    result = api.create_namespaced_pod(
                        namespace=resource_namespace, body=manifest,
                    )
                    return {
                        "action": "created",
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": result.metadata.namespace,
                    }
                except ApiException as exc:
                    if exc.status == 409:
                        # Pods cannot be patched in place; report conflict.
                        return {
                            "action": "conflict",
                            "kind": kind,
                            "name": resource_name,
                            "namespace": resource_namespace,
                            "message": "Pod already exists. Delete first to re-create.",
                        }
                    raise

            else:
                return {
                    "error": f"Unsupported resource kind: {kind!r}. "
                    "Supported kinds: Deployment, Service, ConfigMap, Namespace, Pod."
                }

        try:
            resp = await asyncio.to_thread(_apply)
            logger.info(
                "manifest_applied",
                extra={
                    "kind": kind,
                    "name": resource_name,
                    "action": resp.get("action", "unknown"),
                },
            )
            return resp
        except ApiException as exc:
            logger.error(
                "k8s_apply_manifest_failed",
                extra={"kind": kind, "resource_name": resource_name, "status": exc.status},
            )
            return {"error": f"API error {exc.status}: {exc.reason}"}
        except Exception as exc:
            logger.error("k8s_apply_manifest_failed", extra={"error": str(exc)})
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Internal helpers (used by health_check)
    # ------------------------------------------------------------------

    async def list_nodes(self) -> list[dict[str, Any]]:
        """List cluster nodes with readiness information."""
        if not self._available:
            return []

        def _call() -> list[dict[str, Any]]:
            v1 = self._client.CoreV1Api()
            node_list = v1.list_node()
            results: list[dict[str, Any]] = []
            for node in node_list.items:
                conditions = {
                    c.type: c.status for c in (node.status.conditions or [])
                }
                info = node.status.node_info
                results.append(
                    {
                        "name": node.metadata.name,
                        "ready": conditions.get("Ready", "Unknown"),
                        "os": info.os_image if info else "Unknown",
                        "kubelet_version": info.kubelet_version if info else "Unknown",
                        "cpu_capacity": (
                            node.status.capacity.get("cpu", "0")
                            if node.status.capacity
                            else "0"
                        ),
                        "memory_capacity": (
                            node.status.capacity.get("memory", "0")
                            if node.status.capacity
                            else "0"
                        ),
                    }
                )
            return results

        try:
            return await asyncio.to_thread(_call)
        except Exception as exc:
            logger.error("k8s_list_nodes_failed", extra={"error": str(exc)})
            return []


__all__ = ["K8sClient"]
